# AGENT_HANDOFF.md

## Current state

P5.3 remains **COMPLETE / PASS** on `feat/p5-frontend`.

P5.4 is **IMPLEMENTED / REAL-HA QUALIFICATION PENDING**. P5.5 has not started.

The P5.4 implementation adds the Quiz route and backend-owned orchestration for V1 panel formats: MCQ (4–6 supported by the backend, UI default 4), free_text, and grammar cloze-MCQ. Quiz answers use the dedicated `locklearn/quiz/answer` CAS path; generic `session/answer` is rejected for quiz sessions.

Important contracts already qualified automatically:
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

HACS metadata validation remains red only for repository description/topics/brand assets; that is release-packaging debt outside P5.4.

Remaining P5.4 gate: real Home Assistant qualification of the three V1 quiz formats on desktop/mobile/keyboard. Exercise unrecognized/report and contrastive-feedback paths only when suitable real/temporary fixture content is available; absence of such content must be reported as a fixture limitation rather than a runtime failure.

Do not start P5.5 until P5.4 real-HA qualification is recorded.
