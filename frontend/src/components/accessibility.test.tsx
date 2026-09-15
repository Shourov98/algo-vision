import { render } from "@testing-library/react";
import axe from "axe-core";
import { describe, expect, it } from "vitest";

import { Header } from "@/components/layout/header";
import { SettingsContent } from "@/components/settings/settings-content";
import { VisualizationControls } from "@/components/visualization/visualization-controls";

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
});
