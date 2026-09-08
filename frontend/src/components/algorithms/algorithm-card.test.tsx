import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AlgorithmCard } from "@/components/algorithms/algorithm-card";

describe("AlgorithmCard", () => {
  it("shows the algorithm details and visualization entry point", () => {
    render(
      <AlgorithmCard
        algorithm={{
          slug: "binary-search",
          name: "Binary Search",
          description: "Repeatedly halve a sorted search space.",
          category: "Searching",
          difficulty: "Easy",
          timeComplexity: "O(log n)",
        }}
      />,
    );

    expect(screen.getByRole("heading", { name: "Binary Search" })).toBeInTheDocument();
    expect(screen.getByText("Easy")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /visualize/i })).toHaveAttribute(
      "href",
      "/algorithms/binary-search",
    );
  });
});
