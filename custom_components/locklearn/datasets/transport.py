"""Home Assistant network transport for bounded dataset discovery/downloads."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import uuid
from pathlib import Path
from aiohttp import ClientError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .manager import DatasetDiscoveryError, DatasetInstallError

_STREAM_CHUNK_SIZE = 1024 * 1024


class HomeAssistantDatasetTransport:
    """Perform bounded HTTPS GETs using Home Assistant's shared aiohttp session."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._session = async_get_clientsession(hass)

    async def async_get_json(self, url: str, *, maximum_bytes: int) -> object:
        """Fetch bounded UTF-8 JSON without trusting remote size declarations."""
        try:
            async with self._session.get(url) as response:
                response.raise_for_status()
                declared = response.content_length
                if declared is not None and declared > maximum_bytes:
                    raise DatasetDiscoveryError("dataset catalog exceeds maximum size")
                data = bytearray()
                async for chunk in response.content.iter_chunked(_STREAM_CHUNK_SIZE):
                    data.extend(chunk)
                    if len(data) > maximum_bytes:
                        raise DatasetDiscoveryError("dataset catalog exceeds maximum size")
        except ClientError as err:
            raise DatasetDiscoveryError("cannot fetch dataset release catalog") from err
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
                async with self._session.get(url) as response:
                    response.raise_for_status()
                    declared = response.content_length
                    if declared is not None and declared > maximum_bytes:
                        raise DatasetInstallError("dataset artifact exceeds maximum size")
                    async for chunk in response.content.iter_chunked(_STREAM_CHUNK_SIZE):
                        size += len(chunk)
                        if size > maximum_bytes:
                            raise DatasetInstallError("dataset artifact exceeds maximum size")
                        digest.update(chunk)
                        await asyncio.to_thread(_append_chunk, temporary, chunk)
            except ClientError as err:
                raise DatasetInstallError("cannot download dataset artifact") from err
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
