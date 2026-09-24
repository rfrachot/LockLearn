"""Notification capability and target primitives."""

from .capabilities import (
    Capability,
    LearningNotificationMode,
    LearningSignal,
    TargetCapabilities,
    classify_learning_signal,
)
from .delivery import NotificationDeliveryError, NotificationDeliveryService
from .interactions import (
    NotificationActionDisposition,
    NotificationActionResult,
    NotificationInteractionService,
    NotificationInteractionValidationError,
    NotificationStage,
)
from .renderers import (
    NotificationRenderer,
    NotificationRenderMode,
    QuizOption,
    RenderedNotification,
    decode_action_id,
    effective_lockscreen_visibility,
    encode_action_id,
)
from .targets import NotifyRoute, TargetUnavailableError, async_resolve_notify_route
from .warnings import NotificationWarningService

__all__ = [
    "Capability",
    "LearningNotificationMode",
    "LearningSignal",
    "NotificationActionDisposition",
    "NotificationActionResult",
    "NotificationDeliveryError",
    "NotificationDeliveryService",
    "NotificationInteractionService",
    "NotificationInteractionValidationError",
    "NotificationRenderMode",
    "NotificationRenderer",
    "NotificationStage",
    "NotificationWarningService",
    "NotifyRoute",
    "QuizOption",
    "RenderedNotification",
    "TargetCapabilities",
    "TargetUnavailableError",
    "async_resolve_notify_route",
    "classify_learning_signal",
    "decode_action_id",
    "effective_lockscreen_visibility",
    "encode_action_id",
]
