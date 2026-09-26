# AGENT_HANDOFF.md

## Current state

P5.2 is **COMPLETE / PASS** on `feat/p5-frontend`. P5.3 has not started.

The branch component was deployed directly to the real Home Assistant 2026.7.4
instance through the existing Advanced SSH & Web Terminal add-on, using a staged
full-tree copy and same-filesystem rename. HACS was not used. The deployed
backend is schema 5 and the local/HA bundle SHA-256 is
`c9663f02f2ef7443bbbb8a04ab88cc0be363889144deb077b932d145bb7913b8`.

After Core restart, the sole LockLearn Config Entry is loaded, storage reports
`integrity_check=ok`, zero foreign-key violations and schema 5, and the system
log contains no LockLearn `ERROR`/`CRITICAL` record. `state.db` was never
deleted, recreated, downgraded or manually modified.

Firefox 156 real-instance qualification passed Home empty and Track-card states,
honest `1/2 répondues` rendering, personal-first owner grouping, Profile switch
with only one new dashboard request, full reload with exactly one
bootstrap/profile-list/dashboard sequence, and the responsive three-column
layout without horizontal overflow. The P5.1 regression soak passed 700 `hass`
reassignments over three minutes with no extra request, loading flash or loop.

The temporary qualification Profile/Track/session was created and deleted only
through public APIs; storage counters returned to baseline. A second HA test
user is unavailable, so the real share/outsider scenario remains covered by the
automated backend ACL tests.

The previously exposed HA development token still requires rotation. Renaud has
explicitly deferred that security debt; do not remove it from documentation.

Final repository gate on 2026-09-26: Ruff format PASS (250 files), Ruff lint
PASS, mypy PASS (143 sources), resource registries PASS, pytest PASS (380 tests
in 19.36 seconds), TypeScript PASS, Vitest PASS (9 files / 22 tests), Vite PASS
(25 modules, 45.13 kB / 12.55 kB gzip), and committed-bundle reproducibility
PASS.

Next concrete action: begin P5.3 only when explicitly requested.
