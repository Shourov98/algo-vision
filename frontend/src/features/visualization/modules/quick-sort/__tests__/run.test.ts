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
});
