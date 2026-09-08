import { create } from "zustand";

import type { AlgorithmEvent } from "@/features/visualization/events";
import type { AlgorithmModule } from "@/features/visualization/modules/types";
import { transition, type PlayerStatus } from "@/features/visualization/player/state-machine";

export const playbackSpeeds = [400, 250, 150, 80, 40, 15] as const;
export type PlaybackSpeed = (typeof playbackSpeeds)[number];
export type { PlayerStatus } from "@/features/visualization/player/state-machine";

export interface EngineStore {
  sessionId: string;
  slug: string | null;
  module: AlgorithmModule | null;
  events: AlgorithmEvent[];
  currentStep: number;
  status: PlayerStatus;
  speed: PlaybackSpeed;
  visualizationState: unknown;
  load(module: AlgorithmModule, input: unknown): void;
  play(): void;
  pause(): void;
  next(): void;
  prev(): void;
  reset(): void;
  seek(index: number): void;
  stepEnd(): void;
  setSpeed(speed: PlaybackSpeed): void;
}

let sessionCount = 0;

function createSessionId() {
  sessionCount += 1;
  return `visualization-session-${sessionCount}`;
}

export const useEngineStore = create<EngineStore>()((set) => ({
  sessionId: "",
  slug: null,
  module: null,
  events: [],
  currentStep: 0,
  status: "idle",
  speed: 150,
  visualizationState: null,
  load: (module, input) => {
    const events = module.run(input);
    set({
      sessionId: createSessionId(),
      slug: module.slug,
      module,
      events,
      currentStep: 0,
      status: "idle",
      visualizationState: input,
    });
  },
  play: () => set((state) => transition(state, { type: "play" }, state.events.length)),
  pause: () => set((state) => transition(state, { type: "pause" }, state.events.length)),
  next: () => set((state) => transition(state, { type: "next" }, state.events.length)),
  prev: () => set((state) => transition(state, { type: "prev" }, state.events.length)),
  reset: () => set((state) => transition(state, { type: "reset" }, state.events.length)),
  seek: (index) => set((state) => transition(state, { type: "seek", index }, state.events.length)),
  stepEnd: () => set((state) => transition(state, { type: "stepEnd" }, state.events.length)),
  setSpeed: (speed) => {
    if (!playbackSpeeds.includes(speed)) throw new RangeError("Unsupported playback speed.");
    set({ speed });
  },
}));

export const useEngineStatus = () => useEngineStore((state) => state.status);
export const useCurrentStep = () => useEngineStore((state) => state.currentStep);
export const useEvents = () => useEngineStore((state) => state.events);
