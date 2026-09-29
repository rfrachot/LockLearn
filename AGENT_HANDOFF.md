# AGENT_HANDOFF.md

## Current state

Release UX branch: `release/1.0.0-beta.3`.

P6.1 through P6.11 and the P6 exit gate remain PASS on the qualified V1 feature
baseline. `v1.0.0-beta.2` is published and validated on the real HA test VM,
but real-user review identified pre-stable usability issues that should be
resolved before `v1.0.0`.

Beta.3 starts from the immutable beta.2 tag target
`48f45839d278f87b82f45a6128239f36aa536715`.

## Beta.3 field-UX scope

- Track cards separate essential controls, a collapsed advanced-settings
  section, learning-plan controls and an explicit danger zone.
- Track deletion is labelled unambiguously and requires confirmation. Removing a
  shared Profile member also requires confirmation; existing Profile archive/
  permanent-delete protections remain.
- Language tags remain canonical internally, but UI labels are human-readable;
  `ja-Latn` renders as Japanese romaji.
- Profile Sharing explains viewer/editor/owner meaning.
- Configured Companion targets have an owner-only **Test notification** action.
- `locklearn/session/availability` reports available-now counts and next due
  time without mutating SRS state.
- Learn explains cooldowns and may explicitly continue safe future `learning`
  steps after introduction/success. Failed or relearning cards cannot be pulled
  forward.
- Quiz explains that it tests introduced cards only when due, shows readiness
  before start and displays the next scheduled review when none is ready.

The early-Learn override is deliberately narrow and is covered at both selection
and LearningSession boundaries. It must never bypass a cooldown after failure.

New WebSocket commands are classified under the existing Profile ACL boundary:
`locklearn/session/availability` (Profile READ) and
`locklearn/targets/test` (owner/EDIT_PROFILE).

No stable tag/release and no merge are authorized by this handoff.

## Next gate

1. build the exact frontend bundle for beta.3;
2. run the complete release CI matrix on the immutable candidate SHA;
3. independently review all new UX and safety contracts;
4. only after green CI, publish immutable `v1.0.0-beta.3` as Pre-release;
5. upgrade the real HA VM from beta.2 and re-run the field-UX checklist;
6. stable `v1.0.0` remains forbidden until explicit beta.3 acceptance.
