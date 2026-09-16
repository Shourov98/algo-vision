import { describe, expect, it } from "vitest";

import {
  resolveSortDirection,
  shouldSwapForDirection,
  shouldTakeLeftForDirection,
} from "@/features/visualization/modules/sort-direction";

describe("sort direction helpers", () => {
  it("keeps ascending as the default", () => {
    expect(resolveSortDirection()).toBe("ascending");
    expect(shouldSwapForDirection(5, 2, "ascending")).toBe(true);
    expect(shouldTakeLeftForDirection(2, 5, "ascending")).toBe(true);
  });

  it("reverses ordering decisions for descending runs", () => {
    expect(shouldSwapForDirection(2, 5, "descending")).toBe(true);
    expect(shouldTakeLeftForDirection(5, 2, "descending")).toBe(true);
  });
});
