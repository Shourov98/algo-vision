import { describe, expect, it } from "vitest";
import { GraphAdapter } from "@/features/visualization/adapters/graph-adapter";
import { defaultGraph, runBfs, runDfs } from "@/features/visualization/modules/bfs-dfs";
describe("BFS and DFS", () => {
  it.each([
    ["BFS", runBfs, ["a", "b", "c", "d"]],
    ["DFS", runDfs, ["a", "b", "d", "c"]],
  ] as const)("%s has a deterministic canonical order", (_, run, order) => {
    const input = defaultGraph();
    const events = run(input);
    expect(run(input)).toEqual(events);
    expect(
      events.filter((e) => e.type === "visit").map((e) => (e.type === "visit" ? e.elementId : "")),
    ).toEqual(order);
    expect(events.at(-1)?.type).toBe("complete");
    expect(events.map((e) => e.t)).toEqual(events.map((_, i) => i));
    const state = events.reduce(GraphAdapter.reduce, GraphAdapter.createInitialState(input));
    expect(state.nodes.every((node) => node.status === "visited")).toBe(true);
  });
});
