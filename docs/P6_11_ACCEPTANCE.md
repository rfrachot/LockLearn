# P6.11 — V1 acceptance evidence

`SPEC_V1.md` remains normative. This document is the final 1.0 acceptance map:
it does not invent new requirements and it does not promote V1.1/V2 work.

Evidence labels:

- **AUTO** — permanent automated test in the release suite.
- **E2E** — public WebSocket or browser end-to-end flow.
- **REAL-HA** — previously qualified physical Home Assistant/Companion evidence.
- **CI** — release-matrix gate on minimum/current/latest HA plus HACS/hassfest.

P6.10 release readiness is qualified on rewritten privacy-safe baseline
`93ca19eea3b9e9347fc6f4cd15afe30e3575b49b`; GitHub Actions run
`36474980367` passed every required P6.10 job.

## §129 mandatory 1.0 capabilities

| ID | Capability | Acceptance evidence |
|---|---|---|
| C-01 | HACS installation | REAL-HA `docs/P0_EVIDENCE.md`; CI HACS validation |
| C-02 | UI setup | REAL-HA P5 qualification; E2E panel |
| C-03 | custom panel | AUTO lifecycle + E2E Playwright |
| C-04 | multi-user | AUTO Profiles/ACL |
| C-05 | shared profiles | AUTO WebSocket CRUD/ACL |
| C-06 | multiple tracks | AUTO Track CRUD/configuration |
| C-07 | multilingual terms/facets | AUTO content model/locale tests |
| C-08 | vocabulary | AUTO starter/content tests |
| C-09 | kanji-capable generic content | AUTO content-type/model tests |
| C-10 | grammar reference + cloze-MCQ | AUTO quiz/content-block tests |
| C-11 | learning two-step reveal | AUTO learning state + frontend E2E |
| C-12 | quiz MCQ | AUTO quiz + Playwright |
| C-13 | panel free_text | AUTO grading/WebSocket tests |
| C-14 | free learning session | AUTO persistent/session selection tests |
| C-15 | free quiz session | AUTO quiz session tests |
| C-16 | introduction mode + learning steps | AUTO learning state machine |
| C-17 | basic SRS per card/facets | AUTO review policy/progress |
| C-18 | elapsed-time scheduling + difficulty factor | AUTO review policy |
| C-19 | verified promotion gate | AUTO signal policy |
| C-20 | prerequisite/card unlock rules | AUTO selection constraints |
| C-21 | known-already / suspend / bury | AUTO progress-state tests |
| C-22 | personal annotations/mnemonics | AUTO difficulty/annotation tests |
| C-23 | relearning / relapse | AUTO learning/review policy |
| C-24 | sibling burial | AUTO selection constraints |
| C-25 | weak items / leech / confusion matrix | AUTO difficulties/stats |
| C-26 | reliable undo + rebuild projection | AUTO integrity/review-event tests |
| C-27 | deterministic scheduler | AUTO scheduler |
| C-28 | multi-track + multi-target arbitration | AUTO scheduler |
| C-29 | robust actionable notifications | AUTO notification suite + REAL-HA |
| C-30 | basic stats dashboard | AUTO stats + frontend E2E |
| C-31 | metacognitive calibration | AUTO stats |
| C-32 | SQLite state + content.db + dataset packages | AUTO storage/content generation |
| C-33 | migrations | AUTO migration/recovery |
| C-34 | backup-safe lifecycle | AUTO storage lifecycle + REAL-HA |
| C-35 | Repairs | AUTO lifecycle/dataset/target Repairs |
| C-36 | HA services/events | AUTO HA actions/events contracts |
| C-37 | pack/dataset model | AUTO packs/dataset manager |
| C-38 | provenance/licensing | AUTO dataset catalogue/provenance |
| C-39 | signed dataset update + rollback | AUTO DatasetManager |
| C-40 | commercial-compatible official source policy | AUTO resource/licence policy |
| C-41 | FR + EN UI | AUTO i18n parity + frontend |
| C-42 | secure export/import | AUTO profile transfer/security |
| C-43 | complete core documentation | AUTO P6.9 docs contract |
| C-44 | base HA services/actions | AUTO HA actions/services |
| C-45 | base HA events | AUTO privacy-safe event contracts |
| C-46 | CI/tests | CI full matrix + HACS/hassfest |

## §133 architectural invariants

| ID | Invariant | Evidence |
|---|---|---|
| I-01 | Profile != HA user | Profiles tests |
| I-02 | Profile != device | target/profile identity tests |
| I-03 | Track != pack | Track/PackVersion tests |
| I-04 | Concept != Term | content model tests |
| I-05 | Learning mode != content type | session/content tests |
| I-06 | Progress is card/facet-specific | progress/review tests |
| I-07 | Frontend never owns permissions | WebSocket ACL matrix |
| I-08 | Content data != user state | storage boundary tests |
| I-09 | HA Recorder != LockLearn database | entity/privacy contract |
| I-10 | Core does not depend on Japanese | generic core/content tests |
| I-11 | Released dataset IDs stable or mapped | dataset identity/migration tests |
| I-12 | Official sources commercially compatible | resource policy tests |
| I-13 | Invalid update preserves last-known-good | DatasetManager rollback tests |
| I-14 | Progress belongs to CardDefinition | content/progress tests |
| I-15 | No raw upstream parsing on HA | release payload/source boundary |
| I-16 | Cross-DB integrity application-enforced | integrity/storage tests |
| I-17 | Third-party rich content never trusted HTML | rich-text/SVG security tests |
| I-18 | ReviewEvents audit source, projection rebuildable | review/integrity tests |
| I-19 | Notification actions are not strong authentication | notification threat tests |
| I-20 | Stable progression identity includes facets/card definition | content identity tests |
| I-21 | No promotion after visible answer | signal policy tests |
| I-22 | New quotas counted in CardDefinitions | session selection tests |
| I-23 | Sibling spacing prevents priming | selection tests |
| I-24 | Notification timestamps are not retrieval timestamps | review/notification tests |
| I-25 | Hint quality is persisted | signal/review tests |
| I-26 | Mastered is non-terminal display state | review policy tests |
| I-27 | Self-assessment cannot promote indefinitely | signal policy tests |
| I-28 | New card introduced before testing | learning state tests |
| I-29 | Failed card not immediately re-tested | learning state tests |
| I-30 | receptive_when affects notification delivery | scheduler tests |
| I-31 | Shared-device responses lower confidence | notification action tests |
| I-32 | HA events omit learning content by default | HA event privacy tests |

## §135 Definition of Done

### Adrien

| ID | Scenario step | Evidence |
|---|---|---|
| A-01 | installs from HACS | REAL-HA P0 + HACS CI |
| A-02 | completes onboarding with mini dataset | E2E fresh starter + starter tests |
| A-03 | creates Profile | E2E fresh starter |
| A-04 | creates Track | E2E fresh starter |
| A-05 | configures 08:00–20:00 / learning / quiz | E2E profile/track settings + scheduler |
| A-06 | receives notifications | REAL-HA P0 + notification delivery |
| A-07 | answers 👍/👎 and quizzes | AUTO notification actions + quiz |
| A-08 | opens dashboard | frontend E2E + dashboard backend |
| A-09 | chains a 20-card session | E2E starter selects 20 + session policy tests |
| A-10 | resumes same session from another client | E2E starter + session lifecycle |
| A-11 | sees basic statistics | E2E starter + stats tests |
| A-12 | sees dataset provenance/licence | E2E catalogue + provenance tests |
| A-13 | installs a new dataset version | DatasetManager update test |
| A-14 | sees Pack diff | Track pack-update preview test |
| A-15 | explicitly integrates new PackVersion | WebSocket Track integration test |
| A-16 | loses no progression | DatasetManager + Track integration/progress tests |

### Camille

| ID | Scenario step | Evidence |
|---|---|---|
| CAMILLE-01 | creates a private Profile | Profiles + ACL tests |
| CAMILLE-02 | enables Japanese and Spanish Tracks | generic multilingual Track model/tests |
| CAMILLE-03 | owns independent settings/progression | Profile/Track/progress isolation tests |

### Zoé

| ID | Scenario step | Evidence |
|---|---|---|
| ZOE-01 | child Profile requires no HA account | child Profile test |
| ZOE-02 | Adrien + Camille are owners | multiple-owner child Profile test |
| ZOE-03 | progression remains independent | profile/card progress isolation |
| ZOE-04 | shared-device notifications identify Profile | notification renderer test |

### Resilience

| ID | Scenario | Evidence |
|---|---|---|
| R-01 | HA reload does not duplicate scheduler/resources | lifecycle reload test |
| R-02 | backup/restore preserves state.db | storage lifecycle + REAL-HA P0 |
| R-03 | renamed/unresolved Companion target surfaces Repairs | target + delivery Repairs tests |
| R-04 | invalid/signature-invalid dataset preserves previous version | DatasetManager rollback/signature tests |
| R-05 | concurrent session mutation returns stale_session | persistent session/WebSocket CAS tests |

## V1.1 / V2 non-blockers

The following remain explicitly outside the 1.0 blocking path unless the normative
spec is changed: Exam mode, advanced HA sensors, full image/audio renderers,
enriched statistics, advanced morphology/cloze generation, speech/handwriting/OCR,
FSRS optimization, cloud/sync, native apps, LLM tutoring and complex gamification.

P6.11 qualification must fail on a missing V1 capability or resilience scenario;
it must **not** fail merely because one of these deferred features is absent.
