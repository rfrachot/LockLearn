import type { SessionQuestion, VisibleProfile } from "./protocol";

export function isIntroductionQuestion(
  question: SessionQuestion | null,
): boolean {
  return question?.payload.selection?.progress_state === "new";
}

export function canAnswerProfile(
  profile: VisibleProfile | undefined,
): boolean {
  return profile !== undefined && profile.role !== "viewer";
}
