import { render } from "@testing-library/react";
import axe from "axe-core";
import { describe, expect, it } from "vitest";

import { Header } from "@/components/layout/header";
import { SettingsContent } from "@/components/settings/settings-content";
import { ArrayInputPanel } from "@/components/visualization/array-input-panel";
import { ArrayVisualization } from "@/components/visualization/array-visualization";
import { VisualizationControls } from "@/components/visualization/visualization-controls";
import { ArrayAdapter } from "@/features/visualization/adapters/array-adapter";
import { binarySearchModule } from "@/features/visualization/modules/binary-search";

async function expectNoViolations(container: HTMLElement) {
  const result = await axe.run(container);
  expect(result.violations).toEqual([]);
}

describe("accessibility", () => {
  it("audits primary navigation", async () => {
    const { container } = render(<Header />);
    await expectNoViolations(container);
  });
  it("audits visualization controls", async () => {
    const { container } = render(
      <VisualizationControls
        canNext
        canPrev
        currentStep={0}
        onNext={() => undefined}
        onPause={() => undefined}
        onPlay={() => undefined}
        onPrev={() => undefined}
        onReset={() => undefined}
        onSeek={() => undefined}
        onSpeedChange={() => undefined}
        speed={700}
        status="paused"
        totalSteps={4}
      />,
    );
    await expectNoViolations(container);
  });
  it("audits settings controls", async () => {
    const { container } = render(<SettingsContent />);
    await expectNoViolations(container);
  });
  it("audits the pending Binary Search input workflow", async () => {
    const { container } = render(
      <ArrayInputPanel
        capabilities={binarySearchModule.capabilities}
        configuration={{ direction: "ascending", target: 7, values: [5, 1, 7] }}
        hasPendingChanges
        onChange={() => undefined}
        onSortAndStart={() => undefined}
        onStart={() => undefined}
      />,
    );
    await expectNoViolations(container);
  });
  it("audits Binary Search range labels and excluded values", async () => {
    const initial = ArrayAdapter.createInitialState([1, 3, 5], ["first", "second", "third"]);
    const state = ArrayAdapter.reduce(initial, {
      activeIds: ["second", "third"],
      direction: "ascending",
      eliminatedIds: ["first"],
      highId: "third",
      id: "range-1",
      lowId: "second",
      message: "Search indexes 1 through 2.",
      middleId: "second",
      t: 0,
      target: 5,
      type: "search-range",
    });
    const { container } = render(
      <ArrayVisualization runValues={[1, 3, 5]} state={state} stepDuration={700} />,
    );
    await expectNoViolations(container);
  });
});
