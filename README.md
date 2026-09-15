# LockLearn

> A self-hosted micro-learning platform for Home Assistant.

LockLearn is a local-first learning engine designed as a Home Assistant custom
integration distributed through HACS. It combines active sessions, spaced
review, actionable notifications, multi-user profiles and extensible content
without requiring a LockLearn cloud account.

**Status:** very early bootstrap / P0. The repository is not ready for normal
users yet.

## Core principles

- Home Assistant custom integration + custom panel.
- Python backend, TypeScript/Lit frontend, SQLite storage.
- `state.db` and `content.db` stay strictly separated.
- Progress belongs to a `CardDefinition` (`LearningItem + prompt facet + answer facet`).
- Backend ACL is authoritative; the frontend is never a security boundary.
- The core is content-agnostic and must not depend on Japanese-specific behavior.
- Official datasets must remain compatible with donations, sponsorship and possible commercial use.

The normative product/architecture document is [`SPEC_V1.md`](SPEC_V1.md).

## Repository layout

```text
custom_components/locklearn/  Home Assistant integration
frontend/                     TypeScript/Lit panel sources
datasets/                     schemas, source registry and future build tooling
tests/                        backend/data tests
docs/                         ADRs, architecture, data and development docs
missions/                     bounded missions shared by Claude Code / Codex
```

Large upstream datasets are deliberately **not** committed here. Official data
artifacts are intended to be built separately and distributed as signed,
versioned dataset packages.

## Development bootstrap

On the future development VM:

```bash
./scripts/bootstrap-dev.sh
source .venv/bin/activate
```

Then use the commands documented in [`PROJECT.md`](PROJECT.md).

## Licensing

- LockLearn software: **MIT**.
- Original LockLearn learning/editorial content: **CC BY-SA 4.0 recommended**.
- Third-party datasets/assets: keep their own upstream licenses and attribution.

See [`LICENSING.md`](LICENSING.md) and [`DATA_SOURCES.md`](DATA_SOURCES.md).

## Support the project

The licensing model deliberately allows donations and sponsorship without
turning access to the software or official attribution into a paid entitlement.
GitHub Sponsors metadata is prepared in `.github/FUNDING.yml`; the sponsor page
still has to be enabled on the GitHub account before the button becomes useful.

See [`SUPPORT.md`](SUPPORT.md).
