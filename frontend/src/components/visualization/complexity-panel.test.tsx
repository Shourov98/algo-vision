import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ComplexityPanel } from "@/components/visualization/complexity-panel";

describe("ComplexityPanel", () => {
  it("renders supplied complexity values with their labels", () => {
    render(
      <ComplexityPanel complexity={{ average: "O(n log n)", space: "O(n)", worst: "O(n²)" }} />,
    );
    expect(screen.getByText("Average time")).toBeInTheDocument();
    expect(screen.getByText("O(n log n)")).toBeInTheDocument();
    expect(screen.getByText("Space")).toBeInTheDocument();
  });

  it("renders a fallback when no complexity values exist", () => {
    render(<ComplexityPanel />);
    expect(
      screen.getByText("Complexity details are not available for this algorithm."),
    ).toBeInTheDocument();
  });
});
