import type { SessionQuestion, SessionState, VisibleProfile } from "./protocol";

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


export const KNOWN_ALREADY_STREAK_GUARD = 3;
export const KNOWN_ALREADY_TOTAL_GUARD = 5;

function isKnownAlreadyAnswer(answer: unknown): boolean {
  if (typeof answer !== "object" || answer === null) return false;
  const payload = answer as Record<string, unknown>;
  return payload.kind === "learning" && payload.action === "known_already";
}

export function knownAlreadyBulkGuardTriggerIndex(
  answers: SessionState["answers"],
): number | null {
  let totalKnownAlready = 0;
  let consecutiveKnownAlready = 0;

  for (const [index, entry] of answers.entries()) {
    if (isKnownAlreadyAnswer(entry.answer)) {
      totalKnownAlready += 1;
      consecutiveKnownAlready += 1;
      if (
        consecutiveKnownAlready >= KNOWN_ALREADY_STREAK_GUARD ||
        totalKnownAlready >= KNOWN_ALREADY_TOTAL_GUARD
      ) {
        return index;
      }
      continue;
    }
    consecutiveKnownAlready = 0;
  }
  return null;
}

export function shouldShowKnownAlreadyBulkGuard(
  answers: SessionState["answers"],
): boolean {
  if (answers.length === 0) return false;
  return knownAlreadyBulkGuardTriggerIndex(answers) === answers.length - 1;
}
