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
from .targets import NotifyRoute, TargetUnavailableError, async_resolve_notify_route

__all__ = [
    "Capability",
    "LearningNotificationMode",
    "LearningSignal",
    "NotificationActionDisposition",
    "NotificationActionResult",
    "NotificationInteractionService",
    "NotificationInteractionValidationError",
    "NotificationStage",
    "NotifyRoute",
    "TargetCapabilities",
    "TargetUnavailableError",
    "async_resolve_notify_route",
    "classify_learning_signal",
]
