"use client";

import dynamic from "next/dynamic";

export const DeferredAlgorithmVisualizer = dynamic(
  () =>
    import("@/components/visualization/algorithm-visualizer").then(
      (module) => module.AlgorithmVisualizer,
    ),
  {
    loading: () => (
      <p className="rounded-lg border border-border bg-surface-raised p-6 text-text-muted">
        Loading visualization…
      </p>
    ),
  },
);
