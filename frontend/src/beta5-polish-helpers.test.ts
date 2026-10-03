import { describe, expect, it } from "vitest";

import {
  scheduledLearningReminderAt,
  scheduledLearningWaitingCount,
} from "./learn-model";
import type { SessionAvailability } from "./protocol";

function availability(overrides: Partial<SessionAvailability> = {}): SessionAvailability {
  return {
    profile_id: "p1",
    track_id: "t1",
    session_type: "learn",
    available_now: 8,
    selected_cards: 42,
    introduced_cards: 12,
    new_cards: 30,
    due_now_total: 8,
    known_already_cards: 0,
    known_already_pending_verification: 0,
    suspended_cards: 0,
    buried_cards: 0,
    temporarily_blocked_cards: 0,
    prerequisite_blocked_cards: 0,
    session_capacity: 8,
    remaining_new_quota: 8,
    forceable_early: 0,
    forceable_new: 0,
    next_due_at_utc: null,
    next_available_at_utc: null,
    next_available_reason: null,
    blockers: [],
    ...overrides,
  };
}

describe("Beta.5 Learn availability semantics", () => {
  it("finds a scheduled learning reminder even when a new session is available", () => {
    const state = availability({
      available_now: 8,
      blockers: [
        {
          code: "scheduled_step",
          count: 2,
          until_utc: "2026-10-04T10:10:00+00:00",
          forceable: true,
        },
      ],
    });

    expect(scheduledLearningReminderAt(state)).toBe("2026-10-04T10:10:00+00:00");
    expect(scheduledLearningWaitingCount(state)).toBe(2);
  });

  it("ignores unrelated blockers when deciding whether Learn can be reminded", () => {
    const state = availability({
      blockers: [
        {
          code: "new_quota",
          count: 10,
          until_utc: "2026-10-05T00:00:00+00:00",
          forceable: true,
        },
      ],
    });

    expect(scheduledLearningReminderAt(state)).toBeNull();
    expect(scheduledLearningWaitingCount(state)).toBe(0);
  });

  it("uses the earliest reliable scheduled-step deadline", () => {
    const state = availability({
      blockers: [
        {
          code: "scheduled_step",
          count: 1,
          until_utc: "2026-10-04T10:30:00+00:00",
          forceable: true,
        },
        {
          code: "scheduled_step",
          count: 3,
          until_utc: "2026-10-04T10:10:00+00:00",
          forceable: false,
        },
      ],
    });

    expect(scheduledLearningReminderAt(state)).toBe("2026-10-04T10:10:00+00:00");
    expect(scheduledLearningWaitingCount(state)).toBe(4);
  });
});
