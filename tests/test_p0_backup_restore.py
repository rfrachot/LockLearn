"""Tests for the P0.7 backup/restore qualification harness."""

from scripts.p0_backup_restore import backup_summary, safety_backups


def test_backup_summary_keeps_scope_but_not_unrelated_metadata() -> None:
    """Evidence contains restore scope without dumping arbitrary metadata."""
    summary = backup_summary(
        {
            "backup_id": "test-id",
            "name": "LockLearn P0.7",
            "date": "2026-09-21T00:00:00+00:00",
            "homeassistant_included": True,
            "homeassistant_version": "2026.7.4",
            "database_included": False,
            "addons": [],
            "folders": [],
            "agents": {"hassio.local": {"protected": True}},
            "extra_metadata": {"instance_id": "must-not-be-copied"},
        }
    )

    assert summary["backup_id"] == "test-id"
    assert summary["agents"] == ["hassio.local"]
    assert summary["homeassistant_included"] is True
    assert summary["database_included"] is False
    assert "extra_metadata" not in summary


def test_safety_backup_accepts_announced_and_observed_names() -> None:
    """The harness preserves either known spelling of the independent backup."""
    backups = [
        {"backup_id": "one", "name": "PRE_P0.7"},
        {"backup_id": "two", "name": "Pre-locklearn"},
        {"backup_id": "three", "name": "Unrelated"},
    ]

    assert [item["backup_id"] for item in safety_backups(backups)] == ["one", "two"]
