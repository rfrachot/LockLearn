# AGENT_HANDOFF.md

## Current state

LockLearn bootstrap is now published in the private GitHub repository
`rfrachot/LockLearn`. The complete V1 specification is present as `SPEC_V1.md`.
The shared Claude Code / Codex workflow is being completed from
`Renaud_AIConfig` v1.0.0 and adapted to the Python + TypeScript stack.

## Branch / Git

- Branch: `main`
- Latest known remote commit before this bootstrap-sync commit:
  `58676ca docs: add complete V1 specification`
- Repository: private, `rfrachot/LockLearn`

## What exists

- `SPEC_V1.md` as normative product/architecture source of truth.
- project-specific `AGENTS.md`, `PROJECT.md`, `MASTER_PLAN.md`.
- minimal Home Assistant integration/config-flow skeleton.
- minimal Lit/Vite frontend seed.
- language/license/source registries and validation.
- licensing/source documentation and funding metadata.
- P0 mission `missions/M-001-p0-skeleton.md`.

## Current bootstrap task

Complete the AI-development layer from `Renaud_AIConfig`:

- `CLAUDE.md`;
- `.claude/` rules, commands, skills and sub-agents;
- `.editorconfig`;
- dataset schemas and source audit;
- ChatGPT copilot project instructions.

## Next action

On the dev VM, pull `main`, generate/install the frontend dependency lockfile,
run the repository bootstrap/quality baseline, then start
`missions/M-001-p0-skeleton.md` on a short-lived branch.

Do not claim Home Assistant runtime compatibility or frontend build success until
those checks have actually been executed on the dev VM.
