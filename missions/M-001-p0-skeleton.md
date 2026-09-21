# M-001 — P0 installable skeleton

## Status

Automated toolchain, Config Flow, bundled panel and setup/unload/reload work is
implemented on `feat/p0-foundation`. HACS installation and browser cache/reload
observation on the live HA host remain manual evidence.

## Objective

Turn the bootstrap into an installable development integration on the real HA
VM and validate the first P0 assumptions before business logic starts.

## In scope

- verify dev VM Python/Node versions;
- choose/test HA minimum candidate versus current stable;
- install custom integration via dev config;
- validate config flow single-entry behavior;
- register a minimal custom panel and verify cache/reload behavior;
- verify clean unload/reload;
- establish pytest-homeassistant-custom-component test harness;
- make backend/frontend CI executable rather than structural only.

## Out of scope

- SRS business logic;
- real datasets;
- scheduler;
- mobile notification semantics beyond a later dedicated P0 spike.

## Acceptance criteria

- LockLearn appears in HA integrations and can create exactly one config entry.
- Minimal panel loads from the bundled frontend artifact.
- Reload/unload leaves no duplicate registration.
- Tests cover config flow and setup/unload.
- Commands in `PROJECT.md` are verified on the VM.
- Decisions that change the spec receive ADR/spec updates.
