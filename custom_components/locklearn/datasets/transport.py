"""Home Assistant network transport for bounded dataset discovery/downloads."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from ipaddress import ip_address
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from aiohttp import ClientError, ClientResponse
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .manager import DatasetDiscoveryError, DatasetInstallError

_STREAM_CHUNK_SIZE = 1024 * 1024
_MAX_REDIRECTS = 3
_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})


class DatasetURLPolicyError(ValueError):
    """A URL or redirect destination violates the trusted dataset network boundary."""


def _validate_https_endpoint(url: str, allowed_hosts: frozenset[str]) -> None:
    """Fail closed before every network request, including each redirect hop."""
    try:
        parsed = urlsplit(url)
        host = parsed.hostname
        port = parsed.port
    except ValueError as err:
        raise DatasetURLPolicyError("dataset URL has an invalid authority") from err
    if (
        parsed.scheme != "https"
        or host is None
        or port not in (None, 443)
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or host != host.lower()
        or host not in allowed_hosts
    ):
        raise DatasetURLPolicyError("dataset URL is outside the HTTPS host allowlist")
    try:
        ip_address(host)
    except ValueError:
        pass
    else:
        raise DatasetURLPolicyError("dataset URL must use a trusted hostname, not an IP address")
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        raise DatasetURLPolicyError("dataset URL must not target a local hostname")



class HomeAssistantDatasetTransport:
    """Perform bounded HTTPS GETs using Home Assistant's shared aiohttp session."""

    def __init__(self, hass: HomeAssistant, *, allowed_hosts: frozenset[str]) -> None:
        self._session = async_get_clientsession(hass)
        self._allowed_hosts = frozenset(allowed_hosts)

    @asynccontextmanager
    async def _bounded_get(self, url: str) -> AsyncIterator[ClientResponse]:
        """Follow only bounded, individually validated HTTPS redirects."""
        current_url = url
        for hop in range(_MAX_REDIRECTS + 1):
            _validate_https_endpoint(current_url, self._allowed_hosts)
            async with self._session.get(current_url, allow_redirects=False) as response:
                if response.status in _REDIRECT_STATUSES:
                    location = response.headers.get("Location")
                    if not location or hop == _MAX_REDIRECTS:
                        raise DatasetURLPolicyError("dataset redirect is missing or exceeds limit")
                    current_url = urljoin(current_url, location)
                    continue
                response.raise_for_status()
                yield response
                return
        raise DatasetURLPolicyError("dataset redirect exceeds limit")

    async def async_get_json(self, url: str, *, maximum_bytes: int) -> object:
        """Fetch bounded UTF-8 JSON without trusting remote size declarations."""
        try:
            async with self._bounded_get(url) as response:
                declared = response.content_length
                if declared is not None and declared > maximum_bytes:
                    raise DatasetDiscoveryError("dataset catalog exceeds maximum size")
                data = bytearray()
                async for chunk in response.content.iter_chunked(_STREAM_CHUNK_SIZE):
                    data.extend(chunk)
                    if len(data) > maximum_bytes:
                        raise DatasetDiscoveryError("dataset catalog exceeds maximum size")
        except (ClientError, DatasetURLPolicyError) as err:
            raise DatasetDiscoveryError("cannot fetch dataset release catalog safely") from err
        try:
            return json.loads(bytes(data).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as err:
            raise DatasetDiscoveryError("dataset release catalog is not valid UTF-8 JSON") from err

    async def async_download(
        self,
        url: str,
        destination: Path,
        *,
        maximum_bytes: int,
    ) -> str:
        """Stream a bounded artifact to disk atomically without loop-blocking writes."""
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.part")
        digest = hashlib.sha256()
        size = 0
        try:
            await asyncio.to_thread(_truncate_file, temporary)
            try:
                async with self._bounded_get(url) as response:
                    declared = response.content_length
                    if declared is not None and declared > maximum_bytes:
                        raise DatasetInstallError("dataset artifact exceeds maximum size")
                    async for chunk in response.content.iter_chunked(_STREAM_CHUNK_SIZE):
                        size += len(chunk)
                        if size > maximum_bytes:
                            raise DatasetInstallError("dataset artifact exceeds maximum size")
                        digest.update(chunk)
                        await asyncio.to_thread(_append_chunk, temporary, chunk)
            except (ClientError, DatasetURLPolicyError) as err:
                raise DatasetInstallError("cannot download dataset artifact safely") from err
            await asyncio.to_thread(_finalize_download, temporary, destination)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
        return digest.hexdigest()


def _truncate_file(path: Path) -> None:
    with path.open("wb"):
        pass


def _append_chunk(path: Path, chunk: bytes) -> None:
    with path.open("ab") as stream:
        stream.write(chunk)


def _finalize_download(temporary: Path, destination: Path) -> None:
    with temporary.open("rb") as stream:
        os.fsync(stream.fileno())
    os.replace(temporary, destination)
    _fsync_directory(destination.parent)


def _fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
