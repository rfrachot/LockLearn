import { describe, expect, it } from "vitest";

import {
  evidenceTotals,
  formatPercent,
  recentDaily,
} from "./stats-view";
import type { StatsDailyRecord } from "./protocol";

function row(
  date: string,
  trackId: string,
  exposures: number,
  verified: number,
): StatsDailyRecord {
  return {
    profile_id: "p1",
    track_id: trackId,
    local_date: date,
    timezone_name: "Europe/Paris",
    utc_offset_minutes: 120,
    policy_version: "1",
    learning_exposures: exposures,
    verified_retrievals: verified,
    self_known: 0,
    verified_correct: verified,
    verified_wrong: 0,
    quiz_total: 0,
    free_text_total: 0,
    hints_used: 0,
    new_cards: 0,
    reviewed_cards: verified,
    relearning_cards: 0,
    leech_cards: 0,
    active_seconds: 0,
  };
}

describe("P5.7 statistics view helpers", () => {
  it("keeps exposure counts separate from verified retrieval evidence", () => {
    const totals = evidenceTotals([
      row("2026-09-26", "t1", 12, 3),
      row("2026-09-26", "t2", 8, 5),
    ]);

    expect(totals).toEqual({
      exposures: 20,
      verifiedRetrievals: 8,
    });
  });

  it("aggregates tracks by local date before applying the recent-day window", () => {
    const rows = recentDaily([
      row("2026-09-25", "t1", 1, 1),
      row("2026-09-26", "t1", 2, 2),
      row("2026-09-26", "t2", 3, 4),
      row("2026-09-27", "t1", 5, 6),
    ], 2);

    expect(rows.map((item) => item.local_date)).toEqual([
      "2026-09-27",
      "2026-09-26",
    ]);
    expect(rows[1]?.learning_exposures).toBe(5);
    expect(rows[1]?.verified_retrievals).toBe(6);
  });

  it("formats null and fractional ratios without inventing evidence", () => {
    expect(formatPercent(null)).toBe("—");
    expect(formatPercent(0.823)).toBe("82%");
  });
});
