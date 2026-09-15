# AGENT_HANDOFF.md

## Current state

LockLearn bootstrap is published in the private GitHub repository
`rfrachot/LockLearn`. The complete V1 specification is present as `SPEC_V1.md`.
The shared Claude Code / Codex workflow has been aligned with the updated
`Renaud_AIConfig` model-routing semantics.

## Branch / Git

- Branch: `chore/ai-agent-model-routing`
- Base: `main` at `220cd19 chore: complete Claude and Codex AI bootstrap`
- Repository: private, `rfrachot/LockLearn`

## AI routing

- shared role source under `.ai/agents/` for `explore`, `tests`, `quality`, `review`;
- Claude agents contain the full role text plus `model: haiku`, so each child is autonomous at startup;
- `tests/ai/test_agent_prompt_sync.py` checks that Claude role bodies stay identical to `.ai/agents/`;
- Codex `tests` and `quality`: `gpt-5.6-luna`, low effort;
- Codex `explore`: `gpt-5.6-terra`, medium effort;
- Codex `review`: `gpt-5.6-terra`, high effort;
- generic Codex children are discouraged when they could inherit the expensive parent model;
- maximum two concurrent sub-agents, no recursive delegation.

## Verification

- Claude custom-agent discovery worked on the dev VM.
- A child self-reported `Sonnet 5`, but model self-identification is not sufficient proof of the runtime-selected model.
- The earlier Claude wrappers were replaced by full standalone role prompts before rerunning the model smoke test.
- Codex runtime custom-agent/model selection is still unverified because no Codex credits were available.
- Do not claim either runtime consumed the intended model until the relevant smoke test verifies it externally.

## Next action

On the dev VM, pull this branch, restart Claude Code from the repository root, and rerun the `explore` delegation smoke test. Verify the selected child model from runtime/UI diagnostics rather than asking the model to identify itself. When Codex credits are available, run the equivalent Codex custom-agent smoke test. Then run the repository bootstrap/quality baseline and continue `missions/M-001-p0-skeleton.md`.
