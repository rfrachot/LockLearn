# P3.8 real Home Assistant qualification

## Result

**P3.8 REAL HA QUALIFICATION — PASS**

Tested on 2026-09-23 from `feat/p3-sessions` at
`417ff41df90cf137e2751320d72e3166bdc0793b`.

The qualification uses only the public P3.9 path:

```text
locklearn/session/start
-> backend selection
-> persisted backend-owned current_question
-> locklearn/session/answer
```

No client-prepared question, test fixture, direct `SessionQuestion` injection,
state.db mutation or ACL bypass was used. The reproducible, secret-safe harness
is `python -m scripts.p3_8_real_ha_qualification`.

## Environment and deployment

- Home Assistant Core: 2026.7.4
- LockLearn source: HACS `rfrachot/LockLearn`, explicitly redownloaded from
  `feat/p3-sessions`, then Home Assistant Core restarted.
- The first probe detected an older HACS artifact despite its branch label:
  public `session/start` returned zero questions and no P3.9 `fatigue_advice`.
  After the explicit branch download/restart, it returned two selected questions,
  a current question and fatigue advice.
- Secrets, instance URL, Profile IDs and learning content are not retained here.

## Real-instance results

| Scenario | Result | Evidence |
|---|---|---|
| A — P3.9 bootstrap | PASS | A temporary owner Profile plus a real Track pinned to the signed Japanese Starter PackVersion started a bounded session with `question_count=2`, a non-null current question, real CardDefinition identity and a non-empty backend-pinned `dataset_generation`. |
| B — concurrent `session/answer` | PASS | Two independent authenticated WebSockets reconstructed the same `(session_id, version=1, question_id)` snapshot. Sent concurrently, primary won and advanced to version 2; the other client received exactly `locklearn/stale_session`. The session snapshot had one answer attempt and the privacy-safe state.db diagnostic answer count rose by exactly one. |
| B — subscriber | PASS | The subscribed client received only the winning version-2 mutation; the stale answer did not publish a notification. |
| C — navigation undo | PASS | `session/undo` at version 2 advanced to 3, restored the original question as current and retained the one immutable answer row. An undo with the stale version failed with `locklearn/stale_session`. This is the P3.8 navigation/audit path only; it does not claim P3.12 pedagogical undo or alter ReviewEvents/Progress. |
| D — reconnect | PASS | After subscriber disconnect, a new client reconstructed the persisted version-3 snapshot and its one answer row through `session/get`. |
| D — Config Entry reload | PASS | A real `homeassistant.reload_config_entry` preserved that same session snapshot. The pre-reload process-local subscription received no subsequent event; a new subscription received the post-reload pause mutation. Exactly one LockLearn Config Entry and one panel remained. |
| E — storage/logs | PASS | Before/after: `integrity_check=['ok']`, zero FK violations, WAL mode, reader off the event loop and initialized writer. No new LockLearn ERROR/CRITICAL `system_log` record appeared. |
| F — cleanup | PASS | Public Profile deletion removed all temporary Profile/Track/session/audit state. The runtime returned to its baseline of three sessions and three answer rows; no temporary Profile remained. |

`session/undo` executed the append-only P3.8 `session_undo_navigation` writer
path; the public diagnostic intentionally exposes only privacy-safe aggregates.
The same audit insertion and the no-ReviewEvent/no-Progress-mutation boundary
remain covered by the focused automated P3.8 tests. The real run specifically
exercised that path without any database injection or deletion.

## ACL qualification

Owner ACL was exercised by every public operation above. The repository contains
one configured development-user access token only; no second usable development
token was found without searching outside the declared environment.

**viewer/outsider real-HA ACL remains BLOCKED — second HA development-user token unavailable.**

This is supplemental evidence, not a formal P3.8 exit blocker: the P3.8 exit
criteria are the one-winner answer CAS and cross-client resume, both now proven
on real HA. Viewer/outsider behavior remains additionally covered by the
automated authenticated-WebSocket harness and ADR-0029's ACL contract.

## Repository verification

Final post-qualification gate in the project virtual environment:

- `python3 -m ruff format --check .`: PASS, 193 files already formatted.
- `python3 -m ruff check .`: PASS.
- `python3 -m mypy custom_components datasets tests`: PASS, 106 source files.
- `python3 datasets/tools/validate_resources.py`: PASS.
- `python3 -m pytest -q --tb=short`: PASS, 287 tests in 6.85 s.
