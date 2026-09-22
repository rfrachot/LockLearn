# REQUIREMENTS_TRACEABILITY.md

> Generated from `SPEC_V1.md` Draft v0.6 (2026-09-15).  
> This file is a coverage index, not a replacement for the specification.  
> A row means “this work package is responsible for proving this section”; it does not mean every sentence in the section is complete.

## 1. How to use this matrix

- `SPEC_V1.md` is normative.
- `MASTER_PLAN.md` owns execution sequencing and work-package acceptance.
- Mission files own the current implementation slice.
- A spec section is considered **implemented** only when its behavioral requirements have tests/evidence and the owning work packages are complete.
- If a future spec edit adds/removes/renumbers a numbered section, this matrix must be updated in the same change.
- Cross-cutting invariants in §133 are expanded separately below because section-level mapping alone is not sufficient.

## 2. Numbered spec coverage

| Spec | Title | Disposition | Owning work package(s) |
|---|---|---|---|
| §1 | Vision | V1 / cross-cutting | P6.11 |
| §2 | Principes du projet | V1 / cross-cutting | P6.11 |
| §2.1 | Local-first | V1 / cross-cutting | P6.11 |
| §2.2 | Multi-utilisateur natif | V1 / cross-cutting | P6.11 |
| §2.3 | Content-agnostic | V1 / cross-cutting | P6.11 |
| §2.4 | Multilingue dans les deux sens | V1 / cross-cutting | P6.11 |
| §2.5 | Progression indépendante de la direction | V1 / cross-cutting | P6.11 |
| §3 | Scope fonctionnel V1 | V1 / cross-cutting | P6.11 |
| §3.1 | Apprentissage passif | V1 / cross-cutting | P0.4, P3.2, P3.4, P4.7, P6.11 |
| §3.2 | Quiz passif | V1 / cross-cutting | P0.4, P3.4, P3.6, P4.7, P6.11 |
| §3.3 | Sessions actives | V1 / cross-cutting | P3.8, P5.3, P6.11 |
| §3.4 | Mode examen — V1.1 | V1.1 | P6.11, P7.1 |
| §4 | Modèle de domaine | V1 / cross-cutting | P1.1 |
| §5 | Concept | V1 / cross-cutting | P1.1 |
| §6 | Term | V1 / cross-cutting | P1.1 |
| §7 | Relation Concept ↔ Term | V1 / cross-cutting | P1.1 |
| §8 | LearningItem | V1 / cross-cutting | P1.1, P1.3, P3.7 |
| §9 | ContentBlock | V1 / cross-cutting | P1.3 |
| §10 | Exemple : contenu kanji | V1 / cross-cutting | P1.4 |
| §11 | Exemple : grammaire | V1 / cross-cutting | P1.3, P3.6 |
| §12 | Images | V1 / cross-cutting | P1.11, P7.3 |
| §13 | Audio | V1 / cross-cutting | P1.11, P7.3 |
| §14 | Tags | V1 / cross-cutting | P1.4 |
| §15 | Packs | V1 / cross-cutting | P1.4, P3.5 |
| §16 | Dataset versus Pack | V1 / cross-cutting | P1.1 |
| §17 | Multilinguisme | V1 / cross-cutting | P1.3, P1.4, P3.7 |
| §18 | Profil utilisateur | V1 / cross-cutting | P2.1, P2.2, P5.5 |
| §19 | Relation avec les utilisateurs Home Assistant | V1 / cross-cutting | P0.5, P2.2 |
| §20 | ACL des profils | V1 / cross-cutting | P0.5, P2.1, P2.3, P5.5 |
| §21 | Plusieurs owners | V1 / cross-cutting | P0.5, P2.3 |
| §22 | Confidentialité entre profils | V1 / cross-cutting | P0.5, P2.3 |
| §23 | Administrateurs Home Assistant | V1 / cross-cutting | P0.5, P2.3 |
| §24 | Track / parcours | V1 / cross-cutting | P1.4, P2.1, P2.4, P5.5 |
| §25 | Plusieurs tracks simultanés | V1 / cross-cutting | P2.4, P2.5, P4.3, P5.5 |
| §26 | Direction | V1 / cross-cutting | P1.4, P2.4 |
| §27 | Pondération des contenus | V1 / cross-cutting | P1.4, P2.4, P2.5, P3.9 |
| §28 | Progression | V1 / cross-cutting | P2.1, P3.1, P3.2, P3.10 |
| §29 | SRS V1 | V1 / cross-cutting | P2.5, P3.2, P3.3, P3.4, P3.5, P3.14 |
| §30 | Correspondance des actions | V1 / cross-cutting | P3.1, P3.2, P3.3, P3.4, P3.7, P3.9 |
| §31 | Leech | V1 / cross-cutting | P3.11, P5.7 |
| §31.1 | Annotations personnelles | V1 / cross-cutting | P3.11, P5.7 |
| §32 | Annulation d'une réponse | V1 / cross-cutting | P3.12 |
| §33 | Historique événementiel | V1 / cross-cutting | P2.1, P3.1, P3.12 |
| §34 | Scheduler | V1 / cross-cutting | P0.4, P4.1, P4.2, P4.3, P4.4, P4.5 |
| §35 | Fenêtre active | V1 / cross-cutting | P2.5, P3.14, P4.1, P4.4 |
| §36 | Distribution temporelle | V1 / cross-cutting | P4.1, P4.2 |
| §37 | Paramètres scheduler | V1 / cross-cutting | P4.1, P4.2, P4.3 |
| §38 | Notifications manquées | V1 / cross-cutting | P0.4, P4.5 |
| §39 | Notification en attente | V1 / cross-cutting | P0.4, P4.5 |
| §40 | Notifications V1 | V1 / cross-cutting | P0.4, P3.4, P4.6, P4.7 |
| §41 | Live Updates | research / optional | P0.4, P7.4 |
| §42 | Images dans les notifications | V1 / cross-cutting | P0.4, P1.11, P4.7, P7.3 |
| §43 | Appareils et targets | V1 / cross-cutting | P0.4, P0.5, P3.4, P4.3, P4.7 |
| §44 | Plusieurs appareils | V1 / cross-cutting | P0.4, P0.5, P4.3, P4.7 |
| §45 | Dashboard LockLearn | V1 / cross-cutting | P5.1 |
| §46 | Stack frontend | V1 / cross-cutting | P5.1 |
| §47 | Navigation du dashboard | V1 / cross-cutting | P5.1 |
| §48 | Home | V1 / cross-cutting | P5.2 |
| §49 | Profile switcher | V1 / cross-cutting | P5.2 |
| §50 | Learn | V1 / cross-cutting | P3.2, P5.3 |
| §51 | Quiz | V1 / cross-cutting | P1.3, P3.6, P3.7, P5.4 |
| §52 | Distracteurs | V1 / cross-cutting | P3.5, P3.6, P3.11, P5.4 |
| §53 | Session | V1 / cross-cutting | P0.6, P2.1, P3.8, P3.9 |
| §53.1 | Gestion de la fatigue intra-session | V1 / cross-cutting | P0.6, P2.1, P3.8, P3.9 |
| §54 | Reprise cross-platform | V1 / cross-cutting | P0.6, P3.8 |
| §55 | Examen | V1.1 | P7.1 |
| §56 | Sélection examen | V1.1 | P7.1 |
| §57 | Statistiques | V1 / cross-cutting | P2.1, P3.1, P3.12, P3.13, P5.7 |
| §58 | Statistiques dashboard | V1 / cross-cutting | P2.5, P3.11, P3.13, P5.2, P5.7, P7.2 |
| §59 | Home Assistant entities | V1 / cross-cutting | P6.5, P7.2 |
| §60 | Confidentialité des sensors HA | V1 / cross-cutting | P2.3, P6.5 |
| §61 | Automatisations HA | V1 / cross-cutting | P0.5, P4.8, P4.9 |
| §62 | Architecture backend | V1 / cross-cutting | P0.2 |
| §62.1 | Cycle de vie Home Assistant et intégrations natives | V1 / cross-cutting | P0.2, P0.5, P1.9, P4.3, P4.8, P6.2, P6.3 |
| §63 | Config Entry Home Assistant | V1 / cross-cutting | P0.2 |
| §64 | Pourquoi pas ConfigSubentries pour les profils ? | V1 / cross-cutting | P0.2 |
| §65 | Frontend ↔ Backend | V1 / cross-cutting | P0.6, P5.1 |
| §65.1 | Serving des assets | V1 / cross-cutting | P0.6, P0.7, P1.11, P5.1, P6.4, P6.6 |
| §66 | API WebSocket indicative | V1 / cross-cutting | P0.6, P2.6, P3.7, P3.8, P3.12 |
| §67 | Base de données | V1 / cross-cutting | P0.3, P1.6 |
| §68 | content.db | V1 / cross-cutting | P0.3, P1.6, P1.11, P6.7 |
| §69 | state.db | V1 / cross-cutting | P0.3, P2.1, P6.7 |
| §70 | Emplacement des DB | V1 / cross-cutting | P0.3, P6.2 |
| §71 | Accès SQLite | V1 / cross-cutting | P0.3, P2.1 |
| §72 | Migrations DB | V1 / cross-cutting | P0.3, P6.1 |
| §73 | Migration Config Entry | V1 / cross-cutting | P0.3, P6.1 |
| §74 | Sources de contenu et chaîne de mise à jour | V1 / cross-cutting | P1.8 |
| §74.1 | Source | V1 / cross-cutting | P1.7, P1.8 |
| §74.2 | SourceSnapshot | V1 / cross-cutting | P1.7, P1.8 |
| §74.3 | Provenance au niveau des données | V1 / cross-cutting | P1.7, P1.8 |
| §74.4 | Stable IDs et mises à jour | V1 / cross-cutting | P1.7, P1.8 |
| §74.5 | DatasetBuild | V1 / cross-cutting | P1.2, P1.8 |
| §74.5.1 | Format d’artefact dataset | V1 / cross-cutting | P1.2, P1.8, P6.7 |
| §74.6 | Distribution des mises à jour | V1 / cross-cutting | P1.8 |
| §74.7 | Pipeline GitHub Actions recommandé | V1 / cross-cutting | P1.8 |
| §74.8 | Update Manager Home Assistant | V1 / cross-cutting | P1.8, P1.9, P5.6 |
| §74.9 | Stratégie d'activation | V1 / cross-cutting | P1.2, P1.6, P1.8, P1.9 |
| §74.10 | Fréquence et données obsolètes | V1 / cross-cutting | P1.8, P1.9 |
| §74.11 | Pas de dépendance runtime aux sources amont | V1 / cross-cutting | P1.8 |
| §75 | IDs stables | V1 / cross-cutting | P1.1, P1.6 |
| §76 | Pack format | V1 / cross-cutting | P1.4, P2.4, P5.5 |
| §76.1 | Règles de curation japonaises recommandées | V1 / cross-cutting | P1.4, P2.4, P3.5, P5.5 |
| §77 | Politique de licences et sources fortement recommandées | V1 / cross-cutting | P1.7 |
| §77.1 | Principe général | V1 / cross-cutting | P1.7 |
| §77.2 | Licence recommandée du projet | V1 / cross-cutting | P1.7 |
| §77.3 | EDRDG — JMdict | V1 / cross-cutting | P1.7 |
| §77.4 | EDRDG — KANJIDIC2 + RADKFILE/KRADFILE | V1 / cross-cutting | P1.7 |
| §77.5 | Wiktionary via Wiktextract / Kaikki | V1 / cross-cutting | P1.7 |
| §77.6 | Tatoeba | V1 / cross-cutting | P1.7 |
| §77.7 | KanjiVG | V1 / cross-cutting | P1.7 |
| §77.8 | Grammaire | V1 / cross-cutting | P1.7 |
| §77.9 | JLPT | V1 / cross-cutting | P1.7 |
| §77.9.1 | Compatibilité de distribution et marques | V1 / cross-cutting | P1.7 |
| §77.10 | Registre de licences | V1 / cross-cutting | P1.7 |
| §77.11 | Écran Sources & Licences | V1 / cross-cutting | P1.7, P5.6 |
| §78 | Localisation de l'interface | V1 / cross-cutting | P1.4, P5.8 |
| §79 | Accessibilité | V1 / cross-cutting | P5.3, P5.4, P5.8 |
| §80 | Performance | V1 / cross-cutting | P0.3, P0.6, P0.7, P3.14, P5.9, P6.7 |
| §81 | Batterie téléphone | V1 / cross-cutting | P0.4, P5.9 |
| §82 | Sécurité | V1 / cross-cutting | P0.5, P0.7, P1.2, P1.3, P4.6, P6.4, P6.6 |
| §83 | Diagnostics | V1 / cross-cutting | P6.3 |
| §84 | Export / import | V1 / cross-cutting | P6.4 |
| §84.1 | Désinstallation et récupération | V1 / cross-cutting | P6.2, P6.4 |
| §85 | Suppression d'un profil | V1 / cross-cutting | P6.4 |
| §86 | Suppression d'un pack | V1 / cross-cutting | P1.9, P6.4 |
| §87 | Statistiques longues durée Home Assistant | V1 / cross-cutting | P6.5, P7.2 |
| §88 | Installation | V1 / cross-cutting | P0.2, P1.10, P6.10 |
| §89 | Config Flow initial | V1 / cross-cutting | P0.2, P1.10, P2.2, P5.5 |
| §90 | Pas de YAML obligatoire | V1 / cross-cutting | P0.2 |
| §91 | Frontend packaging | V1 / cross-cutting | P1.4, P5.1, P5.8, P6.10 |
| §92 | Architecture repo recommandée | V1 / cross-cutting | P0.1 |
| §93 | Tests backend | V1 / cross-cutting | P6.8 |
| §94 | Tests ACL | V1 / cross-cutting | P2.3, P6.8 |
| §95 | Tests scheduler | V1 / cross-cutting | P4.1, P4.2, P6.8 |
| §96 | Tests SRS | V1 / cross-cutting | P3.3, P3.5, P3.14, P6.8 |
| §97 | Tests DB | V1 / cross-cutting | P6.8 |
| §98 | Tests frontend | V1 / cross-cutting | P5.9, P6.8 |
| §99 | CI | V1 / cross-cutting | P1.8, P6.8, P6.10 |
| §100 | Versioning | V1 / cross-cutting | P6.10 |
| §101 | Compatibility matrix | V1 / cross-cutting | P0.1, P0.7, P5.9, P6.8, P6.10 |
| §102 | Documentation : principe général | V1 / cross-cutting | P6.9 |
| §103 | Documentation requise | V1 / cross-cutting | P6.9 |
| §104 | SPEC_V1.md | V1 / cross-cutting | P6.9 |
| §105 | ARCHITECTURE.md | V1 / cross-cutting | P6.9 |
| §106 | DATA_MODEL.md | V1 / cross-cutting | P6.9 |
| §107 | DATABASE.md | V1 / cross-cutting | P6.9 |
| §108 | PACK_FORMAT.md | V1 / cross-cutting | P6.9 |
| §108.1 | DATA_SOURCES.md | V1 / cross-cutting | P6.9 |
| §108.2 | DATA_UPDATES.md | V1 / cross-cutting | P6.9 |
| §108.3 | LICENSING.md | V1 / cross-cutting | P6.9 |
| §109 | PERMISSIONS.md | V1 / cross-cutting | P2.3, P6.9 |
| §110 | SRS.md | V1 / cross-cutting | P6.9 |
| §111 | SCHEDULER.md | V1 / cross-cutting | P6.9 |
| §112 | NOTIFICATIONS.md | V1 / cross-cutting | P0.4, P6.9 |
| §113 | FRONTEND.md | V1 / cross-cutting | P6.9 |
| §114 | API.md | V1 / cross-cutting | P6.9 |
| §115 | MIGRATIONS.md | V1 / cross-cutting | P6.1, P6.9 |
| §116 | SECURITY.md | V1 / cross-cutting | P2.3, P6.6, P6.9 |
| §117 | PRIVACY.md | V1 / cross-cutting | P2.3, P6.6, P6.9 |
| §118 | DEVELOPMENT.md | V1 / cross-cutting | P6.9 |
| §119 | TESTING.md | V1 / cross-cutting | P6.9 |
| §120 | RELEASE.md | V1 / cross-cutting | P6.9, P6.10 |
| §121 | TROUBLESHOOTING.md | V1 / cross-cutting | P6.9 |
| §122 | ROADMAP.md | V1 / cross-cutting | P6.9 |
| §123 | ADR — Architecture Decision Records | V1 / cross-cutting | P0.7, P6.9 |
| §124 | AGENTS.md | V1 / cross-cutting | P6.9 |
| §125 | CHANGELOG.md | V1 / cross-cutting | P6.9 |
| §126 | Commentaires de code | V1 / cross-cutting | P6.9 |
| §127 | Documentation générée | V1 / cross-cutting | P6.9 |
| §128 | MVP technique | V1 / cross-cutting | P0.1, P0.2, P0.3, P0.4, P0.5, P0.6, P0.7 |
| §129 | V1 obligatoire | V1 / cross-cutting | P1.10, P3.10, P3.14, P6.11 |
| §130 | Prévu dans le data model mais pas obligatoirement complet en 1.0 | schema-ready / V1.1 candidate | P6.5, P7.1, P7.2, P7.3, P7.4 |
| §131 | Hors scope V1 | out of scope V1 | P7.4 |
| §132 | Évolutions candidates V2+ | V2+ candidates | P7.1, P7.3, P7.4 |
| §133 | Invariants architecturaux V1 | V1 / cross-cutting | P0.7, P1.1, P3.1, P3.4, P4.8, P6.11 |
| §134 | Critères de qualité | V1 / cross-cutting | P0.1, P6.8 |
| §135 | Definition of Done V1 | V1 / cross-cutting | P6.11 |
| §136 | Objectif produit final de V1 | V1 / cross-cutting | P6.11 |
| §137 | Philosophie finale | V1 / cross-cutting | P6.11 |

## 3. Architectural invariant coverage (§133)

These 32 invariants are release gates. They must stay true even if the implementation changes.

| Invariant | Requirement | Primary proof owner(s) |
|---|---|---|
| I-01 | `Profile != HA user` | P2.2, P2.3 |
| I-02 | `Profile != device` | P0.5, P4.7 |
| I-03 | `Track != pack` | P2.4 |
| I-04 | `Concept != term` | P1.1 |
| I-05 | `Learning mode != content type` | P1.1, P3.6 |
| I-06 | Progress is card/facet-specific | P3.1 |
| I-07 | Frontend never owns permissions | P2.3, P5.1 |
| I-08 | Content data != user state | P1.6, P2.1 |
| I-09 | HA Recorder != LockLearn database | P6.5 |
| I-10 | Core must not depend on Japanese | P1.1, P1.4 |
| I-11 | Released dataset IDs stay stable unless explicit mapping exists | P1.1, P1.6 |
| I-12 | Official datasets reject NC/ND/unknown/commercially incompatible data | P1.7 |
| I-13 | Dataset update never replaces last-known-good before validation | P1.9 |
| I-14 | Progress belongs to CardDefinition, not Concept | P3.1 |
| I-15 | HA runtime never parses large raw upstream corpora | P1.8 |
| I-16 | Cross-database referential integrity is application-enforced and tested | P2.1 |
| I-17 | Third-party rich content is never trusted HTML | P1.3, P6.6 |
| I-18 | Review events are audit source; progress is rebuildable projection | P3.1, P3.12 |
| I-19 | Notification actions are not strong authentication | P0.5, P4.6 |
| I-20 | Stable progression identity includes facet/card-definition identity | P1.1, P3.1 |
| I-21 | No SRS box promotion from self-assessment when answer was visible | P3.4 |
| I-22 | New-item quotas count CardDefinitions, not LearningItems | P2.5 |
| I-23 | Sibling cards are spaced to avoid priming | P3.5 |
| I-24 | Notification timestamps never replace actual retrieval timestamps | P3.1, P3.4 |
| I-25 | Hint use changes and persists signal quality | P3.4 |
| I-26 | `mastered` is a display label, not terminal scheduling state | P3.3 |
| I-27 | Self-assessment cannot indefinitely promote without verified retrieval | P3.4 |
| I-28 | New card is introduced before testing; first exposure is not failure | P3.2 |
| I-29 | Failed card is not immediately retested from working memory | P3.2 |
| I-30 | Notification delivery is context-aware when `receptive_when` is configured | P4.4 |
| I-31 | Shared-device responses are lower confidence unless explicitly trusted | P0.5, P3.4 |
| I-32 | HA quiz/result events do not expose learning content by default | P4.8 |

## 4. V1 mandatory capability coverage (§129)

The following is the release-facing checklist. Detailed acceptance remains in the owning work packages.

| Capability group | Work packages |
|---|---|
| HACS install, UI setup, custom panel | P0.2, P5.1, P6.10 |
| Multi-user, shared profiles, multiple tracks | P2.2, P2.3, P2.4 |
| Multilingual terms/facets + vocabulary/kanji/grammar | P1.1–P1.4 |
| Learning reveal, MCQ, panel free-text, cloze | P3.2, P3.6, P3.7, P5.3, P5.4 |
| Introduction, learning/relearning, SRS and verified gate | P3.2–P3.5 |
| Prerequisites, known/suspend/bury, annotations, calibration | P3.5, P3.10, P3.11 |
| Leech, confusion, undo and rebuild | P3.11, P3.12 |
| Scheduler + multi-track/target + actionable notifications | P4.1–P4.7 |
| Basic stats + metacognitive calibration | P3.13, P5.7 |
| SQLite state/content generations + migrations | P0.3, P1.6, P2.1, P6.1 |
| Backup lifecycle + Repairs | P6.2, P6.3 |
| HA services/events | P4.8, P4.9 |
| Pack/dataset provenance/licensing/signatures/update/rollback | P1.2, P1.5, P1.7–P1.10 |
| FR + EN UI | P5.8 |
| Secure export/import | P6.4 |
| Core documentation | P6.9 |
| CI/tests | P6.8 |
| Exact end-to-end DoD scenarios | P6.11 |

## 5. Explicit 1.0 non-blockers

These are intentionally tracked but must not expand the 1.0 critical path:

- §3.4 / §55 / §56 exam mode → P7.1.
- Advanced/optional HA sensors and richer stats → P7.2; P6.5 only freezes the privacy/interface contract.
- Image/audio renderers → P7.3; P1.11 provides the V1 schema compatibility.
- Live Updates/Activities and other research → P7.4.
- §131 remains outside V1.
- §132 is a candidate backlog, not a promise.

## 6. Coverage sanity check

At generation time this matrix covers **all numbered headings/subheadings present in SPEC_V1 v0.6** and expands all 32 explicit §133 invariants. When the spec changes, coverage must be re-audited rather than assuming section-number stability.
