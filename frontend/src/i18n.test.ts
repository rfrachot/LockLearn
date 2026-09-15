import { describe, expect, it } from "vitest";
import { languageFallback } from "./i18n";

describe("languageFallback", () => {
  it("uses French for French regional locales", () => {
    expect(languageFallback("fr-FR")).toBe("fr");
  });

  it("falls back to English", () => {
    expect(languageFallback("de-DE")).toBe("en");
  });
});
