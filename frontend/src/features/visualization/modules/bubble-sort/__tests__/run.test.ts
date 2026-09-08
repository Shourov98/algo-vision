import { describe, expect, it } from "vitest";

import { ArrayAdapter } from "@/features/visualization/adapters/array-adapter";
import { run } from "@/features/visualization/modules/bubble-sort/run";
import {
  CANONICAL_EVENT_COUNT,
  CANONICAL_INPUT,
} from "@/features/visualization/modules/bubble-sort/__tests__/canonical/trace";

describe("bubble-sort/run", () => {
  it("produces the locked canonical event count", () => {
    expect(run([...CANONICAL_INPUT])).toHaveLength(CANONICAL_EVENT_COUNT);
  });

  it("is deterministic and does not mutate its input", () => {
    const input = [...CANONICAL_INPUT];
    expect(run(input)).toEqual(run(input));
    expect(input).toEqual(CANONICAL_INPUT);
  });

  it("produces monotonic step identifiers and finishes with complete", () => {
    const events = run([...CANONICAL_INPUT]);
    expect(events.map((event) => event.id)).toEqual(
      events.map((_, index) => `bubble-sort-${index}`),
    );
    expect(events.map((event) => event.t)).toEqual(events.map((_, index) => index));
    expect(events.at(-1)?.type).toBe("complete");
  });

  it("reduces to a sorted array with stable element IDs", () => {
    const initial = ArrayAdapter.createInitialState([...CANONICAL_INPUT]);
    const finalState = run([...CANONICAL_INPUT]).reduce(ArrayAdapter.reduce, initial);

    expect(finalState.items.map((item) => item.value)).toEqual([1, 2, 4, 5, 8]);
    expect(finalState.items.map((item) => item.id)).toEqual([
      "element-4",
      "element-2",
      "element-5",
      "element-1",
      "element-3",
    ]);
    expect(finalState.items.map((item) => item.status)).toEqual([
      "sorted",
      "sorted",
      "sorted",
      "sorted",
      "sorted",
    ]);
  });
});
