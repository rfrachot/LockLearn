"""Deterministic long-horizon SRS quality simulation for P3.14."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from statistics import mean
from typing import Any

from .learning import LearningStateMachine
from .leeches import LeechPolicyV1
from .profiles import ProfilePreset, profile_preset_defaults
from .review_policy import ReviewPolicyV1


@dataclass
class _SimulationClock:
    current: datetime

    def now(self) -> datetime:
        return self.current


@dataclass(frozen=True, slots=True)
class SyntheticLearnerPattern:
    """Deterministic learner response model."""

    name: str
    learning_success_rate: float
    review_success_rate: float
    burst_period_days: int | None = None
    burst_review_success_rate: float | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("learning_success_rate", self.learning_success_rate),
            ("review_success_rate", self.review_success_rate),
        ):
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be within [0, 1]")
        if self.burst_period_days is not None and self.burst_period_days < 1:
            raise ValueError("burst_period_days must be >= 1")
        if (
            self.burst_review_success_rate is not None
            and not 0 <= self.burst_review_success_rate <= 1
        ):
            raise ValueError("burst_review_success_rate must be within [0, 1]")


@dataclass(frozen=True, slots=True)
class SimulationScenario:
    """Declared quality-gate scenario, not a product runtime preset."""

    name: str
    preset: ProfilePreset
    pattern: SyntheticLearnerPattern
    horizon_days: int = 180
    corpus_cards: int | None = None
    max_reviews_per_day_cards: int | None = None
    required_sustainable: bool = True
    seed: str = "locklearn-p3.14-v1"

    def resolved_max_new_per_day(self) -> int:
        return int(profile_preset_defaults(self.preset)["max_new_per_day_cards"])

    def resolved_corpus_cards(self) -> int:
        return self.corpus_cards or self.resolved_max_new_per_day() * self.horizon_days

    def resolved_review_capacity(self) -> int:
        return self.max_reviews_per_day_cards or self.resolved_max_new_per_day() * 10


@dataclass(frozen=True, slots=True)
class DailySimulationSample:
    day: int
    introduced: int
    due_opening: int
    reviews_treated: int
    interactions: int
    backlog_end: int
    max_overdue_days: int
    relearning_cap_hits: int


@dataclass(frozen=True, slots=True)
class SimulationReport:
    """Explainable output of one synthetic 180-day run."""

    scenario: str
    preset: str
    pattern: str
    horizon_days: int
    corpus_cards: int
    max_new_per_day_cards: int
    max_reviews_per_day_cards: int
    introduced_cards: int
    verified_reviews: int
    verified_correct: int
    verified_wrong: int
    verified_accuracy: float | None
    final_backlog: int
    max_backlog: int
    mean_last_30_backlog: float
    peak_daily_interactions: int
    p95_daily_interactions: int
    max_overdue_days: int
    starvation_days: int
    relearning_oscillation_cards: int
    overpromoted_cards: int
    leech_cards: int
    max_box: int
    sustainable: bool
    warnings: tuple[str, ...]
    required_sustainable: bool
    daily: tuple[DailySimulationSample, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "scenario": self.scenario,
            "preset": self.preset,
            "pattern": self.pattern,
            "horizon_days": self.horizon_days,
            "corpus_cards": self.corpus_cards,
            "max_new_per_day_cards": self.max_new_per_day_cards,
            "max_reviews_per_day_cards": self.max_reviews_per_day_cards,
            "introduced_cards": self.introduced_cards,
            "verified_reviews": self.verified_reviews,
            "verified_correct": self.verified_correct,
            "verified_wrong": self.verified_wrong,
            "verified_accuracy": self.verified_accuracy,
            "final_backlog": self.final_backlog,
            "max_backlog": self.max_backlog,
            "mean_last_30_backlog": self.mean_last_30_backlog,
            "peak_daily_interactions": self.peak_daily_interactions,
            "p95_daily_interactions": self.p95_daily_interactions,
            "max_overdue_days": self.max_overdue_days,
            "starvation_days": self.starvation_days,
            "relearning_oscillation_cards": self.relearning_oscillation_cards,
            "overpromoted_cards": self.overpromoted_cards,
            "leech_cards": self.leech_cards,
            "max_box": self.max_box,
            "sustainable": self.sustainable,
            "warnings": list(self.warnings),
            "required_sustainable": self.required_sustainable,
        }


TYPICAL_PATTERN = SyntheticLearnerPattern(
    name="typical",
    learning_success_rate=0.95,
    review_success_rate=0.90,
)
MIXED_PATTERN = SyntheticLearnerPattern(
    name="mixed",
    learning_success_rate=0.90,
    review_success_rate=0.82,
)
BURSTY_PATTERN = SyntheticLearnerPattern(
    name="bursty",
    learning_success_rate=0.90,
    review_success_rate=0.88,
    burst_period_days=14,
    burst_review_success_rate=0.62,
)
STRESS_PATTERN = SyntheticLearnerPattern(
    name="stress",
    learning_success_rate=0.78,
    review_success_rate=0.62,
)


def default_simulation_scenarios() -> tuple[SimulationScenario, ...]:
    """Return the declared P3.14 quality matrix."""
    return (
        SimulationScenario(
            name="child_typical",
            preset=ProfilePreset.CHILD,
            pattern=TYPICAL_PATTERN,
        ),
        SimulationScenario(
            name="standard_typical",
            preset=ProfilePreset.STANDARD,
            pattern=TYPICAL_PATTERN,
        ),
        SimulationScenario(
            name="standard_mixed",
            preset=ProfilePreset.STANDARD,
            pattern=MIXED_PATTERN,
        ),
        SimulationScenario(
            name="standard_bursty",
            preset=ProfilePreset.STANDARD,
            pattern=BURSTY_PATTERN,
        ),
        SimulationScenario(
            name="intensive_typical",
            preset=ProfilePreset.INTENSIVE,
            pattern=TYPICAL_PATTERN,
        ),
        SimulationScenario(
            name="standard_stress_detector",
            preset=ProfilePreset.STANDARD,
            pattern=STRESS_PATTERN,
            max_reviews_per_day_cards=32,
            required_sustainable=False,
        ),
    )


class LongHorizonSRSSimulator:
    """Exercise the real V1 learning/review policy over synthetic time."""

    _MAX_SHORT_STEP_ATTEMPTS_PER_CARD_DAY = 12
    _STARVATION_THRESHOLD_DAYS = 7
    _OVERPROMOTION_MIN_BOX = 6
    _OVERPROMOTION_MAX_ACCURACY = 0.75

    def run(self, scenario: SimulationScenario) -> SimulationReport:
        if scenario.horizon_days < 1:
            raise ValueError("horizon_days must be >= 1")
        max_new = scenario.resolved_max_new_per_day()
        corpus_cards = scenario.resolved_corpus_cards()
        review_capacity = scenario.resolved_review_capacity()
        if corpus_cards < 1:
            raise ValueError("corpus_cards must be >= 1")
        if review_capacity < 1:
            raise ValueError("max_reviews_per_day_cards must be >= 1")

        start = datetime(2026, 1, 1, 8, 0, tzinfo=UTC)
        clock = _SimulationClock(start)
        learning = LearningStateMachine(clock=clock)
        review = ReviewPolicyV1(clock=clock, learning=learning)
        leech_policy = LeechPolicyV1()

        cards = [self._new_snapshot(index) for index in range(corpus_cards)]
        review_history: dict[str, list[dict[str, Any]]] = {}
        relapse_days: dict[str, list[int]] = {}
        daily: list[DailySimulationSample] = []
        next_new_index = 0
        verified_reviews = 0
        verified_correct = 0
        verified_wrong = 0
        oscillation_cards: set[str] = set()
        starvation_days = 0

        for day_index in range(scenario.horizon_days):
            day_start = start + timedelta(days=day_index)
            day_end = day_start + timedelta(days=1)
            clock.current = day_start

            due_long = [
                card
                for card in cards[:next_new_index]
                if str(card["state"]) in {"review", "leech"}
                and self._is_due(card, at=day_start)
            ]
            due_long.sort(
                key=lambda card: (
                    str(card["state"]) == "leech",
                    str(card.get("next_due_at_utc") or ""),
                    str(card["card_key"]),
                )
            )
            due_opening = len(due_long)
            max_overdue = max(
                (
                    self._overdue_days(card, at=day_start)
                    for card in due_long
                ),
                default=0,
            )
            if max_overdue > self._STARVATION_THRESHOLD_DAYS:
                starvation_days += 1

            interactions = 0
            treated = 0
            relearning_cap_hits = 0
            for card in due_long[:review_capacity]:
                treated += 1
                clock.current = max(
                    day_start,
                    self._due_time(card) or day_start,
                )
                success = self._outcome(
                    scenario,
                    card_key=str(card["card_key"]),
                    day_index=day_index,
                    stage="review",
                    attempt=int(card["verified_correct_count"])
                    + int(card["verified_wrong_count"])
                    + 1,
                )
                pre = dict(card)
                if success:
                    transition = review.review_success(card, verified=True)
                    verified_correct += 1
                else:
                    transition = review.review_failure(card, verified=True)
                    verified_wrong += 1
                    relapse_days.setdefault(str(card["card_key"]), []).append(day_index)
                verified_reviews += 1
                interactions += 1
                card.update(transition.post_state)

                history = review_history.setdefault(str(card["card_key"]), [])
                leech_event = {
                    "mode": "verified_mcq",
                    "result": "correct" if success else "wrong",
                    "retrieval_occurred": True,
                    "signal_quality": "strong",
                    "pre_state_snapshot": pre,
                    "post_state_snapshot": dict(card),
                    "created_at_utc": clock.current.isoformat(),
                }
                decision = leech_policy.evaluate(
                    tuple(history),
                    current=leech_event,
                    now=clock.current,
                )
                if decision.detected:
                    card["state"] = "leech"
                    card["leech_score"] = max(
                        float(card.get("leech_score", 0.0)),
                        decision.score,
                    )
                history.append(leech_event)

                if str(card["state"]) == "relearning":
                    short_interactions, hit_cap = self._drain_short_steps(
                        scenario,
                        card,
                        day_index=day_index,
                        day_end=day_end,
                        learning=learning,
                        review=review,
                        clock=clock,
                        state="relearning",
                    )
                    interactions += short_interactions
                    if hit_cap:
                        oscillation_cards.add(str(card["card_key"]))
                        relearning_cap_hits += 1

            introduced = min(max_new, corpus_cards - next_new_index)
            for _ in range(introduced):
                card = cards[next_new_index]
                next_new_index += 1
                clock.current = day_start + timedelta(hours=4)
                card.update(learning.introduce(card).post_state)
                interactions += 1
                short_interactions, hit_cap = self._drain_short_steps(
                    scenario,
                    card,
                    day_index=day_index,
                    day_end=day_end,
                    learning=learning,
                    review=review,
                    clock=clock,
                    state="learning",
                )
                interactions += short_interactions
                if hit_cap:
                    oscillation_cards.add(str(card["card_key"]))

            backlog_end = sum(
                1
                for card in cards[:next_new_index]
                if str(card["state"]) in {"learning", "review", "relearning", "leech"}
                and self._is_due(card, at=day_end)
            )
            daily.append(
                DailySimulationSample(
                    day=day_index + 1,
                    introduced=introduced,
                    due_opening=due_opening,
                    reviews_treated=treated,
                    interactions=interactions,
                    backlog_end=backlog_end,
                    max_overdue_days=max_overdue,
                    relearning_cap_hits=relearning_cap_hits,
                )
            )

        active_cards = cards[:next_new_index]
        overpromoted = sum(
            1
            for card in active_cards
            if int(card.get("box", 0)) >= self._OVERPROMOTION_MIN_BOX
            and self._verified_accuracy(card) < self._OVERPROMOTION_MAX_ACCURACY
        )
        max_box = max((int(card.get("box", 0)) for card in active_cards), default=0)
        final_backlog = daily[-1].backlog_end
        max_backlog = max(sample.backlog_end for sample in daily)
        last_30 = daily[-min(30, len(daily)) :]
        mean_last_30_backlog = round(mean(sample.backlog_end for sample in last_30), 3)
        interaction_values = sorted(sample.interactions for sample in daily)
        p95_index = max(0, math.ceil(len(interaction_values) * 0.95) - 1)
        p95_interactions = interaction_values[p95_index]
        peak_interactions = max(interaction_values)
        max_overdue_days = max(sample.max_overdue_days for sample in daily)

        warnings: list[str] = []
        if final_backlog > review_capacity * 2 or mean_last_30_backlog > review_capacity:
            warnings.append("due_queue_explosion")
        if max_overdue_days > self._STARVATION_THRESHOLD_DAYS:
            warnings.append("review_starvation")
        if oscillation_cards:
            warnings.append("relearning_oscillation")
        if overpromoted:
            warnings.append("over_promotion")
        workload_budget = review_capacity + max_new * 5
        if p95_interactions > workload_budget:
            warnings.append("unrealistic_daily_workload")

        sustainable = not warnings
        return SimulationReport(
            scenario=scenario.name,
            preset=scenario.preset.value,
            pattern=scenario.pattern.name,
            horizon_days=scenario.horizon_days,
            corpus_cards=corpus_cards,
            max_new_per_day_cards=max_new,
            max_reviews_per_day_cards=review_capacity,
            introduced_cards=next_new_index,
            verified_reviews=verified_reviews,
            verified_correct=verified_correct,
            verified_wrong=verified_wrong,
            verified_accuracy=(
                None
                if verified_reviews == 0
                else round(verified_correct / verified_reviews, 6)
            ),
            final_backlog=final_backlog,
            max_backlog=max_backlog,
            mean_last_30_backlog=mean_last_30_backlog,
            peak_daily_interactions=peak_interactions,
            p95_daily_interactions=p95_interactions,
            max_overdue_days=max_overdue_days,
            starvation_days=starvation_days,
            relearning_oscillation_cards=len(oscillation_cards),
            overpromoted_cards=overpromoted,
            leech_cards=sum(str(card["state"]) == "leech" for card in active_cards),
            max_box=max_box,
            sustainable=sustainable,
            warnings=tuple(warnings),
            required_sustainable=scenario.required_sustainable,
            daily=tuple(daily),
        )

    def run_suite(
        self,
        scenarios: tuple[SimulationScenario, ...] | None = None,
    ) -> tuple[SimulationReport, ...]:
        return tuple(self.run(scenario) for scenario in scenarios or default_simulation_scenarios())

    def _drain_short_steps(
        self,
        scenario: SimulationScenario,
        card: dict[str, Any],
        *,
        day_index: int,
        day_end: datetime,
        learning: LearningStateMachine,
        review: ReviewPolicyV1,
        clock: _SimulationClock,
        state: str,
    ) -> tuple[int, bool]:
        interactions = 0
        for attempt in range(1, self._MAX_SHORT_STEP_ATTEMPTS_PER_CARD_DAY + 1):
            due = self._due_time(card)
            if due is None or due >= day_end:
                return interactions, False
            clock.current = due
            success = self._outcome(
                scenario,
                card_key=str(card["card_key"]),
                day_index=day_index,
                stage=state,
                attempt=attempt,
            )
            if state == "learning":
                transition = learning.learning_result(card, success=success)
            else:
                transition = learning.relearning_result(card, success=success)
            card.update(transition.post_state)
            interactions += 1
            if transition.ready_for_long_review:
                card.update(review.graduate_short_steps(transition).post_state)
                return interactions, False
        return interactions, True

    @staticmethod
    def _new_snapshot(index: int) -> dict[str, Any]:
        return {
            "profile_id": "simulation-profile",
            "track_id": "simulation-track",
            "card_key": f"simulation-card-{index:05d}",
            "learning_item_id": f"simulation-item-{index:05d}",
            "prompt_facet_id": f"simulation-prompt-{index:05d}",
            "answer_facet_id": f"simulation-answer-{index:05d}",
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
            "policy_version": 1,
            "dataset_generation": "simulation",
            "normalization_version": 1,
            "updated_at_utc": "",
        }

    def _outcome(
        self,
        scenario: SimulationScenario,
        *,
        card_key: str,
        day_index: int,
        stage: str,
        attempt: int,
    ) -> bool:
        if stage in {"learning", "relearning"}:
            rate = scenario.pattern.learning_success_rate
        else:
            rate = scenario.pattern.review_success_rate
            period = scenario.pattern.burst_period_days
            burst_rate = scenario.pattern.burst_review_success_rate
            if period is not None and burst_rate is not None and (day_index + 1) % period == 0:
                rate = burst_rate
        payload = (
            f"{scenario.seed}|{scenario.name}|{card_key}|{day_index}|{stage}|{attempt}".encode()
        )
        unit = int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") / (2**64 - 1)
        return unit < rate

    @staticmethod
    def _due_time(card: dict[str, Any]) -> datetime | None:
        raw = card.get("next_due_at_utc")
        if not isinstance(raw, str) or not raw:
            return None
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            raise ValueError("simulation due timestamp must be timezone-aware")
        return parsed

    @classmethod
    def _is_due(cls, card: dict[str, Any], *, at: datetime) -> bool:
        due = cls._due_time(card)
        return due is not None and due <= at

    @classmethod
    def _overdue_days(cls, card: dict[str, Any], *, at: datetime) -> int:
        due = cls._due_time(card)
        if due is None or due >= at:
            return 0
        return max(0, int((at - due).total_seconds() // 86400))

    @staticmethod
    def _verified_accuracy(card: dict[str, Any]) -> float:
        correct = int(card.get("verified_correct_count", 0))
        wrong = int(card.get("verified_wrong_count", 0))
        total = correct + wrong
        return 0.0 if total == 0 else correct / total
