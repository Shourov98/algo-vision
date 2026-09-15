"use client";

import { useLayoutEffect, useRef } from "react";

import type { ArrayState } from "@/features/visualization/adapters/array-adapter";
import type { AlgorithmEvent, MarkStatus } from "@/features/visualization/events";

const statusStyles: Record<MarkStatus, string> = {
  idle: "border-slate-600 bg-slate-700 text-slate-100",
  active: "border-sky-300 bg-sky-500 text-slate-950",
  comparing: "border-amber-200 bg-amber-400 text-slate-950",
  swapping: "border-fuchsia-200 bg-fuchsia-500 text-white",
  sorted: "border-emerald-200 bg-emerald-500 text-slate-950",
  pivot: "border-violet-200 bg-violet-500 text-white",
  visited: "border-cyan-200 bg-cyan-500 text-slate-950",
  frontier: "border-orange-200 bg-orange-500 text-slate-950",
  current: "border-blue-200 bg-blue-500 text-white",
  target: "border-rose-200 bg-rose-500 text-white",
  found: "border-lime-200 bg-lime-500 text-slate-950",
};

const legend: Array<{ label: string; status: MarkStatus }> = [
  { label: "Comparing", status: "comparing" },
  { label: "Moving", status: "active" },
  { label: "Swapping", status: "swapping" },
  { label: "Sorted", status: "sorted" },
  { label: "Pivot", status: "pivot" },
];

function highlightedIds(event?: AlgorithmEvent) {
  if (!event) return [];
  if ("ids" in event) return event.ids;
  if ("elementId" in event) return [event.elementId];
  return [];
}

function barHeight(value: unknown, min: number, range: number) {
  if (typeof value !== "number") return 72;
  return 46 + Math.round(((value - min) / range) * 128);
}

export function ArrayVisualization({
  currentEvent,
  state,
  stepDuration,
}: {
  currentEvent?: AlgorithmEvent;
  state: ArrayState;
  stepDuration: number;
}) {
  const numericValues = state.items
    .map((item) => item.value)
    .filter((value): value is number => typeof value === "number");
  const min = numericValues.length ? Math.min(...numericValues) : 0;
  const max = numericValues.length ? Math.max(...numericValues) : 1;
  const range = Math.max(max - min, 1);
  const activeIds = highlightedIds(currentEvent);
  const barRefs = useRef(new Map<string, HTMLDivElement>());
  const previousPositions = useRef(new Map<string, DOMRect>());
  const leftIds =
    currentEvent?.type === "select" && currentEvent.leftIds ? currentEvent.leftIds : [];
  const rightIds =
    currentEvent?.type === "select" && currentEvent.rightIds ? currentEvent.rightIds : [];

  useLayoutEffect(() => {
    const nextPositions = new Map<string, DOMRect>();
    const animationDuration = Math.min(Math.max(Math.round(stepDuration * 0.8), 260), 900);

    for (const item of state.items) {
      const bar = barRefs.current.get(item.id);
      if (!bar) continue;
      const nextPosition = bar.getBoundingClientRect();
      const previousPosition = previousPositions.current.get(item.id);
      if (previousPosition) {
        const translateX = previousPosition.left - nextPosition.left;
        const translateY = previousPosition.top - nextPosition.top;
        if (translateX || translateY) {
          bar.animate(
            [
              { transform: `translate(${translateX}px, ${translateY}px)` },
              { transform: "translate(0, 0)" },
            ],
            { duration: animationDuration, easing: "cubic-bezier(0.22, 1, 0.36, 1)" },
          );
        }
      }
      nextPositions.set(item.id, nextPosition);
    }
    previousPositions.current = nextPositions;
  }, [state.items, stepDuration]);

  return (
    <section
      aria-label="Array visualization"
      className="rounded-xl border border-border bg-surface-raised p-5 shadow-sm"
    >
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-foreground">Live array</p>
          <p className="text-sm text-text-muted">
            Each bar is one value in the current order. Moved values glide into their new position.
          </p>
        </div>
        <div aria-label="Visualization legend" className="flex flex-wrap gap-2 text-xs">
          {legend.map(({ label, status }) => (
            <span
              className="inline-flex items-center gap-1.5 rounded-full border border-border px-2 py-1 text-text-muted"
              key={status}
            >
              <i aria-hidden className={`h-2.5 w-2.5 rounded-full ${statusStyles[status]}`} />
              {label}
            </span>
          ))}
        </div>
      </div>
      {leftIds.length || rightIds.length ? (
        <p
          aria-live="polite"
          className="mb-4 rounded-md border border-border bg-surface px-3 py-2 text-sm text-text-muted"
        >
          <span className="font-semibold text-sky-300">Left half</span> and{" "}
          <span className="font-semibold text-violet-300">right half</span> are ready to merge.
        </p>
      ) : null}
      <div className="grid min-h-64 grid-cols-[repeat(auto-fit,minmax(3.5rem,1fr))] items-end gap-3">
        {state.items.map((item, index) => {
          const isActive = activeIds.includes(item.id);
          const isSwap = currentEvent?.type === "swap" && isActive;
          const isLeftHalf = leftIds.includes(item.id);
          const isRightHalf = rightIds.includes(item.id);
          const statusStyle = isLeftHalf
            ? "border-sky-200 bg-sky-500 text-slate-950"
            : isRightHalf
              ? "border-violet-200 bg-violet-500 text-white"
              : statusStyles[item.status];
          return (
            <div
              className="flex min-w-0 flex-col items-center gap-2"
              key={item.id}
              ref={(element) => {
                if (element) barRefs.current.set(item.id, element);
                else barRefs.current.delete(item.id);
              }}
            >
              <span className="font-mono text-xs text-text-subtle">{index}</span>
              <div className="flex h-48 w-full items-end rounded-lg bg-surface p-1.5">
                <div
                  aria-label={`Value ${String(item.value)} at index ${index}${isActive ? ", active" : ""}`}
                  className={`flex w-full items-start justify-center rounded-md border pt-2 font-mono text-sm font-bold shadow-sm transition-[height,background-color,border-color,box-shadow] duration-300 ease-out ${statusStyle} ${isSwap ? "ring-4 ring-fuchsia-300/40" : ""} ${isActive && !isSwap ? "ring-2 ring-white/40" : ""}`}
                  style={{ height: `${barHeight(item.value, min, range)}px` }}
                >
                  {String(item.value)}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
