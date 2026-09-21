# M-003 — P0 Companion capabilities and identity spike

## Status

Runtime gates, inventory and opt-in probe delivered; real Android/iOS results
remain open because no target was selected and no iOS device is registered.

## Objective

Establish device-registry identity, capability-driven notification fallbacks,
shared-device signal quality and the unattended-action boundary for P0.4/P0.5.

## Delivered

- tri-state target capability model with fail-closed `exposure_only` fallback;
- stable device-registry ID to current notify route resolution and rename tests;
- reduced shared-target signal quality;
- unattended allowlist, durable audit and negative security tests;
- read-only HA inventory and explicit opt-in Companion event probe;
- ADR-0005 and the pending matrix in `docs/P0_EVIDENCE.md`.

## Remaining external evidence

- select one Android target and perform the action/replacement/dismissal tests;
- register/select an iOS target and run the same matrix;
- perform lockscreen, visible-action, TTL, channel and free-text visual checks.
