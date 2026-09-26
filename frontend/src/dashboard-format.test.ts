import { describe, expect, it } from "vitest";

import type { DashboardResponse } from "./protocol";

describe("dashboard payload shape", () => {
  it("keeps Home cards content-agnostic", () => {
    const payload: DashboardResponse = {
      profile: {
        profile_id: "profile-1",
        name: "Renaud",
        preset: "standard",
        timezone: "Europe/Paris",
      },
      generated_at_utc: "2026-09-26T20:00:00+00:00",
      tracks: [
        {
          track_id: "track-1",
          name: "Japanese N5",
          source_language: "ja",
          target_language: "ja-Latn",
          due_today: 12,
          recent_verified_retention: {
            retained: true,
            created_at_utc: "2026-09-26T19:00:00+00:00",
          },
          recent_verified_accuracy: {
            correct: 26,
            total: 30,
            accuracy: 0.866667,
          },
          states: { new: 3, review: 12 },
          last_session: {
            session_id: "session-1",
            session_type: "learn",
            status: "completed",
            question_count: 20,
            answered_count: 18,
            started_at_utc: "2026-09-26T18:00:00+00:00",
            last_activity_at_utc: "2026-09-26T18:20:00+00:00",
            completed_at_utc: "2026-09-26T18:20:00+00:00",
          },
          next_notification: {
            slot_type: "learning",
            status: "scheduled",
            effective_for_utc: "2026-09-26T20:42:00+00:00",
          },
        },
      ],
    };

    const serialized = JSON.stringify(payload);
    expect(serialized).not.toContain("card_key");
    expect(serialized).not.toContain("learning_item_id");
    expect(serialized).not.toContain("prompt");
    expect(serialized).not.toContain("answer_text");
  });
});
