# PROJECT.md

## Objective

Build LockLearn V1: a local-first, self-hosted micro-learning platform deeply
integrated into Home Assistant and distributed as a HACS custom integration.

`SPEC_V1.md` is the normative functional and architectural source of truth.

## Scope

V1 includes the generic learning engine, content/data model, profiles/ACL,
tracks, SRS, scheduler, actionable notifications, active learning/quiz panel,
basic statistics, dataset provenance/licensing/update foundations and secure
lifecycle behavior.

## Out of scope for 1.0

See `SPEC_V1.md` §131. In particular: cloud accounts/sync, LLM tutoring,
speech/handwriting recognition, native LockLearn mobile apps, complex
gamification and optimized FSRS.

## Languages / stacks

Backend:
- Python, async Home Assistant custom integration.
- SQLite through worker-thread boundaries; never block the HA event loop.

Frontend:
- TypeScript + Lit + Vite.

Development Python:
- use the newest stable interpreter installed on the dev VM that is compatible
  with the supported Home Assistant versions;
- current HA development requires Python 3.14.2+, but the V1 HA floor remains a
  P0 decision because `SPEC_V1.md` still names HA >= 2025.2 as a candidate.

## AI workflow

Renaud is the only human developer and alternates mainly between Claude Code and
Codex. Both may modify, test and commit locally. Push/PR/merge/tag/release only
on explicit request.

The shared AI layer is based on `Renaud_AIConfig` v1.2.0 semantics and adapted
to LockLearn's mixed Python + TypeScript stack. Shared sub-agent roles live in
`.ai/agents/`; Claude and Codex wrappers select explicit cheaper models for
bounded delegated work.

## Commands

```text
Bootstrap : ./scripts/bootstrap-dev.sh
Backend   : python -m pytest -q --tb=short
Format    : python -m ruff format --check .
Lint      : python -m ruff check .
Types     : python -m mypy custom_components datasets tests
Data      : python datasets/tools/validate_resources.py
Frontend  : cd frontend && npm run typecheck && npm test && npm run build
```

Commands that depend on Home Assistant or npm packages become authoritative only
after P0 validates the VM environment.

## Architecture invariants

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
- no blocking SQLite I/O on the HA event loop;
- released content IDs are stable unless an explicit migration mapping exists;
- review events are the audit source, progress is a rebuildable projection;
- official datasets reject NC, ND, unknown and commercially incompatible data;
- no runtime parsing of raw upstream corpora on the HA instance.
