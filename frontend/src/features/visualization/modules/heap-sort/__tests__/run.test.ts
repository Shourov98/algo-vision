import { describe, expect, it } from "vitest";
import { HeapAdapter } from "@/features/visualization/adapters/heap-adapter";
import { run } from "@/features/visualization/modules/heap-sort/run";
describe("heap-sort/run", () => {
  it("is deterministic and reduces to sorted values", () => {
    const input = [5, 2, 8, 1, 4];
    const events = run(input);
    const state = events.reduce(HeapAdapter.reduce, HeapAdapter.createInitialState(input));
    expect(run(input)).toEqual(events);
    expect(state.items.map((x) => x.value)).toEqual([1, 2, 4, 5, 8]);
    expect(events.at(-1)?.type).toBe("complete");
  });
});
