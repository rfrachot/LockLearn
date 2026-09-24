"""Notification capability and target primitives."""

from .capabilities import (
    Capability,
    LearningNotificationMode,
    LearningSignal,
    TargetCapabilities,
    classify_learning_signal,
)
from .interactions import (
    NotificationActionDisposition,
    NotificationActionResult,
    NotificationInteractionService,
    NotificationInteractionValidationError,
    NotificationStage,
)
from .renderers import (
    NotificationRenderMode,
    NotificationRenderer,
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
    "NotificationInteractionService",
    "NotificationInteractionValidationError",
    "NotificationRenderMode",
    "NotificationRenderer",
    "NotificationWarningService",
    "QuizOption",
    "RenderedNotification",
    "NotificationStage",
    "NotifyRoute",
    "TargetCapabilities",
    "TargetUnavailableError",
    "async_resolve_notify_route",
    "decode_action_id",
    "effective_lockscreen_visibility",
    "encode_action_id",
    "classify_learning_signal",
]
