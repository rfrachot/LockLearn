# P0.1–P0.6 evidence record

Evidence date: 2026-09-21. The normative requirements remain in
`SPEC_V1.md`; this file separates observed facts from pending manual evidence.

## Compatibility and toolchain (P0.1)

| Surface | Minimum / CI floor | Latest tested | Local evidence |
|---|---:|---:|---|
| Home Assistant | 2025.2.5 | 2026.9.3 | Both backend suites pass |
| Python | 3.13.15 | 3.14.4 | Both interpreters run the suite |
| Node | 22 in CI | 24.20.0 local | typecheck/test/build pass |
| LockLearn | 0.0.1 | 0.0.1 | development version |
| state.db schema | 1 | 1 | schema/version tests |
| content.db schema | 1 | 1 | merge/attach tests |
| frontend protocol | 1 | 1 | WebSocket bootstrap contract |

The V1 compatibility floor is confirmed as **Home Assistant 2025.2**; CI pins
the latest patch in that month (`2025.2.5`) and a separate current-stable job.
As of the evidence date, current stable is `2026.9.3`. The configured live
development instance answered successfully on `2026.7.4`; this was an API
inventory check, not an integration installation claim.

The CI workflow runs Ruff, mypy, pytest, dataset validation, frontend
typecheck/test/build, the two-version HA matrix, hassfest and HACS validation.

## Installable lifecycle (P0.2)

Automated evidence:

- `single_config_entry` is declared and the second Config Flow aborts;
- no YAML path exists or is required;
- the built panel artifact is committed and served through HA's asynchronous
  static-path API with a version cache-buster;
- panel registration is removed on unload and can be registered again without
  duplication;
- session subscriptions, operations and SQLite executors are drained on
  unload;
- the same lifecycle suite passes on HA 2025.2.5 and 2026.9.3.

Still requiring a real install/browser observation:

- HACS custom-repository install on the live HA host;
- visual panel load and full-browser cache behavior after an upgrade.

`LOCKLEARN_HA_CONFIG_DIR` is not configured, so this checkout cannot install
files into the live instance without inventing a deployment path.

## SQLite, content boundary and backup (P0.3)

Implemented and tested:

- one state writer connection confined to `ThreadPoolExecutor(max_workers=1)`;
- short-lived readers on a distinct executor with one read-only active
  `content.db` attachment;
- WAL, `synchronous=NORMAL`, `busy_timeout=5000` and foreign keys;
- physically separate state and reconstructible content paths, both outside
  `custom_components/`;
- package merge by attaching exactly one package at a time;
- HA pre/post backup hooks pause writes, checkpoint WAL with a strict timeout,
  then resume; explicit snapshots use `Connection.backup()`;
- cancellation/progress primitives yield between chunks and never occupy the
  state-writer executor.

Local representative benchmark (60,000 cards, 20,000 progress rows, 100 query
and answer samples):

| Measurement | Result | P0/V1 budget |
|---|---:|---:|
| content merge | 0.033–0.056 s | recorded baseline |
| due query p95 | 4.321–5.422 ms | selection < 150 ms |
| new anti-join p95 | 8.828–13.987 ms | selection < 150 ms |
| session answer p95 | 0.468–0.500 ms | answer < 100 ms |

Run with `python -m scripts.p0_benchmark`. Results are machine-specific and CI
does not assert wall-clock timings.

HA 2025.2 has global backup filters but no custom-integration API for adding a
per-integration exclusion. Consequently `state.db` and reconstructible content
inside the HA config directory are included by default. LockLearn must expose
that fact and offer purge/re-download until a later supported HA floor provides
a safe exclusion mechanism. A real Supervisor backup/restore remains a manual
host test.

## Companion capability matrix (P0.4)

The runtime model is deliberately tri-state (`supported`, `unsupported`,
`unknown`). Unknown never enables a feature. Two-step reveal requires proven
same-tag replacement, proven silent replacement and at least two visible
actions; otherwise the renderer selects `exposure_only`, which cannot promote
an SRS box.

Read-only inventory of the configured HA instance found two Android phones and
one Android watch with stable device-registry IDs and notify entities. No iOS
target is registered, and `.env` does not select an Android/iOS/shared target.
The following facts therefore remain `unknown`, not assumed:

| Capability | Android | iOS |
|---|---|---|
| same-tag replacement and latency | pending device gesture | no target |
| silent `alert_once` replacement | pending | no target |
| visible action limit | pending visual check | no target |
| cleared signal | pending dismissal | no target |
| TTL/expiration | pending elapsed-time check | no target |
| channel/importance | pending settings check | no target |
| lockscreen public/private/secret | pending locked-device check | no target |
| free-text input | pending | no target |

The opt-in probe is:

```text
python -m scripts.p0_ha_probe inventory
python -m scripts.p0_ha_probe companion --device-id <id> --platform android
```

The second command sends a labelled notification to the explicit stable device
ID and records action context, replacement request latency and cleared events.
It is never run against an inferred service name.

## Identity and unattended actions (P0.5)

Implemented and tested:

- target identity is `device_registry_id`; a current notify entity or legacy
  service is resolved on every send and a rename changes only the route;
- unresolved/disabled targets fail closed;
- shared devices default to `signal_quality=reduced` unless explicitly trusted;
- HA admin state is not an input to profile membership;
- actions without `context.user_id` are denied unless the profile explicitly
  allows unattended actions and the action is in the narrow `send_now`,
  `snooze`, `pause_track` allowlist;
- read, export, delete and session-start actions are never unattended;
- the audit storage accepts actor kind/user id without private content.

Real `event.context.user_id` observations for Companion actions still require
running the explicit device probe. Profile owner/editor/viewer behavior remains
backend-authoritative work in P2; no P0 endpoint exposes real profile data.

## WebSocket, CAS and operation streams (P0.6)

The HA test harness proves command registration, two simultaneous clients,
atomic version CAS, `locklearn/stale_session`, session subscriptions and
disconnect cleanup on both supported HA versions. P0 sessions live in an
isolated per-HA-user probe namespace; this provides backend authorization
without pretending that a HA user is a product Profile.

Long operations expose `operation_id`, phase, normalized progress,
cancellability, safe error type and status. Cancellation and unload cancel
tasks and detach subscriptions. The benchmark above establishes the initial
answer-latency baseline.

## Remaining manual gates

P0.1–P0.6 code, automated tests and reproducible probes are present. The only
unclosed evidence is intrinsically external: Android/iOS gestures and visual
behavior, HACS/browser installation, and a real HA backup/restore. P0.7 must not
freeze the notification protocol until Android **and** iOS results exist.
