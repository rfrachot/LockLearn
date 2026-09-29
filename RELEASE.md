# Release

P6.10 owns the executable release contract for LockLearn. `SPEC_V1.md` remains
normative; this file describes how a concrete software release is prepared and
published.

## Version identity

- LockLearn software follows SemVer.
- `custom_components/locklearn/manifest.json` is the Home Assistant/HACS release
  version and is mirrored by `INTEGRATION_VERSION` in
  `custom_components/locklearn/const.py`; CI requires them to match.
- The current field-validation prerelease is `1.0.0-beta.1`; the stable target remains `1.0.0`.
- `frontend/package.json` is private npm toolchain metadata and is not the LockLearn product version.
  The shipped frontend identity comes from the integration version plus the committed bundle hash.
- Dataset/package versions are independent of the LockLearn software version.
- Stable software tags use `vMAJOR.MINOR.PATCH`.
- Field-validation prereleases use `vMAJOR.MINOR.PATCH-beta.N`.

P6.11 and the P6 exit gate are PASS. Stable `v1.0.0` remains withheld until
the Home Assistant beta field-validation cycle below is explicitly accepted.

## Beta field-validation sequence

`1.0.0-beta.1` is an installable prerelease, not a development-branch shortcut.

1. start from the qualified P6 exit-gate baseline;
2. bump only release/version/docs contracts to `1.0.0-beta.1`;
3. require the complete CI release matrix on the exact beta commit;
4. create tag `v1.0.0-beta.1` and a GitHub Release marked **Pre-release**;
5. create a Home Assistant backup/snapshot before installation;
6. install the prerelease through HACS as a custom integration repository;
7. validate fresh setup, bundled starter, Learn/Quiz, Profiles/Tracks, real
   Companion notifications, reload/restart, backup/restore and dataset update/
   rollback on the test instance;
8. record every beta defect. Runtime defects require a new beta commit/tag
   (`beta.2`, `beta.3`, ...), never mutation of an already published tag;
9. promote to stable `1.0.0` only after explicit field-validation acceptance.

Do not downgrade a database already migrated by beta code. Restore a pre-beta
backup or move forward to a fixed beta.

## Home Assistant compatibility

- HACS advertises the accepted monthly floor `2025.2.0`, as fixed by ADR-0003.
- The minimum full CI lane is the tested patch `2025.2.5` on Python 3.13.
- The current full harness lane is HA `2026.9.3`.
- HA `2026.9.4` is covered by the latest-stable import and isolated release-payload
  smoke while the matching pytest Home Assistant harness is unavailable.

Raising the support floor requires evidence and an ADR update; a newer latest-stable
patch does not silently change the minimum.

## HACS release payload

LockLearn uses the normal HACS custom-integration layout rather than a bespoke
`zip_release` asset. Every file required at runtime lives under:

```text
custom_components/locklearn/
```

This includes Python runtime code, translations/service metadata, the compiled
`frontend/locklearn-panel.js`, dataset trust/registry resources and the signed
offline Japanese Starter artifact. Root `frontend/`, `datasets/`, `tests/`,
`scripts/` and `docs/` are build/test/documentation sources and are not runtime
dependencies.

The three automation blueprints under `blueprints/automation/locklearn/` remain
separately importable examples from a published tag; the integration does not depend
on them to start or learn.

The permanent payload gate is:

```bash
python scripts/p6_10_release_smoke.py
```

It copies only `custom_components/locklearn/` into a temporary HACS-like layout,
imports the integration in a fresh subprocess with the repository root absent from
`PYTHONPATH`, loads all runtime dataset registries, verifies the bundled starter hash,
checks the compiled frontend and rejects repository-only imports or private-key
material.

## Supported upgrade path for 1.0.0-beta.1 and 1.0.0

The latest real published predecessor is `v0.0.2`. It shipped `state.db` schema v1
and Config Entry schema v1. P6.10 freezes that exact released state schema as an
upgrade fixture and verifies:

```text
v0.0.2 / state schema v1
        -> sequential v1 -> v2 -> v3 -> v4 -> v5 migrations
        -> 1.0.0-beta.1 field candidate
        -> future 1.0.0 stable
```

The smoke preserves legacy session/progress/audit rows and the coherent
`state.db.pre-migration-v1.bak` recovery snapshot. `v0.0.1` also used schema v1, but
`v0.0.2` is the normative previous-release upgrade fixture because it is the latest
published predecessor.

Never test an upgrade by deleting, recreating, downgrading or manually rewriting the
user database.

## Before tagging

From a clean candidate commit:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy custom_components datasets tests
python datasets/tools/validate_resources.py
python datasets/tools/validate_schemas.py
python scripts/generate_docs_contracts.py --check
python scripts/p6_10_release_smoke.py
python -m pytest -q --tb=short

cd frontend
npm install
npm run lint
npm run typecheck
npm test
npm run check:no-polling
npm run build
npm run check:bundle
npm run test:e2e
```

After `npm run build`, the committed
`custom_components/locklearn/frontend/locklearn-panel.js` must match the source build;
CI rejects drift.

The GitHub Actions candidate must also pass:

- backend quality/full pytest and migration/recovery contracts;
- P6.10 isolated payload + real v0.0.2 upgrade contracts;
- dataset schema/licence/provenance/signature/reproducibility gates;
- frontend lint/typecheck/Vitest/no-polling/build/bundle/Playwright;
- HA 2025.2.5 minimum and 2026.9.3 current full harness lanes;
- HA 2026.9.4 latest-stable smoke;
- hassfest and HACS validation;
- the documented P6.7 normative performance qualification.

## Release

Only after P6.11/P6 exit-gate PASS **and** explicit beta field-validation acceptance:

1. ensure the release commit is on clean `main` and every required CI job is green;
2. ensure `CHANGELOG.md` has no release-candidate-only wording and move the final
   1.0 notes from `Unreleased` to a dated `1.0.0` section;
3. rerun the release payload and generated-contract checks;
4. create annotated tag `v1.0.0` at that exact commit;
5. publish the GitHub Release from that tag with the changelog notes;
6. verify HACS discovers `v1.0.0` and reports the expected HA floor;
7. perform one real clean HACS install and first-run starter check;
8. perform one real HACS upgrade from `v0.0.2` and verify user state;
9. record the acceptance evidence and only then call the release complete.

Do not publish private dataset signing keys, profile exports, `.env` contents or
temporary recovery state as release assets.

## Rollback and failed releases

A code rollback must not install an older integration over a `state.db` that has
already migrated beyond that code's supported schema. Use the recovery snapshot or a
forward fix; never rewrite state backwards to make an old release start.

Dataset rollback remains independent and continues to use the last-known-good signed
content generation.
