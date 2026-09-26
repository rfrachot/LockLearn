# AGENT_HANDOFF.md

## Current state

Branch: `feat/p5-dataset-ui`.

P5.5 is **COMPLETE / REAL-HA PASS**. The 2026-09-26 real-instance gate covered
Profile CRUD/settings, Track configuration, workload preview-before-apply,
aggressive-quota warning, keyboard operation, clean LockLearn logs and cleanup.
ACL role presentation, notification targets and PackVersion diff were fixture
unavailable on that instance; automated backend coverage remains authoritative
for those paths. Firefox WebDriver's 500 px minimum remains a harness limit for
the exact narrow-mobile viewport.

Roadmap P5.6 — Dataset updates, Sources & Licences UI — is **PASS**.

P5.6 provides:
- a dedicated Sources & Licences route;
- installed and available dataset versions, update state, source age/staleness,
  reconstructible cache size and release changelog;
- provenance and licence details sourced from the active signed content
  generation, not frontend constants;
- paginated per-record attribution details for sources that require individual
  attribution;
- visibility of installed datasets outside the official discovery registry;
- HA-admin-only catalog refresh and verified install actions, with read-only
  provenance/licence visibility for authenticated panel users;
- HTTP(S)-only external links for untrusted catalog/source metadata.

Backend mutations still delegate to DatasetManager, preserving host allowlists,
checksum/signature/schema/licence validation, staging, atomic activation and
rollback. No new dataset trust path was introduced.

Automated qualification on 2026-09-26:
- authoritative gate: `99351bb0e1d996835495c788a2b99aae9091fcd0`;
- Ruff format PASS — 259 files;
- Ruff lint PASS;
- mypy PASS — 149 source files;
- resource registries PASS;
- pytest PASS — 393 tests;
- HA 2025.2.5 PASS — 300 backend tests;
- HA 2026.9.3 PASS — 300 backend tests;
- TypeScript PASS;
- Vitest PASS — 13 files / 37 tests;
- Vite PASS — 31 modules, 155.07 kB / 31.41 kB gzip;
- committed frontend bundle reproducibility PASS.

The generated bundle was materialized by GitHub Actions and committed before the
final reproducibility gate. The temporary branch-only qualification workflow was
removed afterward; no PR, merge, tag or release was created.

REAL HA qualification on 2026-09-27 passed on Home Assistant 2026.7.4 after
deploying the complete tree from this branch and restarting Core. Firefox
verified the route and backend-fed dataset facts, admin refresh, 722-record
individual attribution fixture with pagination, keyboard actions and HTTP(S)
source/licence/release links. The installed and discovered versions were both
1.0.0; refresh left the content hash and PackVersion unchanged. No Track, safe
new release, invalid/repaired state or second non-admin token was available, so
those scenarios are explicitly `FIXTURE UNAVAILABLE`. Firefox's requested
390-pixel viewport was clamped to 500 px (`HARNESS LIMIT`); the available mobile
viewport had no horizontal overflow or off-screen action.

The first log pass found a blocking synchronous read of bundled registry JSON
during runtime creation. `runtime.py` now loads all five registries through
`hass.async_add_executor_job`, with a lifecycle regression assertion; the
post-fix redeployment/restart produced no LockLearn WARNING, ERROR or CRITICAL
system-log entries. The authoritative post-fix gates passed Ruff format/lint,
mypy (149 sources), resource registries, pytest (393 tests), TypeScript, Vitest
(13 files / 37 tests), Vite (155.07 kB / 31.41 kB gzip) and bundle diff.

The earlier realistic-content scale qualification remains **PASS** and is
separate from roadmap P5.6. Evidence: 20,000 LearningItems, 40,000
CardDefinitions, next-card p95 19.81 ms, generation activation/rollback PASS.

## Next action

P5.6 is complete. P5.7 may be considered separately; it was not started by
this qualification mission.

Deployment safety:
- deploy the complete `custom_components/locklearn/` tree;
- never leave backup directories under `/config/custom_components`;
- never modify/remove Advanced SSH & Web Terminal credentials;
- temporary SSH_ASKPASS helpers only may be deleted.
