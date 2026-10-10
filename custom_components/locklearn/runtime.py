"""Per-config-entry LockLearn runtime."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from contextlib import suppress
from dataclasses import dataclass
from urllib.parse import urlsplit

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.template import Template, result_as_boolean

from .const import DOMAIN
from .core.acl import ProfileACLService
from .core.content_reports import ContentReportService
from .core.dashboard import DashboardService
from .core.difficulties import DifficultyService
from .core.grading import FreeTextGrader
from .core.integrity import IntegrityService
from .core.learning_sessions import LearningSessionService
from .core.notification_selection import NotificationSelectionService
from .core.operations import OperationRegistry
from .core.planning import LearningPlanService
from .core.presentation import CardPresentationService
from .core.profiles import ProfileService
from .core.progress_state import ProgressUserStateService
from .core.quiz import QuizEngine
from .core.quiz_sessions import QuizSessionService
from .core.ready_reminders import ReadyReminderService
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
from .notifications.actions import NotificationActionProcessor
from .notifications.delivery import NotificationDeliveryService
from .notifications.ha_bridge import NotificationHomeAssistantBridge
from .notifications.interactions import NotificationInteractionService
from .notifications.reveal import NotificationRevealService
from .notifications.warnings import NotificationWarningService
from .profile_transfer import ProfileTransferService, ProfileTransferStore
from .scheduler_ha import SchedulerHomeAssistantBridge
from .storage import SQLiteStorage, StoragePaths


@dataclass(slots=True)
class LockLearnRuntime:
    """Own all resources that must be drained on reload/unload."""

    storage: SQLiteStorage
    sessions: SessionService
    learning_sessions: LearningSessionService
    presentation: CardPresentationService
    operations: OperationRegistry
    profiles: ProfileService
    acl: ProfileACLService
    tracks: TrackService
    planning: LearningPlanService
    progress_state: ProgressUserStateService
    grading: FreeTextGrader
    integrity: IntegrityService
    content_reports: ContentReportService
    dashboard: DashboardService
    difficulties: DifficultyService
    quiz: QuizEngine
    quiz_sessions: QuizSessionService
    review_policy: ReviewPolicyV1
    signal_policy: SignalPolicy
    selection: SelectionConstraintService
    session_selection: SessionSelectionService
    stats: StatsService
    reviews: ReviewEventService
    notification_actions: NotificationActionProcessor
    notification_delivery: NotificationDeliveryService
    notification_ha: NotificationHomeAssistantBridge
    notification_interactions: NotificationInteractionService
    notification_warnings: NotificationWarningService
    ready_reminders: ReadyReminderService
    scheduler: SchedulerService
    scheduler_ha: SchedulerHomeAssistantBridge
    datasets: DatasetManager
    profile_transfers: ProfileTransferService

    @classmethod
    async def async_create(cls, hass: HomeAssistant) -> LockLearnRuntime:
        """Create and open a runtime from HA's persistent config directory."""
        storage = SQLiteStorage(StoragePaths.from_config_dir(hass.config.config_dir))
        await storage.async_open()
        transfer_store = ProfileTransferStore.private_runtime_root(hass.config.config_dir)

        async def report_issue(
            issue_id: str,
            translation_key: str,
            placeholders: Mapping[str, str],
        ) -> None:
            severity = (
                ir.IssueSeverity.WARNING
                if translation_key
                in {
                    "dataset_discovery_failed",
                    "dataset_sources_stale",
                    "dataset_cache_budget_warning",
                }
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
            await transfer_store.async_initialize()
            (
                dataset_definitions,
                trust_store,
                dataset_policy,
                freshness_targets,
                bundled_datasets,
            ) = await asyncio.gather(
                hass.async_add_executor_job(load_runtime_dataset_definitions),
                hass.async_add_executor_job(load_runtime_trust_store),
                hass.async_add_executor_job(OfficialRegistryPolicy.from_runtime),
                hass.async_add_executor_job(load_runtime_source_freshness),
                hass.async_add_executor_job(load_runtime_bundled_datasets),
            )
            datasets = DatasetManager(
                storage=storage,
                transport=HomeAssistantDatasetTransport(
                    hass,
                    allowed_hosts=frozenset(
                        host
                        for definition in dataset_definitions
                        for host in (
                            urlsplit(definition.catalog_url).hostname,
                            *definition.artifact_hosts,
                        )
                        if host is not None
                    ),
                ),
                definitions=dataset_definitions,
                trust_store=trust_store,
                policy=dataset_policy,
                freshness_targets=freshness_targets,
                issue_callback=report_issue,
                issue_clear_callback=clear_issue,
            )
            for bundled in bundled_datasets:
                with suppress(Exception):
                    await datasets.async_install_bundled(bundled)
            await datasets.async_statuses()
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
            signal_policy = SignalPolicy(review_policy)
            stats = StatsService(
                storage.repositories.profiles,
                storage.repositories.tracks,
                storage.repositories.progress,
                storage.repositories.review_events,
                review_policy=review_policy,
            )
            notification_interactions = NotificationInteractionService(
                storage.repositories.notification_interactions,
                acl,
                review_events=storage.repositories.review_events,
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
            sessions = SessionService(storage)
            learning_sessions = LearningSessionService(
                storage,
                sessions,
                reviews,
                review_policy,
                signal_policy,
                dataset_generation=lambda: (
                    storage.content_generations.active_metadata.generation_id
                ),
            )
            presentation = CardPresentationService(storage)
            grading = FreeTextGrader()
            quiz = QuizEngine()
            quiz_sessions = QuizSessionService(
                storage,
                sessions,
                presentation,
                reviews,
                review_policy,
                signal_policy,
                quiz,
                grading,
                dataset_generation=lambda: (
                    storage.content_generations.active_metadata.generation_id
                ),
                event_emitter=lambda event_type, data: hass.bus.async_fire(
                    event_type,
                    data,
                ),
            )
            scheduler_ha = SchedulerHomeAssistantBridge(
                hass,
                storage.repositories.profiles,
                scheduler,
            )
            notification_delivery = NotificationDeliveryService(
                hass,
                storage.repositories.notification_targets,
                issue_callback=report_issue,
                issue_clear_callback=clear_issue,
            )
            notification_reveal = NotificationRevealService(
                storage.repositories.profiles,
                storage.repositories.notification_targets,
                presentation,
                notification_interactions,
                notification_delivery,
            )
            notification_actions = NotificationActionProcessor(
                notification_interactions,
                storage.repositories.profiles,
                storage.repositories.tracks,
                storage.repositories.progress,
                storage.repositories.notification_targets,
                scheduler,
                reviews,
                storage.repositories.review_events,
                signal_policy,
                review_policy,
                stats,
                dataset_generation=lambda: (
                    storage.content_generations.active_metadata.generation_id
                ),
                event_emitter=lambda event_type, data: hass.bus.async_fire(
                    event_type,
                    data,
                ),
                reveal_service=notification_reveal,
            )
            notification_ha = NotificationHomeAssistantBridge(
                hass,
                notification_interactions,
                notification_actions,
                scheduler,
            )
            ready_reminders = ReadyReminderService(
                storage.repositories.settings,
                storage.repositories.profiles,
                storage.repositories.notification_targets,
                session_selection,
                notification_delivery,
            )
            runtime = cls(
                storage=storage,
                sessions=sessions,
                learning_sessions=learning_sessions,
                presentation=presentation,
                operations=OperationRegistry(),
                profiles=ProfileService(
                    storage.repositories.profiles,
                    permanent_delete_cleanup=transfer_store.async_purge_profile,
                ),
                acl=acl,
                tracks=TrackService(storage.repositories.tracks),
                planning=LearningPlanService(
                    storage.repositories.tracks,
                    storage.repositories.profiles,
                ),
                progress_state=ProgressUserStateService(
                    storage.repositories.tracks,
                    storage.repositories.progress,
                    reviews,
                    dataset_generation=lambda: (
                        storage.content_generations.active_metadata.generation_id
                    ),
                ),
                grading=grading,
                integrity=IntegrityService(
                    storage.repositories.review_events,
                    storage.repositories.progress,
                    storage.repositories.profiles,
                ),
                content_reports=ContentReportService(
                    storage.repositories.content_reports,
                    storage.repositories.tracks,
                ),
                dashboard=DashboardService(
                    storage.repositories.profiles,
                    storage.repositories.tracks,
                    storage.repositories.scheduler,
                    storage,
                    stats,
                ),
                difficulties=DifficultyService(
                    storage.repositories.progress,
                    storage.repositories.review_events,
                    storage.repositories.user_annotations,
                    reviews,
                ),
                quiz=quiz,
                quiz_sessions=quiz_sessions,
                review_policy=review_policy,
                signal_policy=signal_policy,
                selection=selection,
                session_selection=session_selection,
                stats=stats,
                reviews=reviews,
                notification_actions=notification_actions,
                notification_delivery=notification_delivery,
                notification_ha=notification_ha,
                notification_interactions=notification_interactions,
                notification_warnings=NotificationWarningService(
                    storage.repositories.notification_warnings,
                ),
                ready_reminders=ready_reminders,
                scheduler=scheduler,
                scheduler_ha=scheduler_ha,
                datasets=datasets,
                profile_transfers=ProfileTransferService(storage, transfer_store),
            )
            await runtime.scheduler_ha.async_start()
            await runtime.notification_ha.async_start()
            await runtime.ready_reminders.async_start()
            return runtime
        except Exception:
            if "datasets" in locals():
                await datasets.async_close()
            await transfer_store.async_close()
            await storage.async_close()
            raise

    async def async_close(self) -> None:
        """Cancel callbacks/operations, then drain and close SQLite."""
        self.notification_ha.close()
        self.ready_reminders.close()
        self.scheduler_ha.close()
        self.sessions.close()
        await self.operations.async_close()
        await self.profile_transfers.store.async_close()
        await self.datasets.async_close()
        await self.storage.async_close()
