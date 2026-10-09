"""Permanent contracts for the trusted self-hosted CI boundary."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = ROOT / ".github" / "workflows"


def test_normal_workflows_have_no_hosted_runner_or_pull_request_trigger() -> None:
    for name in ("ci.yml", "datasets.yml"):
        source = (WORKFLOW_ROOT / name).read_text(encoding="utf-8")
        assert "ubuntu-latest" not in source
        assert "pull_request" not in source
        assert "runs-on: [self-hosted, locklearn-dev]" in source


def test_ci_keeps_explicit_job_timeouts() -> None:
    source = (WORKFLOW_ROOT / "ci.yml").read_text(encoding="utf-8")
    job_names = (
        "backend-quality",
        "dataset-contracts",
        "home-assistant-compatibility",
        "latest-home-assistant-smoke",
        "frontend",
        "frontend-e2e",
        "home-assistant-validation",
    )
    for job_name in job_names:
        block = re.search(
            rf"^  {re.escape(job_name)}:\n(?P<block>.*?)(?=^  [a-z0-9-]+:|\Z)",
            source,
            flags=re.MULTILINE | re.DOTALL,
        )
        assert block is not None, job_name
        assert re.search(r"^    timeout-minutes: [1-9][0-9]*$", block.group("block"), re.MULTILINE)


def test_dataset_signing_job_is_main_only_and_inputs_are_not_shell_interpolated() -> None:
    source = (WORKFLOW_ROOT / "datasets.yml").read_text(encoding="utf-8")
    assert "environment: dataset-release" in source
    assert "github.ref == 'refs/heads/main'" in source
    signing_start = source.index("  manual-build:")
    signing_job = source[signing_start:]
    assert '"${{ inputs.' not in signing_job
    assert "contents: write" in signing_job
