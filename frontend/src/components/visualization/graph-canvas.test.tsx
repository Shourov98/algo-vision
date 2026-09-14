import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { GraphAdapter } from "@/features/visualization/adapters/graph-adapter";
import { GraphCanvas } from "@/components/visualization/graph-canvas";

describe("GraphCanvas", () => {
  it("renders positioned nodes, edges, and weights accessibly", () => {
    const state = GraphAdapter.createInitialState({
      nodes: [
        { id: "a", label: "A", position: { x: 0, y: 0 } },
        { id: "b", label: "B", position: { x: 100, y: 20 } },
      ],
      edges: [{ id: "a-b", from: "a", to: "b", weight: 3 }],
    });
    render(<GraphCanvas state={state} />);
    expect(screen.getByRole("region", { name: "Graph visualization" })).toBeInTheDocument();
    expect(screen.getByLabelText("Node A: idle")).toBeInTheDocument();
    expect(screen.getByLabelText("Edge a to b")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });
});
