# AGENT_HANDOFF.md

## Current state

Release UX branch: `release/1.0.0-beta.4`.

Beta.4 qualification found and fixed a real readiness/start divergence on top of
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

No deployment has been performed for this fix.

## Next gate

1. qualify the exact new branch HEAD with Ruff, mypy, full pytest and frontend
   lint/typecheck/tests/build/E2E;
2. adversarially reproduce standard Quiz and child Learn availability/start
   parity, plus an explicit requested-card override;
3. if and only if all gates pass, deploy that exact SHA to the existing HA test
   instance;
4. smoke Learn/Quiz readiness, next-due guidance, safe Continue now and Companion
   target UX;
5. only then allow Renaud to begin manual beta.4 UI testing.

Do not start beta.5 and do not publish/merge/tag a stable release during this gate.
