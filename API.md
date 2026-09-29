# WebSocket API

LockLearn exposes its application API through Home Assistant's authenticated
WebSocket connection. There is no separate LockLearn cloud/API account.

## Version

The frontend/backend contract is guarded by `FRONTEND_PROTOCOL_VERSION`.
Current values are declared in:

- backend: `custom_components/locklearn/const.py`;
- frontend: `frontend/src/protocol.ts`.

A protocol mismatch requires a frontend reload/update instead of best-effort
execution against an unknown contract.

## Command contract

Every command is registered in
`custom_components/locklearn/api/websocket.py` and has:

- request schema (required/optional fields);
- handler;
- backend permission boundary;
- HA WebSocket success/error envelope;
- version through the frontend protocol.

The current generated command matrix is:

- human-readable: `docs/generated/WEBSOCKET_CONTRACTS.md`;
- machine-readable: `docs/generated/websocket-contracts.json`.

Run `python scripts/generate_docs_contracts.py --check` to detect drift.

## Permission classes

Commands fall into one explicit class:

- authenticated/global read or onboarding;
- owner-bound private upload capability;
- Profile ACL;
- Track -> Profile ACL;
- Session -> Profile ACL;
- Home Assistant administrator;
- owner/admin long-operation access.

P6.8 tests fail if a new command is not classified or loses its expected guard.

## Errors

Handlers return Home Assistant WebSocket errors with stable LockLearn error codes
where applicable (invalid request, forbidden/not found, stale session, etc.).
Clients must treat error text as diagnostic, not as a stable parsing contract.

## Subscriptions

Session and long-operation subscriptions emit server-pushed state after the
initial successful subscription response. Polling is intentionally avoided.

## Security

Never treat frontend route visibility or request parameters as authorization.
All scoped IDs are resolved/rechecked server-side. Private exports/imports and
operation handles are owner-bound.
