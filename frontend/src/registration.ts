import { FRONTEND_PROTOCOL_VERSION } from "./protocol";

export interface LockLearnElementConstructor extends CustomElementConstructor {
  locklearnFrontendProtocol?: number;
}

export type RegistrationDecision =
  | { kind: "define" }
  | { kind: "reuse" }
  | {
      kind: "reload";
      existingProtocol: number | null;
      frontendProtocol: number;
    };

export function registrationDecision(
  existing: LockLearnElementConstructor | undefined,
): RegistrationDecision {
  if (existing === undefined) return { kind: "define" };
  const existingProtocol =
    typeof existing.locklearnFrontendProtocol === "number"
      ? existing.locklearnFrontendProtocol
      : null;
  if (existingProtocol === FRONTEND_PROTOCOL_VERSION) {
    return { kind: "reuse" };
  }
  return {
    kind: "reload",
    existingProtocol,
    frontendProtocol: FRONTEND_PROTOCOL_VERSION,
  };
}
