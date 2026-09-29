import { css, html, nothing, type TemplateResult } from "lit";

import type { LearnContentBlock } from "./protocol";

interface RubySegmentPayload {
  text: string;
  reading: string | null;
}

interface RichNode {
  type: string;
  text?: string;
  reading?: string;
  children?: unknown[];
}

export const contentRendererStyles = css`
  .content-block {
    min-width: 0;
    max-width: 100%;
    overflow-wrap: anywhere;
    word-break: normal;
    line-height: 1.55;
  }

  .content-block:lang(ja) {
    font-family:
      "Hiragino Sans",
      "Hiragino Kaku Gothic ProN",
      "Yu Gothic",
      "YuGothic",
      "Noto Sans CJK JP",
      "Noto Sans JP",
      Meiryo,
      sans-serif;
    font-size: max(1.125rem, 1em);
    line-height: 1.75;
    text-autospace: normal;
  }

  .content-block ruby {
    ruby-position: over;
    ruby-align: center;
  }

  .content-block rt {
    font-size: 0.55em;
    line-height: 1;
    font-weight: 400;
  }

  .content-block p {
    margin: 0.35em 0;
  }

  .content-block code {
    font-family: ui-monospace, "SFMono-Regular", Consolas, monospace;
    overflow-wrap: anywhere;
  }
`;

export const interactiveAccessibilityStyles = css`
  :where(button, a, input, select, textarea):focus-visible {
    outline: 3px solid var(--primary-color, currentColor);
    outline-offset: 2px;
  }

  :where(button, a, input, select, textarea) {
    max-width: 100%;
  }

  :where(a, label, p, li, dd, dt, button) {
    overflow-wrap: anywhere;
  }
`;

export function safeRubySegments(
  payload: Record<string, unknown>,
  visibleText: string,
): RubySegmentPayload[] | null {
  const raw = payload.ruby_segments;
  if (!Array.isArray(raw) || raw.length === 0) return null;

  const segments: RubySegmentPayload[] = [];
  for (const item of raw) {
    if (typeof item !== "object" || item === null) return null;
    const candidate = item as Record<string, unknown>;
    if (typeof candidate.text !== "string" || candidate.text === "") return null;
    const reading =
      candidate.reading === undefined || candidate.reading === null
        ? null
        : typeof candidate.reading === "string" && candidate.reading !== ""
          ? candidate.reading
          : undefined;
    if (reading === undefined) return null;
    segments.push({ text: candidate.text, reading });
  }

  if (segments.map((segment) => segment.text).join("") !== visibleText) return null;
  return segments;
}

function renderRubySegments(segments: RubySegmentPayload[]): TemplateResult {
  return html`${segments.map((segment) =>
    segment.reading === null
      ? segment.text
      : html`<ruby>${segment.text}<rp>(</rp><rt>${segment.reading}</rt><rp>)</rp></ruby>`,
  )}`;
}

function richNode(value: unknown, depth = 0): TemplateResult | string | typeof nothing {
  if (depth > 16 || typeof value !== "object" || value === null) return nothing;
  const node = value as RichNode;

  if ((node.type === "text" || node.type === "inline_code") && typeof node.text === "string") {
    return node.type === "inline_code" ? html`<code>${node.text}</code>` : node.text;
  }
  if (node.type === "line_break") return html`<br />`;
  if (
    node.type === "ruby" &&
    typeof node.text === "string" &&
    node.text !== "" &&
    typeof node.reading === "string" &&
    node.reading !== ""
  ) {
    return html`<ruby>${node.text}<rp>(</rp><rt>${node.reading}</rt><rp>)</rp></ruby>`;
  }
  if (
    (node.type === "paragraph" || node.type === "emphasis" || node.type === "strong") &&
    Array.isArray(node.children)
  ) {
    const children = node.children.map((child) => richNode(child, depth + 1));
    if (node.type === "paragraph") return html`<p>${children}</p>`;
    if (node.type === "emphasis") return html`<em>${children}</em>`;
    return html`<strong>${children}</strong>`;
  }
  return nothing;
}

function renderPayload(block: LearnContentBlock): TemplateResult | string | typeof nothing {
  const rawText = block.payload.text;
  if (typeof rawText === "string" && rawText !== "") {
    const segments = safeRubySegments(block.payload, rawText);
    return segments === null ? rawText : renderRubySegments(segments);
  }

  if (
    block.kind === "rich_text" &&
    block.payload.type === "document" &&
    Array.isArray(block.payload.children)
  ) {
    return html`${block.payload.children.map((node) => richNode(node, 1))}`;
  }

  return nothing;
}

export function renderContentBlock(block: LearnContentBlock, primary = false) {
  const rendered = renderPayload(block);
  if (rendered === nothing) return nothing;
  return html`
    <div
      class="content-block ${primary ? "primary-content" : ""}"
      lang=${block.language_tag ?? nothing}
    >
      ${rendered}
    </div>
  `;
}
