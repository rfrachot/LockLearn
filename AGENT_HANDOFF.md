# AGENT_HANDOFF.md

## Current state

P5.4 remains **COMPLETE / PASS** on `feat/p5-frontend`.

P5.5 remains **IMPLEMENTED / REAL-HA QUALIFICATION PENDING** in the repository
handoff. The P5.6 mission brief supplied a qualified P5.5 starting point; this
mission did not rerun the separate P5.5 UI gate.

P5.6 realistic-content scale qualification is **COMPLETE / PASS locally**.
This is the scale qualification requested by the mission brief and is distinct
from the roadmap's future P5.6 Dataset updates/Sources UI work.

P5.5 provides management routes for Profiles, Tracks, Packs and Settings. Profile owners can create/edit/archive/delete Profiles and manage HA-user sharing roles. Owners/editors can create/edit/delete Tracks, including direction, priority, content weights, scheduler learning/quiz demand and scoped notification targets. Viewers remain read-only.

Track planning is preview-first: the UI requests a non-mutating forecast before applying a LearningPlan. Forecasts surface required new cards/day, reviews/day at 3 weeks and 3 months, notification-deliverable workload and active-session spillover. PackVersion changes are also preview-first and require an explicit integration action after showing added/removed/changed learning-item counts.

Profile settings expose the preset as initial defaults only, session length, max new/day, daily push budget, quiet hours and the scheduler active window. Backend validation remains authoritative for all editable values.

Automated evidence on 2026-09-26:
- authoritative source-code gate `19ba314c74541e2add22713f98c8234103cd9d7c`;
- Ruff format PASS — 256 files;
- Ruff lint PASS;
- mypy PASS — 148 source files;
- resource registries PASS;
- pytest PASS — 391 tests;
- HA 2025.2.5 PASS — 298 backend tests;
- HA 2026.9.3 PASS — 298 backend tests;
- TypeScript PASS;
- Vitest PASS — 12 files / 34 tests;
- Vite PASS — 30 modules, 136.76 kB / 28.21 kB gzip;
- frontend bundle materialized at `adff7377420cf8a6648ba80469abbd5a5765ba4a`;
- normal bundle reproducibility PASS at `7a1af65e2963638ba5eb76a7b3052f633e7d2fe7`.

HACS metadata validation remains red only for repository description/topics/brand assets; this is release-packaging debt outside P5.5.

Remaining P5.5 gate: real HA 2026.7.4 qualification of Profile/ACL presentation, Track/settings mutations, workload preview-before-apply, PackVersion diff/integration when fixture content permits, keyboard/mobile behavior and clean logs.

Deployment safety for Luna/Codex:
- deploy the complete `custom_components/locklearn/` tree;
- never leave backup directories under `/config/custom_components`;
- never modify/remove Advanced SSH & Web Terminal credentials;
- temporary SSH_ASKPASS helpers only may be deleted.

P5.6 scale evidence is recorded in `docs/P5_6_REALISTIC_SCALE_QUALIFICATION.md`.
The local generated ZIP/database and raw JMdict download remain ignored build
artifacts; no private signing key was committed.

Scale qualification state:
- 20,000 LearningItems, 40,000 CardDefinitions, one PackVersion;
- signed package validation, schema/integrity/foreign-key validation, two
  generation activations and rollback all PASS;
- next-card selection p95 19.81 ms; session preparation 0.43 s after removing
  the observed unconstrained-pack N+1 constraint reads;
- REAL HA: NOT EXECUTED — HARNESS UNAVAILABLE.

Checks on 2026-09-26:
- Ruff format PASS;
- Ruff lint PASS;
- mypy PASS — 150 source files including the qualification harness;
- resource registries PASS;
- pytest PASS — 392 tests.

Commit: `feat(scale): qualify realistic content volume` (local only).
Push: not executed; explicit push authorization was not provided.
Next action: review the P5.5 real-HA gate separately, then decide whether to
promote the scale harness into a later CI/release qualification.
