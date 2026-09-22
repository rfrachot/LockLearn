# ADR-0020 — Track configuration, explicit PackVersion pinning and card rules

## Status

Accepted for P2.4 on 2026-09-22, pending final quality gate.

## Context

P1 defines immutable PackVersions and stable CardDefinitions. P2 must turn those
content contracts into per-profile learning Tracks without collapsing
`Track == Pack` or making a UI direction such as `EN → FR` part of card
identity.

A Track must also remain stable when a newer PackVersion appears. New content
must not enter an active curriculum until the learner deliberately integrates
that version.

## Decision

### Track and Pack remain distinct

A Track is persistent user state. It stores profile ownership, source/target
preferences, status, priority and Track settings in `state.db`.

Each Track pins one explicit immutable `pack_version_id` in
`track_pack_versions`. The pin also records the active content generation at
integration time.

### Direction is resolved to exact CardDefinitions

Source/target language direction is an interface/configuration preference only.
At Track configuration time LockLearn resolves that preference against the
pinned PackVersion and materializes exact card rules containing:

- `card_key`;
- `prompt_facet_id`;
- `answer_facet_id`.

Pack-owned `enabled_by_default = false` card defaults are respected when the
rules are generated from a broad direction. Explicit card selection can choose a
specific active card deliberately.

The core therefore continues to identify learning progress by CardDefinition,
not by a language-direction enum.

### Card rules are Track-owned state

Resolved rules live in `track_card_rules`. Direction-generated rules and
explicit-card rules use distinct `rule_kind` values so later pack integration
can preserve the user's selection model.

Track content weights live in `track_content_weights` as non-negative relative
volume targets. They do not force block scheduling; P3/P4 still own selection,
interleaving, quotas and due/relearning precedence.

### Pack updates require deliberate integration

Merely activating a content generation with a newer PackVersion does not mutate
a Track pin.

The Track service first exposes a deterministic PackVersion diff over added,
removed and changed LearningItems. Only an explicit integrate operation changes
`track_pack_versions`.

For direction-mode Tracks, integration resolves the same source/target
preference against the new PackVersion. For explicit-card Tracks, integration
refuses to proceed if a selected card no longer belongs to the target
PackVersion; LockLearn never silently drops an explicit learner choice.

Pin replacement and regenerated card rules are written in one state transaction.

### Cross-database boundary

Pack/card discovery reads the active immutable `content.db` through the
existing reader lease. Persistent Track state remains in `state.db`; no SQL
foreign key crosses the database boundary.

## Consequences

- Multiple Tracks may use the same PackVersion while keeping independent
  progression.
- A Pack update cannot silently inject new cards into an existing Track.
- Friendly language direction remains UI/configuration syntax rather than core
  identity.
- Japanese-specific card defaults remain pack data rather than Track/core
  branches.
- P2.6 can expose create/update/integrate actions over this service without
  duplicating selection or pinning logic.
- P3/P4 can consume exact Track card rules and relative content weights without
  reinterpreting PackVersion semantics.

## Verification

P2.4 tests cover direction-to-card resolution, explicit-card validation,
relative content weights, PackVersion preview, unchanged pins before explicit
integration, and rule regeneration after integration. Final Ruff/mypy/resource/
pytest results are recorded in the handoff when the quality gate passes.
