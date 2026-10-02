# LockLearn UX no-dead-end v0.3 — implementation wireframes

**Status:** validated implementation baseline for beta.5  
**Date:** 2026-09-30  
**Normative source:** `SPEC_V1.md` §0.1 + validated `LOCKLEARN_SPEC_UX_NO_DEAD_END_v0.3`

These are behavior-first wireframes. They deliberately avoid visual-polish decisions that belong to implementation CSS. Every waiting surface keeps one dominant next action and never relies on a Home escape hatch alone.

## M1 — Learn, cards ready

- Header: Track selector + concise state sentence.
- Facts: at most two headline numbers: ready now / session capacity.
- Primary CTA: **Commencer à apprendre**.
- Secondary: **Calibration rapide** when unstarted cards exist and prior knowledge is plausible.
- Expandable **Pourquoi ?** contains blockers and detailed counts.

## M2 — Learn, no card ready but timed return exists

- Title: **Rien à apprendre maintenant**.
- Sentence: next effective opportunity in Profile local time.
- Primary CTA: **Me prévenir quand ce sera prêt** when a compatible target exists; otherwise **Configurer les notifications**.
- Secondary CTA: deterministic cross-track alternative when one exists.
- Automatic refresh is announced; no polling.

## M3 — Learn, only prerequisite/suspended blockers

- No invented next time.
- Primary CTA targets the actual unblock action: **Voir les cartes concernées** / **Réactiver des cartes**.
- Secondary CTA is the best cross-track alternative.

## M4 — Learn introduction

- Full encoding material.
- Primary CTA: **J’ai lu / Continuer**.
- Secondary action: **Je la connais déjà** only while `state=new` and the current phase is introduction.
- The action creates calibration-pending `known_already`; it never counts as verified retrieval.

## M5 — Known-already confirmation

- Fixed snackbar, no layout shift, visible for 8 seconds.
- Copy: **Marquée comme déjà connue. Vérification plus tard.**
- Action: **Annuler**; keyboard reachable and screen-reader announced politely.
- Bulk-guard sheet appears at most once per session when either threshold is first crossed: **3 consecutive** `known_already` actions, or **5 total** `known_already` actions in the same session.
- Rationale: 3 consecutive self-known cards is an early strong signal of prior knowledge; 5 total catches a broader mismatch without interrupting occasional isolated known cards.
- The sheet recommends Quick calibration but always offers **Continue this session**; it does not reinterpret prior self-assessments as verified retrieval.

## M6 — Learn waiting inside an active session

- Preserve session identity and current progress.
- Show exact effective due in Profile timezone.
- If safe early learning is forceable, primary CTA **Continuer maintenant** with the actual forceable count capped by session length.
- Otherwise reminder/cross-track CTA; never advance the question while unavailable.

## M7 — Learn completion

- Explicit `completed / requested` count.
- Next action derived from fresh availability: new Learn session, Quiz, reminder, cross-track alternative, or Home only after an actionable route is already present.

## M8 — Quick calibration start

- Explanation: “20 questions pour estimer ce que tu connais déjà; les réponses ne sont jamais montrées avant ton choix.”
- Default 20; selector 20–40.
- Primary CTA **Démarrer la calibration**.

## M9 — Quick calibration question

- Reuse Quiz retrieval renderers; no introduction/reveal before the answer.
- `Je ne sais pas` always available.
- Correct verified answer enters SRS as verified evidence; wrong/IDK stays learnable.

## M10 — Quick calibration completion

- Show known/needs-learning counts, not a mastery percentage.
- Primary CTA **Apprendre les cartes restantes**.
- Secondary CTA **Quiz** when verified cards are already eligible.

## M11 — Connection/answer uncertainty

- While mutation is in flight: **Envoi…**; mutating buttons disabled, no visual advancement.
- At 8 s without acknowledgement: **Réponse non confirmée** with **Vérifier / Réessayer**.
- Verify first refetches canonical session state. Already-consumed answer becomes **Réponse appliquée**; still-current question may be resubmitted with the same client mutation id; another winner becomes an explicit conflict.

## M12 — Loading failure

- Initial load timeout at 10 s: **Réessayer** + Home.
- After two failed retries: add **Copier le diagnostic** while keeping Retry.
- A stale/disconnected connection indicator is visible without taking over the whole screen.

## D1 — Desktop waiting detail

- Main card follows the same max-one-title/one-sentence/two-numbers rule.
- Side/details sheet lists blockers grouped by code and “Cartes concernées” filters: `known_pending`, `suspended`, `buried`, `prerequisite_support`, `current_waiting_context`.
- Per-card actions are contextual: **Apprendre finalement** for pending-known; **Réactiver** for suspended/buried.

## D2 — Desktop settings / dirty scope

- Each saveable section owns its own dirty state.
- Primary save is sticky only for that scope on narrow/mobile layouts.
- Navigation/profile/track changes with dirty data trigger Save / Discard / Stay.
- Validation errors focus the first invalid field and preserve edits.

## Deterministic cross-track fallback

When the current mode is unavailable, candidates are ordered:

1. same Track, other mode;
2. another Track, same mode;
3. another Track, other mode;
4. Track priority ascending, then available count descending, then `track_id`.

The UI never claims an alternative before the backend reports it as effectively available.
