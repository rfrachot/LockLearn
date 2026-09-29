import { describe, expect, it } from "vitest";

import { canEditTrackRole, canManageProfileRole } from "./management-view";

describe("management ACL presentation", () => {
  it("keeps Profile/ACL/settings mutations owner-only", () => {
    expect(canManageProfileRole("owner")).toBe(true);
    expect(canManageProfileRole("editor")).toBe(false);
    expect(canManageProfileRole("viewer")).toBe(false);
  });

  it("allows Track planning for owners/editors but not viewers", () => {
    expect(canEditTrackRole("owner")).toBe(true);
    expect(canEditTrackRole("editor")).toBe(true);
    expect(canEditTrackRole("viewer")).toBe(false);
  });
});
