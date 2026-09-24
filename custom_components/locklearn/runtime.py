"""Per-config-entry LockLearn runtime."""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import suppress
from dataclasses import dataclass

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.template import Template, result_as_boolean

from .const import DOMAIN
from .core.acl import ProfileACLService
from .core.content_reports import ContentReportService
from .core.difficulties import DifficultyService
from .core.grading import FreeTextGrader
from .core.integrity import IntegrityService
from .core.notification_selection import NotificationSelectionService
from .core.operations import OperationRegistry
from .core.planning import LearningPlanService
from .core.profiles import ProfileService
from .core.progress_state import ProgressUserStateService
from .core.quiz import QuizEngine
from .core.review_policy import ReviewPolicyV1
from .core.reviews import ReviewEventService
from .core.scheduler import SchedulerService, SchedulerValidationError
from .core.selection import SelectionConstraintService
from .core.session_selection import SessionSelectionService
from .core.sessions import SessionService
from .core.signals import SignalPolicy
from .core.stats import StatsService
from .core.tracks import TrackService
from .datasets.manager import (
    DatasetManager,
    load_runtime_bundled_datasets,
    load_runtime_dataset_definitions,
    load_runtime_source_freshness,
    load_runtime_trust_store,
)
from .datasets.policy import OfficialRegistryPolicy
from .datasets.transport import HomeAssistantDatasetTransport
from .notifications.delivery import NotificationDeliveryService
from .notifications.interactions import NotificationInteractionService
from .notifications.warnings import NotificationWarningService
from .scheduler_ha import SchedulerHomeAssistantBridge
from .storage import SQLiteStorage, StoragePaths


@dataclass(slots=True)
class LockLearnRuntime:
    """Own all resources that must be drained on reload/unload."""

    storage: SQLiteStorage
    sessions: SessionService
    operations: OperationRegistry
    profiles: ProfileService
    acl: ProfileACLService
    tracks: TrackService
    planning: LearningPlanService
    progress_state: ProgressUserStateService
    grading: FreeTextGrader
    integrity: IntegrityService
    content_reports: ContentReportService
    difficulties: DifficultyService
    quiz: QuizEngine
    review_policy: ReviewPolicyV1
    signal_policy: SignalPolicy
    selection: SelectionConstraintService
    session_selection: SessionSelectionService
    stats: StatsService
    reviews: ReviewEventService
    notification_delivery: NotificationDeliveryService
    notification_interactions: NotificationInteractionService
    notification_warnings: NotificationWarningService
    scheduler: SchedulerService
    scheduler_ha: SchedulerHomeAssistantBridge
    datasets: DatasetManager

    @classmethod
    async def async_create(cls, hass: HomeAssistant) -> LockLearnRuntime:
        """Create and open a runtime from HA's persistent config directory."""
        storage = SQLiteStorage(StoragePaths.from_config_dir(hass.config.config_dir))
        await storage.async_open()

        async def report_issue(
            issue_id: str,
            translation_key: str,
            placeholders: Mapping[str, str],
        ) -> None:
            severity = (
                ir.IssueSeverity.WARNING
                if translation_key in {"dataset_discovery_failed", "dataset_sources_stale"}
                else ir.IssueSeverity.ERROR
            )
            ir.async_create_issue(
                hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                is_persistent=True,
                severity=severity,
                translation_key=translation_key,
                translation_placeholders=dict(placeholders),
            )

        async def clear_issue(issue_id: str) -> None:
            ir.async_delete_issue(hass, DOMAIN, issue_id)

        async def evaluate_receptive_when(expression: str) -> bool:
            try:
                rendered = Template(expression, hass).async_render(parse_result=False)
            except TemplateError as err:
                raise SchedulerValidationError(f"receptive_when template failed: {err}") from err
            return result_as_boolean(rendered)

        try:
            datasets = DatasetManager(
                storage=storage,
                transport=HomeAssistantDatasetTransport(hass),
                definitions=load_runtime_dataset_definitions(),
                trust_store=load_runtime_trust_store(),
                policy=OfficialRegistryPolicy.from_runtime(),
                freshness_targets=load_runtime_source_freshness(),
                issue_callback=report_issue,
                issue_clear_callback=clear_issue,
            )
            for bundled in load_runtime_bundled_datasets():
                # DatasetManager already raises a persistent Repair. Keep HA usable
                # and preserve the empty/last-known-good generation.
                with suppress(Exception):
                    await datasets.async_install_bundled(bundled)
            review_policy = ReviewPolicyV1()
            acl = ProfileACLService(storage.repositories.profiles)
            selection = SelectionConstraintService(storage.repositories.tracks)
            session_selection = SessionSelectionService(
                storage.repositories.tracks,
                storage.repositories.profiles,
                storage.repositories.review_events,
                selection,
            )
            reviews = ReviewEventService(
                storage.repositories.review_events,
                storage.repositories.profiles,
            )
            notification_selection = NotificationSelectionService(
                storage.repositories.tracks,
                storage.repositories.profiles,
                storage.repositories.review_events,
                storage.repositories.scheduler,
                selection,
            )
            scheduler = SchedulerService(
                storage.repositories.profiles,
                storage.repositories.tracks,
                storage.repositories.notification_targets,
                storage.repositories.scheduler,
                storage.repositories.settings,
                notification_selection,
                issue_callback=report_issue,
                issue_clear_callback=clear_issue,
                receptive_evaluator=evaluate_receptive_when,
            )
            scheduler_ha = SchedulerHomeAssistantBridge(
                hass,
                storage.repositories.profiles,
                scheduler,
            )
            runtime = cls(
                storage=storage,
                sessions=SessionService(storage),
                operations=OperationRegistry(),
                profiles=ProfileService(storage.repositories.profiles),
                acl=acl,
                tracks=TrackService(storage.repositories.tracks),
                planning=LearningPlanService(
                    storage.repositories.tracks,
                    storage.repositories.profiles,
                ),
                progress_state=ProgressUserStateService(
                    storage.repositories.tracks,
                    storage.repositories.progress,
                    dataset_generation=lambda: (
                        storage.content_generations.active_metadata.generation_id
                    ),
                ),
                grading=FreeTextGrader(),
                integrity=IntegrityService(
                    storage.repositories.review_events,
                    storage.repositories.progress,
                    storage.repositories.profiles,
                ),
                content_reports=ContentReportService(
                    storage.repositories.content_reports,
                    storage.repositories.tracks,
                ),
                difficulties=DifficultyService(
                    storage.repositories.progress,
                    storage.repositories.review_events,
                    storage.repositories.user_annotations,
                    reviews,
                ),
                quiz=QuizEngine(),
                review_policy=review_policy,
                signal_policy=SignalPolicy(review_policy),
                selection=selection,
                session_selection=session_selection,
                stats=StatsService(
                    storage.repositories.profiles,
                    storage.repositories.tracks,
                    storage.repositories.progress,
                    storage.repositories.review_events,
                    review_policy=review_policy,
                ),
                reviews=reviews,
                notification_delivery=NotificationDeliveryService(
                    hass,
                    storage.repositories.notification_targets,
                    issue_callback=report_issue,
                    issue_clear_callback=clear_issue,
                ),
                notification_interactions=NotificationInteractionService(
                    storage.repositories.notification_interactions,
                    acl,
                ),
                notification_warnings=NotificationWarningService(
                    storage.repositories.notification_warnings,
                ),
                scheduler=scheduler,
                scheduler_ha=scheduler_ha,
                datasets=datasets,
            )
            await runtime.scheduler.async_reconcile(reason="startup")
            await runtime.scheduler_ha.async_start()
            return runtime
        except Exception:
            await storage.async_close()
            raise

    async def async_close(self) -> None:
        """Cancel callbacks/operations, then drain and close SQLite."""
        self.scheduler_ha.close()
        self.sessions.close()
        await self.operations.async_close()
        await self.storage.async_close()
