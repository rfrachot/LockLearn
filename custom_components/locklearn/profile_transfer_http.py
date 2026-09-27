"""Authenticated private HTTP transfer routes for profile export/import."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

from aiohttp import web
from homeassistant.components.http import KEY_HASS, KEY_HASS_USER, HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DATA_RUNTIME, DOMAIN
from .profile_transfer import ProfileTransferError, _MAX_ARCHIVE_BYTES
from .runtime import LockLearnRuntime


def _runtime_from_request(request: web.Request) -> LockLearnRuntime:
    hass: HomeAssistant = request.app[KEY_HASS]
    runtime = hass.data.get(DOMAIN, {}).get(DATA_RUNTIME)
    if not isinstance(runtime, LockLearnRuntime):
        raise web.HTTPServiceUnavailable(text="LockLearn runtime is unavailable")
    return runtime


def _authenticated_user_id(request: web.Request) -> str:
    user: Any = request.get(KEY_HASS_USER)
    if user is None or not getattr(user, "id", None):
        raise web.HTTPUnauthorized
    return str(user.id)


async def _read_limited_body(request: web.Request) -> bytes:
    if request.content_length is not None and request.content_length > _MAX_ARCHIVE_BYTES:
        raise web.HTTPRequestEntityTooLarge(
            max_size=_MAX_ARCHIVE_BYTES,
            actual_size=request.content_length,
        )
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await request.content.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > _MAX_ARCHIVE_BYTES:
            raise web.HTTPRequestEntityTooLarge(
                max_size=_MAX_ARCHIVE_BYTES,
                actual_size=total,
            )
        chunks.append(chunk)
    if not chunks:
        raise web.HTTPBadRequest(text="Profile import archive is empty")
    return b"".join(chunks)


class ProfileExportDownloadView(HomeAssistantView):
    """Serve one owner-bound export exactly once."""

    url = "/api/locklearn/profile-export/{token}"
    name = "api:locklearn:profile-export"

    async def get(self, request: web.Request, token: str) -> web.Response:
        runtime = _runtime_from_request(request)
        user_id = _authenticated_user_id(request)
        consumed = await runtime.profile_transfers.store.async_consume_export(
            token,
            user_id,
        )
        if consumed is None:
            raise web.HTTPNotFound(text="Export is unavailable or expired")
        record, data = consumed
        return web.Response(
            body=data,
            content_type="application/zip",
            headers={
                "Cache-Control": "no-store, max-age=0",
                "Content-Disposition": f'attachment; filename="{record.filename}"',
                "X-Content-Type-Options": "nosniff",
            },
        )


class ProfileImportUploadView(HomeAssistantView):
    """Accept one bounded authenticated ZIP upload into private temporary storage."""

    url = "/api/locklearn/profile-import"
    name = "api:locklearn:profile-import"

    async def post(self, request: web.Request) -> web.Response:
        runtime = _runtime_from_request(request)
        user_id = _authenticated_user_id(request)
        archive = await _read_limited_body(request)
        try:
            record = await runtime.profile_transfers.store.async_store_import(
                owner_user_id=user_id,
                archive_bytes=archive,
            )
        except ProfileTransferError as err:
            return self.json_message(
                str(err),
                status_code=HTTPStatus.BAD_REQUEST,
                message_code="invalid_profile_archive",
            )
        return self.json(
            {
                "upload_token": record.token,
                "expires_at_utc": record.expires_at.isoformat(),
            },
            status_code=HTTPStatus.CREATED,
            headers={"Cache-Control": "no-store"},
        )


def register_profile_transfer_views(hass: HomeAssistant) -> None:
    """Register process-lifetime authenticated transfer routes exactly once."""
    hass.http.register_view(ProfileExportDownloadView())
    hass.http.register_view(ProfileImportUploadView())
