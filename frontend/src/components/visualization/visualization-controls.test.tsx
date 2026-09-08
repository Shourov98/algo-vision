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
        onNext={onNext}
        onPause={vi.fn()}
        onPlay={onPlay}
        onPrev={vi.fn()}
        onReset={vi.fn()}
        onSeek={vi.fn()}
        onSpeedChange={onSpeedChange}
        speed={150}
        status="paused"
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Play" }));
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    fireEvent.change(screen.getByLabelText("Playback speed"), { target: { value: "80" } });
    expect(onPlay).toHaveBeenCalledOnce();
    expect(onNext).toHaveBeenCalledOnce();
    expect(onSpeedChange).toHaveBeenCalledWith(80);
  });
});
