"""Dataset HTTPS redirect policy: never contact a forbidden destination."""

from __future__ import annotations

import hashlib
from collections.abc import AsyncIterator
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from custom_components.locklearn.datasets.manager import (
    DatasetDiscoveryError,
    DatasetInstallError,
)
from custom_components.locklearn.datasets.transport import HomeAssistantDatasetTransport


class _Body:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    async def iter_chunked(self, chunk_size: int) -> AsyncIterator[bytes]:
        assert chunk_size > 0
        yield self.payload


class _Response:
    def __init__(
        self, status: int, *, location: str | None = None, body: bytes = b"{}"
    ) -> None:
        self.status = status
        self.headers = {} if location is None else {"Location": location}
        self.content_length: int | None = len(body)
        self.content = _Body(body)

    async def __aenter__(self) -> _Response:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    def raise_for_status(self) -> None:
        assert self.status < 400


class _Session:
    def __init__(self, responses: list[_Response]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, bool]] = []

    def get(self, url: str, *, allow_redirects: bool) -> _Response:
        self.calls.append((url, allow_redirects))
        return self.responses[len(self.calls) - 1]


def _transport(*responses: _Response) -> tuple[HomeAssistantDatasetTransport, _Session]:
    session = _Session(list(responses))
    with patch(
        "custom_components.locklearn.datasets.transport.async_get_clientsession",
        return_value=session,
    ):
        transport = HomeAssistantDatasetTransport(
            SimpleNamespace(),  # type: ignore[arg-type]
            allowed_hosts=frozenset({"catalog.example.org", "cdn.example.org"}),
        )
    return transport, session


async def test_catalog_redirect_to_allowed_host_is_explicitly_validated() -> None:
    transport, session = _transport(
        _Response(302, location="https://cdn.example.org/catalog.json"),
        _Response(200, body=b'{"schema_version":1}'),
    )
    result = await transport.async_get_json(
        "https://catalog.example.org/catalog.json", maximum_bytes=1024
    )
    assert result == {"schema_version": 1}
    assert session.calls == [
        ("https://catalog.example.org/catalog.json", False),
        ("https://cdn.example.org/catalog.json", False),
    ]


@pytest.mark.parametrize(
    "location",
    [
        "http://cdn.example.org/catalog.json",
        "https://127.0.0.1/admin",
        "https://[::1]/admin",
        "https://localhost/admin",
        "https://metadata.google.internal/computeMetadata/v1/",
        "https://evil.example.net/steal",
        "https://cdn.example.org:444/catalog",
        "https://user@cdn.example.org/catalog",
    ],
)
async def test_catalog_redirect_rejects_unsafe_destinations_without_fetch(
    location: str,
) -> None:
    transport, session = _transport(_Response(302, location=location))
    with pytest.raises(DatasetDiscoveryError, match="safely"):
        await transport.async_get_json(
            "https://catalog.example.org/catalog.json", maximum_bytes=1024
        )
    assert session.calls == [("https://catalog.example.org/catalog.json", False)]


async def test_catalog_rejects_redirect_loops_and_unapproved_initial_url() -> None:
    transport, session = _transport(
        *(_Response(302, location="/again") for _ in range(4))
    )
    with pytest.raises(DatasetDiscoveryError, match="safely"):
        await transport.async_get_json(
            "https://catalog.example.org/catalog", maximum_bytes=1024
        )
    assert len(session.calls) == 4
    other, no_requests = _transport()
    with pytest.raises(DatasetDiscoveryError, match="safely"):
        await other.async_get_json(
            "https://evil.example.net/catalog", maximum_bytes=1024
        )
    assert not no_requests.calls


async def test_artifact_redirect_rejected_and_partial_file_removed(tmp_path: Path) -> None:
    transport, session = _transport(_Response(302, location="http://127.0.0.1/private"))
    destination = tmp_path / "dataset.zip"
    with pytest.raises(DatasetInstallError, match="safely"):
        await transport.async_download(
            "https://cdn.example.org/archive.zip", destination, maximum_bytes=1024
        )
    assert not destination.exists()
    assert not tuple(tmp_path.glob("*.part"))
    assert session.calls == [("https://cdn.example.org/archive.zip", False)]


async def test_artifact_allowed_redirect_keeps_sha256(tmp_path: Path) -> None:
    payload = b"bounded-artifact"
    transport, session = _transport(
        _Response(307, location="/final.zip"),
        _Response(200, body=payload),
    )
    destination = tmp_path / "archive.zip"
    checksum = await transport.async_download(
        "https://cdn.example.org/archive.zip", destination, maximum_bytes=1024
    )
    assert checksum == hashlib.sha256(payload).hexdigest()
    assert destination.read_bytes() == payload
    assert len(session.calls) == 2
