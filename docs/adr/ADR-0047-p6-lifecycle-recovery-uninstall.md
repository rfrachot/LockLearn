# ADR-0047 — P6.2 backup, recovery and uninstall lifecycle

## Status

Accepted and qualified for P6.2 on 2026-09-27.

## Context

LockLearn separates persistent user state in `.storage/locklearn/state.db`
from reconstructible content under `locklearn-content/`. The V1 contract
requires coherent Home Assistant backups, clean unload/reload, explicit
uninstall retention choices, bounded recovery snapshots and a fail-closed path
when SQLite integrity validation fails.

ADR-0004 established that the Home Assistant 2025.2 compatibility floor does
not provide a safe per-integration exclusion for the reconstructible content
directory. P6.2 must therefore report the real backup scope rather than pretend
that the cache is excluded.

## Decision

### Home Assistant backup

The pre-backup hook holds the state write gate, drains the single writer,
checkpoints WAL and creates a validated coherent snapshot using
`sqlite3.Connection.backup()`. The snapshot is published atomically as
`.storage/locklearn/snapshots/ha-backup-latest.db` while the write gate
remains closed. Post-backup releases the gate.

The existing strict hook timeout remains authoritative. Cancellation or failure
during preparation releases the write gate. No active WAL-backed database is
copied with a raw filesystem copy.

At the 2025.2 floor, `locklearn-content/` remains included in the Home
Assistant archive. The Options Flow reports state/cache/asset/recovery sizes and
the effective backup policy. It also offers an explicit cache purge; LockLearn
unloads first, removes only reconstructible content, then sets the Config Entry
up again so bundled/signed content follows the normal rebuild path.

### Integrity failure and recovery

An existing `state.db` is inspected through a read-only SQLite URI before any
writer connection or journal-mode mutation is allowed. Integrity or foreign-key
failure therefore leaves the live files untouched and prevents the normal
runtime from starting.

LockLearn raises a persistent Home Assistant Repair describing the failure and
the number of validated recovery snapshots. P6.2 does not add the broader P6.3
diagnostics/Repair catalogue.

Recovery is always explicit through the Config Entry Options Flow. A candidate
snapshot is validated, copied through SQLite's backup API into a temporary
candidate and validated again. Before replacement, the current live DB/WAL/SHM
files are moved into a bounded quarantine. Only then is the candidate atomically
published. A failed replacement restores the quarantined files.

Recovery and cache purge run with the LockLearn Config Entry unloaded. Setup is
retried after the offline action.

### Snapshot retention

- Home Assistant recovery snapshot: one rolling `ha-backup-latest.db`.
- Pre-migration coherent snapshots: retain the three most recent.
- Pre-recovery quarantines: retain the two most recent.

The bounded policy prevents maintenance snapshots from growing without limit.

### Config Entry removal

Home Assistant does not expose a LockLearn-specific removal confirmation surface
at the supported floor. The explicit choice therefore lives in the Config Entry
Options Flow and is persisted before removal.

The default is `keep_user_data`. Available policies are:

- `keep_user_data`;
- `delete_user_state`;
- `delete_content_cache`;
- `delete_everything`.

`async_remove_entry` applies only the persisted choice after unload/removal.
Unknown values fail safe to `keep_user_data`. User state is never silently
purged.

## Consequences

- The backup archive may be larger while Home Assistant 2025.2 remains
  supported, but the UI is honest about that cost and cache rebuild is explicit.
- A corrupt state DB causes LockLearn to remain unavailable until recovery
  rather than opening a write-capable connection.
- Restore/purge actions temporarily unload LockLearn, so scheduler/notification
  callbacks and SQLite readers/writer cannot survive across file replacement.
- P6.3 still owns the complete Repairs/diagnostics catalogue; P6.4 still owns
  profile export/import and permanent personal-data deletion.
