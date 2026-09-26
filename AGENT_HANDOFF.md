# AGENT_HANDOFF.md

## Current state

P5.2 remains **COMPLETE / PASS** on `feat/p5-frontend`.

P5.3 is **IMPLEMENTED / REAL-HA QUALIFICATION PENDING**. The authoritative code gate passed at `48a911bc6d04d41dd6f0007099941410e417156f`; this documentation commit is its descendant.

P5.3 now provides the Learn UI and backend contract for direction-aware CardDefinition presentation, explicit introduction, reveal / I-don't-know / hint / known / review interactions, known-already/suspend, question reporting and personal mnemonic creation. The frontend remains non-authoritative: permissions, CardDefinition identity, presentation mapping, progress mutation and learning-signal semantics are enforced by the backend.

A qualification review found and fixed one important normative gap before closing the phase: introduction previously set `next_due_at_utc` but simply advanced the session, so a one-card session could finish without the mandatory first retrieval. The fix atomically appends a learning-step retrieval to the same persistent session when introduction commits. Its `available_at_utc == progress.next_due_at_utc`; the backend rejects an answer before that instant, while the frontend renders only a waiting surface and reveals no prompt/answer/hint until due. No state.db migration was needed.

Final automated gate on 2026-09-26:
- Ruff format PASS — 253 files.
- Ruff lint PASS.
- mypy PASS — 146 source files.
- resource registries PASS.
- pytest PASS — 382 tests.
- HA 2025.2.5 compatibility PASS — 289 backend tests.
- HA 2026.9.3 compatibility PASS — 289 backend tests.
- TypeScript PASS.
- Vitest PASS — 10 files / 26 tests.
- Vite PASS — 27 modules, 71.19 kB / 17.52 kB gzip.
- committed frontend bundle reproducibility PASS.
- hassfest PASS.
- HACS metadata validation still fails only because the repository has no description, valid topics or brand asset. That is release-packaging metadata debt, not a P5.3 functional regression.

The remaining P5.3 exit gate is manual qualification on the real Home Assistant instance: complete a Learn session by keyboard and on mobile, including introduction -> delayed first retrieval -> reveal / IDK / hint / known paths, and verify accessibility/focus/readability. P5.4 must not start until that gate is recorded.

P5.2 real-instance baseline remains valid: HA 2026.7.4, schema 5, `integrity_check=ok`, zero FK violations, no LockLearn ERROR/CRITICAL, and `state.db` was not deleted, recreated, downgraded or manually modified.

The previously exposed HA development token still requires rotation. Renaud has explicitly deferred that security debt; do not remove it from documentation.
