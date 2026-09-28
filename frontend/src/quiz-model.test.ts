import { describe, expect, it } from "vitest";

import {
  canQuizProfile,
  canReportFreeText,
  isChoiceQuiz,
  quizPayload,
} from "./quiz-model";
import type {
  QuizFeedback,
  QuizQuestionPayload,
  SessionQuestion,
  VisibleProfile,
} from "./protocol";

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

const choice: QuizQuestionPayload = {
  format: "mcq",
  prompt_text: "Prompt",
  context_hint: null,
  options: [
    { answer_id: "a1", text: "One" },
    { answer_id: "a2", text: "Two" },
    { answer_id: "a3", text: "Three" },
    { answer_id: "a4", text: "Four" },
  ],
  idk_available: true,
  reportable: true,
  hint_blocks: [],
  content_type: "vocabulary",
};

describe("Quiz UI semantics", () => {
  it("keeps viewer profiles read-only", () => {
    expect(canQuizProfile(profile("owner"))).toBe(true);
    expect(canQuizProfile(profile("editor"))).toBe(true);
    expect(canQuizProfile(profile("viewer"))).toBe(false);
  });

  it("recognizes choice formats without guessing from content type", () => {
    expect(isChoiceQuiz(choice)).toBe(true);
    expect(isChoiceQuiz({ ...choice, format: "cloze_mcq" })).toBe(true);
    expect(isChoiceQuiz({ ...choice, format: "free_text" })).toBe(false);
  });

  it("uses only the backend quiz payload", () => {
    const question = {
      position: 0,
      question_id: "q1",
      card_key: "c1",
      learning_item_id: "i1",
      prompt_facet_id: "p1",
      answer_facet_id: "a1",
      status: "presented",
      payload: { quiz: choice },
    } satisfies SessionQuestion;
    expect(quizPayload(question)).toEqual(choice);
  });

  it("offers free-text recovery only with complete report metadata", () => {
    const feedback: QuizFeedback = {
      format: "free_text",
      result: "wrong",
      immediate: true,
      reveal_correct_answer: true,
      correct_answer: "answer",
      contrastive_feedback: null,
      submitted_text: "answr",
      normalized_submission: null,
      reportable: true,
      grading_policy_kind: "exact",
      grading_policy_version: 1,
      normalization_version: 1,
      hint_used: false,
    };
    expect(canReportFreeText(feedback)).toBe(true);
    expect(canReportFreeText({ ...feedback, result: "correct" })).toBe(false);
    expect(canReportFreeText({ ...feedback, normalization_version: undefined })).toBe(false);
  });
});
