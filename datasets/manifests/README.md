# Dataset build manifests

This directory is reserved for reviewed **build configurations**, not downloaded
upstream corpora and not generated release artifacts.

P1.8 keeps the responsibilities separate:

- `datasets/resources/sources.json` — legal/provenance policy;
- `datasets/resources/source_builds.json` — fetch/discovery metadata and size bounds;
- `datasets/adapters/` — source-native parsers;
- `datasets/pipeline.py` — deterministic normalize/build/sign/package pipeline;
- build configuration — exact source versions/URLs plus a dataset recipe;
- generated `manifest.json` — signed provenance embedded in the release ZIP.

Raw downloads belong under ignored `datasets/downloads/` or
`datasets/staging/` and must never be committed.

No production build configuration is committed in P1.8. P1.10 owns the first
reviewed signed Japanese Starter recipe/configuration. Tiny synthetic fixtures
remain test-only.
