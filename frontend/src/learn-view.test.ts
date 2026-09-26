import { describe, expect, it } from "vitest";

import {
  canAnswerProfile,
  isIntroductionQuestion,
  questionAvailableAtMs,
} from "./learn-model";
import type { SessionQuestion, VisibleProfile } from "./protocol";

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
