import { describe, expect, it } from "vitest";

import {
  contentRendererStyles,
  interactiveAccessibilityStyles,
  renderContentBlock,
  safeRubySegments,
} from "./content-renderer";
import type { LearnContentBlock } from "./protocol";

function block(
  payload: Record<string, unknown>,
  languageTag = "ja",
): LearnContentBlock {
  return {
    content_block_id: "locklearn:block:test",
    position: 0,
    kind: "text",
    role: "prompt",
    reveals_answer: false,
    mask_strategy: "none",
    payload,
    language_tag: languageTag,
    script: languageTag === "ja" ? "Jpan" : "Latn",
  };
}

describe("P5.8 content renderer", () => {
  it("accepts ruby segments only when they exactly reconstruct visible text", () => {
    expect(
      safeRubySegments(
        {
          ruby_segments: [
            { text: "休", reading: "やす" },
            { text: "む", reading: null },
          ],
        },
        "休む",
      ),
    ).toEqual([
      { text: "休", reading: "やす" },
      { text: "む", reading: null },
    ]);

    expect(
      safeRubySegments(
        { ruby_segments: [{ text: "休", reading: "やす" }] },
        "休む",
      ),
    ).toBeNull();
  });

  it("rejects malformed ruby metadata and safely falls back to plain text", () => {
    expect(
      safeRubySegments(
        { ruby_segments: [{ text: "休", reading: "" }, { text: "む" }] },
        "休む",
      ),
    ).toBeNull();

    const rendered = renderContentBlock(
      block({ text: "<script>alert(1)</script>" }, "en"),
    );
    expect(rendered).toBeTruthy();
    expect(rendered.values).toContain("<script>alert(1)</script>");
  });

  it("ships the system CJK stack, ruby styling and visible keyboard focus", () => {
    expect(contentRendererStyles.cssText).toContain(':lang(ja)');
    expect(contentRendererStyles.cssText).toContain('"Yu Gothic"');
    expect(contentRendererStyles.cssText).toContain('"Noto Sans CJK JP"');
    expect(contentRendererStyles.cssText).toContain("ruby-position");
    expect(contentRendererStyles.cssText).toContain("rt");

    expect(interactiveAccessibilityStyles.cssText).toContain(":focus-visible");
    expect(interactiveAccessibilityStyles.cssText).toContain("outline: 3px");
  });
});
