import type { VisualizationAdapter } from "@/features/visualization/adapters/types";

export interface VisualizationCanvasProps {
  adapterKind: VisualizationAdapter<unknown>["kind"];
  state: unknown;
}

export function VisualizationCanvas({ adapterKind, state }: VisualizationCanvasProps) {
  return (
    <section
      aria-label={`${adapterKind} visualization canvas`}
      className="min-h-72 rounded-lg border border-border bg-surface-raised p-6"
      data-adapter-kind={adapterKind}
    >
      {state === null ? (
        <p className="text-text-subtle">Load an algorithm to begin visualizing.</p>
      ) : (
        <p className="text-text-muted">{adapterKind} visualization state is ready.</p>
      )}
    </section>
  );
}
