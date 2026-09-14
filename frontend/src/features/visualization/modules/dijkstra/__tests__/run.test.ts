import { describe, expect, it } from "vitest";
import { GraphAdapter } from "@/features/visualization/adapters/graph-adapter";
import { defaultDijkstraGraph, run } from "@/features/visualization/modules/dijkstra";
describe("dijkstra/run", () => {
  it("is deterministic and finds canonical distances", () => {
    const input = defaultDijkstraGraph();
    const events = run(input);
    expect(run(input)).toEqual(events);
    const last = events.at(-1);
    expect(last?.type).toBe("complete");
    if (!last || last.type !== "complete") throw new Error("Expected completion");
    expect(last.summary).toEqual({ distances: { a: 0, b: 3, c: 1, d: 4 } });
    expect(
      events
        .reduce(GraphAdapter.reduce, GraphAdapter.createInitialState(input))
        .nodes.every((n) => n.status === "visited"),
    ).toBe(true);
  });
});
