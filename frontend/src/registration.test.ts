import { describe, expect, it } from "vitest";

import { FRONTEND_PROTOCOL_VERSION } from "./protocol";
import { registrationDecision } from "./registration";

describe("custom-element registration", () => {
  it("defines the element when none is loaded", () => {
    expect(registrationDecision(undefined)).toEqual({ kind: "define" });
  });

  it("reuses a matching registered element", () => {
    class Existing extends HTMLElement {
      static locklearnFrontendProtocol = FRONTEND_PROTOCOL_VERSION;
    }
    expect(registrationDecision(Existing)).toEqual({ kind: "reuse" });
  });

  it("requires a full reload for an unknown or mismatched registered element", () => {
    class Legacy extends HTMLElement {}
    expect(registrationDecision(Legacy)).toEqual({
      kind: "reload",
      existingProtocol: null,
      frontendProtocol: FRONTEND_PROTOCOL_VERSION,
    });

    class OtherProtocol extends HTMLElement {
      static locklearnFrontendProtocol = FRONTEND_PROTOCOL_VERSION + 1;
    }
    expect(registrationDecision(OtherProtocol)).toEqual({
      kind: "reload",
      existingProtocol: FRONTEND_PROTOCOL_VERSION + 1,
      frontendProtocol: FRONTEND_PROTOCOL_VERSION,
    });
  });
});
