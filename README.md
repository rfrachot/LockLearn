# LockLearn

> Local-first spaced-repetition learning for Home Assistant.

LockLearn is a self-hosted learning engine distributed as a Home Assistant custom
integration. It combines active study sessions, deterministic spaced repetition,
actionable Companion notifications, multi-user learner Profiles and signed
versioned datasets without requiring a LockLearn cloud account.

**Status:** 1.0.0-beta.3 field-validation candidate. P6.1 through P6.11 and the
P6 exit gate are qualified; stable 1.0.0 is intentionally withheld until real
Home Assistant beta validation is accepted.

SPEC_V1.md is the normative product and architecture source of truth.

## Vision

LockLearn turns Home Assistant into a private learning surface that can study with
you during active sessions and reach you through carefully bounded notifications,
while keeping learner state local and auditable.

Core principles:

- local-first and self-hosted;
- backend ACL is authoritative;
- private learner state is separate from public/reconstructible content;
- deterministic, explainable SRS before clever optimization;
- signed, provenance-aware datasets;
- no language-specific behavior in the generic learning core;
- no private learning data exposed through HA entities by default.

## Screenshots

![LockLearn Home dashboard](docs/assets/locklearn-home.png)

The screenshot above is captured from the real compiled LockLearn panel by the
same deterministic Playwright harness used by E2E tests. It is not a hand-drawn
mockup. CI also regenerates the full-resolution panel capture as the
`locklearn-docs-screenshot` workflow artifact so documentation imagery remains
tied to tested UI behavior.

## Features

### Learning

- persistent resumable Learn/Quiz sessions;
- exact CardDefinition progress identity;
- deterministic V1 learning/relearning/review policy;
- verified-retrieval signal gate;
- leech detection, targeted remediation and annotations;
- undo/rebuild/recompute audit boundaries;
- private stats, streak and metacognitive calibration.

### Scheduling and notifications

- deterministic Profile scheduler with windows, quiet hours and DST handling;
- multi-Track arbitration and target/shared-device capacity limits;
- send-time pedagogical content selection;
- Android/iOS Companion actionable notification handling;
- restart/clock-jump reconciliation without catch-up floods.

### Data

- signed Ed25519 dataset packages;
- source snapshots, provenance and license policy;
- immutable generated content.db activation/rollback;
- bundled offline Japanese Starter dataset;
- public signed media-asset boundary;
- explicit PackVersion pinning for Tracks.

### Home Assistant

- HACS-compatible custom integration;
- custom Lit panel;
- Repairs and privacy-redacted diagnostics;
- backup/recovery lifecycle hooks;
- minimum/current/latest compatibility CI.

## Installation

LockLearn is not yet a final 1.0 release. For beta/pre-release testing:

1. add https://github.com/rfrachot/LockLearn as a custom **Integration**
   repository in HACS;
2. install the selected published/pre-release version;
3. restart Home Assistant when requested;
4. add the **LockLearn** integration from Settings → Devices & services;
5. open the LockLearn panel from the sidebar.

Development branches should be deployed as the complete
custom_components/locklearn/ directory; do not use HACS to mix a release
frontend with a development backend.

## Quick start

After setup:

1. open the LockLearn panel;
2. create or use your personal Profile;
3. create a Track from an installed PackVersion;
4. start a Learn or Quiz session;
5. optionally configure a Companion notification target and scheduler windows.

The bundled Japanese Starter dataset makes first-run content available without
upstream network access.

## Compatibility

| Contract | Current V1 hardening value |
|---|---|
| LockLearn runtime | 1.0.0-beta.3 field-validation candidate |
| HACS minimum Home Assistant | 2025.2.0 |
| Minimum full CI lane | 2025.2.5 |
| Current full harness lane | 2026.9.3 |
| Latest stable smoke tested | 2026.9.4 |
| Config Entry schema | 1 |
| state.db schema | 5 |
| content schema | 2 |
| frontend protocol | 3 |

Compatibility CI installs and verifies the actual HA versions. See TESTING.md and
RELEASE.md.

## Documentation

- [Architecture](ARCHITECTURE.md)
- [Data model](DATA_MODEL.md)
- [Database](DATABASE.md)
- [Pack/dataset format](PACK_FORMAT.md)
- [Data sources](DATA_SOURCES.md)
- [Data update pipeline](DATA_UPDATES.md)
- [Licensing](LICENSING.md)
- [Permissions](PERMISSIONS.md)
- [SRS](SRS.md)
- [Scheduler](SCHEDULER.md)
- [Notifications](NOTIFICATIONS.md)
- [Frontend](FRONTEND.md)
- [WebSocket API](API.md)
- [Migrations](MIGRATIONS.md)
- [Security](SECURITY.md)
- [Privacy](PRIVACY.md)
- [Development](DEVELOPMENT.md)
- [Testing](TESTING.md)
- [Release checklist](RELEASE.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Roadmap](ROADMAP.md)
- [Generated runtime contracts](docs/generated/README.md)
- [Architecture decisions](docs/adr/)

## Repository layout

~~~text
custom_components/locklearn/  Home Assistant integration/runtime
frontend/                     TypeScript/Lit panel + browser E2E harness
datasets/                     schemas, registries, adapters and build tooling
tests/                        backend/dataset/HA tests
docs/                         generated contracts, ADRs, plans and evidence
scripts/                      qualification and contract-generation tooling
~~~

Large raw upstream corpora are intentionally not committed and are never parsed on
the Home Assistant runtime.

## Development

~~~bash
./scripts/bootstrap-dev.sh
source .venv/bin/activate
python -m pip install -r requirements-dev.txt

python -m ruff format --check .
python -m ruff check .
python -m mypy custom_components datasets tests
python -m pytest -q --tb=short
python datasets/tools/validate_resources.py
python datasets/tools/validate_schemas.py
python scripts/generate_docs_contracts.py --check

cd frontend
npm install
npm run lint
npm run typecheck
npm test
npm run build
npm run test:e2e
~~~

See DEVELOPMENT.md and AGENTS.md before structural changes.

## License

- LockLearn software and authored tooling/schemas: **MIT** unless stated otherwise.
- Original LockLearn editorial learning content: explicit content license,
  currently CC BY-SA 4.0 for the bundled starter.
- Third-party datasets/assets retain their upstream licenses and attribution.

See LICENSING.md.

## Support and security

- User/developer troubleshooting: TROUBLESHOOTING.md
- Security model and vulnerability reporting: SECURITY.md
- Privacy model: PRIVACY.md

## Sponsors / donations

The project supports GitHub Sponsors metadata through .github/FUNDING.yml.
Donations/sponsorship do not change the open-source or dataset attribution
boundaries.

See SUPPORT.md.
