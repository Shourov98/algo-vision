import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CurrentStepPanel } from "@/components/visualization/current-step-panel";

describe("CurrentStepPanel", () => {
  it("renders one-based progress, an explanation, and simple metadata", () => {
    render(
      <CurrentStepPanel
        currentStep={2}
        message="Comparing 4 and 8."
        metadata={{ comparisons: 3, stable: true }}
        totalSteps={12}
      />,
    );
    expect(screen.getByText("Step 3 of 12")).toBeInTheDocument();
    expect(screen.getByText("Comparing 4 and 8.")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("true")).toBeInTheDocument();
  });

  it("has a useful empty-session state", () => {
    render(<CurrentStepPanel currentStep={0} totalSteps={0} />);
    expect(screen.getByText("Ready")).toBeInTheDocument();
    expect(screen.getByText("Choose Play or Next to begin the visualization.")).toBeInTheDocument();
  });
});
