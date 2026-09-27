import { describe, expect, it } from "vitest";

import { CATALOG, languageFallback } from "./i18n";

describe("languageFallback", () => {
  it("keeps the FR and EN catalogs in complete key parity", () => {
    expect(Object.keys(CATALOG.fr).sort()).toEqual(Object.keys(CATALOG.en).sort());
  });


  it("uses exact supported locales", () => {
    expect(languageFallback("fr")).toBe("fr");
    expect(languageFallback("en")).toBe("en");
  });

  it("falls back from regional locale to supported base language", () => {
    expect(languageFallback("fr-FR")).toBe("fr");
    expect(languageFallback("fr_CA")).toBe("fr");
    expect(languageFallback("en-GB")).toBe("en");
  });

  it("falls back to English for unsupported languages", () => {
    expect(languageFallback("de-DE")).toBe("en");
    expect(languageFallback("ja")).toBe("en");
    expect(languageFallback("")).toBe("en");
  });
});
