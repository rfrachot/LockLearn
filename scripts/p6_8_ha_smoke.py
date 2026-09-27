"""P6.8 latest-stable Home Assistant import/contract smoke."""

from __future__ import annotations

import importlib
import json
import os
from importlib.metadata import version
from pathlib import Path

from awesomeversion import AwesomeVersion

ROOT = Path(__file__).resolve().parents[1]

MODULES = (
    "custom_components.locklearn",
    "custom_components.locklearn.api.websocket",
    "custom_components.locklearn.profile_transfer",
    "custom_components.locklearn.runtime",
    "custom_components.locklearn.scheduler_ha",
)


def main() -> int:
    expected = os.environ.get("LOCKLEARN_EXPECTED_HA_VERSION")
    actual = version("homeassistant")
    if expected is not None and actual != expected:
        raise RuntimeError(f"Home Assistant pin mismatch: expected {expected}, got {actual}")

    hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
    minimum = str(hacs["homeassistant"])
    if AwesomeVersion(actual) < AwesomeVersion(minimum):
        raise RuntimeError(f"Home Assistant {actual} is below supported minimum {minimum}")

    manifest = json.loads(
        (ROOT / "custom_components" / "locklearn" / "manifest.json").read_text(encoding="utf-8")
    )
    if manifest.get("domain") != "locklearn" or manifest.get("config_flow") is not True:
        raise RuntimeError("LockLearn manifest contract is invalid")

    for module_name in MODULES:
        importlib.import_module(module_name)

    print(
        "LockLearn latest-HA smoke: PASS "
        f"(Home Assistant {actual}, minimum {minimum}, {len(MODULES)} modules)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
