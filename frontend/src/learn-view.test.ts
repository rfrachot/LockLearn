import { describe, expect, it } from "vitest";

import {
  canAnswerProfile,
  isIntroductionQuestion,
  KNOWN_ALREADY_STREAK_GUARD,
  KNOWN_ALREADY_TOTAL_GUARD,
  knownAlreadyBulkGuardTriggerIndex,
  questionAvailableAtMs,
  shouldShowKnownAlreadyBulkGuard,
} from "./learn-model";
import type { SessionQuestion, SessionState, VisibleProfile } from "./protocol";

function profile(role: VisibleProfile["role"]): VisibleProfile {
  return {
    profile_id: "p1",
    name: "Profile",
    preset: "standard",
    timezone: "Europe/Paris",
    status: "active",
    role,
  };
}

describe("Learn UI semantics", () => {
  it("keeps viewer profiles read-only in the UI boundary", () => {
    expect(canAnswerProfile(profile("owner"))).toBe(true);
    expect(canAnswerProfile(profile("editor"))).toBe(true);
    expect(canAnswerProfile(profile("viewer"))).toBe(false);
  });

  it("keeps a scheduled first retrieval hidden until its backend due instant", () => {
    const question = {
      position: 1,
      question_id: "q1:learning-step-1",
      card_key: "c1",
      learning_item_id: "i1",
      prompt_facet_id: "p1",
      answer_facet_id: "a1",
      status: "presented",
      payload: {
        available_at_utc: "2026-09-26T12:01:00+00:00",
        selection: { progress_state: "learning" },
      },
    } satisfies SessionQuestion;

    expect(questionAvailableAtMs(question)).toBe(
      Date.parse("2026-09-26T12:01:00+00:00"),
    );
    expect(isIntroductionQuestion(question)).toBe(false);
  });

  it("uses backend progress state to select introduction rendering", () => {
    const question = {
      position: 0,
      question_id: "q1",
      card_key: "c1",
      learning_item_id: "i1",
      prompt_facet_id: "p1",
      answer_facet_id: "a1",
      status: "presented",
      payload: { selection: { progress_state: "new" } },
    } satisfies SessionQuestion;
    expect(isIntroductionQuestion(question)).toBe(true);
    expect(
      isIntroductionQuestion({
        ...question,
        payload: { selection: { progress_state: "learning" } },
      }),
    ).toBe(false);
  });
});


function sessionAnswer(
  action: string,
  id: number,
): SessionState["answers"][number] {
  return {
    id,
    question_id: `q${id}`,
    answer: { kind: "learning", action },
    resulting_version: id + 1,
    created_at_utc: "2026-10-02T06:00:00+00:00",
  };
}

describe("known-already bulk guard", () => {
  it("uses the documented streak and total thresholds", () => {
    expect(KNOWN_ALREADY_STREAK_GUARD).toBe(3);
    expect(KNOWN_ALREADY_TOTAL_GUARD).toBe(5);
  });

  it("triggers on three consecutive known-already answers", () => {
    const answers = [
      sessionAnswer("introduce", 1),
      sessionAnswer("known_already", 2),
      sessionAnswer("known_already", 3),
      sessionAnswer("known_already", 4),
    ];
    expect(knownAlreadyBulkGuardTriggerIndex(answers)).toBe(3);
    expect(shouldShowKnownAlreadyBulkGuard(answers)).toBe(true);
  });

  it("triggers on five total known-already answers even when interrupted", () => {
    const answers = [
      sessionAnswer("known_already", 1),
      sessionAnswer("introduce", 2),
      sessionAnswer("known_already", 3),
      sessionAnswer("review", 4),
      sessionAnswer("known_already", 5),
      sessionAnswer("known_already", 6),
      sessionAnswer("introduce", 7),
      sessionAnswer("known_already", 8),
    ];
    expect(knownAlreadyBulkGuardTriggerIndex(answers)).toBe(7);
    expect(shouldShowKnownAlreadyBulkGuard(answers)).toBe(true);
  });

  it("does not retrigger after the threshold-crossing answer", () => {
    const answers = [
      sessionAnswer("known_already", 1),
      sessionAnswer("known_already", 2),
      sessionAnswer("known_already", 3),
      sessionAnswer("introduce", 4),
    ];
    expect(knownAlreadyBulkGuardTriggerIndex(answers)).toBe(2);
    expect(shouldShowKnownAlreadyBulkGuard(answers)).toBe(false);
  });
});
