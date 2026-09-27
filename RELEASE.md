# Release checklist

This is the descriptive V1 release checklist. P6.10 owns final release packaging.

## Before tagging

- [ ] `main`/release commit is clean and reviewed.
- [ ] Ruff format/lint pass.
- [ ] mypy passes.
- [ ] full backend pytest passes.
- [ ] dataset resource/schema/reproducibility checks pass.
- [ ] migration/recovery tests pass.
- [ ] generated documentation `--check` passes.
- [ ] frontend lint/typecheck/Vitest/no-polling/build/bundle pass.
- [ ] Playwright E2E passes.
- [ ] HA minimum/current/latest compatibility lanes pass.
- [ ] hassfest passes.
- [ ] HACS validation passes.
- [ ] normative performance qualification remains valid.
- [ ] compatibility matrix is updated.
- [ ] user-visible changes/migrations are recorded in `CHANGELOG.md`.
- [ ] software version follows SemVer and is independent of dataset versions.
- [ ] committed frontend production artifact matches the source build.

## Release

- [ ] bump version in authoritative runtime/package metadata;
- [ ] create signed/annotated Git tag according to release policy;
- [ ] publish GitHub release and changelog notes;
- [ ] verify HACS sees the intended release;
- [ ] verify clean install on supported Home Assistant;
- [ ] verify upgrade from previous supported release preserves state;
- [ ] verify bundled starter/offline first run;
- [ ] verify no private signing/export data is present in release assets.

## Dataset releases

Dataset artifacts have independent versions and signing keys. Never bundle private
dataset signing material into LockLearn runtime releases.
