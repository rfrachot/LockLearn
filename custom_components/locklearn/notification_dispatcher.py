"""Home Assistant dispatcher for materialized LockLearn notification slots."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later

from .core.learning import LearningStateMachine
from .notifications.capabilities import TargetCapabilities
from .notifications.delivery import NotificationDeliveryError
from .notifications.interactions import NotificationStage
from .notifications.renderers import (
    PANEL_URI,
    NotificationRenderMode,
    NotificationRenderer,
    RenderedNotification,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from .runtime import LockLearnRuntime

_LOGGER = logging.getLogger(__name__)
_DISPATCH_GRACE = timedelta(seconds=90)
_MAINTENANCE_INTERVAL = timedelta(minutes=5)
_INTERACTION_TTL = timedelta(minutes=30)


class NotificationSchedulerDispatcher:
    """Wake on materialized scheduler deadlines and execute the send pipeline."""

    def __init__(self, hass: HomeAssistant, runtime: LockLearnRuntime) -> None:
        self._hass = hass
        self._runtime = runtime
        self._renderer = NotificationRenderer()
        self._learning = LearningStateMachine()
        self._unsub: Callable[[], None] | None = None
        self._lock = asyncio.Lock()
        self._closed = False

    async def async_start(self) -> None:
        """Materialize today's slots, dispatch anything due, then arm the next wake."""
        self._closed = False
        await self._async_cycle(startup=True)

    def close(self) -> None:
        """Cancel the next HA timer."""
        self._closed = True
        if self._unsub is not None:
            self._unsub()
            self._unsub = None

    async def _async_cycle(self, *, startup: bool = False) -> None:
        if self._closed:
            return
        async with self._lock:
            now = datetime.now(UTC)
            if not startup:
                await self._async_dispatch_due(now)
                await self._runtime.scheduler.async_reconcile(reason="timer")
            await self._async_materialize_today()
            if startup:
                # Startup reconciliation intentionally owns genuinely missed slots.
                # Newly materialized slots are always in the future.
                await self._async_dispatch_due(datetime.now(UTC))
            await self._async_schedule_next()

    async def _async_materialize_today(self) -> None:
        for profile in await self._runtime.storage.repositories.profiles.async_list_active():
            try:
                await self._runtime.scheduler.async_generate(profile_id=str(profile["profile_id"]))
            except Exception:
                _LOGGER.exception(
                    "LockLearn scheduler materialization failed for an active profile"
                )

    async def _async_dispatch_due(self, now: datetime) -> None:
        start = (now - _DISPATCH_GRACE).isoformat()
        end = (now + timedelta(seconds=1)).isoformat()
        due: list[dict[str, Any]] = []
        for profile in await self._runtime.storage.repositories.profiles.async_list_active():
            rows = await self._runtime.storage.repositories.scheduler.async_list_slots(
                profile_id=str(profile["profile_id"]),
                start_utc=start,
                end_utc=end,
            )
            for slot in rows:
                if str(slot.get("status")) not in {"scheduled", "deferred"}:
                    continue
                due_at = self._effective_due(slot)
                if due_at is None or due_at > now or due_at < now - _DISPATCH_GRACE:
                    continue
                due.append(slot)

        due.sort(key=lambda slot: (self._effective_due(slot) or now, str(slot["slot_id"])))
        for slot in due:
            try:
                await self._async_dispatch_slot(slot)
            except Exception:
                # Leave the slot pending inside the short grace window so the next
                # wake can retry. Reconciliation will eventually expire it as missed.
                _LOGGER.exception("LockLearn scheduled notification dispatch failed")

    async def _async_dispatch_slot(self, slot: dict[str, Any]) -> None:
        slot_id = str(slot["slot_id"])
        decision = await self._runtime.scheduler.async_prepare_delivery(slot_id)
        if not bool(decision.get("ready")):
            return

        fresh = await self._runtime.storage.repositories.scheduler.async_get_slot(slot_id)
        if fresh is None or str(fresh.get("status")) not in {"scheduled", "deferred"}:
            return
        profile_id = str(fresh["profile_id"])
        track_id = fresh.get("track_id")
        target_id = fresh.get("target_id")
        card_key = fresh.get("card_key")
        if not all(isinstance(value, str) and value for value in (track_id, target_id, card_key)):
            await self._runtime.storage.repositories.scheduler.async_expire_slot(
                slot_id=slot_id,
                reason="no_candidate",
                updated_at_utc=datetime.now(UTC).isoformat(),
            )
            return

        profile = await self._runtime.storage.repositories.profiles.async_get(profile_id)
        target = await self._runtime.storage.repositories.notification_targets.async_get(
            str(target_id)
        )
        if profile is None or target is None or not bool(target.get("enabled")):
            return

        presentation = await self._runtime.presentation.async_for_card(
            track_id=str(track_id),
            card_key=str(card_key),
        )
        prompt = self._facet_text(presentation.get("prompt"))
        answer = self._facet_text(presentation.get("answer"))
        slot_type = str(fresh.get("slot_type") or "learning")
        selection_reason = str(fresh.get("selection_reason") or "")

        if slot_type == "quiz":
            rendered = self._render_quiz_handoff(
                profile=profile,
                target=target,
                slot_id=slot_id,
                prompt=prompt,
            )
            await self._runtime.notification_delivery.async_send(rendered)
            await self._runtime.scheduler.async_record_delivery(slot_id=slot_id)
            await self._runtime.storage.repositories.scheduler.async_set_slot_status(
                slot_id,
                "consumed",
                updated_at_utc=datetime.now(UTC).isoformat(),
            )
            return

        capabilities = TargetCapabilities.from_mapping(
            device_registry_id=str(target["device_registry_id"]),
            platform=str(target["platform"]),
            shared_device=bool(target.get("shared_device")),
            values=dict(target.get("capabilities") or {}),
        )
        interaction = await self._runtime.notification_interactions.async_create(
            profile_id=profile_id,
            target_id=str(target_id),
            track_id=str(track_id),
            card_key=str(card_key),
            stage=NotificationStage.PROMPT,
            expires_at=datetime.now(UTC) + _INTERACTION_TTL,
            tag=f"locklearn-slot-{slot_id}",
            payload={
                "slot_id": slot_id,
                "kind": "learning",
                "selection_reason": selection_reason,
            },
        )
        rendered = self._renderer.render_learning_prompt(
            profile_id=profile_id,
            profile_name=str(profile.get("name") or "LockLearn"),
            target_id=str(target_id),
            tag=f"locklearn-slot-{slot_id}",
            prompt=prompt,
            answer=answer,
            token=interaction.token,
            capabilities=capabilities,
            visibility=str(target.get("lockscreen_visibility") or "private"),
            slot_type=("relearning" if selection_reason == "relearning_due" else "learning"),
        )
        try:
            await self._runtime.notification_delivery.async_send(rendered)
        except NotificationDeliveryError:
            await self._runtime.notification_interactions.async_clear_tag(
                tag=f"locklearn-slot-{slot_id}"
            )
            raise

        await self._runtime.scheduler.async_record_delivery(slot_id=slot_id)
        if rendered.mode is NotificationRenderMode.DIRECT_EXPOSURE:
            if selection_reason == "teaser_new":
                await self._async_record_direct_teaser_exposure(
                    profile_id=profile_id,
                    track_id=str(track_id),
                    card_key=str(card_key),
                    notification_id=interaction.interaction_id,
                )
            await self._runtime.notification_interactions.async_clear_tag(
                tag=f"locklearn-slot-{slot_id}"
            )
            await self._runtime.storage.repositories.scheduler.async_set_slot_status(
                slot_id,
                "consumed",
                updated_at_utc=datetime.now(UTC).isoformat(),
            )

    async def _async_record_direct_teaser_exposure(
        self,
        *,
        profile_id: str,
        track_id: str,
        card_key: str,
        notification_id: str,
    ) -> None:
        progress = self._runtime.storage.repositories.progress
        current = await progress.async_get(
            profile_id=profile_id,
            track_id=track_id,
            card_key=card_key,
        )
        if current is not None and str(current.get("state")) != "new":
            return
        card = await self._runtime.storage.repositories.tracks.async_card_reference(
            track_id=track_id,
            card_key=card_key,
        )
        if card is None:
            return
        now = datetime.now(UTC).isoformat()
        identity = {
            "profile_id": profile_id,
            "track_id": track_id,
            "card_key": card.card_key,
            "learning_item_id": card.learning_item_id,
            "prompt_facet_id": card.prompt_facet_id,
            "answer_facet_id": card.answer_facet_id,
        }
        pre = current or {
            **identity,
            "state": "new",
            "mastery": 0.0,
            "box": 0,
            "seen_count": 0,
            "verified_correct_count": 0,
            "verified_wrong_count": 0,
            "self_known_count": 0,
            "self_review_count": 0,
            "first_seen_at_utc": None,
            "last_seen_at_utc": None,
            "last_result": None,
            "next_due_at_utc": None,
            "streak_correct": 0,
            "leech_score": 0.0,
            "difficulty_factor": 1.0,
            "last_verified_at_utc": None,
            "verified_success_since_box": 0,
            "user_state": "active",
            "suspend_until_utc": None,
            "example_rotation_index": 0,
            "content_status": "active",
            "policy_version": self._runtime.review_policy.policy_version,
            "dataset_generation": self._runtime.storage.content_generations.active_metadata.generation_id,
            "normalization_version": 1,
            "updated_at_utc": now,
        }
        transition = self._learning.introduce(dict(pre))
        await self._runtime.reviews.async_record(
            profile_id=profile_id,
            track_id=track_id,
            learning_item_id=card.learning_item_id,
            prompt_facet_id=card.prompt_facet_id,
            answer_facet_id=card.answer_facet_id,
            card_key=card.card_key,
            mode="introduction",
            question_type="learning",
            result="exposure",
            signal_quality="none",
            policy_version=self._runtime.review_policy.policy_version,
            dataset_generation=str(pre["dataset_generation"]),
            normalization_version=int(pre["normalization_version"]),
            pre_state_snapshot=dict(pre),
            post_state_snapshot=transition.post_state,
            retrieval_occurred=False,
            notification_id=notification_id,
        )

    async def _async_schedule_next(self) -> None:
        if self._closed:
            return
        if self._unsub is not None:
            self._unsub()
            self._unsub = None
        now = datetime.now(UTC)
        next_due: datetime | None = None
        horizon = now + timedelta(days=2)
        for profile in await self._runtime.storage.repositories.profiles.async_list_active():
            slots = await self._runtime.storage.repositories.scheduler.async_list_slots(
                profile_id=str(profile["profile_id"]),
                start_utc=now.isoformat(),
                end_utc=horizon.isoformat(),
            )
            for slot in slots:
                if str(slot.get("status")) not in {"scheduled", "deferred"}:
                    continue
                candidate = self._effective_due(slot)
                if candidate is None or candidate < now:
                    continue
                if next_due is None or candidate < next_due:
                    next_due = candidate

        delay = _MAINTENANCE_INTERVAL.total_seconds()
        if next_due is not None:
            delay = min(delay, max(0.0, (next_due - now).total_seconds()))
        self._unsub = async_call_later(self._hass, delay, self._handle_wake)

    async def _handle_wake(self, _now: datetime) -> None:
        self._unsub = None
        try:
            await self._async_cycle()
        except Exception:
            _LOGGER.exception("LockLearn notification dispatcher cycle failed")
            if not self._closed:
                self._unsub = async_call_later(
                    self._hass,
                    _MAINTENANCE_INTERVAL.total_seconds(),
                    self._handle_wake,
                )

    @staticmethod
    def _effective_due(slot: dict[str, Any]) -> datetime | None:
        raw = (
            slot.get("deferred_until_utc")
            if str(slot.get("status")) == "deferred"
            else slot.get("scheduled_for_utc")
        )
        if not isinstance(raw, str):
            return None
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(UTC)

    @staticmethod
    def _facet_text(facet: Any) -> str:
        if not isinstance(facet, dict):
            return "LockLearn"
        blocks = facet.get("blocks")
        if not isinstance(blocks, list):
            return "LockLearn"
        for block in blocks:
            if not isinstance(block, dict):
                continue
            payload = block.get("payload")
            if isinstance(payload, dict) and isinstance(payload.get("text"), str):
                text = str(payload["text"]).strip()
                if text:
                    return text
        return "LockLearn"

    @staticmethod
    def _render_quiz_handoff(
        *,
        profile: dict[str, Any],
        target: dict[str, Any],
        slot_id: str,
        prompt: str,
    ) -> RenderedNotification:
        profile_name = str(profile.get("name") or "LockLearn")
        shared = bool(target.get("shared_device"))
        title = f"LockLearn Quiz · {profile_name}" if shared else "LockLearn Quiz"
        tag = f"locklearn-slot-{slot_id}"
        return RenderedNotification(
            profile_id=str(profile["profile_id"]),
            target_id=str(target["target_id"]),
            tag=tag,
            stage="prompt",
            mode=NotificationRenderMode.PANEL_HANDOFF,
            title=title,
            message=prompt,
            data={
                "tag": tag,
                "ttl": 1800,
                "channel": "LockLearn Quiz",
                "visibility": str(target.get("lockscreen_visibility") or "private"),
                "actions": [{"action": "URI", "title": "Ouvrir LockLearn", "uri": PANEL_URI}],
            },
            pedagogical_signal="no_result",
            panel_required=True,
        )
