import { describe, expect, it } from "vitest";

import { findReadyAlternative } from "./next-action";
import type { DashboardResponse, HomeAssistantLike } from "./protocol";

const dashboard: DashboardResponse = {
  profile: { profile_id: "p1", name: "Learner", preset: "standard", timezone: "Europe/Paris" },
  generated_at_utc: "2026-09-30T20:00:00+00:00",
  tracks: [
    {
      track_id: "current",
      name: "Current",
      priority: 5,
      source_language: "ja",
      target_language: "fr",
      due_today: 0,
      recent_verified_retention: null,
      recent_verified_accuracy: { correct: 0, total: 0, accuracy: null },
      states: {},
      last_session: null,
      next_notification: null,
    },
    {
      track_id: "b",
      name: "B",
      priority: 2,
      source_language: "en",
      target_language: "fr",
      due_today: 0,
      recent_verified_retention: null,
      recent_verified_accuracy: { correct: 0, total: 0, accuracy: null },
      states: {},
      last_session: null,
      next_notification: null,
    },
    {
      track_id: "a",
      name: "A",
      priority: 2,
      source_language: "es",
      target_language: "fr",
      due_today: 0,
      recent_verified_retention: null,
      recent_verified_accuracy: { correct: 0, total: 0, accuracy: null },
      states: {},
      last_session: null,
      next_notification: null,
    },
  ],
};

function hass(counts: Record<string, number>): HomeAssistantLike {
  return {
    async callWS<T>(message: Record<string, unknown>): Promise<T> {
      const key = String(message.track_id) + ":" + String(message.session_type);
      return { available_now: counts[key] ?? 0 } as T;
    },
  };
}

describe("findReadyAlternative", () => {
  it("prefers the other mode on the same track", async () => {
    const result = await findReadyAlternative(
      hass({ "current:quiz": 1, "a:learn": 20 }),
      dashboard,
      "current",
      "learn",
    );
    expect(result).toMatchObject({ trackId: "current", mode: "quiz", availableNow: 1 });
  });

  it("uses priority then availability then track id across other tracks", async () => {
    const result = await findReadyAlternative(
      hass({ "a:learn": 3, "b:learn": 8 }),
      dashboard,
      "current",
      "learn",
    );
    expect(result).toMatchObject({ trackId: "b", mode: "learn", availableNow: 8 });
  });

  it("never returns a destination with zero effective availability", async () => {
    const result = await findReadyAlternative(hass({}), dashboard, "current", "quiz");
    expect(result).toBeUndefined();
  });
});
