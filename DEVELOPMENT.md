# Development

## Prerequisites

- Python compatible with the target HA lane (development currently uses Python 3.14;
  minimum compatibility lane uses Python 3.13);
- Node/npm for the Lit frontend;
- a Home Assistant development/test instance for real integration qualification.

## Bootstrap

```bash
./scripts/bootstrap-dev.sh
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cd frontend && npm install && cd ..
```

See `PROJECT.md` for verified environment facts.

## Backend workflow

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy custom_components datasets tests
python datasets/tools/validate_resources.py
python datasets/tools/validate_schemas.py
python -m pytest -q --tb=short
```

Do not run blocking SQLite work on the HA event loop. Use injectable Clock for
time-sensitive domain logic and preserve `state.db != content.db`.

## Home Assistant development instance

Development branches are deployed by copying the complete
`custom_components/locklearn/` directory to the HA config integration directory,
preferably staging/renaming on the same filesystem. Never deploy only the frontend
bundle against a mismatched backend.

HACS is the release installation path, not the development-branch deployment path.

## Frontend workflow

```bash
cd frontend
npm run lint
npm run typecheck
npm test
npm run check:no-polling
npm run dev
npm run build
npm run check:bundle
npm run test:e2e
```

## Dataset build

Official data builds are offline/CI workflows. Runtime HA never parses the large
raw upstream corpora.

Relevant commands:

```bash
python datasets/tools/validate_resources.py
python datasets/tools/validate_schemas.py
python datasets/tools/build_dataset.py --help
```

See `DATA_UPDATES.md`.

## Generated documentation

```bash
python scripts/generate_docs_contracts.py
python scripts/generate_docs_contracts.py --check
```

Generated files under `docs/generated/` must be committed with the runtime source
change that caused them to change.

## Agent/contributor rules

Read `AGENTS.md` first. Structural work must consult `SPEC_V1.md` and relevant
ADRs. Never bypass ACL, silently alter released schemas or expose private learning
data through HA entities by default.
