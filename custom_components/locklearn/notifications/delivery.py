"""Home Assistant delivery boundary for rendered LockLearn notifications."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping

from homeassistant.core import HomeAssistant

from ..core.clock import Clock, SystemClock
from ..storage.repositories import NotificationTargetsRepository
from .renderers import NotificationRenderMode, RenderedNotification
from .targets import NotifyRoute, TargetUnavailableError, async_resolve_notify_route

IssueCallback = Callable[[str, str, Mapping[str, str]], Awaitable[None]]
IssueClearCallback = Callable[[str], Awaitable[None]]


class NotificationDeliveryError(RuntimeError):
    """Raised when a rendered notification cannot be delivered safely."""


class NotificationDeliveryService:
    """Resolve stable targets at send time and deliver through Home Assistant."""

    def __init__(
        self,
        hass: HomeAssistant,
        targets: NotificationTargetsRepository,
        *,
        issue_callback: IssueCallback | None = None,
        issue_clear_callback: IssueClearCallback | None = None,
        clock: Clock | None = None,
    ) -> None:
        self._hass = hass
        self._targets = targets
        self._issue_callback = issue_callback
        self._issue_clear_callback = issue_clear_callback
        self._clock = clock or SystemClock()

    @staticmethod
    def _issue_id(target_id: str) -> str:
        return f"notification_target_unavailable_{target_id}"

    async def _report_unavailable(self, target: dict[str, object]) -> None:
        if self._issue_callback is None:
            return
        target_id = str(target["target_id"])
        await self._issue_callback(
            self._issue_id(target_id),
            "notification_target_unavailable",
            {
                "target_id": target_id,
                "friendly_name": str(target.get("friendly_name") or target_id),
            },
        )

    async def async_send(self, rendered: RenderedNotification) -> NotifyRoute:
        """Deliver once; target identity remains the persisted LockLearn target_id."""
        target = await self._targets.async_get(rendered.target_id)
        if target is None:
            raise NotificationDeliveryError("notification target does not exist")
        if str(target["profile_id"]) != rendered.profile_id:
            raise NotificationDeliveryError("notification target belongs to another profile")
        if not bool(target["enabled"]):
            raise NotificationDeliveryError("notification target is disabled")

        require_platform_data = rendered.mode is not NotificationRenderMode.DIRECT_EXPOSURE
        try:
            route = await async_resolve_notify_route(
                self._hass,
                str(target["device_registry_id"]),
                require_platform_data=require_platform_data,
            )
        except TargetUnavailableError as err:
            await self._report_unavailable(target)
            raise NotificationDeliveryError("notification target route is unavailable") from err

        domain, service = route.service.split(".", 1)
        service_data = rendered.service_data()
        if not route.supports_platform_data:
            service_data.pop("data", None)

        try:
            await self._hass.services.async_call(
                domain,
                service,
                service_data,
                target=route.target,
                blocking=True,
            )
        except Exception as err:
            await self._report_unavailable(target)
            raise NotificationDeliveryError("notification delivery failed") from err

        now_utc = self._clock.now().isoformat()
        await self._targets.async_set_last_resolved_service(
            target_id=rendered.target_id,
            service=route.service,
            updated_at_utc=now_utc,
        )
        if self._issue_clear_callback is not None:
            await self._issue_clear_callback(self._issue_id(rendered.target_id))
        return route
