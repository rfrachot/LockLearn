# AGENT_HANDOFF.md

## Current state

LockLearn bootstrap is published in the private GitHub repository
`rfrachot/LockLearn`. The complete V1 specification is present as `SPEC_V1.md`.
The shared Claude Code / Codex workflow has now been aligned with the updated
`Renaud_AIConfig` model-routing semantics.

## Branch / Git

- Branch: `chore/ai-agent-model-routing`
- Base: `main` at `220cd19 chore: complete Claude and Codex AI bootstrap`
- Repository: private, `rfrachot/LockLearn`

## AI routing added

- shared roles under `.ai/agents/` for `explore`, `tests`, `quality`, `review`;
- Claude wrappers explicitly use `model: haiku`;
- Codex `tests` and `quality`: `gpt-5.6-luna`, low effort;
- Codex `explore`: `gpt-5.6-terra`, medium effort;
- Codex `review`: `gpt-5.6-terra`, high effort;
- generic Codex children are discouraged when they could inherit the expensive
  parent model (for example Astra);
- maximum two concurrent sub-agents, no recursive delegation.

## Verification

- GitHub compare against `main`: branch is ahead only, no divergence.
- Configuration files were created/updated directly on the branch.
- Runtime execution of Claude/Codex custom-agent selection still needs to be
  validated on the dev VM; do not claim the runtime consumed the intended model
  until that smoke test is performed.

## Next action

On the dev VM, pull/switch to this branch and run a tiny delegation smoke test
for one Claude role and one Codex role. Verify that Codex actually selects the
custom agent/model rather than silently inheriting the parent model. Then run
the repository bootstrap/quality baseline and continue `missions/M-001-p0-skeleton.md`.
