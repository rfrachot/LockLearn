import type { TemplateResult } from "lit";
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
  kind: LearnContentBlock["kind"] = "text",
): LearnContentBlock {
  return {
    content_block_id: "locklearn:block:test",
    position: 0,
    kind,
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
    const template = rendered as TemplateResult;
    expect(template.values).toContain("<script>alert(1)</script>");
  });



  it("keeps malicious rich-text text in Lit values, never template markup", () => {
    const malicious = '<img src=x onerror="alert(1)"><script>alert(2)</script>';
    const rendered = renderContentBlock(
      block(
        {
          type: "document",
          children: [
            {
              type: "paragraph",
              children: [{ type: "text", text: malicious }],
            },
          ],
        },
        "en",
        "rich_text",
      ),
    );
    expect(rendered).toBeTruthy();

    const templateMarkup: string[] = [];
    const stringValues: string[] = [];
    const visit = (value: unknown): void => {
      if (
        typeof value === "object" &&
        value !== null &&
        "strings" in value &&
        "values" in value
      ) {
        const template = value as TemplateResult;
        templateMarkup.push(...template.strings);
        template.values.forEach(visit);
        return;
      }
      if (Array.isArray(value)) {
        value.forEach(visit);
        return;
      }
      if (typeof value === "string") stringValues.push(value);
    };
    visit(rendered);

    expect(templateMarkup.join("")).not.toContain("<img");
    expect(templateMarkup.join("")).not.toContain("<script");
    expect(stringValues).toContain(malicious);
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
