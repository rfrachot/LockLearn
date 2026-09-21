import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_manifest_is_single_entry_custom_integration() -> None:
    manifest = json.loads(
        (ROOT / "custom_components" / "locklearn" / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["domain"] == "locklearn"
    assert manifest["config_flow"] is True
    assert manifest["single_config_entry"] is True
    assert manifest["codeowners"] == ["@rfrachot"]
