import { describe, expect, it } from "vitest";

import { defaultProfileId, groupProfiles } from "./profile-switcher";
import type { BootstrapResponse, VisibleProfile } from "./protocol";

function profile(
  profileId: string,
  role: VisibleProfile["role"],
): VisibleProfile {
  return {
    profile_id: profileId,
    name: profileId,
    preset: "standard",
    timezone: "Europe/Paris",
    status: "active",
    role,
  };
}

function bootstrap(
  personalProfile: VisibleProfile | null,
): BootstrapResponse {
  return {
    frontend_protocol: 1,
    backend_version: "0.0.2",
    panel_path: "/locklearn",
    authenticated_user_id: "user-1",
    personal_profile: personalProfile,
  };
}

describe("profile switcher", () => {
  it("groups owned profiles separately from shared profiles", () => {
    const groups = groupProfiles([
      profile("mine", "owner"),
      profile("edit", "editor"),
      profile("view", "viewer"),
    ]);

    expect(groups.mine.map((item) => item.profile_id)).toEqual(["mine"]);
    expect(groups.shared.map((item) => item.profile_id)).toEqual([
      "edit",
      "view",
    ]);
  });

  it("prefers the visible personal profile", () => {
    const personal = profile("personal", "owner");
    expect(
      defaultProfileId(
        [profile("other-owner", "owner"), personal],
        bootstrap(personal),
      ),
    ).toBe("personal");
  });

  it("falls back to an owner and then to a shared profile", () => {
    expect(
      defaultProfileId(
        [profile("shared", "viewer"), profile("mine", "owner")],
        bootstrap(null),
      ),
    ).toBe("mine");
    expect(
      defaultProfileId([profile("shared", "viewer")], bootstrap(null)),
    ).toBe("shared");
    expect(defaultProfileId([], bootstrap(null))).toBeNull();
  });
});
