# ADR-0053 — Documentation source of truth and generated runtime contracts

## Status

Accepted for P6.9 on 2026-09-27.

## Context

V1 requires both durable human documentation and precise technical contracts for
database schemas, WebSocket commands and pack/data formats.

Copying full SQLite DDL or the WebSocket command inventory into hand-maintained
documentation would create a second source of truth and inevitably drift from the
runtime. Conversely, generated output alone is not enough to explain architecture,
rationale, operational behavior or contributor workflows.

SPEC_V1.md must remain normative for product scope and invariants.

## Decision

LockLearn documentation has four layers:

1. `SPEC_V1.md` — normative product/architecture requirements.
2. Human reference docs at repository root — current descriptive architecture,
   operations and contributor guidance.
3. ADRs — rationale and consequences of structural decisions.
4. Generated contracts under `docs/generated/` — exact runtime-derived schema/API
   reference.

`scripts/generate_docs_contracts.py` derives:

- state.db DDL/index/ER reference from `STATE_SCHEMA`;
- content.db DDL/index/ER reference from `CONTENT_SCHEMA`;
- human-readable and JSON WebSocket command inventories from the registered
  command schemas and handlers.

CI executes the generator in `--check` mode. A runtime change that makes the
committed generated output stale is therefore a release-gate failure.

Human docs link to generated contracts rather than duplicating exhaustive DDL/API
tables.

README screenshots must be captured from the real Playwright E2E panel harness.
A hand-drawn mockup is not accepted as release documentation.

## Alternatives

### Maintain all reference tables manually

Rejected because schema/API drift would be easy and hard to review.

### Generate all documentation

Rejected because generated output cannot capture design rationale, security
boundaries, migration policy, troubleshooting or contributor workflows.

### Treat code comments as documentation

Rejected because users/contributors need stable navigable contracts outside the
implementation files.

## Consequences

- schema/API changes may require regenerated committed documentation;
- CI detects generated-contract drift;
- root reference docs stay shorter and focus on behavior/rationale;
- SPEC changes remain deliberate instead of being inferred from code;
- documentation screenshots are reproducible from the tested browser harness;
- P6.9 qualification must include documentation contract tests and the screenshot
  capture path.
