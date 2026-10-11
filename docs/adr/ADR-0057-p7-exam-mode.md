# ADR-0057 — Closed-book exam attempts and deferred correction

## Status

Accepted for P7.1 on 2026-10-11.

## Decision

Exam questions are prepared and frozen by the backend before the attempt starts.
The client receives only the prompt and answer choices; the accepted answer is
stored in the private `exam_attempts.settings_json` payload and is never returned
while the attempt is active. Each answer is persisted through the normal session
CAS, but generic `session/answer`, `session/complete` and `session/undo` paths are
rejected both at WebSocket and storage boundaries.

Finalization uses one writer transaction for all neutral `exam_retrieval`
ReviewEvents, the result summary, the exam attempt and the session status. The
event sets `retrieval_occurred=1`, `signal_quality=none`, and identical pre/post
progress snapshots, so it records retrieval without changing SRS boxes. Automatic
notification selection excludes those cards for 12 hours.

Selection is deterministic per attempt seed, stratified by content type, level and
coarse difficulty, and supports direction, pack, tag and content-type filters.
Completed results remain readable through ACL-guarded history/result commands.
Active attempts are pause/resume safe across Home Assistant restarts.

Profile exports redact active answer keys; completed results remain private profile
data and are deleted with the profile.

## Consequences

- No immediate feedback or partial score can become an answer oracle.
- A crash before commit leaves no partial exam finalization.
- Exam retrieval is visible in raw audit history without being treated as a normal
  quiz/SRS success.
- Importing an unfinished attempt safely abandons it because its private key is
  intentionally not exported.
