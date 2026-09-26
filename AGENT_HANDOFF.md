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

Roadmap P5.6 — Dataset updates, Sources & Licences UI — is **IMPLEMENTED /
AUTOMATED QUALIFICATION PASS / REAL-HA PENDING**.

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

The earlier realistic-content scale qualification remains **PASS** and is
separate from roadmap P5.6. Evidence: 20,000 LearningItems, 40,000
CardDefinitions, next-card p95 19.81 ms, generation activation/rollback PASS.

## Remaining gate

REAL HA P5.6 has not been executed in this session because the real HA/browser
harness is not available here. Qualify on the development HA instance:
1. open Sources & Licences as an HA admin;
2. verify installed/version/source-age/cache/changelog and provenance/licence;
3. expand individual attribution details where fixture content provides them;
4. run check-for-updates without changing content unexpectedly;
5. verify a non-admin can read provenance but cannot refresh/install;
6. if a safe update fixture/version exists, verify install → activation and
   explicit Track PackVersion pinning remains unchanged;
7. verify keyboard/mobile layout and clean LockLearn logs;
8. clean temporary fixtures.

After REAL HA PASS, mark P5.6 complete and proceed to P5.7.

Deployment safety:
- deploy the complete `custom_components/locklearn/` tree;
- never leave backup directories under `/config/custom_components`;
- never modify/remove Advanced SSH & Web Terminal credentials;
- temporary SSH_ASKPASS helpers only may be deleted.
