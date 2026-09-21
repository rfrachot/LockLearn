# AGENT_HANDOFF.md

## Current state

P0.1–P0.7 are complete on `feat/p0-foundation`. All four real-instance gates
are qualified and the P0 architecture gate is closed. The next planned phase is
P1; no P1 implementation has started.

## Branch / releases

- Branch: `feat/p0-foundation`
- Released/tagged commit: `95cc173 chore(release): prepare 0.0.2`
- GitHub releases: `v0.0.1`, `v0.0.2`
- Repository: public after a history secret audit
- HACS live instance: `v0.0.2` installed
- Remote feature branch was not pushed; only release tags were pushed with
  explicit authorization.

## P0.7 outcome

- Gate A — HACS / Config Flow / panel: PASS
- Gate B — Android Companion: PASS as a capability qualification; same-tag
  replacement worked, but incomplete silent-replacement evidence keeps tested
  targets on the conservative `exposure_only` path.
- Gate C — HAOS/Supervisor backup/restore: PASS; pre-backup state restored,
  post-backup state absent, integrity `ok`, writer/readers/panel/API healthy.
- Gate D — iPadOS Companion: PASS as a capability qualification; missing tag
  replacement and unreliable visibility require `exposure_only`.

Exact sub-test statuses, devices, timings, limitations and backup scope are in
`docs/P0_EVIDENCE.md`. ADR-0006 freezes notification fallbacks; ADR-0007 freezes
HACS/panel serving. `SPEC_V1.md` now states that lockscreen visibility is not a
security boundary.

## Corrections and tooling

- Actionable notifications resolve to data-capable `notify.mobile_app_*`
  actions; generic notify entities are plain-message only.
- Admin-only storage health reports SQLite integrity without private rows.
- `scripts/p0_real_instance.py` reproduces Companion probes without secrets.
- `scripts/p0_backup_restore.py` reproduces the controlled Supervisor
  backup/restore markers and verification; it never triggers restore.
- `.env` loaders accept only `LOCKLEARN_HA_*` and never print values.

## Verification

- Ruff format/check: pass (98 files).
- mypy (`custom_components datasets tests scripts`): pass (44 source files).
- pytest HA 2026.9.3 / Python 3.14.4: 30 passed.
- pytest backend HA 2025.2.5 / Python 3.13.15: 24 passed.
- dataset validation: pass.
- frontend typecheck + 3 Vitest tests + production build: pass; bundle 21.96 kB
  / 7.13 kB gzip.
- npm audit: 0 vulnerabilities.
- hassfest: 1 integration, 0 invalid.
- real post-restore system log: no LockLearn match; exactly one loaded Config
  Entry; HACS `v0.0.2` installed.

## Remaining risks / next action

- Android channel importance is user-controlled and not observable through HA;
  do not infer it.
- Samsung produced a second vibration with `alert_once`; Pixel silence was not
  isolable because its initial delivery did not vibrate.
- iPadOS action events omitted device/tag, same-tag replacement failed, and
  visibility values did not redact lockscreen content.
- Persistent notification replay/single-use is intentionally P4 work;
  Profile/shared-device ACL is intentionally P2 work.
- HAOS included `ssl` in the partial test backup despite an empty requested
  folder list; always show actual restore scope.

Next concrete action: review the local P0 closure commits, then start a separate
P1 mission/branch only when requested. Do not retag or mutate `v0.0.2`.
