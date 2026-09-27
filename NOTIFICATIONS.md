# Notifications

LockLearn uses Home Assistant Companion notifications as a delivery surface, not
as a trusted learning/security authority.

## Platforms

Android and iOS capabilities are discovered/stored per notification target.
Action count, replacement behavior and visibility are capability-driven rather
than assumed identical across platforms.

## Actions and signal semantics

Actions may expose an answer or submit a compact response. The backend rechecks
authorization and normalizes the interaction through the same signal policy used
by active sessions.

An actionable notification does not imply strong evidence. If a platform cannot
guarantee a real retrieval before reveal, the result may be exposure-only or
reduced-quality evidence.

## Tag / replace / clear

Delivery uses platform-capable tags/replacement when appropriate to avoid stale
stacks. Clearing/replacement is operational UI behavior and never constitutes a
learning result by itself.

## TTL / expiration

Scheduled slots have validity windows. Expired unsent slots are not replayed as
catch-up floods after downtime. Pending/deferred state is persisted separately
from ReviewEvents.

## Channels / importance

Home Assistant/Companion channel and importance behavior is treated as platform
delivery configuration. LockLearn does not use notification importance as a
pedagogical weight.

## Connectivity

Push delivery depends on Home Assistant and Companion connectivity. Installed
learning content and active-session study remain local even when push/upstream
dataset discovery is unavailable.

## Quotas and provider limits

LockLearn enforces its own Profile, Track, target and shared-device budgets/gaps.
External provider/OS limits may still delay/drop delivery; failures are operational
status, not incorrect-answer evidence.

## Shared targets

A physical target can be marked shared. Shared-device responses are conservative
unless explicitly trusted; they cannot silently produce high-confidence private
learning evidence for the wrong person.

## Lifecycle

```text
materialized generic slot
 -> send-time content selection
 -> target resolution/capability check
 -> delivery attempt
 -> pending interaction
 -> action/clear/expiry
 -> optional normalized ReviewEvent
```

Delivery-to-action latency is stored separately from cognitive
presentation-to-answer latency.

## Threat model

- action payloads are untrusted input;
- backend ACL is rechecked;
- session/Profile identity is not trusted from UI text alone;
- repeated/replayed actions are bounded/idempotent where required;
- private learning content is not exposed via HA entities by default;
- lockscreen visibility is advisory OS rendering, not a confidentiality boundary.

See `SECURITY.md`, `PRIVACY.md` and ADR-0040 through ADR-0043.
