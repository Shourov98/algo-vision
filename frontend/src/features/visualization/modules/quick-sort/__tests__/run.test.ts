import { describe, expect, it } from "vitest";
import { ArrayAdapter } from "@/features/visualization/adapters/array-adapter";
import { run } from "@/features/visualization/modules/quick-sort/run";
import {
  CANONICAL_EVENT_COUNT,
  CANONICAL_INPUT,
} from "@/features/visualization/modules/quick-sort/__tests__/canonical/trace";
describe("quick-sort/run", () => {
  it("produces the locked canonical trace", () => {
    expect(run([...CANONICAL_INPUT])).toHaveLength(CANONICAL_EVENT_COUNT);
  });
  it("is deterministic and reduces to sorted values", () => {
    const events = run([...CANONICAL_INPUT]);
    const state = events.reduce(
      ArrayAdapter.reduce,
      ArrayAdapter.createInitialState([...CANONICAL_INPUT]),
    );
    expect(run([...CANONICAL_INPUT])).toEqual(events);
    expect(state.items.map((item) => item.value)).toEqual([1, 2, 4, 5, 8]);
    expect(events.at(-1)?.type).toBe("complete");
  });
  it("sorts in descending order with stable element IDs", () => {
    const input = [...CANONICAL_INPUT];
    const events = run(input, { direction: "descending" });
    const state = events.reduce(ArrayAdapter.reduce, ArrayAdapter.createInitialState(input));

    expect(run(input, { direction: "descending" })).toEqual(events);
    expect(state.items.map((item) => item.value)).toEqual([8, 5, 4, 2, 1]);
    expect(new Set(state.items.map((item) => item.id))).toHaveLength(input.length);
  });
});
