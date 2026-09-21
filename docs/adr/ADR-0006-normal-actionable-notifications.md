# ADR-0006 — Normal actionable notifications and conservative fallbacks

## Status

Accepted after P0.7 real-device qualification on 2026-09-21.

## Context

LockLearn needs a prompt-first learning notification without exposing the
answer, then ideally replaces it after `Reveal`. Companion behavior differs by
device, OS settings and platform. Platform documentation alone cannot prove
same-tag replacement, silence, action count, clear events or lockscreen
redaction.

## Decision

- Capabilities are stored per target with `supported`, `unsupported` or
  `unknown`; no platform-wide optimistic default is allowed.
- Two-step reveal is enabled only when the target proves same-tag replacement,
  silent replacement and at least two accessible actions.
- Every other target uses `exposure_only`; visible-answer assessment can never
  promote an SRS box.
- Notification content is spoiler-safe and privacy-minimal independently of
  the requested lockscreen visibility. `private` is an OS rendering preference,
  not a security boundary.
- Android renderers use no more than three actions. iPadOS exposed four only
  after expansion, but V1 still favors binary/reveal flows.
- Free-text is an independent capability. Android events may be correlated by
  action, tag and device. iPadOS must use the unique persisted action token
  because its event omitted tag and device ID.
- A cleared signal is optional. Android produced it; iPadOS did not.
- Persistent single-use/replay protection remains the P4 interaction-store
  responsibility. Random action IDs and bus-event de-duplication in P0 do not
  pretend to implement that state machine.

## Evidence

- Samsung SM-S928B and Pixel 9 Pro both replaced by tag, exposed three actions,
  returned device/tag/user context, supported text input and emitted clear
  events.
- Samsung emitted a second vibration despite `alert_once`; Pixel silence could
  not be isolated because its initial delivery did not vibrate.
- iPadOS exposed four actions after expansion and supported action/text events,
  but stacked the replacement, omitted device/tag fields, emitted no clear
  event and displayed all tested visibility levels on the lockscreen.
- Full sub-test statuses and timestamps are in `docs/P0_EVIDENCE.md`.

## Consequences

- The initially qualified targets remain `exposure_only`; this is the safe P0
  outcome, not a release defect.
- P4 must provide a capability requalification path after Companion/OS changes
  and must never silently promote `unknown` to `supported`.
- Shared/child profile privacy cannot rely on OS notification redaction.
- iPadOS users must expand/appui long the notification; tapping its body opens
  Home Assistant and loses the action surface.
