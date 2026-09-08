export type PlayerStatus = "idle" | "playing" | "paused" | "seeking" | "complete";

export interface PlayerState {
  currentStep: number;
  status: PlayerStatus;
}

export type PlayerTransition =
  | { type: "play" }
  | { type: "pause" }
  | { type: "next" }
  | { type: "prev" }
  | { type: "reset" }
  | { type: "seek"; index: number }
  | { type: "stepEnd" };

export function transition(
  state: PlayerState,
  event: PlayerTransition,
  totalSteps: number,
): PlayerState {
  if (event.type === "reset" || totalSteps === 0) return { currentStep: 0, status: "idle" };

  const lastStep = totalSteps - 1;
  switch (event.type) {
    case "play":
      return state.status === "complete" ? state : { ...state, status: "playing" };
    case "pause":
      return state.status === "playing" ? { ...state, status: "paused" } : state;
    case "next":
    case "stepEnd": {
      if (state.status === "complete") return state;
      if (state.status === "idle") return { currentStep: 0, status: "paused" };
      const currentStep = Math.min(state.currentStep + 1, lastStep);
      return {
        currentStep,
        status:
          currentStep === lastStep ? "complete" : event.type === "next" ? "paused" : "playing",
      };
    }
    case "prev":
      if (state.currentStep === 0) return { currentStep: 0, status: "idle" };
      return { currentStep: state.currentStep - 1, status: "paused" };
    case "seek": {
      const currentStep = Math.max(0, Math.min(event.index, lastStep));
      return { currentStep, status: state.status === "playing" ? "playing" : "paused" };
    }
  }
}
