# ADR-0029 — Persistent session CAS and cross-client resume

## Status

Accepted for P3.8 on 2026-09-22, pending final quality gate.

## Context

LockLearn sessions must survive browser/mobile disconnects and be resumable from
another Home Assistant client. The session state lives in Home Assistant, not
inside a frontend tab.

The V1 specification requires persistent Session metadata, question state,
optimistic concurrency through a monotonically increasing version, one-winner
answer CAS, WebSocket subscriptions, pause/complete/undo boundaries and
cross-platform resume.

P3.8 must establish those persistence/concurrency semantics without absorbing
P3.9 card selection/fatigue policy or P3.12 pedagogical ReviewEvent undo.

## Decision

### Session is the authoritative resumable state

The existing state.db Session tables are now used as the complete persisted
runtime state:

- sessions stores profile/track/type/strategy/status/version/timestamps,
  question_count/current_position and settings_json;
- session_items stores the prepared question identity, status and renderer
  payload;
- session_answers stores immutable answer attempts keyed by resulting session
  version.

session/get returns one complete snapshot containing metadata, settings, items,
answer history and the current question derived from current_position.

### Question preparation is backend-owned

SessionService accepts prepared SessionQuestion objects from backend code.

Each prepared question is validated against:

- the real Profile/Track relationship;
- enabled Track card rules;
- the exact active CardDefinition identity.

The service overwrites the persisted question payload's dataset_generation with
the backend's current active content generation. A caller cannot pin an
arbitrary generation.

The public session/start WebSocket does not accept raw prepared questions.
P3.9 will later own candidate selection/interleaving and will call the same
backend preparation boundary.

### Version is the CAS token

Every mutable session operation takes expected_version.

For session/answer, the SQLite writer transaction verifies all of:

- session exists;
- status is active;
- stored version equals expected_version;
- question_id equals the question at current_position;
- that question is still queued/presented.

Only then does it atomically:

- mark the current item answered;
- present the next item when one exists;
- advance current_position;
- increment version;
- append session_answers.

Two clients using the same version/question therefore cannot both win.

Pause, resume, complete and navigation undo are also CAS mutations and increment
the same version.

### Lifecycle transitions

P3.8 supports:

- active -> paused;
- paused -> active;
- active/paused -> completed.

Completed sessions cannot be resumed.

The indicative V1 API has one session/pause command; P3.8 uses
paused=true/false to pause or resume without inventing a second public command.

### Subscription

session/subscribe returns the current persistent snapshot and registers a
process-local WebSocket listener.

Every successful answer/lifecycle/undo mutation publishes the new persistent
snapshot. Stale/failed mutations publish nothing.

Disconnect cleanup removes the subscription, while the session itself remains
in state.db.

### Session undo boundary

P3.8 implements only session-navigation undo.

The last answered session item can be reopened through CAS while preserving the
original session_answers row and appending a private session_undo_navigation
audit event. The historical answer is never deleted.

This operation does not alter ReviewEvent/progress state.

Safe pedagogical undo using pre_state_snapshot or a compensating ReviewEvent
remains P3.12. P3.8 therefore does not pretend that rewinding the UI cursor is
equivalent to undoing SRS history.

### ACL

All public session commands use real Profile ACL:

- READ for get/subscribe;
- ANSWER for start/answer/pause/resume/complete/undo.

There is no HA-admin bypass.

An invisible Profile follows the existing privacy-preserving not_found behavior;
a visible viewer receives forbidden for mutation.

## Consequences

- a browser/device can reconnect and reconstruct the current session entirely
  from state.db;
- simultaneous clients have a single concurrency token and cannot double-answer
  a question;
- prepared question identity survives client switches and carries the content
  generation it was presented from;
- session subscriptions are synchronization helpers rather than the source of
  truth;
- P3.9 can add selection/interleaving without changing concurrency semantics;
- P3.12 can add SRS-safe undo without deleting answer/session audit history.

## Verification

P3.8 tests cover persisted strategy/settings/question state, storage close/open
resume, current-question CAS, simultaneous same-version answers, wrong-question
CAS rejection, pause/resume/complete transitions, navigation undo with preserved
answer history, subscription winner-only publication, real Profile ACL and
cross-WebSocket-client resume.

Final Ruff/mypy/resource/pytest results are recorded after the quality gate.
