import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { VisualizationControls } from "@/components/visualization/visualization-controls";

describe("VisualizationControls", () => {
  it("calls playback handlers from accessible controls", () => {
    const onPlay = vi.fn();
    const onNext = vi.fn();
    const onSpeedChange = vi.fn();
    render(
      <VisualizationControls
        canNext
        canPrev={false}
        currentStep={0}
        onNext={onNext}
        onPause={vi.fn()}
        onPlay={onPlay}
        onPrev={vi.fn()}
        onReset={vi.fn()}
        onSeek={vi.fn()}
        onSpeedChange={onSpeedChange}
        speed={700}
        status="paused"
        totalSteps={4}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Play" }));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    fireEvent.change(screen.getByLabelText("Playback speed"), { target: { value: "200" } });
    expect(onPlay).toHaveBeenCalledOnce();
    expect(onNext).toHaveBeenCalledOnce();
    expect(onSpeedChange).toHaveBeenCalledWith(200);
  });

  it("supports documented keyboard shortcuts", () => {
    const onPlay = vi.fn();
    const onNext = vi.fn();
    const onPrev = vi.fn();
    const onReset = vi.fn();
    render(
      <VisualizationControls
        canNext
        canPrev
        currentStep={0}
        onNext={onNext}
        onPause={vi.fn()}
        onPlay={onPlay}
        onPrev={onPrev}
        onReset={onReset}
        onSeek={vi.fn()}
        onSpeedChange={vi.fn()}
        speed={700}
        status="paused"
        totalSteps={4}
      />,
    );
    fireEvent.keyDown(window, { key: " " });
    fireEvent.keyDown(window, { key: "ArrowLeft" });
    fireEvent.keyDown(window, { key: "ArrowRight" });
    fireEvent.keyDown(window, { key: "r" });
    expect(onPlay).toHaveBeenCalled();
    expect(onPrev).toHaveBeenCalled();
    expect(onNext).toHaveBeenCalled();
    expect(onReset).toHaveBeenCalled();
  });
});
