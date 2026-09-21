# ADR-0005 — P0 session concurrency and target identity

## Status

Accepted and qualified on real Android and iPadOS targets on 2026-09-21.

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
- Actionable payloads require a data-capable `notify.mobile_app_*` action. The
  generic notify entity route is only an explicit plain-message fallback
  because HA 2026.7 rejects Companion `data` on that action.
- Unknown notification capabilities fail closed to `exposure_only`.

## Consequences

- `Profile != HA User` and `Profile != Device` remain true.
- P2 replaces the synthetic P0 namespace with real profile membership checks
  at every command boundary.
- Android action events carried `device_id`, `tag` and user context on both
  tested phones. iPadOS action events carried user context and the unique
  action ID but no `device_id` or `tag`; inbound attribution must therefore use
  the persisted interaction/action token and never invent missing fields.
- Detailed renderer capabilities and fallbacks are fixed in ADR-0006.
