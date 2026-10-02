import type {
  DashboardSession,
  QuizFeedback,
  QuizQuestionPayload,
  SessionQuestion,
  VisibleProfile,
} from "./protocol";

export function isResumableQuizSession(
  last: DashboardSession | null | undefined,
): last is DashboardSession {
  return last !== null && last !== undefined &&
    ["quiz", "calibration"].includes(last.session_type) &&
    ["active", "paused"].includes(last.status);
}

export function canQuizProfile(profile: VisibleProfile | undefined): boolean {
  return profile !== undefined && profile.role !== "viewer";
}

export function quizPayload(
  question: SessionQuestion | null | undefined,
): QuizQuestionPayload | undefined {
  return question?.payload.quiz;
}

export function isChoiceQuiz(payload: QuizQuestionPayload | undefined): boolean {
  return payload?.format === "mcq" || payload?.format === "cloze_mcq";
}

export function canReportFreeText(
  feedback: QuizFeedback | undefined,
): boolean {
  return (
    feedback?.format === "free_text" &&
    feedback.result === "wrong" &&
    feedback.reportable &&
    typeof feedback.submitted_text === "string" &&
    feedback.grading_policy_kind !== undefined &&
    feedback.grading_policy_version !== undefined &&
    feedback.normalization_version !== undefined
  );
}
