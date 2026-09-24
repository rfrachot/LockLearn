import { describe, expect, it } from "vitest";

import { FRONTEND_PROTOCOL_VERSION } from "./protocol";
import {
  registrationDecision,
  type LockLearnElementConstructor,
} from "./registration";

function constructorWithProtocol(
  protocol?: number,
): LockLearnElementConstructor {
  class Existing {}
  if (protocol !== undefined) {
    Object.defineProperty(Existing, "locklearnFrontendProtocol", {
      value: protocol,
    });
  }
  return Existing as unknown as LockLearnElementConstructor;
}

describe("custom-element registration", () => {
  it("defines the element when none is loaded", () => {
    expect(registrationDecision(undefined)).toEqual({ kind: "define" });
  });

  it("reuses a matching registered element", () => {
    expect(
      registrationDecision(
        constructorWithProtocol(FRONTEND_PROTOCOL_VERSION),
      ),
    ).toEqual({ kind: "reuse" });
  });

  it("requires a full reload for an unknown or mismatched registered element", () => {
    expect(registrationDecision(constructorWithProtocol())).toEqual({
      kind: "reload",
      existingProtocol: null,
      frontendProtocol: FRONTEND_PROTOCOL_VERSION,
    });

    expect(
      registrationDecision(
        constructorWithProtocol(FRONTEND_PROTOCOL_VERSION + 1),
      ),
    ).toEqual({
      kind: "reload",
      existingProtocol: FRONTEND_PROTOCOL_VERSION + 1,
      frontendProtocol: FRONTEND_PROTOCOL_VERSION,
    });
  });
});
