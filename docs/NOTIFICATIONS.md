# Notifications

LockLearn V1 treats Companion notification actions as a **single-use transport
capability**, not as strong user authentication.

## P4.6 persistent interaction contract

Every actionable notification stage is backed by a row in
`notification_interactions` containing an opaque random token, optional
replacement tag, Profile/Track/target/CardDefinition identity, protocol stage,
expiry and lifecycle status.

The actionable stages are `prompt`, `revealed` and `answered`. A renderer
that replaces a prompt with a revealed answer creates a **fresh token for the
new actionable stage**. The visible notification tag may stay the same for
replacement semantics; the bearer token does not.

Tokens are generated with cryptographically strong randomness in production and
must never be logged, copied to `audit_events`, exposed through diagnostics or
embedded in learned text. Action IDs are protocol identifiers and must likewise
remain content-free.

## Action consumption and replay protection

Incoming actions are handled in this order:

1. resolve the opaque token;
2. when Home Assistant supplies `context.user_id`, require Profile
   `ANSWER` permission;
3. atomically claim the interaction only while it is `pending` and unexpired;
4. return a claim that allows downstream pedagogical mutation only for the
   single `consumed` winner.

The SQLite claim runs under the dedicated state writer transaction. Concurrent
or repeated delivery therefore produces at most one `consumed` result.
Expired, replayed, unknown and ACL-forbidden attempts never authorize a
ReviewEvent/Progress mutation.

When Companion omits user context, as observed during P0 qualification on one
iPadOS path, the valid single-use bearer token remains the correlation gate.
This does **not** make the notification action strong authentication. Shared
device and signal-quality policy remain separate concerns.

P4.6 does not yet interpret `reveal`, `known`, quiz choice or other action
semantics. P4.7 owns renderers and platform behavior; later code may apply a
pedagogical result only after P4.6 returns a successful claim.

## Audit

Suspicious or invalid action attempts are recorded in `audit_events` with a
minimal reason and, when already known, interaction/target/stage/status
identifiers. Bearer tokens, notification tags and learned content are excluded.

Successful consumption also records a minimal transport audit so available HA
user context is retained without turning the HA event bus into a source of
truth.

## Storage and migrations

The P2 state foundation already reserved the complete
`notification_interactions` table required by P4.6, so P4.6 adds repository
and service behavior without changing state schema version 5.
