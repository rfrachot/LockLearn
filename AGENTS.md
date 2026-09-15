# AGENTS.md — LockLearn

This repository is developed by Renaud with Claude Code and Codex as code
copilots. There is no fixed ownership split between the two agents.

## 1. Sources of truth

Before structural work, read only what is relevant, in this order:

1. `AGENTS.md` — working rules.
2. `SPEC_V1.md` — normative product and architecture source of truth.
3. `PROJECT.md` — verified repository/environment facts and commands.
4. `AGENT_HANDOFF.md` — current state when a mission is in progress.
5. active file in `missions/`, if any.
6. relevant section of `MASTER_PLAN.md`.
7. relevant ADRs, code and tests.

If a request conflicts with the spec, do not silently work around it: identify
the conflict, explain the impact and either follow the spec or propose the spec
+ ADR change.

## 2. Never invent missing project facts

Inspect the repository first. Ask only when a genuinely missing fact changes
architecture, compatibility, data, security or expected behavior. Do not turn a
minor preference into a blocker.

## 3. Non-negotiable architecture invariants

```text
Profile != HA User
Profile != Device
Track != Pack
Concept != Term
Learning mode != Content type
Progress belongs to CardDefinition
Frontend != security authority
Content data != User state
HA Recorder != LockLearn database
Core != Japanese-specific
```

Also:
- never bypass backend ACL;
- never perform blocking DB I/O on the HA event loop;
- never mutate a released DB schema without migration;
- never expose private learning content through HA entities/events by default;
- never store runtime user state under `custom_components/`;
- never parse large raw upstream corpora on a HA instance;
- never render third-party dataset HTML with `unsafeHTML`;
- never promote an SRS box from self-assessment when the answer was already visible.

## 4. Git workflow

`main` is the only long-lived branch. For non-trivial work:

1. start from a clean `main`;
2. create a short branch (`feat/`, `fix/`, `docs/`, `test/`, `refactor/`, `chore/`);
3. implement narrowly;
4. run relevant checks;
5. commit locally with Conventional Commits;
6. prepare PR;
7. CI green;
8. squash merge recommended.

Claude Code and Codex may create branches, modify files, test and **commit**.
They must not push, create/modify remote PRs, merge, tag or publish releases
without an explicit request from Renaud.

Always preserve unknown worktree changes. Never use destructive cleanup as a
shortcut.

## 5. Backend rules

- Python async Home Assistant integration.
- Type public/non-trivial APIs; prefer useful types over type-gymnastics.
- Ruff + mypy + pytest by default.
- Use an injectable Clock for time-sensitive domain logic.
- SQLite access uses a dedicated writer and separate/thread-local readers.
- `state.db` and active `content.db` stay separate.
- Cross-database integrity is application-enforced and tested.
- Long operations are chunked, cancellable, observable and backpressured.

## 6. Frontend rules

- TypeScript + Lit + Vite.
- Home Assistant WebSocket API is the application boundary.
- No runtime CDN dependency.
- No direct DB access.
- No third-party raw HTML; rich content is a strict AST/allowlist.
- Accessible, responsive, keyboard-friendly, theme-aware and CJK-safe.
- Isolate reliance on HA frontend internals and test compatibility.

## 7. Content/data/licensing rules

Official data builds must preserve source, snapshot, record identity, license
and attribution. Never merge semantic concepts across independent sources merely
because gloss text looks similar.

Reject official content with NC, ND, unknown or commercially ambiguous license.
Keep software licensing separate from dataset and asset licensing.

Large upstream corpora do not belong in this repository or on the HA runtime.
This repository may contain adapters, schemas, manifests, tiny fixtures and
curated demo content whose license is explicit.

## 8. Verification

Run targeted tests first, then relevant full checks. Baseline:

```text
python -m ruff format --check .
python -m ruff check .
python -m mypy custom_components datasets tests
python -m pytest -q --tb=short
python datasets/tools/validate_resources.py
cd frontend && npm run typecheck && npm test && npm run build
```

Do not claim a command passed if dependencies/environment were unavailable.

## 9. Definition of Done

Treat the relevant items explicitly:

```text
implementation
tests
typing/lint
security
ACL
migration
documentation
ADR when structural
CHANGELOG when user-visible/backward relevant
backward compatibility
```

## 10. Handoff

Before switching agents or ending a substantial session, update
`AGENT_HANDOFF.md` with current branch, mission, verified state, tests run,
commit(s), remaining risks and the next concrete action. Keep it short.

## 11. Delegation and model routing

Claude Code and Codex share four bounded roles defined in `.ai/agents/`:
`explore`, `tests`, `quality` and `review`. Use a sub-agent only when isolation
reduces context or output noise; do not delegate trivial commands by habit.
Never allow a sub-agent to spawn another sub-agent. Keep at most two children
running concurrently.

Model routing is intentional:

```text
Claude explore/tests/quality/review -> Haiku
Codex tests/quality                -> gpt-5.6-luna, low effort
Codex explore                      -> gpt-5.6-terra, medium effort
Codex review                       -> gpt-5.6-terra, high effort
```

For Codex, prefer the matching custom agent from `.codex/agents/` and an
isolated child context (`fork_turns="none"` or equivalent). Do **not** launch a
generic child for routine exploration/tests/quality/review if that child can
silently inherit the parent model (for example Astra). If the runtime cannot
select or verify the intended cheaper model, keep the task in the parent and
use `.ai/agents/<role>.md` as the checklist instead.
