# M-004 — P0 WebSocket, session CAS and operation streams

## Status

Automated implementation complete on `feat/p0-foundation`.

## Objective

Prove HA WebSocket registration, persistent session concurrency, subscription
cleanup, cancellable operation streams and initial latency budgets for P0.6.

## Delivered

- bootstrap/session/operation WebSocket commands with LockLearn error codes;
- atomic session version CAS and two-client stale-session tests;
- authenticated-user isolation without treating a HA User as a product Profile;
- disconnect/unload cleanup for session and operation subscriptions;
- owner/admin boundary for operation streams;
- cancellable progress model and representative answer/selection benchmark;
- compatibility tests on HA 2025.2.5 and HA 2026.9.3.
