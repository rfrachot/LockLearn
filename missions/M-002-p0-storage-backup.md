# M-002 — P0 SQLite concurrency and backup spike

## Status

Automated implementation complete on `feat/p0-foundation`; live Supervisor
backup/restore remains external evidence.

## Objective

Prove the state/content boundary, non-blocking SQLite access, representative
query/merge performance and coherent backup lifecycle required by P0.3.

## Delivered

- dedicated thread-confined state writer and separate short-lived readers;
- immutable active content attachment and one-package-at-a-time generation merge;
- WAL/foreign-key/busy-timeout setup;
- pre/post HA backup write gate plus `Connection.backup()` snapshots;
- representative benchmark and restore/concurrency tests;
- ADR-0004 and `docs/P0_EVIDENCE.md`.

## Remaining external evidence

- perform and restore a real Supervisor backup on the development host;
- confirm the documented content-cache inclusion warning in the backup archive.
