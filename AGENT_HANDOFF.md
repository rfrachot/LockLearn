# AGENT_HANDOFF.md

## Current state

P5.4 remains **COMPLETE / PASS** on `feat/p5-frontend`.

P5.5 is **IMPLEMENTED / REAL-HA QUALIFICATION PENDING**. P5.6 has not started.

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

Do not start P5.6 until P5.5 real-HA qualification is recorded.
