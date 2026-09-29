# AGENT_HANDOFF.md

## Current state

Release UX branch: `release/1.0.0-beta.4`.

Beta.4 qualification passed on candidate
`741c94be7e8c8b2f42478b227fbfc8964a7d9413`.

The candidate fixed a real readiness/start divergence on top of
`3af7c4a63967c124babb9b6ee808b3ce146c91da`.

Root cause: the frontend started Quiz with a hard-coded 10 cards and Learn with
a hard-coded 20 cards, while `session/availability` resolved
`profile.settings.session_length_cards`. This produced standard Quiz
availability=20/start=10 and child Learn availability=10/start=20.

## Fix now on branch

- Learn and Quiz no longer invent a default requested-card count. When the user
  has not explicitly chosen a size, `session/start` lets the backend resolve
  the Profile's `session_length_cards`.
- `locklearn/session/availability` accepts optional selection `settings` and
  resolves requested cards, content-type filters and leech-only filtering through
  the same backend selection path as `async_prepare`.
- Availability continues to be read-only and preserves the narrow safe
  early-learning override; failed/relearning cooldowns remain authoritative.
- Regression coverage locks child/standard/intensive profile lengths, explicit
  requested-card overrides and content-type parity, plus frontend protocol
  contracts that omit hard-coded default lengths.
- Generated WebSocket contracts and changelog were updated.

The existing HA deployment was already on this exact candidate; it was verified
in place and not redeployed unnecessarily.

## Qualification evidence

- GitHub CI run `36617120890`: all jobs green, including backend-quality,
  frontend, frontend-e2e, dataset-contracts, Home Assistant validation,
  HA 2025.2.5, HA 2026.9.3 and HA 2026.9.4.
- Focused session-selection tests: 5 passed, covering profile 10, Quiz 20/30,
  explicit 7 and content-type parity.
- Existing HA 2026.7.4 deployment remains loaded; static bundle is 214857 bytes
  with SHA-256 `9e5f8f492cd56fa4cd8a1b3eff73c2b7251f5f8f3fde242146209486f26469af`.
- Real UI smoke passed for Learn completion, resume, safe Continue now, Tracks,
  responsive layout and Companion targets. Quiz currently has an honest 0/0
  fixture with next due displayed; this is neutral under the beta.4 rule.
- No Profile was created or deleted during qualification.

Manual beta.4 UI testing may now begin. Do not start beta.5 or publish/merge/tag
a stable release during this gate.
