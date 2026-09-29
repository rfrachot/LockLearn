import { describe, expect, it } from "vitest";

describe("LockLearn panel module", () => {
  it("guards custom-element registration across module reloads", async () => {
    const definitions = new Map<string, unknown>();
    Object.defineProperty(globalThis, "customElements", {
      configurable: true,
      value: {
        define: (name: string, constructor: unknown) => {
          if (definitions.has(name)) throw new Error("duplicate definition");
          definitions.set(name, constructor);
        },
        get: (name: string) => definitions.get(name),
      },
    });

    await import("./locklearn-panel");
    expect(definitions.has("locklearn-panel")).toBe(true);

    const PanelConstructor = definitions.get("locklearn-panel") as new () => object;
    const panel = new PanelConstructor();
    expect(Object.hasOwn(panel, "route")).toBe(false);
  });
});
