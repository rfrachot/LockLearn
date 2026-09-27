# AGENT_HANDOFF.md

## Current state

Branch: feat/p6-hardening.

P5 and its real-HA exit gate remain PASS. P6.1 through P6.6 are PASS.

P6.7 — performance, scale and storage-budget validation — is implementation
complete. Automated/reference-hardware qualification is pending. No P6.8 work
has started.

## P6.7 implementation

The existing scripts/p5_9_performance.py remains authoritative for the V1
session-answer, next-card and scheduler wall-clock budgets.

New scripts/p6_7_scale_validation.py adds:
- the same P5.9 hot-path gate;
- a 60,000-card normalized content build/activation measurement;
- a 1,826-day state.db materialization using the real STATE_SCHEMA;
- Standard assumptions of 8 new cards/day, 80 verified reviews/day from P3.14,
  four 20-card sessions/day, six notification slots/day and two audit rows/day;
- SQLite integrity/FK/page geometry, row-count, bytes/day and MiB/year output.

Dataset storage policy is centralized at 150 MiB per official artifact, a
500 MiB aggregate reconstructible-cache warning, and activation free space of
at least 2x estimated generated content plus a 32 MiB safety margin. New builds
sign a floor and runtime recomputes a package-set floor for historical manifests.

Bounded process-local metrics now cover writer queue wait, session answer,
scheduler generation and clock drift, content build and content activation.
They expose aggregate-only count/last/p95/max values and never become HA
sensors. No schema migration or frontend production-source change is involved.

ADR-0052 documents these choices.

## Luna qualification contract

Luna must ONLY execute tests and report results. It must not edit, format,
commit, push, merge or start P6.8.

Run:

~~~bash
git pull --ff-only origin feat/p6-hardening
git status --short --branch
git rev-parse HEAD

.venv/bin/python -m pytest -q --tb=short \
  tests/backend/test_observability.py \
  tests/backend/test_storage.py \
  tests/backend/test_scheduler.py \
  tests/backend/test_diagnostics.py \
  tests/datasets/test_build_pipeline.py \
  tests/datasets/test_dataset_manager.py

.venv/bin/python scripts/p5_9_performance.py
.venv/bin/python scripts/p6_7_scale_validation.py

python3 -VV
uname -a
lscpu
free -h
df -h .

.venv/bin/python -m ruff format --check .
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy custom_components datasets tests
.venv/bin/python datasets/tools/validate_resources.py
.venv/bin/python -m pytest -q --tb=short

cd frontend
npm run typecheck
npm test
npm run build
cd ..
sha256sum custom_components/locklearn/frontend/locklearn-panel.js

git diff --check
git status --short --branch
git rev-parse HEAD
~~~

P6.6 reference frontend bundle hash:
d1626186b8fe1cf50f81efb5a4f3dd05de3dd54e22ec86b20612000c9b259385

Because P6.7 changes no frontend production source, the bundle is expected to
remain byte-identical. Any difference must be reported rather than committed.

## Report required from Luna

Return:
1. tested HEAD;
2. targeted pytest result;
3. complete P5.9 JSON;
4. complete P6.7 scale JSON;
5. Python/kernel/CPU/RAM/filesystem facts;
6. exact five-year state.db size and MiB/year;
7. 60k package/candidate size and build/activation time;
8. Ruff, mypy, resources and full pytest results;
9. frontend typecheck/test/build result;
10. final frontend bundle hash;
11. final git status;
12. every warning/anomaly.

P6.7 remains qualification-pending until those measurements are reviewed.
