# AGENT_HANDOFF.md

## Current state

P5.3 remains **COMPLETE / PASS** on `feat/p5-frontend`.

P5.4 is **COMPLETE / PASS**. P5.5 has not started.

P5.4 adds the Quiz route and backend-owned orchestration for V1 panel formats: MCQ (4–6 supported by the backend, UI default 4), free_text, and grammar cloze-MCQ. Quiz answers use the dedicated `locklearn/quiz/answer` CAS path; generic `session/answer` is rejected for quiz sessions.

Important contracts qualified automatically:
- MCQ/cloze session payloads do not expose `correct_index` or `correct_answer`.
- Choice answers grade and persist atomically.
- Explicit IDK is supported for choice and free-text.
- Free-text provisional grading does not advance the session and does not reveal the correct answer on a wrong provisional result.
- A disputed free-text answer can be reported as “should be accepted”; it is recorded as `unrecognized` and does not create an automatic SRS failure.
- Cloze-MCQ requires grammar content plus explicit maskable source content; it does not synthesize a blank from unmarked prose.
- Known-confusable distractors can emit contrastive corrective feedback.
- Feedback is textual and not color-only.
- Hint usage, when content exposes a hint, is included in the quiz signal.

Authoritative automated evidence on 2026-09-26:
- pre-bundle code HEAD `3f7047697d8dc56565cf717106d52c6e3823cfab`;
- Ruff format PASS — 256 files;
- Ruff lint PASS;
- mypy PASS — 148 source files;
- registries PASS;
- pytest PASS — 389 tests;
- HA 2025.2.5 PASS — 296 backend tests;
- HA 2026.9.3 PASS — 296 backend tests;
- TypeScript PASS;
- Vitest PASS — 11 files / 31 tests;
- Vite PASS — 29 modules, 97.71 kB / 20.94 kB gzip;
- generated frontend bundle materialized;
- normal frontend reproducibility gate PASS on `948bb03e5a974ec5b68fb99ed076990bc9dcea8a`.

Real HA 2026.7.4 qualification used a temporary QA Profile/Track created only through LockLearn public APIs and cleaned afterward. MCQ PASS, free_text PASS, unrecognized/report PASS, keyboard PASS, LockLearn logs PASS. The active pack had no grammar card with explicit maskable content and no confusable group, so cloze-MCQ and contrastive-feedback were fixture unavailable rather than product failures.

Firefox WebDriver enforced a 500 px CSS minimum, so the exact 390×844 viewport could not be certified. No mobile overflow or inaccessible action was observed in the available harness. This limitation is recorded explicitly as a harness limitation and does not keep P5.4 open.

HACS metadata validation remains red only for repository description/topics/brand assets; that is release-packaging debt outside P5.4.

P5.5 must not start until explicitly requested.
