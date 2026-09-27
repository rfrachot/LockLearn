# ADR-0052 — P6.7 performance, scale and storage-budget qualification

## Status

Accepted and qualified on 2026-09-27. P6.7 is PASS.

## Context

The V1 specification already defines measurable hot-path budgets: session
answer p95 below 100 ms, next-card selection p95 below 150 ms and scheduler
slot generation below 250 ms/Profile/day. It also requires a documented and
tested five-year state.db estimate, content activation measured by corpus size,
a 150 MiB default official-artifact ceiling, a warning above 500 MiB cumulative
installed dataset data, and activation with at least twice the generated-content
footprint plus margin.

P5.9 already owns the permanent wall-clock gate for the three hot paths. P6.7
must not fork a second implementation merely to rename the phase.

The spec defines neither a numeric maximum for five-year state.db nor one
corpus-independent activation-time ceiling. Inventing either would turn an
observation into an unsupported release gate.

## Decision

### Reuse the existing hot-path gate

scripts/p5_9_performance.py remains authoritative for session answer,
next-card selection and scheduler generation. P6.7 invokes the same benchmark
code and preserves its budgets.

### Qualify content at the P0 representative scale

P6.7 materializes a normalized 60,000-card synthetic package through the real
content schema and ContentGenerationBuilder, then measures build and atomic
activation separately. The report includes package/candidate/active sizes,
build/activation durations, per-10k-card rates and database-attachment bounds.

These activation numbers are evidence, not a new threshold. A new release gate
requires documented measurements or an explicit spec change.

### Materialize five years of the real state schema

The reference projection covers 1,826 days and reuses established project
assumptions:
- 8 new cards/day from the Standard Profile preset;
- 80 verified reviews/day from the P3.14 Standard quality-bench capacity;
- four sessions of 20 cards/day;
- six notification slots/interactions/receptivity samples/day;
- two small audit events/day.

The projection checkpoints WAL and reports integrity/FK status, SQLite page
geometry, file bytes, bytes/day, MiB/year and table row counts. There is no
PASS/FAIL size ceiling because none is normative.

### Centralize dataset storage budgets

The default official artifact ceiling is 150 MiB and the aggregate
reconstructible dataset-cache warning is 500 MiB.

The V1 activation safety margin is 32 MiB. The free-space floor is:

    required_free_disk >= 2 * estimated_generated_content + 32 MiB

For new dataset builds, the signed manifest requirement is raised to at least
the generated dataset-DB floor. At runtime LockLearn also recomputes a
package-set estimate and uses the maximum of that floor and the signed
requirement. Historical signed packages therefore remain compatible without
being trusted to declare enough free space.

The 500 MiB threshold is warning-only, configurable on DatasetManager,
auto-clears below threshold and never makes last-known-good content unusable.

### Keep metrics internal and privacy-safe

The process-local collector retains at most 256 samples per fixed metric and
exposes only aggregate count/last/p95/max values. It records writer-queue wait,
session-answer latency, scheduler slot generation, detected scheduler clock
drift/jump, content build duration and content activation duration.

Metric names are code-owned, values are numeric timings, samples are not
persisted and no HA sensor/entity is created. Redacted diagnostics may include
these aggregate timings. Existing Repairs and diagnostics remain authoritative
for unresolved targets and operational failures.

## Consequences

- P6.7 changes no database schema and needs no migration.
- P6.7 changes no frontend production source; the committed bundle should stay
  byte-identical during qualification.
- Wall-clock timings are not asserted inside ordinary pytest, avoiding
  machine-dependent flaky tests.
- Reference-hardware JSON from P5.9 and the P6.7 scale harness is required
  before the plan is marked PASS.
- Optimization remains evidence-driven: a budget miss must be profiled before
  code is tuned.

## Qualification evidence

Reference qualification ran at HEAD
`f05aab04b48baf8f8f73937cb8b3c5039e4d5b3d` on CPython 3.14.4 / Linux 7.0
with 6 logical CPUs and 15 GiB RAM.

- P5.9: session answer p95 1.137 ms, next-card p95 62.046 ms, scheduler-day
  p95 4.064 ms; all normative budgets passed.
- Integrated P6.7 hot paths: 1.150 ms, 65.403 ms and 3.983 ms respectively.
- 60,000 cards: 137,302,016-byte package, 177,299,456-byte candidate/active
  generation, 4.724 s build, 1.640 s activation.
- Activation free-space requirement: 388,153,344 bytes; gate passed.
- 1,826-day state projection: 218,955,776 bytes, 41.74 MiB/year,
  integrity_check=ok and zero foreign-key violations.
- Ruff format/lint, mypy, resource validation, targeted/full pytest and
  frontend typecheck/tests/build passed. The frontend bundle remained unchanged.
