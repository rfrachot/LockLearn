# AGENT_HANDOFF.md

## Current state

Branch: `feat/p6-hardening`.

P5 and its real-HA exit gate remain PASS.

P6.1 — database/config/content migrations and recovery — PASS.

P6.2 — backup hooks, unload/reload and uninstall/recovery UX — PASS.

P6.3 — Repairs and diagnostics — PASS.

P6.4 — secure export/import and data deletion — PASS.

P6.5 — HA entity/sensor privacy contract and optional integration boundary —
PASS at `a3cd543` and pushed before P6.6 started.

P6.6 — security hardening and threat-model tests — PASS after deep review and
qualification on 2026-09-27.

## P6.6 implementation

### XSS / rich text

- third-party rich text remains a closed AST, never arbitrary HTML;
- dataset build canonicalizes rich-text payloads before canonical hashing and
  signing;
- existing package/generation validation remains an independent parser;
- frontend continues to use Lit interpolation, never `unsafeHTML`;
- P6.6 frontend regression verifies hostile HTML-looking text remains an
  interpolated value rather than template markup.

### SVG

- `image/svg+xml` is now an allowed public image MIME only because P6.6 adds
  dedicated build-time sanitation;
- original third-party SVG bytes are never hashed/signed/packaged directly;
- sanitizer strips scripts, foreignObject/style/iframe/object/embed,
  `on*`/style attributes, remote/data/javascript/file references and unsafe
  namespaces;
- href/xlink references are local-fragment-only;
- DTD/entity declarations are rejected;
- XML depth/node budgets prevent parser-tree abuse;
- package manifest, SQLite metadata and SHA-256 bind the sanitized bytes;
- runtime package validation rejects raw SVG bytes even when re-signed by a
  trusted key;
- this supersedes ADR-0018 only where it previously rejected SVG pending a
  sanitizer.

### Pack filters / SQL

New `core/pack_filters.py` and
`datasets/schemas/content-filter.schema.json` define the closed V1 filter
grammar:

- fields: `content_type`, `register`, `dataset_id`;
- operators: `eq`, `in`;
- conjunction only through `all`;
- unknown keys/fields/operators/types fail closed;
- SQL identifiers/operators are code constants;
- package values are emitted separately as sqlite3 parameters.
- compiler array inputs are restricted to JSON list types, matching the schema.

Injection tests execute a malicious literal against SQLite and verify it cannot
alter query structure or schema.

### Existing threat regressions reused by the P6.6 gate

- `tests/backend/test_acl.py`: Profile ACL authority and no HA-admin bypass;
- `tests/backend/test_notification_interactions.py`: concurrent single-use
  action replay/expiry and bearer redaction;
- `tests/datasets/test_dataset_package.py`: hostile signed-dataset ZIP;
- `tests/backend/test_profile_transfer.py`: hostile Profile archive,
  owner-bound/one-shot private transfer lifecycle;
- `tests/datasets/test_assets.py` and
  `tests/datasets/test_asset_pipeline.py`: signed public asset binding,
  traversal checks, cache tamper detection.

New `tests/backend/test_security_p6_6.py` adds rich-text, SVG primitive,
parameterized Pack-filter and private/static-root regressions.

New `tests/datasets/test_svg_security.py` proves that the **signed packaged SVG
bytes** are the sanitized derivative, that runtime rejects a raw re-signed SVG,
and that unsafe rich text fails before a dataset can be signed.

Deep review fixes also make Profile archive JSON/member reads enforce actual
decompressed-byte ceilings and convert malformed-compression errors into the
normal transfer error boundary. Dataset package payload and SQLite streaming
enforce actual member/total bounds before trusting bytes.

### Documentation

- `SECURITY.md` is now the consolidated V1 threat model;
- ADR-0051 records the security-hardening decisions and reuse of prior
  regressions.

No P6.7 performance/scale/storage-budget work is included.

## Verification state

Final P6.6 qualification is complete.

Recommended targeted backend/dataset gate:

```text
.venv/bin/python -m pytest -q --tb=short \
  tests/backend/test_security_p6_6.py \
  tests/backend/test_acl.py \
  tests/backend/test_notification_interactions.py \
  tests/backend/test_profile_transfer.py \
  tests/datasets/test_svg_security.py \
  tests/datasets/test_dataset_package.py \
  tests/datasets/test_assets.py \
  tests/datasets/test_asset_pipeline.py
```

Then backend full gate:

```text
.venv/bin/python -m ruff format --check .
.venv/bin/python -m ruff check .
.venv/bin/python -m mypy custom_components datasets tests
.venv/bin/python datasets/tools/validate_resources.py
.venv/bin/python -m pytest -q --tb=short
```

P6.6 changes a frontend security test, so qualification must also run:

```text
cd frontend
npm run typecheck
npm test
npm run build
```

If build output changes unexpectedly despite no frontend source change, inspect
and explain before committing generated artifacts.

Do not start P6.7 during qualification.

## Qualification result

- targeted gate: `98 passed, 1 warning` (expected duplicate ZIP member warning);
- Ruff format/check: PASS (`280 files already formatted`, lint clean);
- mypy: PASS (`163 source files`);
- resource validation: PASS;
- full pytest: `455 passed, 1 warning` (same expected warning);
- frontend typecheck: PASS;
- frontend tests: `49 passed` across 15 files;
- frontend build: PASS; tracked bundle hash stayed
  `d1626186b8fe1cf50f81efb5a4f3dd05de3dd54e22ec86b20612000c9b259385` and no
  bundle diff was generated;
- no frontend production source changed and no P6.7 work started.

Current branch remains `feat/p6-hardening`; the qualification fixes are in the
local commit recorded below.

Commit: `f1d4568 fix(security): close P6.6 review gaps`.
