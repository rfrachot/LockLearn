import { describe, expect, it } from "vitest";

import { isRouteVisible, visibleNavigation } from "./navigation";
import type { VisibleProfile } from "./protocol";

function profile(role: VisibleProfile["role"]): VisibleProfile {
  return {
    profile_id: `profile-${role}`,
    name: role,
    preset: "standard",
    timezone: "Europe/Paris",
    status: "active",
    role,
  };
}

describe("permission-aware navigation", () => {
  it("shows no product routes without any visible Profile", () => {
    expect(visibleNavigation([])).toEqual([]);
  });

  it("keeps Settings hidden for viewer/editor-only users", () => {
    const routes = visibleNavigation([profile("viewer"), profile("editor")]).map(
      (item) => item.route,
    );
    expect(routes).toContain("home");
    expect(routes).not.toContain("settings");
  });

  it("shows Settings when at least one owned Profile is visible", () => {
    const profiles = [profile("viewer"), profile("owner")];
    expect(isRouteVisible("settings", profiles)).toBe(true);
  });
});
