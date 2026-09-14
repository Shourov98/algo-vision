import { describe, expect, it } from "vitest";
import { GraphAdapter } from "@/features/visualization/adapters/graph-adapter";
import { EngineInvariantError } from "@/features/visualization/errors";

const graph = {
  nodes: [
    { id: "a", label: "A", position: { x: 0, y: 0 } },
    { id: "b", label: "B", position: { x: 120, y: 40 } },
  ],
  edges: [{ id: "a-b", from: "a", to: "b", weight: 2 }],
};

describe("GraphAdapter", () => {
  it("preserves static positions and reduces graph events immutably", () => {
    const initial = GraphAdapter.createInitialState(graph);
    const next = GraphAdapter.reduce(initial, {
      id: "event-1",
      t: 0,
      type: "relax",
      from: "a",
      to: "b",
      weight: 2,
      message: "Relax A to B.",
    });
    expect(initial.nodes[1]?.status).toBe("idle");
    expect(next.nodes[1]?.status).toBe("frontier");
    expect(next.nodes[1]?.position).toEqual({ x: 120, y: 40 });
    expect(next.edges).not.toBe(initial.edges);
  });
  it("rejects duplicate IDs, missing positions, and invalid edges", () => {
    expect(() =>
      GraphAdapter.createInitialState({
        nodes: [
          { id: "a", position: { x: 0, y: 0 } },
          { id: "a", position: { x: 1, y: 1 } },
        ],
        edges: [],
      }),
    ).toThrow(EngineInvariantError);
    expect(() => GraphAdapter.createInitialState({ nodes: [{ id: "a" }], edges: [] })).toThrow(
      /static position/,
    );
    expect(() =>
      GraphAdapter.createInitialState({
        nodes: [{ id: "a", position: { x: 0, y: 0 } }],
        edges: [{ id: "bad", from: "a", to: "b" }],
      }),
    ).toThrow(/unknown node/);
  });
});
