# AGENT_HANDOFF.md

## Current state

P0.1–P0.6 automated foundations are implemented on `feat/p0-foundation`.
Evidence and explicit manual gaps are in `docs/P0_EVIDENCE.md`; P0.7 is not
started and notification decisions are not frozen.

## Branch / commit

- Branch: `feat/p0-foundation`
- Implementation commit: `e01775c feat: implement P0 foundation spikes`
- No push, PR, merge, tag or release was performed.

## Delivered

- HA 2025.2/current CI matrix, real HA test harness, HACS/hassfest jobs;
- single Config Entry, bundled/versioned panel, clean setup/unload/reload;
- thread-confined SQLite, state/content split, merge benchmark and backup hooks;
- capability-gated notifications, stable device target resolution, unattended audit;
- persistent session CAS, cross-user denial, subscriptions and cancellable operations;
- ADR-0003 through ADR-0005 and missions M-002 through M-004.

## Verification

- Ruff format/check: pass.
- mypy (`custom_components datasets tests`, plus scripts): pass.
- pytest current HA 2026.9.3/Python 3.14.4: 21 passed.
- pytest HA 2025.2.5/Python 3.13.15 backend matrix: 20 passed.
- dataset validation: pass.
- frontend typecheck + 3 Vitest tests + build: pass; bundle 21.96 kB / 7.13 kB gzip.
- npm audit: 0 vulnerabilities.
- hassfest Docker validation: 1 integration, 0 invalid.
- configured HA API inventory: reachable on 2026.7.4; two Android phones and one
  Android watch found; no iOS target.
- HACS validation is wired in CI; local Docker action was not claimed because it
  requires a GitHub token.

## Remaining risks / next action

Select an explicit Android device, add/select an iOS device, configure
`LOCKLEARN_HA_*_DEVICE_ID` and run the Companion gesture/lockscreen/TTL matrix.
Also configure `LOCKLEARN_HA_CONFIG_DIR` to install through HACS, verify the
panel in a browser and perform a real Supervisor backup/restore. Record those
results before P0.7 freezes notification, backup and panel ADRs.
