# AGENT_HANDOFF.md

## Current state

Branch: `feat/p6-hardening`.

P5 and its real-HA exit gate remain PASS. P6.1 through P6.7 are PASS.

P6.7 — performance, scale and storage-budget validation — is fully implemented
and qualified. No P6.8 implementation has started.

## P6.7 qualification

Qualified on 2026-09-27 at HEAD:

`f05aab04b48baf8f8f73937cb8b3c5039e4d5b3d`

Reference VM:
- CPython 3.14.4;
- Linux 7.0.0-30-generic x86_64;
- 6 logical CPUs;
- 15 GiB RAM.

Permanent P5.9 budgets:
- session answer p95: 1.137 ms / 100 ms budget;
- next-card p95: 62.046 ms / 150 ms budget;
- scheduler-day p95: 4.064 ms / 250 ms budget.

Integrated P6.7 run:
- session answer p95: 1.150 ms;
- next-card p95: 65.403 ms;
- scheduler-day p95: 3.983 ms.

60,000-card content scale:
- package: 137,302,016 bytes;
- candidate/active generation: 177,299,456 bytes;
- build: 4.724 s;
- activation: 1.640 s;
- required activation free space: 388,153,344 bytes;
- free-space gate: PASS;
- maximum attached databases: 2.

Five-year state projection:
- 1,826 days;
- state.db: 218,955,776 bytes;
- 41.74 MiB/year;
- 146,080 review events;
- 14,608 progress rows;
- integrity_check: ok;
- foreign-key violations: 0.

Quality gates:
- Ruff format: PASS — 285 files formatted;
- Ruff lint: PASS;
- mypy: PASS — 166 sources;
- resource validation: PASS;
- targeted pytest: 57 passed;
- full pytest: 464 passed, one known duplicate `profile.json` ZIP warning;
- frontend typecheck: PASS;
- frontend tests: 49 passed / 15 files;
- frontend build: PASS;
- git diff check: PASS.

Frontend bundle unchanged:

`d1626186b8fe1cf50f81efb5a4f3dd05de3dd54e22ec86b20612000c9b259385`

## P6.7 architecture retained

- P5.9 remains authoritative for normative session-answer, next-card and
  scheduler wall-clock budgets.
- `scripts/p6_7_scale_validation.py` remains the scale/storage evidence harness.
- Dataset policy remains 150 MiB per official artifact, 500 MiB aggregate-cache
  warning and activation free space >= 2x estimated generation + 32 MiB margin.
- Runtime metrics remain bounded, process-local, aggregate-only and never become
  Home Assistant sensors.
- No DB schema migration or frontend production-source change was required.

ADR-0052 contains the design and final qualification evidence.

## Next work

P6.8 — Full test matrix and CI release gates.

Do not reopen P6.7 unless a regression, spec change or materially different
reference-hardware result requires it.
