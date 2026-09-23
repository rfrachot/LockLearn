# P3.8 real Home Assistant qualification

## Result

**P3.8 REAL HA QUALIFICATION — BLOCKED**

Tested on 2026-09-23 from `feat/p3-sessions` at
`7857143376c317f955bfd783196aeb5effea0982`.

The real-instance lifecycle, persistence and storage checks passed, but the
mandatory concurrent `session/answer` proof could not be executed. P3.8
deliberately does not prepare questions through the public `session/start`
command: the created real session therefore had `question_count=0` and
`current_question=null`. Question selection/preparation remains P3.9 scope.
The automated P3.8 harness covers answer CAS, but it is not accepted as real-HA
evidence for this gate.

## Environment

- Home Assistant Core: 2026.7.4
- Supervisor: 2026.09.2
- Home Assistant OS: 18.2
- LockLearn source: HACS download of `feat/p3-sessions`
- State migration observed on the real instance: schema 1 to schema 2
- Secrets, instance URL and private profile data were not retained

## Local gate

The repository gate passed in `.venv`:

- Ruff format: PASS, 188 files already formatted
- Ruff lint: PASS
- mypy: PASS, 104 source files
- resource registries: PASS
- pytest: PASS, 280 tests in 6.77 s

The system `python3` did not contain Ruff, so the verified project virtual
environment was used as required by `PROJECT.md`.

## Real-instance results

| Scenario | Result | Evidence |
|---|---|---|
| A — bootstrap | PASS | A temporary owner Profile and Track backed by the signed Japanese Starter pack created a persistent session. Type, strategy, settings, status, version and position round-tripped through `session/get`. |
| B — two WebSocket clients | PASS | Independent authenticated connections read identical version, position and current-question state; a second client subscribed successfully. |
| C — concurrent answer CAS | **BLOCKED** | No backend-prepared question is reachable through the P3.8 public API before P3.9. No answer-CAS claim is made. |
| C — lifecycle CAS control | PASS | Two clients paused from version 1 concurrently: exactly one succeeded, exactly one returned `locklearn/stale_session`, version advanced once and the subscriber received only version 2. |
| D — pause/resume | PASS | Cross-client pause and resume persisted; an obsolete version returned `locklearn/stale_session` without publishing an event. |
| E — disconnect/reconnect | PASS | After subscriber disconnect, a new connection reconstructed version, status, position, current question, answers, settings and strategy from persistent state. |
| F — integration reload | PASS | A real Config Entry reload preserved the exact session snapshot. One panel and one LockLearn Config Entry remained. A pre-reload subscription received no post-reload mutation, while new connections and mutations worked. |
| G — completion | PASS | Completion incremented the version and populated `completed_at_utc`. Resume, answer and navigation undo were then rejected with `locklearn/stale_session` and did not alter the completed snapshot. |
| H — owner ACL | PASS (partial) | The authenticated Profile owner could start, read, subscribe and mutate the session through backend ACL checks. |
| H — viewer/outsider ACL | NOT EXECUTED | Only one HA access token was configured. Viewer and invisible-user behavior remains covered only by the automated harness; no real-instance proof is claimed. |
| I — storage/lifecycle | PASS | Before and after reload: `integrity_check=ok`, zero FK violations, WAL, reader off the event loop and initialized writer. No LockLearn ERROR/CRITICAL record was present in `system_log`. |

The initial P0 runtime contained three sessions and three answers. After schema
migration, qualification and cleanup, those same counts remained, providing a
targeted no-loss lifecycle check. The temporary Profile, Track and session were
removed; no qualification Profile remained.

## Required follow-up

Do not mark P3.8 PASS and do not begin P3.9 from this result alone. Complete the
mandatory real-HA answer race by providing a non-shipping, backend-owned way to
prepare at least one valid `SessionQuestion` inside the live HA runtime (or an
equivalent supported development-instance fixture), then verify:

- exactly one same-version `session/answer` winner;
- exactly one `locklearn/stale_session` loser;
- one version/position advance and one immutable answer row;
- winner-only subscription publication;
- reconnect and reload preservation of that answer history.

If real viewer/outsider ACL evidence is desired in the same rerun, configure a
second HA development user token; never infer that result from the owner token.
