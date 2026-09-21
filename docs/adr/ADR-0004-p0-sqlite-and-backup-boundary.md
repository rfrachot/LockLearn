# ADR-0004 — P0 SQLite and backup boundary

## Status

Accepted for the P0 storage foundation on 2026-09-21.

## Context

SQLite must never block HA's event loop or share connections arbitrarily across
threads. User state must remain separate from reconstructible content, and HA
backups must capture coherent state.

## Decision

- `state.db` uses one connection confined to a dedicated single-worker
  executor.
- Readers use separate short-lived connections and attach only the active
  `content.db` read-only.
- Long content work uses its own executor and attaches one package at a time.
- HA pre-backup pauses new writes, drains the writer, checkpoints WAL and keeps
  the gate closed until post-backup. Explicit snapshots use
  `sqlite3.Connection.backup()`.
- Persistent state lives under `.storage/locklearn`; reconstructible content
  lives under `locklearn-content`. Neither lives in `custom_components/`.

HA 2025.2 cannot accept a custom per-integration backup exclusion. Content is
therefore included by default at this floor and must be reported honestly to
the user until a safe supported exclusion exists.

## Consequences

- Every released schema change needs a sequential migration.
- Content/state integrity is application-enforced; no cross-DB foreign key is
  introduced.
- A live Supervisor backup/restore remains a release gate in addition to the
  automated hook and restore tests.

## P0.7 real-instance evidence

On HAOS 18.2 / Core 2026.7.4 / Supervisor 2026.09.2, a partial Supervisor
backup containing Home Assistant but excluding Recorder and add-ons restored a
recent WAL-backed LockLearn session exactly to its pre-backup version. A
post-backup mutation and a post-only session were absent after restore.

After restore, `PRAGMA integrity_check` returned `ok`, `foreign_key_check`
returned zero violations, WAL was active, reads ran outside the event loop and
the recreated writer completed a controlled mutation. The panel and WebSocket
API also returned. HAOS included the `ssl` folder even though an empty folder
list was requested; backup/restore UI must report the actual archive scope.

The independent safety backup remained available and was not restored.
