import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { excerpt, relativeTime } from "./format.js";

describe("excerpt", () => {
  it("collapses whitespace and leaves short text alone", () => {
    expect(excerpt("  one\n\n two   three ")).toBe("one two three");
  });

  it("truncates at the limit with an ellipsis", () => {
    expect(excerpt("abcdefghij", 5)).toBe("abcde…");
    expect(excerpt("abcd efgh", 5)).toBe("abcd…");
  });
});

describe("relativeTime", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-09-18T12:00:00Z"));
  });

  afterEach(() => vi.useRealTimers());

  it("says just now inside 45 seconds", () => {
    expect(relativeTime("2026-09-18T11:59:30Z")).toBe("just now");
  });

  it("picks the largest unit that fits", () => {
    expect(relativeTime("2026-09-18T11:57:00Z")).toBe("3 minutes ago");
    expect(relativeTime("2026-09-18T09:00:00Z")).toBe("3 hours ago");
    expect(relativeTime("2026-09-16T12:00:00Z")).toBe("2 days ago");
    expect(relativeTime("2025-09-18T12:00:00Z")).toBe("last year");
  });
});
