# AGENT_HANDOFF.md

## Current state

P5.3 is **COMPLETE / PASS** on `feat/p5-frontend`. P5.4 has not started.

The final P5.3 code/bundle gate is rooted at `28bc6f58ae1a7c0b16524b1fb94db30307ad1845`; the documentation-only commits that follow do not change runtime code.

P5.3 provides the Learn UI and backend contract for direction-aware CardDefinition presentation, explicit introduction, reveal / I-don't-know / hint / known / review interactions, known-already/suspend, question reporting and personal mnemonic creation. The frontend remains non-authoritative: permissions, CardDefinition identity, presentation mapping, progress mutation and learning-signal semantics are enforced by the backend.

Two qualification defects were found and corrected before closure:
1. Introduction originally set `next_due_at_utc` but could end a one-card session without the mandatory first retrieval. The fix atomically appends a learning-step retrieval to the same persistent session. Its `available_at_utc == progress.next_due_at_utc`; the backend rejects answers before that instant and the frontend reveals no prompt/answer/hint until due.
2. At a real 390×844 viewport, the essential “Continuer” action overflowed horizontally. Responsive containment was corrected and the real-instance requalification passed at 390×844.

Real Home Assistant 2026.7.4 qualification passed introduction, delayed first retrieval in the same session, answer hiding before due, reveal/known, IDK, keyboard operation, mobile 390×844 and clean LockLearn logs.

The active pack contained no card with `hint_blocks` or `mnemonic_blocks` among the 100 cards inspected, so real-instance hint interaction could not be exercised. Automated backend/frontend tests cover hint visibility and persistence of `hint_used=true`; this is recorded as a content-fixture limitation, not a P5.3 runtime failure.

Final post-fix CI: backend-quality PASS; frontend PASS including generated-bundle reproducibility; HA 2025.2.5 PASS; HA 2026.9.3 PASS; hassfest PASS. HACS metadata validation still fails only for missing repository description, valid topics and brand asset, which remains release-packaging debt outside P5.3.

P5.2 remains COMPLETE / PASS. The previously exposed HA development token still requires rotation; Renaud has explicitly deferred that security debt.

Next concrete action: begin P5.4 only when explicitly requested.
