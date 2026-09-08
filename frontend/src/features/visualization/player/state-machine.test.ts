import { describe, expect, it } from "vitest";

import { transition } from "@/features/visualization/player/state-machine";

describe("player transition", () => {
  it("enters and advances a loaded session", () => {
    expect(transition({ currentStep: 0, status: "idle" }, { type: "play" }, 3)).toEqual({
      currentStep: 0,
      status: "playing",
    });
    expect(transition({ currentStep: 0, status: "idle" }, { type: "next" }, 3)).toEqual({
      currentStep: 0,
      status: "paused",
    });
    expect(transition({ currentStep: 1, status: "paused" }, { type: "next" }, 3)).toEqual({
      currentStep: 2,
      status: "complete",
    });
  });

  it("preserves player boundaries and reset behavior", () => {
    expect(transition({ currentStep: 0, status: "paused" }, { type: "prev" }, 3)).toEqual({
      currentStep: 0,
      status: "idle",
    });
    expect(transition({ currentStep: 2, status: "complete" }, { type: "play" }, 3)).toEqual({
      currentStep: 2,
      status: "complete",
    });
    expect(transition({ currentStep: 2, status: "complete" }, { type: "reset" }, 3)).toEqual({
      currentStep: 0,
      status: "idle",
    });
  });

  it("clamps seeks and keeps autoplay running when applicable", () => {
    expect(
      transition({ currentStep: 1, status: "playing" }, { type: "seek", index: 99 }, 3),
    ).toEqual({ currentStep: 2, status: "playing" });
    expect(
      transition({ currentStep: 1, status: "paused" }, { type: "seek", index: -1 }, 3),
    ).toEqual({ currentStep: 0, status: "paused" });
  });
});
