import { describe, expect, it } from "vitest";

import { canEditTrackRole, canManageProfileRole, errorMessage } from "./management-view";

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


describe("management error presentation", () => {
  it("renders Home Assistant WebSocket object errors as their message", () => {
    expect(errorMessage({
      code: "locklearn/invalid_request",
      message: "track selection resolves to no active cards",
    })).toBe("track selection resolves to no active cards");
  });

  it("never degrades an object error to [object Object]", () => {
    expect(errorMessage({ code: "locklearn/forbidden" })).toBe("locklearn/forbidden");
  });
});
