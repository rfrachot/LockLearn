# ADR-0049 — P6.4 private Profile transfer and deletion lifecycle

## Status

Accepted and qualified for P6.4 on 2026-09-27.

## Context

V1 requires Profile export/import without turning private learning data into a
public static asset, plus a clear distinction between reversible archival and
irreversible deletion. Imports are hostile input and must not be allowed to
overwrite an existing Profile, bind another Home Assistant user's ACL, or
silently discard history when referenced content is absent locally.

The existing `profiles/delete` command permanently deleted state immediately
after ACL authorization and the frontend presented a single destructive action.
The content schema already modeled removed/superseded identities, but persistent
`progress.content_status` was not reconciled after content generation
activation.

## Decision

### Private export transport

Profile archives are generated in a runtime-private temporary directory outside
the Home Assistant configuration tree and therefore outside LockLearn's normal
backup/static-content roots. Directories are mode 0700 and files mode 0600.

The export operation uses the existing cancellable operation registry and
returns a high-entropy owner-bound capability URL:

`/api/locklearn/profile-export/<token>`

The route is a normal authenticated Home Assistant `HomeAssistantView`. The
token expires after five minutes and is consumed exactly once. The ZIP is
removed from private temporary storage before the response is returned.
Responses use `Cache-Control: no-store` and are never mounted under the public
LockLearn static path.

Full Profile export is owner-only. Viewer/editor read permissions are not
sufficient because exports may contain progression, annotations, reviews and
sessions.

### Versioned archive

Export schema version 1 uses a deterministic JSON envelope containing:

- `manifest.json`;
- `profile.json`;
- `tracks.json`, including Track rules and content weights;
- `progress.json`;
- `annotations.json`;
- `stats.json`;
- optional `reviews.json`;
- optional `sessions.json`.

The manifest records LockLearn/state/content versions plus exact SHA-256 and
byte size for every payload member.

### Import transport and hostile-input boundary

Authenticated uploads are bounded to 64 MiB and stored only in the same private
runtime directory. Upload capabilities are bound to the authenticated HA user
and expire after fifteen minutes.

Before dry-run or apply, the archive is validated with:

- exact filename allowlist and required members;
- no absolute/traversal/backslash/NUL paths;
- no directories, symlinks or special files;
- no encrypted members;
- stored/deflate compression only;
- member, total-uncompressed and expansion-ratio limits;
- duplicate and case-insensitive collision rejection;
- manifest membership, size and SHA-256 validation;
- supported Profile preset/timezone/settings shape.

Dry-run reports mapping/counts and missing Pack/Card references without mutating
state.

### Import mapping

Apply always creates a new Profile, Track and Session identity. It never
overwrites an existing Profile.

The authenticated importing HA user becomes the new sole owner. Source ACL
members, Companion notification targets and scheduler target IDs are never
imported. The Profile and Tracks are created archived; previously active
sessions become paused.

Missing PackVersion bindings are left unbound on archived Tracks. Progress
referencing unavailable cards is retained with `content_status='removed'`.
Reviews, annotations, stats and optional session history keep their historical
stable content references.

The complete state import is one `BEGIN IMMEDIATE` transaction.

### Archive versus permanent delete

`locklearn/profiles/delete` is backward-compatible but safe by default:
omitting `action` now archives rather than permanently deletes.

Archive:

- sets the Profile to archived;
- pauses active sessions;
- cancels scheduled/deferred slots;
- clears pending notification interactions;
- preserves history/statistics/configuration.

Permanent deletion requires owner-only DELETE permission and the exact backend
confirmation phrase:

`DELETE <profile_id>`

The repository transaction deletes all Profile-scoped state directly or via
foreign-key cascades. The Profile service then purges outstanding private export
capabilities for that Profile. The frontend exposes separate Archive and Delete
permanently actions and requires the same exact phrase.

### Content tombstones

Every successful content-generation activation and rollback reconciles
persistent `progress.content_status` against the newly active
`card_definitions`:

- active card -> `active`;
- superseded card -> `superseded`;
- removed or absent card -> `removed`.

Progress/history rows are never deleted because content disappears. If
reconciliation after activation fails, LockLearn rolls back to the prior
generation and reconciles that generation before surfacing the failure.

## Consequences

- Profile exports are not public files and do not survive unload/restart.
- Import is deliberately conservative: imported learning state cannot start
  scheduling or notify old devices until the user explicitly reconfigures and
  reactivates it.
- Content removal is represented as a tombstone in persistent progress rather
  than a cascade.
- P6.6 remains responsible for the broader security threat-test matrix; P6.4
  implements the archive protections required for this concrete import surface.
