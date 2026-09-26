import { describe, expect, it } from "vitest";

import { formatDatasetBytes } from "./dataset-view";

describe("dataset sources view", () => {
  it("formats cache sizes without hiding the actual scale", () => {
    expect(formatDatasetBytes(0)).toBe("0 B");
    expect(formatDatasetBytes(1024)).toBe("1.00 KiB");
    expect(formatDatasetBytes(30 * 1024 * 1024)).toBe("30.0 MiB");
    expect(formatDatasetBytes(2 * 1024 * 1024 * 1024)).toBe("2.00 GiB");
  });
});
