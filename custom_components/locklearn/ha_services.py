"""Home Assistant service/action boundary for LockLearn V1."""

from __future__ import annotations

from uuid import uuid4

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import DATA_RUNTIME, DOMAIN
from .core.acl import ProfileAccessDenied, ProfilePermission
from .core.scheduler import SchedulerValidationError
from .core.security import (
    ActionForbiddenError,
    ActionKind,
    ActorKind,
    async_authorize_and_audit,
)
from .core.session_selection import SessionSelectionError
from .core.sessions import SessionQuestion, SessionValidationError
from .core.tracks import TrackValidationError
from .runtime import LockLearnRuntime

SERVICE_START_SESSION = "start_session"
SERVICE_SEND_NOW = "send_now"
SERVICE_SNOOZE = "snooze"
SERVICE_PAUSE_TRACK = "pause_track"
SERVICE_RESUME_TRACK = "resume_track"

_PROFILE = vol.Required("profile_id")
_TRACK = vol.Optional("track_id")


def _runtime(hass: HomeAssistant) -> LockLearnRuntime:
    runtime = hass.data.get(DOMAIN, {}).get(DATA_RUNTIME)
    if not isinstance(runtime, LockLearnRuntime):
        raise HomeAssistantError("LockLearn is not loaded")
    return runtime


async def _authorize(
    runtime: LockLearnRuntime,
    call: ServiceCall,
    *,
    profile_id: str,
    action: ActionKind,
    permission: ProfilePermission,
) -> ActorKind:
    profile = await runtime.storage.repositories.profiles.async_get(profile_id)
    if profile is None:
        raise HomeAssistantError("Profile not found")
    settings = dict(profile.get("settings") or {})
    try:
        actor = await async_authorize_and_audit(
            runtime.storage,
            user_id=call.context.user_id,
            profile_id=profile_id,
            allow_unattended_actions=bool(settings.get("allow_unattended_actions", False)),
            action=action,
        )
    except ActionForbiddenError as err:
        raise HomeAssistantError("LockLearn action is not authorized unattended") from err

    if actor.kind is ActorKind.HA_USER:
        assert actor.user_id is not None
        try:
            await runtime.acl.async_require(
                profile_id=profile_id,
                ha_user_id=actor.user_id,
                permission=permission,
            )
        except ProfileAccessDenied as err:
            raise HomeAssistantError("Profile access denied") from err
    return actor.kind


async def _start_session(hass: HomeAssistant, call: ServiceCall) -> None:
    runtime = _runtime(hass)
    profile_id = str(call.data["profile_id"])
    await _authorize(
        runtime,
        call,
        profile_id=profile_id,
        action=ActionKind.START_SESSION,
        permission=ProfilePermission.ANSWER,
    )
    track_id_raw = call.data.get("track_id")
    track_id = None if track_id_raw is None else str(track_id_raw)
    settings = dict(call.data.get("settings") or {})
    session_type = str(call.data.get("session_type", "learn"))
    strategy = str(call.data.get("strategy", "default"))
    try:
        prepared_questions: tuple[SessionQuestion, ...] = ()
        if track_id is not None:
            track = await runtime.storage.repositories.tracks.async_get(track_id)
            if track is None or str(track["profile_id"]) != profile_id:
                raise HomeAssistantError("Track not found")
            selected = await runtime.session_selection.async_prepare(
                profile_id=profile_id,
                track_id=track_id,
                session_type=session_type,
                settings=settings,
            )
            prepared_questions = tuple(
                SessionQuestion(
                    question_id=f"q-{position + 1}-{candidate.card_key}",
                    card_key=candidate.card_key,
                    learning_item_id=candidate.learning_item_id,
                    prompt_facet_id=candidate.prompt_facet_id,
                    answer_facet_id=candidate.answer_facet_id,
                    payload=dict(candidate.payload),
                )
                for position, candidate in enumerate(selected)
            )
        else:
            runtime.session_selection.validate_session_settings(settings)
        await runtime.sessions.async_start(
            profile_id,
            track_id,
            session_type=session_type,
            strategy=strategy,
            settings=settings,
            questions=prepared_questions,
        )
    except (SessionSelectionError, SessionValidationError) as err:
        raise HomeAssistantError(str(err)) from err


async def _send_now(hass: HomeAssistant, call: ServiceCall) -> None:
    runtime = _runtime(hass)
    profile_id = str(call.data["profile_id"])
    await _authorize(
        runtime,
        call,
        profile_id=profile_id,
        action=ActionKind.SEND_NOW,
        permission=ProfilePermission.ANSWER,
    )
    track_id_raw = call.data.get("track_id")
    target_id_raw = call.data.get("target_id")
    try:
        slot = await runtime.scheduler.async_trigger_routine(
            profile_id=profile_id,
            routine_type="manual_send_now",
            track_id=None if track_id_raw is None else str(track_id_raw),
            target_id=None if target_id_raw is None else str(target_id_raw),
        )
        decision = await runtime.scheduler.async_prepare_delivery(str(slot["slot_id"]))
        if not bool(decision["ready"]):
            raise HomeAssistantError(f"Immediate notification is not ready: {decision['reason']}")
    except SchedulerValidationError as err:
        raise HomeAssistantError(str(err)) from err


async def _snooze(hass: HomeAssistant, call: ServiceCall) -> None:
    runtime = _runtime(hass)
    profile_id = str(call.data["profile_id"])
    await _authorize(
        runtime,
        call,
        profile_id=profile_id,
        action=ActionKind.SNOOZE,
        permission=ProfilePermission.ANSWER,
    )
    try:
        await runtime.scheduler.async_snooze_slot(
            profile_id=profile_id,
            slot_id=str(call.data["slot_id"]),
            minutes=int(call.data.get("minutes", 15)),
        )
    except SchedulerValidationError as err:
        raise HomeAssistantError(str(err)) from err


async def _set_track_status(
    hass: HomeAssistant,
    call: ServiceCall,
    *,
    status: str,
    action: ActionKind,
    event_type: str,
) -> None:
    runtime = _runtime(hass)
    profile_id = str(call.data["profile_id"])
    await _authorize(
        runtime,
        call,
        profile_id=profile_id,
        action=action,
        permission=ProfilePermission.EDIT_TRACK,
    )
    track_id = str(call.data["track_id"])
    track = await runtime.storage.repositories.tracks.async_get(track_id)
    if track is None or str(track["profile_id"]) != profile_id:
        raise HomeAssistantError("Track not found")
    try:
        await runtime.tracks.async_update_track(
            track_id=track_id,
            status=status,
        )
    except TrackValidationError as err:
        raise HomeAssistantError(str(err)) from err
    hass.bus.async_fire(
        event_type,
        {
            "event_id": str(uuid4()),
            "profile_id": profile_id,
            "track_id": track_id,
            "status": status,
        },
    )


async def _pause_track(hass: HomeAssistant, call: ServiceCall) -> None:
    await _set_track_status(
        hass,
        call,
        status="paused",
        action=ActionKind.PAUSE_TRACK,
        event_type="locklearn_track_paused",
    )


async def _resume_track(hass: HomeAssistant, call: ServiceCall) -> None:
    await _set_track_status(
        hass,
        call,
        status="active",
        action=ActionKind.RESUME_TRACK,
        event_type="locklearn_track_resumed",
    )


def async_register_services(hass: HomeAssistant) -> None:
    """Register the V1 service surface for the loaded singleton runtime."""

    async def handle_start_session(call: ServiceCall) -> None:
        await _start_session(hass, call)

    async def handle_send_now(call: ServiceCall) -> None:
        await _send_now(hass, call)

    async def handle_snooze(call: ServiceCall) -> None:
        await _snooze(hass, call)

    async def handle_pause_track(call: ServiceCall) -> None:
        await _pause_track(hass, call)

    async def handle_resume_track(call: ServiceCall) -> None:
        await _resume_track(hass, call)

    hass.services.async_register(
        DOMAIN,
        SERVICE_START_SESSION,
        handle_start_session,
        schema=vol.Schema(
            {
                _PROFILE: cv.string,
                _TRACK: cv.string,
                vol.Optional("session_type", default="learn"): cv.string,
                vol.Optional("strategy", default="default"): cv.string,
                vol.Optional("settings", default={}): dict,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_NOW,
        handle_send_now,
        schema=vol.Schema(
            {
                _PROFILE: cv.string,
                _TRACK: cv.string,
                vol.Optional("target_id"): cv.string,
            }
        ),
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_SNOOZE,
        handle_snooze,
        schema=vol.Schema(
            {
                _PROFILE: cv.string,
                vol.Required("slot_id"): cv.string,
                vol.Optional("minutes", default=15): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=1, max=1440),
                ),
            }
        ),
    )
    track_schema = vol.Schema(
        {
            _PROFILE: cv.string,
            vol.Required("track_id"): cv.string,
        }
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_PAUSE_TRACK,
        handle_pause_track,
        schema=track_schema,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RESUME_TRACK,
        handle_resume_track,
        schema=track_schema,
    )


def async_unregister_services(hass: HomeAssistant) -> None:
    """Remove every LockLearn service on Config Entry unload."""
    for service in (
        SERVICE_START_SESSION,
        SERVICE_SEND_NOW,
        SERVICE_SNOOZE,
        SERVICE_PAUSE_TRACK,
        SERVICE_RESUME_TRACK,
    ):
        hass.services.async_remove(DOMAIN, service)
