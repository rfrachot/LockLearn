# ADR-0054 — `known_already` is calibration-pending evidence

## Context

P3.10 originally modeled `known_already` as a user-owned exclusion overlay that did not mutate SRS state. Field UX showed that this creates a dead end for users who already know starter material: the card disappears from Learn yet has no path into verified review.

## Decision

For a `new` card during the introduction phase only, **Je la connais déjà** creates an auditable non-retrieval transition: `user_state=known_already`, `state=review`, `box=1`, `self_known_count += 1`, `last_result=self_known`, with verified counters and `last_verified_at` unchanged. Its first verification is due after 10 minutes plus deterministic 0–20 minute jitter.

The pending card is excluded from Learn and may enter Quiz only when that verification is actually due. A verified success clears `known_already` and remains in review box 1; a verified failure/IDK clears it and enters relearning. Unrecognized free text does not settle the pending state.

`Apprendre finalement` creates an auditable compensating transition back to `active/new/box 0` before verification. Quick calibration is a separate verified pre-test flow; it is never implemented by bulk `known_already` declarations.

## Alternatives considered

- Keep `known_already` as a permanent exclusion: rejected because it converts confidence into unverified mastery and strands the card.
- Promote directly to a mature review box: rejected because self-report is weaker than retrieval evidence.
- Delete the feature and require calibration only: rejected because the per-card escape remains valuable during normal introduction.

## Consequences

Progress rebuild must preserve these transitions through canonical ReviewEvents. Availability must expose pending-known counts and due times. Existing P3.10 documentation describing `known_already` as pure exclusion is superseded by this ADR and SPEC §0.1.

**Status:** Accepted — 2026-09-30.
