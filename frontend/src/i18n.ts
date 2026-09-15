export const UI_LANGUAGES = ["en", "fr"] as const;
export type UiLanguage = (typeof UI_LANGUAGES)[number];

export function languageFallback(locale: string): UiLanguage {
  const normalized = locale.toLowerCase();
  if (normalized === "fr" || normalized.startsWith("fr-")) return "fr";
  return "en";
}
