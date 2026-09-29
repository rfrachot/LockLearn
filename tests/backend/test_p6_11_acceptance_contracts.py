"""P6.11 V1 acceptance evidence and scope contracts."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACCEPTANCE_DOC = ROOT / "docs" / "P6_11_ACCEPTANCE.md"
SPEC = ROOT / "SPEC_V1.md"

CAPABILITY_IDS = tuple(f"C-{index:02d}" for index in range(1, 47))
INVARIANT_IDS = tuple(f"I-{index:02d}" for index in range(1, 33))
DOD_IDS = (
    *(f"A-{index:02d}" for index in range(1, 17)),
    *(f"CAMILLE-{index:02d}" for index in range(1, 4)),
    *(f"ZOE-{index:02d}" for index in range(1, 5)),
    *(f"R-{index:02d}" for index in range(1, 6)),
)

CRITICAL_NODEIDS = (
    "tests/backend/test_p6_11_v1_acceptance.py::test_fresh_starter_public_api_acceptance",
    "tests/backend/test_profiles.py::test_child_profile_needs_no_dedicated_ha_account_and_supports_multiple_owners",
    "tests/backend/test_websocket_crud.py::test_track_crud_pack_integration_and_catalog_surfaces",
    "tests/backend/test_websocket_sessions.py::test_session_start_pause_resume_complete_and_cross_client_get",
    "tests/backend/test_session_selection.py::test_twenty_card_session_fills_with_due_reviews_in_final_quarter",
    "tests/backend/test_persistent_sessions.py::test_exactly_one_same_version_answer_wins",
    "tests/backend/test_notification_action_processing.py::test_duplicate_quiz_interaction_applies_and_emits_exactly_once",
    "tests/backend/test_notification_renderers.py::test_channels_shared_profile_label_and_profile_target_identity_stay_distinct",
    "tests/backend/test_stats.py::test_daily_projection_and_metacognitive_calibration",
    "tests/backend/test_lifecycle.py::test_setup_unload_and_reload_have_no_duplicate_panel",
    "tests/backend/test_storage_lifecycle.py::test_ha_backup_publishes_valid_coherent_recovery_snapshot",
    "tests/backend/test_targets.py::test_device_registry_id_survives_mobile_app_rename",
    "tests/datasets/test_dataset_manager.py::test_invalid_update_after_valid_install_preserves_installed_version",
    "tests/datasets/test_dataset_manager.py::test_invalid_signature_reports_distinct_repair",
    "tests/backend/test_profile_transfer.py::test_export_import_round_trip_remaps_identity_and_preserves_tombstones",
    "tests/backend/test_p6_10_release_readiness.py::test_real_v0_0_2_state_upgrades_to_v1_candidate_without_data_loss",
)


def _test_names(path: Path) -> set[str]:
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        node.name
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }


def test_acceptance_document_covers_every_normative_gate() -> None:
    content = ACCEPTANCE_DOC.read_text(encoding="utf-8")
    for marker in (*CAPABILITY_IDS, *INVARIANT_IDS, *DOD_IDS):
        assert f"| {marker} |" in content, marker

    for heading in (
        "## §129 mandatory 1.0 capabilities",
        "## §133 architectural invariants",
        "## §135 Definition of Done",
        "## V1.1 / V2 non-blockers",
    ):
        assert heading in content

    for pseudonym in ("Adrien", "Camille", "Zoé"):
        assert pseudonym in content


def test_critical_acceptance_evidence_nodeids_remain_executable() -> None:
    for nodeid in CRITICAL_NODEIDS:
        relative, test_name = nodeid.split("::", 1)
        path = ROOT / relative
        assert path.is_file(), nodeid
        assert test_name in _test_names(path), nodeid


def test_spec_keeps_v1_scope_and_non_blockers_explicit() -> None:
    spec = SPEC.read_text(encoding="utf-8")
    section_129 = spec.split("# 129. V1 obligatoire", 1)[1].split("# 130.", 1)[0]
    section_135 = spec.split("# 135. Definition of Done V1", 1)[1].split("# 136.", 1)[0]

    for required in (
        "HACS installation",
        "multi-user",
        "signed dataset update + rollback",
        "FR + EN UI",
        "secure export/import",
        "CI/tests",
    ):
        assert required in section_129

    for non_blocker in (
        "L'examen",
        "sensors HA avancés",
        "image/audio",
        "statistiques enrichies",
    ):
        assert non_blocker in section_135
    assert "ne bloquent pas `1.0.0`" in section_135


def test_real_ha_acceptance_evidence_remains_committed() -> None:
    evidence = (ROOT / "docs" / "P0_EVIDENCE.md").read_text(encoding="utf-8")
    p5_plan = (ROOT / "docs" / "plan" / "P5.md").read_text(encoding="utf-8")
    assert "HACS install" in evidence
    assert "physical receipt" in evidence
    assert "PASS" in evidence
    assert "**Real-HA qualification — PASS" in p5_plan
