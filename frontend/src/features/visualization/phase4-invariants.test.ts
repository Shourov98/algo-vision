import { describe, expect, it } from "vitest";

import { GraphAdapter } from "@/features/visualization/adapters/graph-adapter";
import { defaultGraph, runBfs, runDfs } from "@/features/visualization/modules/bfs-dfs";
import {
  defaultDijkstraGraph,
  run as runDijkstra,
} from "@/features/visualization/modules/dijkstra";

function expectTrace(events: ReturnType<typeof runBfs>) {
  expect(events.at(-1)?.type).toBe("complete");
  expect(events.map((event) => event.t)).toEqual(events.map((_, index) => index));
  expect(new Set(events.map((event) => event.id))).toHaveLength(events.length);
}

describe("Phase 4 graph invariants", () => {
  it.each([
    ["BFS", defaultGraph, runBfs],
    ["DFS", defaultGraph, runDfs],
    ["Dijkstra", defaultDijkstraGraph, runDijkstra],
  ] as const)("keeps %s deterministic and preserves static layout", (_, createInput, run) => {
    const input = createInput();
    const events = run(input);
    const initial = GraphAdapter.createInitialState(input);
    const final = events.reduce(GraphAdapter.reduce, initial);

    expect(run(input)).toEqual(events);
    expectTrace(events);
    expect(final.nodes.map((node) => node.position)).toEqual(
      initial.nodes.map((node) => node.position),
    );
    expect(final.edges).toEqual(initial.edges);
  });

  it("visits the complete BFS/DFS graph and reports Dijkstra distances", () => {
    const traversalInput = defaultGraph();
    const dijkstraInput = defaultDijkstraGraph();
    const bfs = runBfs(traversalInput).reduce(
      GraphAdapter.reduce,
      GraphAdapter.createInitialState(traversalInput),
    );
    const dfs = runDfs(traversalInput).reduce(
      GraphAdapter.reduce,
      GraphAdapter.createInitialState(traversalInput),
    );
    const complete = runDijkstra(dijkstraInput).at(-1);

    expect(bfs.nodes.every((node) => node.status === "visited")).toBe(true);
    expect(dfs.nodes.every((node) => node.status === "visited")).toBe(true);
    if (!complete || complete.type !== "complete") throw new Error("Expected Dijkstra completion.");
    expect(complete.summary).toEqual({ distances: { a: 0, b: 3, c: 1, d: 4 } });
  });
});
