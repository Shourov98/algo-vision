export interface CurrentStepPanelProps {
  currentStep: number;
  totalSteps: number;
  message?: string;
  metadata?: Record<string, unknown>;
}

function formatMetadata(value: unknown) {
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean")
    return String(value);
  return null;
}

export function CurrentStepPanel({
  currentStep,
  totalSteps,
  message,
  metadata,
}: CurrentStepPanelProps) {
  const hasSteps = totalSteps > 0;
  const step = hasSteps ? Math.min(Math.max(currentStep + 1, 1), totalSteps) : 0;
  const entries = Object.entries(metadata ?? {}).flatMap(([key, value]) => {
    const formatted = formatMetadata(value);
    return formatted === null ? [] : ([[key, formatted]] as const);
  });

  return (
    <section
      aria-live="polite"
      aria-labelledby="current-step-title"
      className="rounded-lg border border-border bg-surface-raised p-5"
    >
      <div className="flex items-baseline justify-between gap-4">
        <h2 id="current-step-title" className="font-semibold text-foreground">
          Current step
        </h2>
        <p className="font-mono text-sm text-accent-strong">
          {hasSteps ? `Step ${step} of ${totalSteps}` : "Ready"}
        </p>
      </div>
      <p className="mt-4 text-text-muted">
        {message ?? "Choose Play or Next to begin the visualization."}
      </p>
      {entries.length ? (
        <dl className="mt-4 grid gap-3 border-t border-border pt-4 sm:grid-cols-2">
          {entries.map(([key, value]) => (
            <div key={key}>
              <dt className="text-xs font-medium tracking-wide text-text-subtle uppercase">
                {key}
              </dt>
              <dd className="mt-1 font-mono text-sm text-foreground">{value}</dd>
            </div>
          ))}
        </dl>
      ) : null}
    </section>
  );
}
