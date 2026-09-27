# ADR-0051 — P6.6 security hardening and threat-test boundary

## Status

Accepted for the P6.6 implementation candidate on 2026-09-27. Final
qualification remains pending.

## Context

LockLearn already had strong isolated controls for Profile ACL, notification
replay protection, signed dataset archives, Profile-transfer ZIP validation,
diagnostics redaction and public-asset integrity. P6.6 closes the remaining V1
security gaps and makes the threat model executable.

The specific unresolved areas were:

- SVG remained forbidden rather than safely sanitizable;
- rich-text safety existed at package validation/rendering but not as an
  explicit pre-signing build canonicalization step;
- the normative Pack `content_filters` contract did not yet exist as a strict
  schema/compiler;
- the cross-boundary threat model was only partially documented.

## Decision

### Rich text

Rich text remains a closed JSON AST, never arbitrary HTML. Dataset builds now
canonicalize rich-text payloads through the security allowlist before canonical
content hashing and signing. The existing package/generation validator remains
an independent second parser. The frontend continues to render through Lit
interpolation without `unsafeHTML`.

### SVG

ADR-0018 rejected SVG until a dedicated sanitizer existed. P6.6 supersedes only
that MIME-policy portion.

`image/svg+xml` may enter a signed dataset only through the build pipeline.
The original third-party bytes are parsed and sanitized before metadata,
SHA-256, manifest generation and signing. The sanitizer removes active
elements/event handlers/style/external references/foreign namespaces and
rejects DTD/entity payloads.

The signed asset is therefore the sanitized derivative. Runtime cache/hash
validation continues unchanged.

### Pack filters and SQL

V1 Pack `content_filters` use a strict JSON schema and an executable compiler.
The grammar contains only a conjunction of terms over allowlisted fields and
operators. SQL identifiers/operators are constants owned by LockLearn; package
values are returned separately for sqlite3 parameter binding.

No raw SQL fragment, column name or operator may come from package content.

### Threat-test reuse

P6.6 does not duplicate mature regressions merely to change filenames. The
security gate explicitly reuses existing tests for:

- ACL/no HA-admin bypass;
- notification single-use replay;
- hostile dataset/Profile archives;
- authenticated owner-bound one-shot Profile transfers;
- public asset integrity and private/static separation.

New P6.6 tests target only missing boundaries: rich-text build/XSS, SVG
sanitization/signature binding, Pack-filter SQL injection and private-static
root separation.

## Consequences

- SVG support is now safe enough for signed public datasets but no new image
  renderer is implied.
- Future Pack-manifest work must use `compile_pack_content_filter()` rather
  than creating ad-hoc SQL.
- SECURITY.md becomes the current V1 threat-model reference.
- P6.7 performance/scale work is intentionally out of scope.
