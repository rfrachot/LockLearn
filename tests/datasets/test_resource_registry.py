from pathlib import Path

from datasets.tools.validate_resources import validate

ROOT = Path(__file__).resolve().parents[2]


def test_resource_registries_are_consistent() -> None:
    validate()


def test_runtime_source_and_license_registries_match_build_policy() -> None:
    runtime = ROOT / "custom_components" / "locklearn" / "datasets" / "resources"
    build = ROOT / "datasets" / "resources"
    assert (runtime / "sources.json").read_bytes() == (build / "sources.json").read_bytes()
    assert (runtime / "licenses.json").read_bytes() == (build / "licenses.json").read_bytes()
