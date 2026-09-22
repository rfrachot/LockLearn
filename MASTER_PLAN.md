# MASTER_PLAN.md — LockLearn V1 execution plan

> `SPEC_V1.md` Draft v0.6 (2026-09-15) is normative.  
> Detailed work-package requirements are in `docs/plan/`.  
> Complete spec coverage is in `docs/REQUIREMENTS_TRACEABILITY.md`.

## Rules

- Spec conflicts are explicit: update this plan or update the spec + relevant ADR.
- P0 is evidence-first; no HA/Companion/storage assumption becomes architecture without a real spike.
- Work packages are durable scopes; implementation is sliced into short `missions/`.
- Definition of Done includes relevant implementation, tests, typing/lint, ACL, security, migration, docs/ADR, changelog and backward compatibility.
- V1.1/V2+/research never silently enter the 1.0 critical path.
- `review_events` is the audit source; projections are rebuildable.
- No blocking SQLite I/O on the HA event loop and no runtime user state under `custom_components/`.
- Core remains content-agnostic; Japanese-specific choices stay in data/curation/adapters.

## Critical path

`P0 → P1 → P2 → P3 → P4 → P5 → P6`  
`P7` is post-1.0 unless deliberately promoted by spec change.

| Phase | Goal | State | 1.0 blocker | Detail |
|---|---|---|---|---|
| P0 | Architecture spikes + installable HA skeleton | complete | yes | `docs/plan/P0.md` |
| P1 | Content core + signed starter dataset | complete | yes | `docs/plan/P1.md` |
| P2 | Profiles/tracks/ACL | complete | yes | `docs/plan/P2.md` |
| P3 | Learning/SRS/sessions/stats | in progress (P3.1–P3.2 complete; P3.3 pending gate) | yes | `docs/plan/P3.md` |
| P4 | Scheduler/notifications/HA automation | queued | yes | `docs/plan/P4.md` |
| P5 | Useful panel | queued | yes | `docs/plan/P5.md` |
| P6 | Hardening/release | queued | yes | `docs/plan/P6.md` |
| P7 | V1.1/research | later | no | `docs/plan/P7.md` |

## Work-package index

### P0

- **P0.1** — Toolchain, compatibility floor and quality baseline
- **P0.2** — Installable HA skeleton, single config entry and lifecycle
- **P0.3** — SQLite concurrency, state/content boundary and backup spike
- **P0.4** — Companion notification capability matrix
- **P0.5** — Identity, target resolution and unattended-action spike
- **P0.6** — WebSocket, session CAS/subscription and operation-stream spike
- **P0.7** — P0 architecture gate and ADR set

### P1

- **P1.1** — Canonical content domain model (complete)
- **P1.2** — Dataset package contract, signatures and hostile-archive handling (complete)
- **P1.3** — Content blocks, grading metadata and safe rich text (complete)
- **P1.4** — Multilingual normalization and locale primitives (complete)
- **P1.5** — Tags, packs, prerequisites and Japanese curation primitives (complete)
- **P1.6** — content.db schema, generations and stable merge (complete)
- **P1.7** — Source/provenance/license registry (complete)
- **P1.8** — Dataset build pipeline and source adapters (complete)
- **P1.9** — DatasetManager, update entity, staging and rollback (complete)
- **P1.10** — Signed first-run mini dataset (complete)
- **P1.11** — Media-ready Asset schema without V1 renderer scope (complete)

### P2

- **P2.1** — state.db foundation and application repositories (complete)
- **P2.2** — Profiles, presets and HA-user mapping (complete)
- **P2.3** — Backend ACL and privacy filtering (complete)
- **P2.4** — Track configuration, pack pinning and card rules (complete)
- **P2.5** — Learning quotas, goals and load forecast (complete)
- **P2.6** — Profiles/tracks WebSocket CRUD and errors (complete)

### P3

- **P3.1** — ReviewEvent audit log and progress projection (complete)
- **P3.2** — Introduction and learning-step state machine (complete)
- **P3.3** — ReviewPolicy V1 core (implemented; verification pending)
- **P3.4** — Verified-retrieval gate and signal weighting
- **P3.5** — Sibling burial, prerequisites and confusable introduction spacing
- **P3.6** — Quiz engine, distractors and corrective feedback
- **P3.7** — Panel free-text grading and content-quality feedback
- **P3.8** — Persistent sessions, concurrency and cross-client resume
- **P3.9** — Fatigue-aware session selection and interleaving
- **P3.10** — Known-already, suspend/bury and calibration
- **P3.11** — Leech detection, confusion matrix and personal annotations
- **P3.12** — Undo, integrity rebuild and algorithmic recompute
- **P3.13** — Basic statistics and metacognitive calibration backend
- **P3.14** — Long-horizon SRS simulation gate

### P4

- **P4.1** — Materialized scheduler slots and deterministic generation
- **P4.2** — Timezone, DST, restart and clock-jump reconciliation
- **P4.3** — Multi-track/multi-target arbitration and capacity Repairs
- **P4.4** — Context-aware receptivity and routine slots
- **P4.5** — Notification selection policy, missed/pending/backoff
- **P4.6** — Persistent notification interactions and replay protection
- **P4.7** — Notification renderers and privacy-safe target behavior
- **P4.8** — HA services/actions and pedagogical events
- **P4.9** — Automation blueprints

### P5

- **P5.1** — Frontend shell, protocol/bootstrap and routing
- **P5.2** — Home dashboard and profile switcher
- **P5.3** — Learn UI and introduction/reveal flow
- **P5.4** — Quiz/free-text/cloze UI
- **P5.5** — Profiles/tracks/packs/settings management UI
- **P5.6** — Dataset updates, Sources & Licences UI
- **P5.7** — Basic stats, difficulties and metacognitive views
- **P5.8** — FR/EN i18n, CJK and accessibility hardening
- **P5.9** — Frontend performance and compatibility gate

### P6

- **P6.1** — Database/config/content migrations and recovery
- **P6.2** — Backup hooks, unload/reload and uninstall/recovery UX
- **P6.3** — Repairs and diagnostics
- **P6.4** — Secure export/import and data deletion
- **P6.5** — HA entity/sensor privacy contract and optional integration boundary
- **P6.6** — Security hardening and threat-model tests
- **P6.7** — Performance, scale and storage-budget validation
- **P6.8** — Full test matrix and CI release gates
- **P6.9** — Documentation set and generated contracts
- **P6.10** — Release packaging, versioning and HACS readiness
- **P6.11** — V1 end-to-end acceptance scenarios

### P7

- **P7.1** — Exam mode V1.1
- **P7.2** — Advanced stats and optional HA sensors
- **P7.3** — Image/audio learning renderers
- **P7.4** — Future research backlog

## Cross-cutting 1.0 gates

- **Security/privacy:** backend ACL everywhere; no private content leakage; hostile inputs; replay-safe notifications; signed official datasets.
- **Pedagogy:** encode before test; no visible-answer promotion; explicit IDK; no immediate retry; hint/shared-device signal reduction; sibling/confusable spacing; card-based quotas.
- **Storage:** separate state/content DBs; no HA-loop blocking; migrations + recovery; stable content IDs; coherent WAL backups.
- **Home Assistant:** one Config Entry; clean unload/reload; registry-based target identity; audited unattended actions; HA bus is output only.
- **Documentation/scope:** rationale-focused ADRs; docs/contracts with code; CHANGELOG when relevant; V1.1/V2+ never become implicit promises.

## 1.0 release gate

1. HACS install + config flow + signed starter content + custom panel.
2. Private/shared/child profiles and multiple tracks with explicit pack versions.
3. Generic multilingual Concept/Term/LearningItem/Facet/CardDefinition model.
4. Vocabulary/kanji/grammar plus introduction, reveal, MCQ, panel free-text and cloze-MCQ.
5. Deterministic versioned SRS with learning/relearning, elapsed time, difficulty, verified gate, prerequisites, sibling burial, leech/confusion, annotations, calibration and known/suspend/bury.
6. Canonical review audit, safe undo and rebuilds.
7. Deterministic/context-aware scheduler, multi-track/target arbitration and robust actionable notifications.
8. Useful FR/EN panel + honest basic stats/metacognitive calibration.
9. Signed dataset update/rollback, provenance/licensing and explicit pack integration.
10. Backup-safe lifecycle, migrations, Repairs, secure export/import and privacy-safe HA services/events.
11. Full tests/CI/support matrix/documentation.
12. Exact §135 Renaud/Tiffanie/Lou + resilience acceptance scenarios.

## Explicit non-blockers for 1.0

Exam mode; advanced/optional sensors; full image/audio renderers; Live Updates; advanced morphology/cloze generation; handwriting/speech/OCR; FSRS optimization; community marketplace/backend; cloud accounts/sync; native apps; LLM tutoring/generated courses; complex gamification/leaderboards/multiplayer.
