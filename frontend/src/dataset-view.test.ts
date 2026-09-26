import { describe, expect, it } from "vitest";

import { formatDatasetBytes, safeExternalUrl } from "./dataset-view";

describe("dataset sources view", () => {
  it("rejects non-http external links from untrusted discovery metadata", () => {
    expect(safeExternalUrl("javascript:alert(1)")).toBeNull();
    expect(safeExternalUrl("data:text/html,test")).toBeNull();
    expect(safeExternalUrl("not a url")).toBeNull();
    expect(safeExternalUrl("https://example.invalid/release")).toBe(
      "https://example.invalid/release",
    );
  });

  it("formats cache sizes without hiding the actual scale", () => {
    expect(formatDatasetBytes(0)).toBe("0 B");
    expect(formatDatasetBytes(1024)).toBe("1.00 KiB");
    expect(formatDatasetBytes(30 * 1024 * 1024)).toBe("30.0 MiB");
    expect(formatDatasetBytes(2 * 1024 * 1024 * 1024)).toBe("2.00 GiB");
  });
});
