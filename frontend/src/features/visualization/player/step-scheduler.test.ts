import { afterEach, describe, expect, it, vi } from "vitest";

import { StepScheduler } from "@/features/visualization/player/step-scheduler";

describe("StepScheduler", () => {
  afterEach(() => vi.useRealTimers());

  it("uses one timeout at a time and continues while requested", () => {
    vi.useFakeTimers();
    const onStep = vi.fn();
    const scheduler = new StepScheduler({
      getDelay: () => 150,
      onStep,
      shouldContinue: () => onStep.mock.calls.length < 2,
    });

    scheduler.play();
    scheduler.play();
    vi.advanceTimersByTime(150);
    expect(onStep).toHaveBeenCalledTimes(1);
    vi.advanceTimersByTime(150);
    expect(onStep).toHaveBeenCalledTimes(2);
  });

  it.each(["pause", "seek", "reset"] as const)("cancels a pending timer on %s", (action) => {
    vi.useFakeTimers();
    const onStep = vi.fn();
    const scheduler = new StepScheduler({
      getDelay: () => 150,
      onStep,
      shouldContinue: () => true,
    });

    scheduler.play();
    scheduler[action]();
    vi.advanceTimersByTime(150);
    expect(onStep).not.toHaveBeenCalled();
  });
});
