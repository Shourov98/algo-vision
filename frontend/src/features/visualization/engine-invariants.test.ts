import { describe, expect, it } from "vitest";

import { ArrayAdapter } from "@/features/visualization/adapters/array-adapter";
import { run as runBubbleSort } from "@/features/visualization/modules/bubble-sort/run";
import { run as runQuickSort } from "@/features/visualization/modules/quick-sort/run";

const inputs = [[], [1], [2, 1], [5, 2, 8, 1, 4], [3, 3, 1, 3]];

describe("visualization engine invariants", () => {
  it.each([
    ["Bubble Sort", runBubbleSort],
    ["Quick Sort", runQuickSort],
  ] as const)("%s produces deterministic, monotonic complete traces", (_, run) => {
    for (const input of inputs) {
      const events = run(input);
      expect(run(input)).toEqual(events);
      expect(events.at(-1)?.type).toBe("complete");
      expect(events.map((event) => event.t)).toEqual(events.map((_, index) => index));
      expect(new Set(events.map((event) => event.id))).toHaveLength(events.length);
    }
  });

  it.each([
    ["Bubble Sort", runBubbleSort],
    ["Quick Sort", runQuickSort],
  ] as const)("%s reduces every sample to ascending values", (_, run) => {
    for (const input of inputs) {
      const finalState = run(input).reduce(
        ArrayAdapter.reduce,
        ArrayAdapter.createInitialState(input),
      );
      expect(finalState.items.map((item) => item.value)).toEqual(
        [...input].sort((left, right) => left - right),
      );
    }
  });

  it("does not mutate the prior state across insert, update, and delete events", () => {
    const initial = ArrayAdapter.createInitialState([4], ["first"]);
    const inserted = ArrayAdapter.reduce(initial, {
      elementId: "second",
      id: "insert-1",
      message: "Insert.",
      t: 0,
      type: "insert",
      value: 8,
    });
    const updated = ArrayAdapter.reduce(inserted, {
      elementId: "second",
      id: "update-1",
      message: "Update.",
      t: 1,
      type: "update",
      value: 9,
    });
    const deleted = ArrayAdapter.reduce(updated, {
      elementId: "first",
      id: "delete-1",
      message: "Delete.",
      t: 2,
      type: "delete",
    });

    expect(initial.items).toEqual([{ id: "first", status: "idle", value: 4 }]);
    expect(inserted.items).toEqual([
      { id: "first", status: "idle", value: 4 },
      { id: "second", status: "active", value: 8 },
    ]);
    expect(updated.items).toEqual([
      { id: "first", status: "idle", value: 4 },
      { id: "second", status: "active", value: 9 },
    ]);
    expect(deleted.items).toEqual([{ id: "second", status: "active", value: 9 }]);
  });
});
