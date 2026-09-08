import { describe, expect, it } from "vitest";

import { bubbleSortModule } from "@/features/visualization/modules/bubble-sort";
import { useEngineStore, type PlaybackSpeed } from "@/stores/engine-store";
import { useUIStore } from "@/stores/ui-store";

describe("visualization stores", () => {
  it("loads execution data into the engine store", () => {
    useEngineStore.getState().load(bubbleSortModule, [3, 1]);

    const state = useEngineStore.getState();
    expect(state.slug).toBe("bubble-sort");
    expect(state.module).toBe(bubbleSortModule);
    expect(state.events).toHaveLength(5);
    expect(state.status).toBe("idle");
    expect(state.sessionId).toMatch(/^visualization-session-\d+$/);
  });

  it("keeps UI updates isolated from the engine store", () => {
    const engineState = useEngineStore.getState();
    const initiallyOpen = useUIStore.getState().isCodePanelOpen;

    useUIStore.getState().toggleCodePanel();

    expect(useUIStore.getState().isCodePanelOpen).toBe(!initiallyOpen);
    expect(useEngineStore.getState()).toBe(engineState);
  });

  it("accepts only supported playback speeds", () => {
    useEngineStore.getState().setSpeed(80);
    expect(useEngineStore.getState().speed).toBe(80);
    expect(() => useEngineStore.getState().setSpeed(100 as PlaybackSpeed)).toThrow(RangeError);
  });
});
