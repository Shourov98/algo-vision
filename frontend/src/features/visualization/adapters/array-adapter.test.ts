import { describe, expect, it } from "vitest";

import { ArrayAdapter } from "@/features/visualization/adapters/array-adapter";
import { EngineInvariantError } from "@/features/visualization/errors";

describe("ArrayAdapter", () => {
  it("uses supplied stable IDs when creating state", () => {
    expect(ArrayAdapter.createInitialState([8, 3], ["first", "second"])).toEqual({
      items: [
        { id: "first", status: "idle", value: 8 },
        { id: "second", status: "idle", value: 3 },
      ],
    });
  });

  it("compares without mutating the previous state", () => {
    const initial = ArrayAdapter.createInitialState([8, 3], ["first", "second"]);
    const compared = ArrayAdapter.reduce(initial, {
      id: "compare-1",
      ids: ["first", "second"],
      message: "Compare values.",
      t: 0,
      type: "compare",
    });

    expect(initial.items.map((item) => item.status)).toEqual(["idle", "idle"]);
    expect(compared.items.map((item) => item.status)).toEqual(["comparing", "comparing"]);
  });

  it("swaps item positions while preserving their IDs", () => {
    const initial = ArrayAdapter.createInitialState([8, 3], ["first", "second"]);
    const swapped = ArrayAdapter.reduce(initial, {
      id: "swap-1",
      ids: ["first", "second"],
      message: "Swap values.",
      t: 1,
      type: "swap",
    });

    expect(swapped.items.map((item) => [item.id, item.value])).toEqual([
      ["second", 3],
      ["first", 8],
    ]);
    expect(swapped.items.map((item) => item.status)).toEqual(["swapping", "swapping"]);
  });

  it("rejects events that reference unknown element IDs", () => {
    const initial = ArrayAdapter.createInitialState([8]);
    expect(() =>
      ArrayAdapter.reduce(initial, {
        elementId: "missing",
        id: "mark-1",
        message: "Mark a missing value.",
        status: "sorted",
        t: 0,
        type: "mark",
      }),
    ).toThrow(EngineInvariantError);
  });
});
