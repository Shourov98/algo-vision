"use client";

import type { PlayerStatus } from "@/features/visualization/player/state-machine";
import { playbackSpeeds } from "@/stores/engine-store";

export interface VisualizationControlsProps {
  status: PlayerStatus;
  canPrev: boolean;
  canNext: boolean;
  speed: number;
  onPlay(): void;
  onPause(): void;
  onNext(): void;
  onPrev(): void;
  onReset(): void;
  onSeek(index: number): void;
  onSpeedChange(milliseconds: number): void;
}

export function VisualizationControls(props: VisualizationControlsProps) {
  const playing = props.status === "playing";
  return (
    <section
      aria-label="Visualization controls"
      className="flex flex-wrap items-center gap-3 rounded-lg border border-border bg-surface-raised p-4"
    >
      <button
        className="rounded-md bg-accent-strong px-3 py-2 font-semibold text-surface"
        onClick={playing ? props.onPause : props.onPlay}
        type="button"
      >
        {playing ? "Pause" : "Play"}
      </button>
      <button
        className="rounded-md border border-border px-3 py-2 disabled:opacity-50"
        disabled={!props.canPrev}
        onClick={props.onPrev}
        type="button"
      >
        Previous
      </button>
      <button
        className="rounded-md border border-border px-3 py-2 disabled:opacity-50"
        disabled={!props.canNext}
        onClick={props.onNext}
        type="button"
      >
        Next
      </button>
      <button
        className="rounded-md border border-border px-3 py-2"
        onClick={props.onReset}
        type="button"
      >
        Reset
      </button>
      <label className="ml-auto text-sm text-text-muted">
        Speed
        <select
          aria-label="Playback speed"
          className="ml-2 rounded-md border border-border bg-surface px-2 py-2 text-foreground"
          onChange={(event) => props.onSpeedChange(Number(event.target.value))}
          value={props.speed}
        >
          {playbackSpeeds.map((speed) => (
            <option key={speed} value={speed}>
              {speed} ms
            </option>
          ))}
        </select>
      </label>
    </section>
  );
}
