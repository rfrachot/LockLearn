# MASTER_PLAN.md

`SPEC_V1.md` defines the product; this file tracks durable execution phases.

| Phase | Goal | State |
|---|---|---|
| P0 | Architecture spikes + installable HA skeleton | current |
| P1 | Content core + signed mini dataset | queued |
| P2 | Profiles, tracks and backend ACL | queued |
| P3 | Learning engine, SRS and review event model | queued |
| P4 | Scheduler + Companion notifications | queued |
| P5 | Useful panel: Home / Learn / Quiz / basic stats | queued |
| P6 | V1 hardening, lifecycle, migrations, docs, release | queued |
| P7 | V1.1 candidates such as exam and richer media/stats | later |

## Current priority — P0

Validate assumptions on a real Home Assistant dev VM before building business
logic. In particular: minimum supported HA/Python, panel registration/cache,
Companion notification replacement semantics on Android+iOS, SQLite threading,
backup hooks, content-cache location, WebSocket subscription and reload/unload.

## Bootstrap already prepared

- repository skeleton;
- Claude Code/Codex shared workflow;
- MIT code license + data/content licensing boundaries;
- FR/EN HA translation seed;
- frontend Lit/Vite seed;
- machine-readable language/license/source registries;
- source/license audit seed;
- CI skeleton and VM bootstrap script.

## Structural risks

- HA >= 2025.2 candidate floor may be too old relative to the intended 1.0 date.
- Companion notification behavior must be tested rather than inferred.
- EDRDG non-English JMdict gloss licensing must not be assumed from the general
  Japanese/English license.
- KANJIDIC imports require a field allowlist because some third-party fields
  have additional conditions.
