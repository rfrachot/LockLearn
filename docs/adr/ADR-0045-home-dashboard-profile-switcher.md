# ADR-0045 — Home dashboard aggregation and Profile switcher privacy

## Status

Accepted after the backend/frontend quality gate and real Home Assistant
qualification on 2026-09-26.

## Context

P5.2 introduces the first product-facing Home dashboard. It must combine several
existing backend domains without duplicating pedagogical calculations in the
browser or leaking Profile identity through a switcher.

The canonical inputs already exist:

- P3.13 StatsService for due counts and verified accuracy/retention;
- persistent session state for recent session summaries;
- P4 scheduler slots for the next notification;
- Profile ACL for user-visible Profile membership.

## Decision

### One ACL-protected dashboard payload

The frontend calls `locklearn/dashboard/get` for exactly one selected
`profile_id`.

The command requires existing Profile READ permission before any aggregation is
performed. A caller without access receives the same not-found behavior used by
other Profile-private commands.

### Backend aggregation only

`DashboardService` combines canonical backend state per active Track:

- cards due today from StatsService;
- latest verified retention result;
- recent verified accuracy;
- state counts;
- latest persistent session summary;
- next effective scheduled/deferred notification.

No SRS, retention, accuracy or due-state calculation is reimplemented in
TypeScript.

The payload deliberately strips CardDefinition/LearningItem identity and learned
text because Home does not need them.

### Last-session semantics

The generic session model does not define one universal pedagogical score for
every session type. Home therefore reports:

- session status/type;
- answered count;
- question count;
- activity/completion timestamps.

It does not fabricate an `18 / 20` correctness score where the canonical
session state does not support one.

### Profile switcher grouping

The frontend receives only Profiles already filtered by backend ACL through
`locklearn/profiles/list`.

The UI groups:

- role `owner` under “My profiles” / “Mes profils”;
- role `editor` or `viewer` under “Shared with me” / “Partagés avec moi”.

This grouping is display metadata only. Selecting a Profile does not widen
permissions; the subsequent dashboard request is authorized independently.

The preferred initial Profile is:

1. visible personal Profile returned by bootstrap, when present;
2. first visible owned Profile;
3. first visible shared Profile;
4. none when no Profile is visible.

### Frontend state

Changing Profile reloads only the Profile dashboard request. It does not rerun
the P5.1 bootstrap or visible-Profile discovery.

Dashboard state remains in the panel instance only and is never treated as a
source of truth.

## Alternatives

### Fetch stats/session/scheduler separately from the browser

Rejected. It creates many calls per Track and encourages client-side aggregation
of pedagogical concepts.

### Include every Profile in bootstrap

Rejected. Bootstrap remains a minimal protocol handshake, and ACL-filtered
Profile discovery already exists.

### Group “personal” using the reserved internal settings marker

Rejected. The switcher needs user-facing ownership semantics, not an internal
onboarding implementation detail. Co-owned/created Profiles still belong under
“My profiles” when the current user is owner.

### Show a generic session score

Rejected. Session answer payloads are heterogeneous and not every session has a
canonical correctness numerator.

## Consequences

- Home remains pedagogically honest and backend-driven;
- unauthorized Profile identity cannot enter the switcher through P5.2 APIs;
- one Profile switch causes one dashboard request rather than a shell bootstrap;
- later P5 milestones may add actions/details without changing the P5.2 metric
  authority model.

## Final qualification — 2026-09-26

The complete `feat/p5-frontend` component was deployed directly to Home
Assistant 2026.7.4. The deployed backend reported state schema 5, used
`_initialize_state_database`, and contained no legacy `state=True` initializer
call. The Config Entry loaded after Core restart, storage integrity and foreign
keys were clean, and no LockLearn `ERROR` or `CRITICAL` record remained.

Firefox 156 loaded the cache-busted bundle whose SHA-256 matched the committed
artifact. A temporary owner Profile, active Track and `1/2` persistent session
were created and removed through public WebSocket APIs. The real panel showed:

- the personal bootstrap Profile as the initial selection;
- owner Profiles under “Mes profils”;
- Track name and languages, due count, verified retention/accuracy empty states,
  last session as `1/2 répondues`, and the empty notification state;
- exactly one `locklearn/dashboard/get` and no bootstrap/Profile-list call when
  changing Profile;
- exactly one bootstrap, Profile-list and dashboard call after a full reload;
- a usable switcher, three-column navigation and no horizontal overflow at the
  browser's 500 px responsive viewport.

Seven hundred ordinary `hass` reassignments over three minutes produced no
additional LockLearn request, reload loop or global loading flash. Only one HA
user token is available, so the real outsider/share scenario was not run; the
not-found behavior before sharing and visibility after READ sharing remain
covered by automated backend tests.
