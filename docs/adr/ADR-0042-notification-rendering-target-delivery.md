# ADR-0042 — Capability-aware notification rendering and target delivery

## Status

Proposed for P4.7. Mark Accepted only after the normal repository quality gate
passes.

## Context

P4.6 established durable single-use interaction tokens and replay protection.
P4.7 must turn those protocol primitives into conservative Companion
notifications without inventing stronger authentication, leaking profile-private
state, or converting transport failures into learning evidence.

P0 real-device qualification also showed that Android and iPadOS differ in
same-tag replacement, silence, action visibility, clear events and attribution.
Those capabilities must select UX paths without rewriting the pedagogical facts
that actually occurred.

## Decision

### Learning renderer

A target with proven actionable delivery and at least two visible actions uses a
two-step flow:

1. prompt only with Reveal and I-don't-know actions;
2. answer/explanation after reveal, using the same notification tag and
   `alert_once=true` as the silent-replacement preference.

The second stage receives a fresh P4.6 interaction token. Reusing the visible tag
never reuses the bearer token.

Same-tag replacement and silent replacement remain technical capabilities. A
device that stacks the answer notification or vibrates again can still preserve
a real prompt-first retrieval attempt.

If prompt-first actionable delivery is unavailable, the renderer falls back to
direct exposure. That payload is explicitly marked `exposure_only`. Existing
SignalPolicy semantics prove that exposure-only assessment cannot produce a box
promotion.

### Quiz renderer

Notification quiz is deliberately smaller than panel quiz:

- exactly two answer choices plus I-don't-know may be rendered as three mobile
  actions when action-data support and visible-action capacity are proven;
- larger MCQ, insufficient capability or other unsafe cases hand off to the
  LockLearn panel;
- the panel handoff carries no pedagogical result by itself.

This keeps iOS/iPadOS conservative even when more actions appear after expansion.

### Channels and privacy

The renderer emits distinct channels for learning/teaser, quiz/review and
relearning.

Notification visibility remains an OS rendering preference, never a security
boundary. The default is private, including child and shared-device use. Shared
devices always label the visible notification title with the LockLearn Profile
name.

Prompt-first notifications never include the answer in the prompt-stage message.
Unknown capabilities never become optimistic support.

### Stable target delivery

`target_id` remains a LockLearn target identity and is never replaced by a
Home Assistant service name.

At send time P4.7 resolves the target's stable `device_registry_id` to the
current mobile_app notify action. The resolved service is stored only as
diagnostic metadata.

Actionable payloads fail closed if no data-capable mobile_app route exists.
Direct-exposure payloads may use the generic notify entity as a plain-message
fallback, with Companion-specific data stripped.

A missing/failed target creates the persistent
`notification_target_unavailable` Repair. Delivery failure never marks a slot
as sent.

### Unrecorded-mobile-response warning

P4.7 exposes a private Profile-scoped dashboard API for recent mobile responses
that arrived after the interaction had already expired.

The warning is derived from the P4.6 privacy-minimal rejection audit with
`reason=expired`. A merely ignored notification is therefore not mislabeled as
a lost response.

The warning contains identifiers/timestamps only, never learned content or the
bearer token.

### P4.8 boundary

P4.7 encodes content-free action IDs carrying the P4.6 token and a protocol
semantic. P4.8 owns action/result services and pedagogical events.

Any later action handler must decode the action ID, consume the P4.6 token, and
proceed toward ReviewEvent/Progress only for the single successful
`consumed` claim.

## Alternatives

### Treat same-tag replacement as required for two-step learning

Rejected. P0 proved a usable iPadOS prompt-first flow despite stacked
notifications.

### Render all 4–6 MCQ options on mobile

Rejected. Action presentation differs by platform and can require expansion;
full MCQ belongs in the panel.

### Use Home Assistant notify service names as persisted target identity

Rejected. Mobile app renames change dynamic services while device-registry
identity stays stable.

### Warn for every expired notification

Rejected. Expiry alone often means the learner simply ignored the notification.
The dashboard warning is reserved for an action that actually arrived after
expiry.

### Trust lockscreen visibility as confidentiality enforcement

Rejected. P0 observed platform/device configurations where requested visibility
was ignored.

## Consequences

- prompt-first learning is capability-driven without optimistic defaults;
- direct fallback cannot promote SRS boxes;
- mobile quiz stays bounded and full MCQ remains in the panel;
- shared-device notifications identify the Profile without conflating it with
  the target;
- delivery follows current HA routes and raises a Repair on target failure;
- recent unrecorded mobile responses become visible without exposing content;
- no state schema migration is required for P4.7.
