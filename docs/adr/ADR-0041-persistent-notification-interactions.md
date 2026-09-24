# ADR-0041 — Persistent notification interactions and replay protection

## Status

Proposed for P4.6. Mark Accepted only after the normal repository quality gate
passes.

## Context

P4.5 binds a CardDefinition to a materialized notification slot only when the
slot is ready to send. P4.6 must prevent delayed, duplicated or maliciously
replayed Companion actions from applying more than one pedagogical result.

P0 also established that Companion metadata is platform-dependent. Android
qualified with useful user/device/tag context, while an iPadOS path omitted
device/tag metadata and therefore requires an opaque persisted action token for
correlation.

The V1 specification explicitly states that notification actions are not strong
authentication and that user context should be checked when Home Assistant
provides it.

## Decision

### One opaque token per actionable stage

Each actionable notification stage receives a fresh cryptographically random
bearer token and a persistent `notification_interactions` row. Reusing a
replacement tag does not reuse the token.

The row stores protocol identity and state only. Learned prompt/answer text is
not copied into state storage.

### Atomic single-use claim

Consumption runs on the dedicated SQLite writer inside `BEGIN IMMEDIATE`.
Only a row that is still `pending` and whose expiry is strictly in the future
can transition to `consumed`.

The action handler receives an explicit disposition. Only `consumed` is
allowed to continue toward a ReviewEvent/Progress mutation. `expired`,
`replayed`, `not_found` and `forbidden` are terminal for that attempted
action and carry no pedagogical authority.

This gives the required at-most-once application gate without inventing action
semantics before P4.7.

### User context and trust boundary

When `context.user_id` exists, P4.6 requires the existing backend Profile
`ANSWER` permission before trying to consume the token. Viewer/outsider
contexts therefore leave a live interaction pending.

When Companion supplies no user context, a live token may still be consumed.
That fallback is necessary for qualified platform behavior but is explicitly
not treated as strong authentication. Shared-device confidence and pedagogical
signal weighting remain separate policies.

### Privacy-minimal audit

Unknown, expired, replayed and ACL-forbidden attempts are durably audited.
Successful claims are also audited so available actor context survives.

Audit payloads never contain the bearer token, replacement tag or learned
content. Action IDs used by later renderers must be opaque protocol identifiers,
not answer text.

### Schema

No migration is required. The P2 state foundation already contains the complete
V1 `notification_interactions` shape, including token, tag, stage, expiry,
status, consumption timestamp and action ID.

## Alternatives

### Deduplicate only in the Home Assistant event listener

Rejected. Event-bus delivery is not the source of truth and de-duplication would
be lost across restart.

### Use notification tag as the replay key

Rejected. Tags are deliberately reused for replacement and were not present in
all qualified Companion action events.

### Require `context.user_id` for every action

Rejected. Real-device qualification showed a supported path where useful action
events can omit that metadata.

### Treat the bearer token as user authentication

Rejected. Anyone able to obtain a live token could replay the user's action.
The token provides correlation and single-use semantics, not user identity.

### Add a new state schema solely for P4.6

Rejected. The reserved table already satisfies the normative data contract.

## Consequences

- concurrent/repeated actions have a single claim winner;
- restart does not reset replay protection;
- expired/replayed actions cannot authorize Progress mutation;
- available HA user context is enforced through existing Profile ACL;
- token-only fallback remains possible where Companion metadata is incomplete;
- later notification renderers must generate a new token per actionable stage;
- P4.7/P4.8 must never bypass the P4.6 claim result when applying learning
  outcomes or emitting pedagogical events.
