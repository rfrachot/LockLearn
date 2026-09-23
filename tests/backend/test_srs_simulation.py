"""P3.14 deterministic long-horizon SRS simulation tests."""

from __future__ import annotations

from custom_components.locklearn.core.profiles import ProfilePreset
from custom_components.locklearn.core.srs_simulation import (
    STRESS_PATTERN,
    TYPICAL_PATTERN,
    LongHorizonSRSSimulator,
    SimulationScenario,
    default_simulation_scenarios,
)


def test_default_simulation_suite_is_deterministic_and_declares_all_presets() -> None:
    simulator = LongHorizonSRSSimulator()

    first = simulator.run_suite()
    second = simulator.run_suite()

    assert [report.as_dict() for report in first] == [report.as_dict() for report in second]
    assert {report.preset for report in first} >= {"child", "standard", "intensive"}
    assert all(report.horizon_days == 180 for report in first)


def test_required_default_scenarios_remain_sustainable() -> None:
    reports = LongHorizonSRSSimulator().run_suite()

    required = [report for report in reports if report.required_sustainable]
    assert required
    for report in required:
        assert report.sustainable, (report.scenario, report.warnings, report.as_dict())
        assert "due_queue_explosion" not in report.warnings
        assert "review_starvation" not in report.warnings
        assert "relearning_oscillation" not in report.warnings
        assert "over_promotion" not in report.warnings


def test_stress_scenario_trips_at_least_one_detector() -> None:
    report = LongHorizonSRSSimulator().run(
        SimulationScenario(
            name="detector-proof",
            preset=ProfilePreset.STANDARD,
            pattern=STRESS_PATTERN,
            max_reviews_per_day_cards=20,
            required_sustainable=False,
        )
    )

    assert report.sustainable is False
    assert report.warnings
    assert set(report.warnings) & {
        "due_queue_explosion",
        "review_starvation",
        "relearning_oscillation",
        "over_promotion",
        "unrealistic_daily_workload",
    }


def test_simulation_uses_preset_card_quota_and_bounded_review_capacity() -> None:
    scenario = SimulationScenario(
        name="quota-proof",
        preset=ProfilePreset.CHILD,
        pattern=TYPICAL_PATTERN,
        horizon_days=30,
        corpus_cards=300,
        max_reviews_per_day_cards=30,
    )

    report = LongHorizonSRSSimulator().run(scenario)

    assert report.max_new_per_day_cards == 3
    assert report.max_reviews_per_day_cards == 30
    assert report.introduced_cards <= 3 * 30
    assert all(sample.reviews_treated <= 30 for sample in report.daily)
    assert all(sample.introduced + sample.new_throttled <= 3 for sample in report.daily)


def test_default_matrix_contains_explicit_negative_detector_case() -> None:
    scenarios = default_simulation_scenarios()

    assert any(not scenario.required_sustainable for scenario in scenarios)
    assert any(scenario.required_sustainable for scenario in scenarios)
