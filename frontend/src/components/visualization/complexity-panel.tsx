import type { AlgorithmMeta } from "@/features/visualization/modules/types";

export interface ComplexityPanelProps {
  complexity?: AlgorithmMeta["complexity"];
}

const labels = {
  best: "Best time",
  average: "Average time",
  worst: "Worst time",
  space: "Space",
} as const;

export function ComplexityPanel({ complexity }: ComplexityPanelProps) {
  const entries = Object.entries(complexity ?? {}).filter(
    (entry): entry is [keyof typeof labels, string] => typeof entry[1] === "string",
  );

  return (
    <section
      aria-labelledby="complexity-title"
      className="rounded-lg border border-border bg-surface-raised p-5"
    >
      <h2 id="complexity-title" className="font-semibold text-foreground">
        Complexity
      </h2>
      {entries.length ? (
        <dl className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {entries.map(([key, value]) => (
            <div key={key}>
              <dt className="text-sm text-text-subtle">{labels[key]}</dt>
              <dd className="mt-1 font-mono text-lg text-accent-strong">{value}</dd>
            </div>
          ))}
        </dl>
      ) : (
        <p className="mt-3 text-sm text-text-muted">
          Complexity details are not available for this algorithm.
        </p>
      )}
    </section>
  );
}
