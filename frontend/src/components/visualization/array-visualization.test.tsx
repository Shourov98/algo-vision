import { afterEach, describe, expect, it, vi } from "vitest";

import { prefersReducedMotion } from "@/components/visualization/array-visualization";

const originalMatchMedia = window.matchMedia;

afterEach(() => {
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    value: originalMatchMedia,
  });
});

describe("prefersReducedMotion", () => {
  it("detects a reduced-motion preference before movement animation runs", () => {
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: vi.fn().mockReturnValue({ matches: true }),
    });

    expect(prefersReducedMotion()).toBe(true);
  });
});
