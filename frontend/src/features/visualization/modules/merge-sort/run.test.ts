import { describe, expect, it } from "vitest";

import { ArrayAdapter } from "@/features/visualization/adapters/array-adapter";
import { run } from "@/features/visualization/modules/merge-sort/run";

describe("merge-sort/run", () => {
  it("produces a deterministic trace without mutating its input", () => {
    const input = [8, 3, 6, 1, 7, 2];
    expect(run(input)).toEqual(run(input));
    expect(input).toEqual([8, 3, 6, 1, 7, 2]);
  });

  it("moves the array into sorted order and completes the trace", () => {
    const input = [8, 3, 6, 1, 7, 2];
    const finalState = run(input).reduce(
      ArrayAdapter.reduce,
      ArrayAdapter.createInitialState(input),
    );

    expect(finalState.items.map((item) => item.value)).toEqual([1, 2, 3, 6, 7, 8]);
    expect(finalState.items.every((item) => item.status === "sorted")).toBe(true);
  });

  it("merges in descending order with deterministic stable IDs", () => {
    const input = [8, 3, 6, 1, 7, 2];
    const events = run(input, { direction: "descending" });
    const finalState = events.reduce(ArrayAdapter.reduce, ArrayAdapter.createInitialState(input));

    expect(run(input, { direction: "descending" })).toEqual(events);
    expect(finalState.items.map((item) => item.value)).toEqual([8, 7, 6, 3, 2, 1]);
    expect(new Set(finalState.items.map((item) => item.id))).toHaveLength(input.length);
  });
});
