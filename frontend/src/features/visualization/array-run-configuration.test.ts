import { describe, expect, it } from "vitest";

import {
  createDeterministicPreset,
  hasSameArrayRunConfiguration,
  isSortedForDirection,
  sortValuesForDirection,
  validateArrayRunConfiguration,
} from "@/features/visualization/array-run-configuration";
import type { ArrayModuleCapabilities } from "@/features/visualization/modules/types";

const searchCapabilities: ArrayModuleCapabilities = {
  maxItems: 12,
  minItems: 2,
  requiresSortedInput: true,
  supportsDirection: true,
  supportsTarget: true,
};

describe("array run configuration", () => {
  it("creates deterministic presets within the supported item range", () => {
    expect(createDeterministicPreset(5)).toEqual([5, 2, 8, 1, 4]);
    expect(() => createDeterministicPreset(1)).toThrow(RangeError);
  });

  it("validates target and sorted order for Binary Search", () => {
    expect(
      validateArrayRunConfiguration(
        { direction: "ascending", target: 7, values: [1, 3, 7] },
        searchCapabilities,
      ),
    ).toEqual({ issues: [], valid: true });
    expect(
      validateArrayRunConfiguration(
        { direction: "descending", values: [1, 3, 7] },
        searchCapabilities,
      ).issues,
    ).toEqual(["missing_target", "unsorted_input"]);
  });

  it("sorts copies without mutating the draft input", () => {
    const values = [5, 1, 3];
    expect(sortValuesForDirection(values, "ascending")).toEqual([1, 3, 5]);
    expect(sortValuesForDirection(values, "descending")).toEqual([5, 3, 1]);
    expect(values).toEqual([5, 1, 3]);
    expect(isSortedForDirection([5, 3, 1], "descending")).toBe(true);
  });

  it("detects a pending change across values, direction, and target", () => {
    const active = { direction: "ascending" as const, target: 7, values: [1, 3, 7] };

    expect(hasSameArrayRunConfiguration(active, { ...active, values: [1, 3, 7] })).toBe(true);
    expect(hasSameArrayRunConfiguration(active, { ...active, direction: "descending" })).toBe(
      false,
    );
    expect(hasSameArrayRunConfiguration(active, { ...active, target: 3 })).toBe(false);
    expect(hasSameArrayRunConfiguration(active, { ...active, values: [1, 7, 3] })).toBe(false);
  });
});
