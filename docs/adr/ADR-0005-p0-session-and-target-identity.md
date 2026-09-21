# ADR-0005 — P0 session concurrency and target identity

## Status

Accepted for P0 prototypes on 2026-09-21. Notification capabilities remain
provisional until real Android and iOS evidence is complete.

## Context

Two clients may resume one session, and Companion service names may change when
a device is renamed. Neither the frontend nor a service name is a security
authority.

## Decision

- Session mutations use a transaction and `WHERE version = expected_version`;
  the losing client receives `locklearn/stale_session`.
- P0 WebSocket sessions are isolated in a synthetic per-authenticated-user
  namespace. They do not expose real Profile data before P2 ACL exists.
- WebSocket subscriptions install HA disconnect callbacks and are cleared on
  unload.
- Notification targets persist `device_registry_id`; notify entities/services
  are resolved at send time and are only ephemeral routes.
- Unknown notification capabilities fail closed to `exposure_only`.

## Consequences

- `Profile != HA User` and `Profile != Device` remain true.
- P2 replaces the synthetic P0 namespace with real profile membership checks
  at every command boundary.
- P0.7 cannot accept two-step notification reveal without device evidence on
  both platforms.
