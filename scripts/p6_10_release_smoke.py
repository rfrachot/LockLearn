"""P6.10 isolated HACS release-payload smoke."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION_ROOT = ROOT / "custom_components" / "locklearn"
CONST_PATH = INTEGRATION_ROOT / "const.py"
MANIFEST_PATH = INTEGRATION_ROOT / "manifest.json"
HACS_PATH = ROOT / "hacs.json"
CI_PATH = ROOT / ".github" / "workflows" / "ci.yml"
FRONTEND_PACKAGE_PATH = ROOT / "frontend" / "package.json"

SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
HACS_MINIMUM_HOME_ASSISTANT = "2025.2.0"
TESTED_MINIMUM_HOME_ASSISTANT = "2025.2.5"
FORBIDDEN_RUNTIME_IMPORT_ROOTS = frozenset({"datasets", "frontend", "scripts", "tests"})
FORBIDDEN_SECRET_SUFFIXES = frozenset({".key", ".p12", ".pfx", ".pem"})
PRIVATE_KEY_MARKERS = (
    b"-----BEGIN PRIVATE KEY-----",
    b"-----BEGIN RSA PRIVATE KEY-----",
    b"-----BEGIN OPENSSH PRIVATE KEY-----",
)
REQUIRED_RUNTIME_FILES = (
    "__init__.py",
    "config_flow.py",
    "manifest.json",
    "services.yaml",
    "strings.json",
    "frontend/locklearn-panel.js",
    "translations/en.json",
    "translations/fr.json",
    "datasets/resources/bundled_datasets.json",
    "datasets/resources/licenses.json",
    "datasets/resources/official_datasets.json",
    "datasets/resources/signing_keys.json",
    "datasets/resources/sources.json",
)

_CHILD_SMOKE = r"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import custom_components.locklearn as integration
from custom_components.locklearn.const import INTEGRATION_VERSION
from custom_components.locklearn.datasets.manager import (
    load_runtime_bundled_datasets,
    load_runtime_dataset_definitions,
    load_runtime_source_freshness,
    load_runtime_trust_store,
)
from custom_components.locklearn.datasets.policy import OfficialRegistryPolicy

root = Path(integration.__file__).resolve().parent
payload_root = Path.cwd().resolve()
assert payload_root in root.parents, (payload_root, root)

manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
assert manifest["version"] == INTEGRATION_VERSION
assert (root / "frontend" / "locklearn-panel.js").is_file()

definitions = load_runtime_dataset_definitions()
assert definitions
load_runtime_trust_store()
OfficialRegistryPolicy.from_runtime()
load_runtime_source_freshness()

bundled = load_runtime_bundled_datasets()
assert bundled
for item in bundled:
    assert item.path.is_file(), item.path
    payload = item.path.read_bytes()
    assert len(payload) == item.size
    assert hashlib.sha256(payload).hexdigest() == item.sha256

print(
    json.dumps(
        {
            "integration_version": INTEGRATION_VERSION,
            "bundled_datasets": len(bundled),
            "dataset_definitions": len(definitions),
        },
        sort_keys=True,
    )
)
"""


def _read_string_constant(path: Path, name: str) -> str:
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Constant) or not isinstance(node.value.value, str):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return node.value.value
    raise AssertionError(f"Missing string constant {name} in {path}")


def _validate_release_metadata() -> str:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    runtime_version = _read_string_constant(CONST_PATH, "INTEGRATION_VERSION")
    assert manifest["version"] == runtime_version
    match = SEMVER_RE.fullmatch(runtime_version)
    assert match is not None, runtime_version
    assert tuple(int(match.group(index)) for index in range(1, 4)) >= (1, 0, 0)

    hacs = json.loads(HACS_PATH.read_text(encoding="utf-8"))
    assert hacs["homeassistant"] == HACS_MINIMUM_HOME_ASSISTANT
    assert hacs["render_readme"] is True

    ci = CI_PATH.read_text(encoding="utf-8")
    assert f'home_assistant: "{TESTED_MINIMUM_HOME_ASSISTANT}"' in ci
    assert "home-assistant/actions/hassfest@master" in ci
    assert "hacs/action@22.5.0" in ci

    frontend_package = json.loads(FRONTEND_PACKAGE_PATH.read_text(encoding="utf-8"))
    assert frontend_package["private"] is True

    assert manifest["config_flow"] is True
    assert manifest["single_config_entry"] is True
    return runtime_version


def _validate_runtime_payload() -> None:
    assert INTEGRATION_ROOT.is_dir()
    for relative in REQUIRED_RUNTIME_FILES:
        path = INTEGRATION_ROOT / relative
        assert path.is_file(), f"Missing HACS runtime payload file: {relative}"
        if path.name == "locklearn-panel.js":
            assert path.stat().st_size > 0

    import_violations: list[str] = []
    for path in sorted(INTEGRATION_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            roots: list[str] = []
            if isinstance(node, ast.Import):
                roots.extend(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                roots.append(node.module.split(".", 1)[0])
            for root in roots:
                if root in FORBIDDEN_RUNTIME_IMPORT_ROOTS:
                    import_violations.append(
                        f"{path.relative_to(INTEGRATION_ROOT)} imports top-level {root}"
                    )
    assert import_violations == []

    secret_violations: list[str] = []
    for path in sorted(INTEGRATION_ROOT.rglob("*")):
        if not path.is_file():
            continue
        assert not path.is_symlink(), f"Release payload contains a symlink: {path}"
        if path.suffix.lower() in FORBIDDEN_SECRET_SUFFIXES:
            secret_violations.append(str(path.relative_to(INTEGRATION_ROOT)))
            continue
        payload = path.read_bytes()
        if any(marker in payload for marker in PRIVATE_KEY_MARKERS):
            secret_violations.append(str(path.relative_to(INTEGRATION_ROOT)))
    assert secret_violations == [], f"Private key material in release payload: {secret_violations}"

    dataset_root = INTEGRATION_ROOT / "datasets"
    registry = json.loads(
        (dataset_root / "resources" / "bundled_datasets.json").read_text(encoding="utf-8")
    )
    assert registry["schema_version"] == 1
    assert registry["datasets"]
    for row in registry["datasets"]:
        artifact = (dataset_root / row["path"]).resolve()
        assert dataset_root.resolve() in artifact.parents
        assert artifact.is_file()
        payload = artifact.read_bytes()
        assert len(payload) == row["size"]
        assert hashlib.sha256(payload).hexdigest() == row["sha256"]


def _run_isolated_import_smoke() -> str:
    with tempfile.TemporaryDirectory(prefix="locklearn-p6-10-") as temporary:
        root = Path(temporary)
        destination = root / "custom_components" / "locklearn"
        destination.parent.mkdir(parents=True)
        shutil.copytree(INTEGRATION_ROOT, destination)

        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(root)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment.pop("PYTHONHOME", None)

        completed = subprocess.run(
            [sys.executable, "-c", _CHILD_SMOKE],
            cwd=root,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise AssertionError(
                "Isolated HACS payload import failed\n"
                f"stdout:\n{completed.stdout}\n"
                f"stderr:\n{completed.stderr}"
            )
        return completed.stdout.strip()


def main() -> int:
    try:
        runtime_version = _validate_release_metadata()
        _validate_runtime_payload()
        child_result = _run_isolated_import_smoke()
    except Exception as err:
        print(f"P6.10 release payload smoke: FAIL: {err}", file=sys.stderr)
        return 1

    print(f"P6.10 release payload smoke: PASS ({runtime_version})")
    if child_result:
        print(child_result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
