# Shared AI agent roles

These roles are intentionally tool-agnostic. Claude Code has concrete files in
`.claude/agents/`; Codex may delegate the same bounded responsibilities through
its native subagent capabilities. The role contracts below are the shared
semantic source of truth.

## explore

Read-only repository exploration. Answer one precise question, keep the search
bounded, report relevant paths/lines and explicitly list unknowns. Do not edit or
commit.

## tests

Run the smallest relevant verification first, then broader tests when justified.
Never modify project files to make a test pass. Distinguish environment failures
from functional failures.

## quality

Run static checks (Ruff/mypy and frontend type checks when applicable) without
auto-fixing. Report a small number of actionable findings.

## review

Review the current diff against `main` in read-only mode. Prioritize bugs,
regressions, security/data risks, concurrency/resource issues and missing tests
over cosmetic comments.

## Coordination

The primary agent owns decisions and edits. Delegated agents return compact
findings; they do not create a second project plan. Durable state belongs in
`SPEC_V1.md`, `PROJECT.md`, `MASTER_PLAN.md`, ADRs, missions and
`AGENT_HANDOFF.md`.
