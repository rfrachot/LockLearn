# P0.1–P0.7 evidence record

Evidence date: 2026-09-21. `SPEC_V1.md` remains normative. Status values in
the real-instance sections are exactly `PASS`, `FAIL`, `BLOCKED_EXTERNAL`, or
`NOT_APPLICABLE` with a justification.

## Compatibility and toolchain (P0.1)

| Surface | Minimum / CI floor | Latest tested | Live qualification |
|---|---:|---:|---:|
| Home Assistant | 2025.2.5 | 2026.9.3 | 2026.7.4 |
| Python | 3.13.15 | 3.14.4 | managed by HAOS |
| Node | 22 in CI | 24.20.0 local | not applicable at runtime |
| LockLearn | 0.0.2 | 0.0.2 | HACS release v0.0.2 |
| state.db schema | 1 | 1 | 1, integrity checked |
| content.db schema | 1 | 1 | 1 |
| frontend protocol | 1 | 1 | 1 |

The V1 compatibility floor remains **Home Assistant 2025.2**. CI pins
2025.2.5/Python 3.13 and 2026.9.3/Python 3.14. The real target was HAOS 18.2,
Core 2026.7.4 and Supervisor 2026.09.2.

## Gate A — HACS, Config Flow and panel (P0.2/P0.7)

Qualification window: 2026-09-21 20:00–21:46 UTC.

| Sub-test | Status | Evidence |
|---|---|---|
| repository security audit before public transition | PASS | 164 reachable Git blobs scanned; no credential/private-key signature; `.env` ignored and never tracked |
| public custom repository | PASS | `rfrachot/LockLearn` anonymously reachable |
| HACS recognition | PASS | custom repository recognized as an integration with `config_flow=true` and HA floor 2025.2.0 |
| HACS install | PASS | release `v0.0.1` installed through HACS, then real HACS update to `v0.0.2` |
| Config Flow | PASS | form opened and created the entry with defaults |
| single Config Entry | PASS | second flow aborted with `single_instance_allowed`; exactly one entry remains |
| sidebar panel and real bundle | PASS | panel displayed; bundle returned JavaScript and matched the release artifact |
| frontend/backend coherence | PASS | bootstrap protocol 1 and authenticated user present |
| cache buster | PASS | module URL is `/locklearn_static/locklearn-panel.js?v=0.0.2` |
| hard refresh | PASS | operator observed the LockLearn bootstrap panel after forced refresh |
| unload/reload | PASS | disable removed panel/API without restart; enable restored both and preserved persistent state |
| stale listeners / duplicate callback | PASS | pre-reload subscription received no post-reload event; no duplicate panel/service observed |
| blocking JavaScript error | PASS | panel rendered after install, reload, update and hard refresh |

Release `v0.0.1` qualifies the initial installation path. Release `v0.0.2`
qualifies the real HACS update path and contains the P0.7 notification-route
fix and privacy-safe storage diagnostic. The branch itself was not pushed;
HACS consumed the released tags.

## SQLite, content boundary and performance (P0.3)

Automated evidence:

- one state writer connection is confined to a dedicated single-worker
  executor;
- readers use separate short-lived connections and attach only active
  `content.db` read-only;
- WAL, `synchronous=NORMAL`, `busy_timeout=5000` and foreign keys are enabled;
- state and reconstructible content are physically separate and outside
  `custom_components/`;
- HA pre/post backup hooks pause writes, checkpoint WAL, and always reopen the
  gate; explicit snapshots use `Connection.backup()`;
- the admin-only diagnostic reports health and aggregate counts without rows,
  identifiers, paths, or learning content.

Representative local benchmark (60,000 cards, 20,000 progress rows):

| Measurement | Result | P0/V1 budget |
|---|---:|---:|
| content merge | 0.033–0.056 s | recorded baseline |
| due query p95 | 4.321–5.422 ms | selection < 150 ms |
| new anti-join p95 | 8.828–13.987 ms | selection < 150 ms |
| session answer p95 | 0.468–0.500 ms | answer < 100 ms |

Run with `python -m scripts.p0_benchmark`. Timings are machine-specific.

## Gate B — Android Companion (P0.4/P0.5)

Targets were resolved from stable device-registry IDs on every send and then
routed through the data-capable `notify.mobile_app_*` action. The generic
`notify.send_message` entity action rejected Companion `data` on the live HA
version; `v0.0.2` therefore uses it only as an explicit plain-message fallback.

The device-registry `sw_version` values were 36 (Samsung SM-S928B) and 37
(Google Pixel 9 Pro). Semantic Companion app versions were not exposed by an
enabled entity.

| Sub-test | Samsung SM-S928B | Pixel 9 Pro |
|---|---|---|
| labelled notification physically received | PASS | PASS |
| stable target resolution | PASS | PASS |
| receipt confirmation event | PASS | PASS |
| unique action event | PASS | PASS |
| action/tag/device attribution | PASS | PASS |
| `event.context.user_id` | PASS | PASS |
| two Android devices not confused | PASS | PASS |
| Reveal action | PASS | PASS |
| same-tag replacement/no stacking | PASS | PASS |
| action-to-replacement API latency | PASS — 233 ms | PASS — 213–230 ms |
| silent replacement | FAIL — second vibration observed despite `alert_once` | BLOCKED_EXTERNAL — device did not vibrate initially, so the second vibration could not be isolated; operator accepted the visual result |
| `I don't know` | PASS | PASS |
| clear/swipe event | PASS | PASS |
| expiration at 10 seconds | PASS | PASS |
| four actions sent | PASS — 3 usable | PASS — 3 usable |
| free-text `P07` | PASS | PASS |
| lockscreen `public` | PASS — full content | PASS — full content |
| lockscreen `private` | PASS — content masked | PASS — full content; OS setting does not redact it |
| lockscreen `secret` | PASS — absent | PASS — absent |
| named Android channel | PASS — received on `LockLearn P0 Learning` | PASS — received on `LockLearn P0 Learning` |
| exact user-overridden channel importance | BLOCKED_EXTERNAL — not exposed to HA | BLOCKED_EXTERNAL — not exposed to HA |
| persistent replay/single-use result | NOT_APPLICABLE — P4 `NotificationInteraction` consumer does not exist in the P0 skeleton; one physical tap produced one bus event and zero duplicates in the grace window | NOT_APPLICABLE — same justification |
| shared-device physical signal quality | NOT_APPLICABLE — no configured shared Profile/device pair and P2 Profile ACL does not yet exist; automated reduced-signal policy tests pass |

Capability decision: both Android targets have `tag_replace=supported`. The
Samsung has `silent_replace=unsupported`; the Pixel remains `unknown` for
silent replacement. Unknown/unsupported therefore keeps two-step learning in
`exposure_only` until a later per-target qualification proves the complete
gate. This is a successful conservative qualification, not a claim that every
platform feature works.

## Gate C — HAOS/Supervisor backup and restore (P0.3/P0.7)

Safety backup observed through the HA API: `Pre-locklearn` (`94bbd79d`), on
both `hassio.local` and `hassio.ha_backup`. This is the operator-announced
`PRE_P0.7` safety point and was never restored.

Test backup: `LockLearn P0.7 state restore BB54319ACAC1` (`c34f8392`), created
2026-09-21 23:36:47 +02:00 on `hassio.local`.

| Sub-test | Status | Evidence |
|---|---|---|
| smallest supported real scope | PASS | partial backup; Home Assistant included; Recorder/add-ons excluded |
| exact archive scope | PASS | HAOS additionally included `ssl`; this was disclosed before restore |
| WAL/recent state captured | PASS | session was committed to version 2 immediately before backup |
| pre/post hooks and resumed writes | PASS | Supervisor backup completed; write gate inactive afterward; post-backup writes succeeded |
| mandatory hard stop | PASS | exact name, ID, type, scope, expected state and safety backup displayed; no automated restore call |
| manual restore | PASS | operator initiated the restore from Home Assistant |
| HA/LockLearn restart | PASS | API returned on Core 2026.7.4; one LockLearn entry loaded; HACS v0.0.2 installed |
| pre-backup state restored | PASS | marked session returned at version 2 rather than post-backup version 3 |
| post-backup state absent | PASS | separately marked post-only session returned `locklearn/not_found` |
| `PRAGMA integrity_check` | PASS | `ok` |
| foreign-key integrity | PASS | zero violations |
| schema/journal | PASS | schema 1, WAL |
| readers/writer recreated | PASS | reader remained off the event loop; writer initialized and completed a controlled version 2→3 mutation |
| panel/API after restore | PASS | bootstrap protocol 1; panel present at cache-buster v0.0.2 |
| duplicate runtime/log error | PASS | exactly one loaded entry; no LockLearn system-log match after restore |

HA 2025.2 cannot exclude reconstructible content per integration. Until a
future supported floor supplies such an API, backup UX must disclose that the
HA config archive contains both `.storage/locklearn/state.db` and any content
cache located under the config directory.

## Gate D — iPadOS Companion (P0.4/P0.5)

Target: Apple iPad12,1, name `iPad de Tiffanie`, device-registry `sw_version`
27.0. The semantic Companion app version entity was unavailable.

| Sub-test | Status | Evidence |
|---|---|---|
| physical receipt | PASS | operator received every labelled notification |
| stable outbound device resolution | PASS | explicit registry target resolved uniquely to `notify.mobile_app_ipad_de_tiffanie` |
| action access | PASS | appui long/expansion exposes actions without opening HA |
| action event and unique ID | PASS | one matching event, zero duplicates |
| `event.context.user_id` | PASS | present |
| inbound `device_id`/`tag` attribution | FAIL | iPadOS action events contained only `action`, plus `reply_text` for text input |
| Reveal | PASS | event received |
| same-tag replacement | FAIL | replacement created a second notification instead of replacing the first |
| silent replacement | NOT_APPLICABLE — no replacement primitive was available to qualify silence |
| four actions sent | PASS — all 4 accessible after expansion |
| `I don't know` | PASS | one action event with user context |
| clear/swipe | NOT_APPLICABLE — no cleared event during a 30-second real swipe probe |
| lockscreen visibility | FAIL | `public`, `private`, and `secret` contents were all visible |
| free-text `P07` | PASS | `action` and exact `reply_text` received once |
| persistent replay/single-use result | NOT_APPLICABLE — P4 interaction consumer does not yet exist; no duplicate bus event was observed |

Tapping the notification body opens Home Assistant and loses the actionable
surface; appui long/expansion is required. iPadOS therefore remains
`exposure_only`: tag replacement and visibility are unsupported. Unique action
IDs can correlate events, but inbound device identity must not be inferred from
fields iOS does not send.

## Security and privacy observations

- All test notifications used non-personal labels and random correlation IDs.
- Harness output records only field names and boolean/value-match results; it
  does not print free-text replies or credentials.
- Only `LOCKLEARN_HA_*` variables are loaded from `.env`; values are never
  logged.
- No HA access token appeared in output, files, evidence, or commits.
- A GitHub CLI auth check displayed only a masked token fragment in the local
  terminal; no complete credential was exposed or committed.
- The public-history scan found no secret signatures. GitHub repository secret
  scanning was not enabled, so that setting is not claimed as evidence.
- The storage diagnostic is administrator-only and returns health plus counts,
  never stored rows or learning content.

## Automated regression evidence

Before the v0.0.2 release:

- Ruff format/check: PASS;
- mypy over `custom_components datasets tests`: PASS;
- dataset registry validation: PASS;
- pytest on HA 2026.9.3/Python 3.14.4: 28 passed;
- frontend typecheck: PASS;
- Vitest: 3 passed;
- production frontend build: PASS (21.96 kB, 7.13 kB gzip);
- npm audit: 0 vulnerabilities.

After the evidence and backup harness were added:

- pytest on HA 2026.9.3/Python 3.14.4: 30 passed;
- pytest backend on HA 2025.2.5/Python 3.13.15: 24 passed;
- hassfest: 1 integration, 0 invalid;
- all other checks above remained PASS.

## P0 disposition

- Gate A — HACS / Config Flow / panel: **PASS**
- Gate B — Android Companion: **PASS** (capabilities measured; conservative
  fallback retained where unsupported/unknown)
- Gate C — HAOS Supervisor backup/restore: **PASS**
- Gate D — iOS/iPadOS Companion: **PASS** (platform limitations measured;
  `exposure_only` selected)

P0 is closed for architecture purposes. `NOT_APPLICABLE` replay/single-use and
shared-Profile cases belong to their already planned P2/P4 implementations;
they are not silently claimed as functional. The notification renderer in P4
must consume the per-target capability decisions above rather than treating a
platform family as uniformly capable.
