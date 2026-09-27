# Security

LockLearn treats frontend input, imported archives, Home Assistant automation
calls and third-party dataset content as untrusted.

Core invariants:

- backend ACL on every profile-scoped operation;
- Home Assistant administrator status never substitutes for LockLearn Profile
  membership;
- unattended actions are a narrow explicit allowlist and require Profile
  opt-in;
- SQL identifiers/operators come from code allowlists and external values are
  bound parameters;
- no blocking DB I/O on the HA event loop;
- no raw third-party HTML or `unsafeHTML`;
- rich text is a closed AST that is validated/canonicalized before dataset
  signing and rendered through Lit interpolation;
- SVG is sanitized before hashing/signing/packaging;
- runtime package validation rejects any signed SVG whose bytes are not the
  sanitized build derivative;
- archive traversal, links, duplicate/case-fold collisions and archive bombs
  are rejected;
- official dataset signatures are verified before activation;
- bearer/action tokens are high-entropy, bounded and single-use;
- public dataset assets and private user/export assets use different storage
  and serving boundaries;
- private learning content stays out of HA entities/events by default;
- diagnostics expose aggregate/redacted metadata only.

## Threat model

### Trusted components

LockLearn trusts:

- Home Assistant's authenticated-user context and HTTP/WebSocket framework;
- its own installed Python/frontend code;
- explicit LockLearn Profile ACL state in `state.db`;
- signed dataset manifests only after Ed25519 verification and package
  validation.

The frontend is **not** an authorization authority. Dataset ZIPs, source data,
Profile imports, notification actions and automation/service input are treated
as hostile until validated.

A Home Assistant administrator remains a highly privileged operator of the HA
instance. LockLearn prevents accidental/API-level Profile ACL bypass but does
not claim cryptographic isolation from an administrator who controls the host.

### Main threats

| Threat | Boundary |
| --- | --- |
| XSS through third-party content | closed rich-text AST + Lit escaping |
| active SVG / external SVG fetch | build-time sanitizer before signature |
| archive traversal / symlink / bomb | bounded structural ZIP validation |
| SQL injection through pack filters | strict schema + field/operator allowlist + bound values |
| notification action replay | persistent atomic single-use token consumption |
| Profile ACL bypass | backend Profile permission checks, no HA-admin shortcut |
| private export leakage | authenticated owner-bound ephemeral HTTP routes outside static roots |
| tampered public assets | signed manifest + hash/size revalidation |
| private data in diagnostics/entities | redacted aggregate contracts |
| unauthenticated automation mutation | unattended allowlist + Profile opt-in + audit |

## Profile ACL authority

Profile authorization is centralized in the backend. The role matrix is
owner/editor/viewer and is evaluated from persistent `profile_members`.
Home Assistant administrator status is intentionally not a profile-ownership
shortcut.

Unauthorized Profiles are omitted from normal listings rather than returned as
discoverable forbidden rows. Direct visibility checks collapse nonexistent and
unauthorized Profiles to the same absence result.

ACL changes are owner-only and cannot remove or demote the final owner of a
Profile. Frontend permission checks never replace backend authority.

See `PERMISSIONS.md` and `PRIVACY.md`.

## SQL security

Runtime values are passed through sqlite3 parameters. External content must not
supply SQL identifiers, clauses or operators.

Pack `content_filters` use the executable contract in
`core/pack_filters.py` and `datasets/schemas/content-filter.schema.json`.
The V1 grammar supports only:

- fields: `content_type`, `register`, `dataset_id`;
- operators: `eq`, `in`;
- conjunction through `all`.

The compiler emits SQL identifiers/operators only from module constants and
returns all package-provided values separately as bound parameters. Unknown
fields/operators/keys fail closed.

## Third-party text and XSS

`rich_text` is not HTML and does not accept arbitrary Markdown extensions.
The allowed AST contains only paragraph/text/emphasis/strong/inline-code/
line-break/ruby primitives.

Dataset build canonicalizes the AST before the canonical content hash and
signature are produced. Package/generation validation independently parses the
same closed content contract.

The frontend uses normal Lit interpolation. It does not use `unsafeHTML`,
`innerHTML`, `eval` or `Function` for third-party learning content.
Text such as `<script>...` is therefore rendered as text, not markup.

## SVG

ADR-0018 originally rejected SVG because no dedicated sanitizer existed.
P6.6 supersedes that narrow MIME decision.

`image/svg+xml` is accepted only by the dataset build pipeline. Before SHA-256,
metadata, signing or packaging, the SVG is parsed as XML and sanitized:

- `script`, `foreignObject`, `style`, iframe/object/embed are removed;
- `on*` event-handler attributes and inline style attributes are removed;
- external/remote/data/javascript/file references are removed;
- `href`/xlink references are local-fragment-only;
- non-SVG namespaces and unsafe URL values are removed;
- DTD/entity declarations are rejected;
- size is bounded.

The signed/package hash describes the sanitized bytes. Runtime never treats the
original third-party SVG as authoritative: package validation reopens SVG
payloads from the signed archive, bounds the read, and rejects bytes whose
sanitized canonical form differs.

## Archive and import security

Dataset packages and Profile imports are hostile ZIP inputs.

Validation covers:

- normalized relative POSIX paths;
- traversal, absolute paths, backslashes and NUL rejection;
- duplicate and case-insensitive name collision rejection;
- symlink/special-file rejection;
- encryption/unsupported compression rejection;
- entry/member/total compressed/decompressed size ceilings;
- expansion-ratio limits;
- signed/declared membership checks;
- SHA-256 and exact byte-size checks.

Profile import additionally binds upload capabilities to one authenticated HA
user, performs dry-run validation and makes apply one-shot/concurrent-safe.

## Replay and tokens

Notification interaction tokens are opaque random bearer capabilities persisted
with expiry/status. Consumption is atomic: concurrent claims produce at most
one `consumed` result; subsequent uses are `replayed`. Expired, unknown and
forbidden attempts cannot apply learning state.

Private Profile export URLs are authenticated, owner-bound, short-lived and
one-shot. Profile import upload tokens are authenticated-user-bound and are
consumed after apply, including failed/cancelled apply attempts.

Bearer values are not written to audit payloads.

## Asset serving boundary

Public dataset assets:

- originate only from verified signed packages;
- live in the reconstructible public content cache;
- resolve only through active `assets_metadata`;
- have signed size/SHA-256 rechecked on resolution.

Private Profile exports/imports:

- live in a private OS temporary root outside Home Assistant config;
- are never placed below the LockLearn static frontend path;
- use authenticated `/api/locklearn/...` views;
- are purged by TTL/unload and Profile deletion rules.

A public static path is acceptable only for immutable public integration
artifacts/content that contains no user-private state.

## Diagnostics and entities

Diagnostics are aggregate/redacted. They intentionally omit Profile names,
learned content, answers, annotations, target names/IDs, raw errors and Repair
placeholders.

LockLearn 1.0 ships no optional private learning SensorEntity platform. Any
future sensor must follow `ha_entity_contract.py`: explicit Profile+Track
opt-in, aggregate-only values, empty default attributes and Recorder-conscious
cadence/state_class semantics.

## Backup and deletion

SQLite backups use coherent snapshots / `Connection.backup()`; raw copying of
an active WAL database is prohibited.

Permanent Profile deletion requires exact backend confirmation and removes
Profile-scoped state plus outstanding private export capabilities. Uninstall
state deletion is controlled by the persisted explicit retention policy.

## Vulnerability reporting

Until a dedicated security advisory address/process is published, report
security issues privately through the repository owner's available private
contact channel rather than filing public exploit details. A public
vulnerability-reporting process is required before the repository is broadly
published.
