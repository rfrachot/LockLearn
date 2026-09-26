import type { SessionQuestion, VisibleProfile } from "./protocol";

export function isIntroductionQuestion(
  question: SessionQuestion | null | undefined,
): boolean {
  return question?.payload.selection?.progress_state === "new";
}

export function questionAvailableAtMs(
  question: SessionQuestion | null | undefined,
): number | null {
  const raw = question?.payload.available_at_utc;
  if (typeof raw !== "string") return null;
  const parsed = Date.parse(raw);
  return Number.isNaN(parsed) ? null : parsed;
}

export function canAnswerProfile(profile: VisibleProfile | undefined): boolean {
  return profile !== undefined && profile.role !== "viewer";
}
