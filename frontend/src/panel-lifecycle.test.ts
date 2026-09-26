import { describe, expect, it } from "vitest";

import { shouldStartInitialLoad } from "./panel-lifecycle";

describe("panel lifecycle", () => {
  it("starts once when hass first becomes available", () => {
    expect(shouldStartInitialLoad(false, true, true)).toBe(true);
  });

  it("does not restart bootstrap for later hass object updates", () => {
    expect(shouldStartInitialLoad(true, true, true)).toBe(false);
    expect(shouldStartInitialLoad(true, false, true)).toBe(false);
  });

  it("waits if hass is not available yet", () => {
    expect(shouldStartInitialLoad(false, true, false)).toBe(false);
  });
});
