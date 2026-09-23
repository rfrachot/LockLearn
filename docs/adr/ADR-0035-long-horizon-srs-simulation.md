# ADR-0035 — Deterministic long-horizon SRS simulation gate

## Status

Proposed for P3.14 on 2026-09-23. Implementation pending repository and
simulation quality gates.

## Context

The V1 SRS policy is intentionally simple, deterministic and explainable, but
local transition tests are not sufficient to prove that the defaults remain
usable over months of continuous introductions and imperfect recall.

P3.14 therefore needs a reproducible quality gate that can expose:

- due-queue explosion;
- review starvation;
- relearning oscillation;
- over-promotion despite poor verified accuracy;
- unrealistic daily interaction load.

The gate must exercise the real V1 learning/review transition code rather than a
separate approximate scheduler model.

## Decision

### The simulator uses production transition primitives

`LongHorizonSRSSimulator` uses:

- `LearningStateMachine`;
- `ReviewPolicyV1`;
- `LeechPolicyV1`;
- the real profile preset new-card quotas.

Synthetic time is supplied through an injectable simulation clock. Outcomes are
derived deterministically from SHA-256 over the declared scenario seed, card
identity, day, stage and attempt. No global RNG or wall clock participates.

### The declared horizon is 180 days

The default matrix keeps a six-month supply of new cards available so the
review system is evaluated under sustained load rather than a small fixed deck
that quickly reaches steady state. `max_new_per_day_cards` remains a ceiling,
not a forced daily injection: when the opening due queue consumes the declared
review/session capacity, the simulator throttles new introductions first, just
like the runtime session selector reserves due work before new cards.

The default new-card quotas are the production preset values:

- child: 3 CardDefinitions/day;
- standard: 8 CardDefinitions/day;
- intensive: 15 CardDefinitions/day.

### Review capacities are quality-bench assumptions, not product defaults

The positive quality scenarios declare review capacities of ten times the
corresponding new-card quota:

- child: 30 review cards/day;
- standard: 80 review cards/day;
- intensive: 150 review cards/day.

These values are explicit simulation assumptions. They are not written into
Profile defaults or Track settings by P3.14.

A deliberately constrained stress scenario is included as a negative control.
At least one sustainability detector must fire in that scenario, proving the
gate is capable of failing. Reports also expose `throttled_new_cards` and
`throttled_new_days` so sustainability cannot hide the cost of deferring new
material.

### Response patterns are deterministic and diverse

The default matrix includes:

- typical learner: high learning-step success and ~90% long-review success;
- mixed learner: moderately higher error rate;
- bursty learner: generally healthy recall with periodic low-retention days;
- stress learner: deliberately poor retention under constrained capacity.

The negative stress scenario is not required to be sustainable.

### Sustainability detectors are explicit

A scenario is flagged when any of these conditions occur:

- sustained/final due backlog exceeds declared capacity bounds;
- a card remains overdue for more than seven days;
- short-step cap exhaustion becomes systemic: at least one card hits the cap
  repeatedly, or cap-hit cards reach at least 1% of introduced cards;
- a card reaches a box that cannot be justified by its accumulated verified
  successes (box > 1 + verified_correct_count, capped at box 7);
- p95 daily interactions exceed the declared review capacity plus the expected
  short-step cost of new cards and a 50% review-capacity burst margin.

The thresholds are quality-gate assumptions and are recorded in the simulator
instead of being hidden in tests.

### Defaults are not tuned without evidence

P3.14 initially changes no SRS interval, difficulty, relapse or preset quota
default.

If a required scenario fails, the failing metrics must be documented first.
Any subsequent default change must cite before/after simulation output and be
covered by the same deterministic gate.

### CI and local execution

`tests/backend/test_srs_simulation.py` proves deterministic replay, preset
coverage, sustainability of required scenarios, bounded quota behavior and
negative-control detector sensitivity.

`python3 scripts/p3_14_srs_simulation.py` prints machine-readable JSON for the
declared matrix and exits non-zero if:

- any required-sustainable scenario fails; or
- the negative-control scenario unexpectedly passes all detectors.

## Consequences

- P3.14 adds no runtime state, WebSocket endpoint or database migration.
- The quality gate can run without Home Assistant or external services.
- Long-horizon results are reproducible from code and declared scenario inputs.
- Product defaults remain unchanged unless measured evidence justifies tuning.
- P3 can close only after both the repository gate and the simulation script are
  green.
