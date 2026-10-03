# LockLearn beta.5 — Field polish v0.4

Status: **implementation-ready**

This document is an additive correction to `LOCKLEARN_UX_NO_DEAD_END_V0_3_WIREFRAMES.md`. It captures defects and UX gaps reproduced during real HA beta.5 use after the v0.3 field qualification. Where this document conflicts with v0.3 on the points below, v0.4 wins.

## Goals

- Remove the remaining dead or misleading actions found in real use.
- Make Learn/Quiz language explain what will happen next without exposing internal identifiers.
- Make quick calibration actually determine the immediate follow-up learning set.
- Keep session recovery/replay-safe behavior correct after resume and refresh.
- Reduce visual layout shift and unfinished-looking surfaces without redesigning the whole panel.

## Non-goals

- No free-text/QCM answering inside Learn in beta.5: Learn keeps reveal + self-evaluation; verified typed/choice retrieval remains Quiz/Calibration.
- No change to the SRS evidence model: self-assessment is not verified retrieval.
- No weakening of prerequisites, sibling/confusable spacing, burial/suspension, CAS, or reminder fail-closed semantics outside the explicit calibration/follow-up rules below.

---

## F1 — Learn retrieval affordance

### Problem

A Learn retrieval screen shows a prompt and `Révéler` / `Je ne sais pas`, but the UI does not explain that the answer is expected mentally before reveal. Users can reasonably think an answer field is missing.

### Requirement

On non-introduction Learn questions, add a short instruction above the actions:

> **Répondez mentalement, puis révélez la réponse pour vous évaluer.**

After reveal, keep `Je savais` and `À revoir` as self-evaluation actions.

### Acceptance

- No text input or MCQ is added to Learn.
- The instruction is visible before reveal on desktop/mobile.
- Quiz/Calibration remain the verified answer-entry modes.

---

## F2 — Introduction CTA wording

### Problem

`Continuer` is too vague; `J’ai vu cette carte` describes the past action but still does not say that clicking moves forward.

### Requirement

For a normal introduction with another session step available, the primary CTA is:

> **Passer à la carte suivante**

If there is no literal next card and the action transitions to waiting/completion, use:

> **Continuer la session**

The label must describe the navigation effect, not merely acknowledge that the card was seen.

### Acceptance

- No bare `Continuer` remains on Learn introduction screens.
- Label selection matches the actual next session state.

---

## F3 — Bulk-guard calibration CTA must work from an active Learn session

### Problem

The bulk guard appears after the configured `known_already` thresholds, but `Démarrer une calibration rapide` can be a dead button while a Learn session is active. The generic `Calibration rapide` entry point works.

### Requirement

- The bulk-guard CTA must open the same 20/30/40 calibration setup used by the generic CTA, even while a Learn session exists.
- Starting calibration preserves the current Learn session unchanged so it can be resumed later.
- `Continuer cette session` dismisses the guard and keeps the current Learn question/session.
- The guard remains one-shot per Learn session according to the existing 3-consecutive / 5-total thresholds.

### Acceptance

E2E sequence:

1. Start Learn.
2. Reach the bulk guard.
3. Click `Démarrer une calibration rapide`.
4. The 20/30/40 setup is visible.
5. Start calibration.
6. Return to Learn after calibration and resume the original session at its canonical state.

---

## F4 — Calibration must drive the immediate Learn follow-up

### Reproduced defect

A real calibration can contain failures/IDK (example: `る`), then `Apprendre` starts unrelated early-pack cards such as `あ / い / う / え / お` instead of the cards actually missed in calibration.

This makes the calibration outcome appear ignored.

### Required semantics

A completed calibration partitions sampled cards into:

- `verified_known`: correct verified retrieval;
- `needs_learning`: wrong, IDK, or unrecognized verified retrieval.

Correctly answered calibration cards must not be reintroduced as `new`.

The CTA **Apprendre les cartes restantes** must start a **targeted calibration follow-up Learn session** containing the `needs_learning` cards from that calibration, not a generic Learn selection.

Rules for the targeted follow-up:

1. Include only cards from that calibration whose result is `wrong`, `idk`, or `unrecognized` and which are still learnable.
2. Do not fill spare slots with unrelated `new` cards.
3. Preserve deterministic identity and canonical progress history.
4. Calibration follow-up may bypass ordinary *introduction-order* constraints for these explicitly failed/IDK calibration cards, just as calibration itself is a pre-test; it must not bypass suspension/burial/disabled content/user ownership safety rules.
5. Once a follow-up card is introduced/learned, it leaves the pending follow-up set normally.
6. Cards never sampled by calibration remain ordinary `new` cards and are eligible only through normal Learn, not through the calibration follow-up CTA.

### Generic Learn after calibration

While a calibration has unresolved `needs_learning` cards:

- the primary Learn recommendation must be **Apprendre les cartes identifiées par la calibration**;
- the generic quick-calibration CTA is suppressed on that Track so the UI does not immediately ask to calibrate again;
- normal unrelated `new` cards may still be started explicitly after the calibration follow-up is cleared or from a separate general Learn action.

### Acceptance

Given a calibration where `る` is wrong and `あ/い/う/え/お` are correct or unrelated:

- `Apprendre les cartes restantes` includes `る`;
- it does not include unrelated `あ/い/う/え/お` merely because they are earlier in pack order;
- a correct calibration card is not shown again as `state=new`;
- no immediate generic `Calibration rapide` CTA is shown while unresolved calibration follow-up exists.

Add backend + E2E regression tests using exact card-key sets, not only counts.

---

## F5 — Session ordering should not always expose pack order

### Problem

Equivalent hiragana can appear in the same order every session (`あ, い, う, え, お...`), which makes sessions predictable and weakens retrieval quality.

### Requirement

- Preserve prerequisite/dependency ordering and all hard eligibility constraints.
- Within cards that are equally eligible at the same priority, vary order per session using a deterministic session seed.
- The same persisted session must resume in exactly the same order.
- A new session should not systematically reuse the same pack-order prefix.
- Calibration sampling should likewise avoid always presenting the same visible prefix when a larger eligible pool exists.

### Implementation constraint

Use deterministic pseudo-randomization/rotation derived from persisted session identity or an explicitly persisted seed. Do not use process-global nondeterministic randomness that breaks replay/tests.

### Acceptance

- Two newly created sessions over the same sufficiently large equivalent pool can have different order.
- Reload/resume of one session preserves order exactly.
- Prerequisite ordering remains intact.

---

## F6 — Translate blocker codes; never expose internal variable names

### Problem

`Qu’attend LockLearn ?` currently exposes values such as `scheduled_step` and `known_already_verification`.

### Requirement

No raw blocker code is rendered to the user. Map every known blocker to localized title + one-line explanation.

Minimum French copy:

- `scheduled_step` → **Prochain rappel planifié** — `{count} carte(s) attendent leur prochaine étape d’apprentissage.`
- `known_already_verification` → **Cartes déjà connues à vérifier** — `{count} carte(s) marquées comme déjà connues seront vérifiées plus tard.`
- `suspended` → **Cartes suspendues** — `{count} carte(s) sont suspendues.`
- `buried` → **Cartes mises de côté temporairement** — `{count} carte(s) sont temporairement mises de côté.`
- `prerequisite` → **Prérequis à apprendre d’abord** — `{count} carte(s) attendent un prérequis.`
- quota/new-limit blocker → **Limite de nouvelles cartes atteinte** — explain local reset time when reliable.
- sibling/confusable spacing blocker → **Cartes similaires espacées** — explain that LockLearn separates similar cards to reduce confusion.
- unknown future blocker code → localized generic fallback **Indisponible pour le moment**, never the raw identifier.

### Acceptance

Raw blocker identifiers do not appear in rendered Learn/Quiz HTML.

---

## F7 — Finish the “Cartes concernées” sheet

### Problem

The current sheet looks like a debug/admin list: raw states/timestamps, weak hierarchy, and `Apprendre finalement` is ambiguous.

### Requirement

- Contextual title, e.g. `Cartes déjà connues à vérifier`, `Cartes suspendues`, `Cartes en attente d’un prérequis`.
- Intro sentence explains why the cards are listed.
- Display user-facing state labels, never `known_already`, `active`, etc. as raw codes.
- Format dates in Profile locale/timezone.
- Use a bounded responsive sheet/modal with sensible max-width, spacing, scroll region, and accessible close button.
- For `known_pending`, rename action:

> **Remettre à apprendre**

  Help text: `Annule le marquage « déjà connue » et remet cette carte dans l’apprentissage normal.`

- For suspended/buried, action remains **Réactiver** with contextual help.
- Cards with no action show an explanation rather than an empty action area.

### Acceptance

No raw user-state/blocker code is visible in the sheet. `Remettre à apprendre` restores canonical `active / new / box=0` without verified retrieval.

---

## F8 — Stable Quiz question geometry

### Problem

The Quiz question area changes height significantly between question formats, causing unpleasant layout shift.

### Requirement

- Define a common minimum visual height for the question/prompt area and answer/feedback area.
- Center short content vertically where appropriate.
- Long content may expand; never clip meaningful content.
- Action buttons should stay in a stable vertical region for common MCQ/cloze/free-text cases.
- Mobile gets a smaller minimum height but the same stability principle.

### Acceptance

Switching among normal MCQ, cloze and short free-text questions does not move the primary answer controls by a large amount solely because prompt content is short.

---

## F9 — Availability copy must describe actionable state, not engine selectability

### Problem

`3 cartes disponibles maintenant` is ambiguous when an unfinished session exists. “Maintenant” sounds immediately actionable although the UI requires resuming the current session first.

### Requirement

Copy depends on session state:

- No active Learn session: **`{count} carte(s) prêtes à apprendre`**.
- Active/resumable Learn session: **`{count} autre(s) carte(s) prêtes après la session en cours`**.
- Zero ready + reliable future time: keep explicit future-time wording.
- Zero ready + no reliable time: explain blockers; never imply a known time.

Do the equivalent for Quiz where relevant.

### Acceptance

The word `maintenant` is not used when the user cannot immediately start those cards because an unfinished session owns the flow.

---

## F10 — Resume/CAS correctness and neutral stale-state copy

### Reproduced defect

After resuming a Learn session, `Je connais déjà cette carte` can appear to do nothing, and the next action can show `La session a changé sur un autre client...` even without another client.

### Requirement

- Resume must load the latest canonical session version before enabling mutations.
- Every successful mutation must replace the local session with the canonical session returned by the backend before availability refreshes can affect rendering.
- Availability/focus refreshes must never overwrite the active session object/version.
- `known_already`, introduce/continue, reveal/self-evaluation, suspend and report actions must all use the current canonical `expected_version`.
- On stale CAS, refetch canonical session and reconcile exactly once; do not silently drop the user action.
- Do not claim “another client” unless the product can actually prove it.

Replace generic stale copy with:

> **La session a été actualisée. Le dernier état enregistré a été rechargé.**

If the original action was not applied, keep the relevant action available so the user can retry safely.

### Mandatory regression sequence

1. Start Learn and advance several cards.
2. Leave the view/reload.
3. Resume session.
4. On a `state=new` introduction, choose `Je connais déjà cette carte`.
5. Confirm mutation is applied and session advances canonically.
6. Continue next step.
7. No false “another client” message and no lost action.

Test the same sequence with a focus/availability refresh occurring between resume and mutation.

---

## F11 — Do not immediately re-suggest calibration after calibration

### Problem

After completing calibration and returning to Learn, the generic `Calibration rapide` CTA can immediately reappear, which feels like a loop and obscures the intended follow-up.

### Requirement

- If the most recent calibration for the Track has unresolved `needs_learning` cards, suppress the generic quick-calibration CTA and surface the targeted follow-up from F4.
- After all follow-up cards are resolved, calibration may be offered again only if there remains a meaningful pool of uncalibrated `new` cards.
- Completing one calibration must not itself create a repeated calibration recommendation loop.

---

## F12 — Quiz availability layout polish

### Problem

The Quiz availability card is visually cramped: metrics, explanation and buttons have insufficient separation.

### Requirement

Structure as three spaced groups:

1. status/title + concise explanation;
2. metrics / next reliable time;
3. actions.

Use the existing spacing tokens / at least one normal vertical gap between groups. Buttons wrap with consistent gaps on narrow widths.

No behavioral change to reminder semantics.

---

## Priority / release blocking

### P0 functional blockers

1. F3 bulk-guard calibration dead CTA.
2. F4 calibration follow-up selects wrong/unrelated cards.
3. F10 resumed session mutation/CAS failure.

### P1 UX correctness

4. F6 blocker translations.
5. F7 concerned-cards sheet polish/copy.
6. F9 availability wording.
7. F11 repeated calibration recommendation.
8. F1 Learn mental-answer instruction.
9. F2 introduction CTA wording.

### P2 polish

10. F5 per-session ordering variation.
11. F8 Quiz geometry stability.
12. F12 Quiz availability spacing.

---

## Required qualification before beta.5 is considered field-complete

Automated:

- backend unit tests for calibration follow-up exact card set;
- backend/session tests for persisted deterministic ordering;
- frontend tests for CTA copy and blocker mapping;
- E2E bulk-guard → calibration setup while Learn is active;
- E2E resume → `known_already` → next action with injected refresh/stale state;
- E2E calibration result → targeted Learn exact failed/IDK cards;
- visual/layout assertions sufficient to catch major Quiz vertical shift and cramped CTA regression;
- existing Ruff, mypy, pytest, datasets, frontend lint/typecheck/tests/build, E2E and HA matrix remain green.

Field HA:

- reproduce and close all three P0 bugs on the same HA test instance;
- verify one calibration with at least one correct, one wrong and one IDK card, then confirm the follow-up Learn card keys match the wrong/IDK set;
- verify resume after reload and `known_already` works without false stale-client messaging;
- verify bulk-guard calibration CTA opens setup from an active Learn session;
- spot-check blocker labels, concerned-cards copy, Quiz stable geometry and availability spacing.

The deployed SHA, CI-green SHA and actually served HA tree/bundle must remain identical.