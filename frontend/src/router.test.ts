import { describe, expect, it } from "vitest";

import { parseRoute, routePath } from "./router";

describe("LockLearn router", () => {
  it("parses panel routes and defaults unknown paths to home", () => {
    expect(parseRoute("/locklearn")).toBe("home");
    expect(parseRoute("/locklearn/quiz")).toBe("quiz");
    expect(parseRoute("/stats")).toBe("stats");
    expect(parseRoute("/locklearn/unknown")).toBe("home");
  });

  it("builds stable panel paths", () => {
    expect(routePath("home")).toBe("/locklearn");
    expect(routePath("settings")).toBe("/locklearn/settings");
  });
});
