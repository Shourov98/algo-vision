const bars = [
  { height: "h-20", value: 32, state: "default" },
  { height: "h-36", value: 64, state: "active" },
  { height: "h-28", value: 48, state: "default" },
  { height: "h-48", value: 91, state: "active" },
  { height: "h-24", value: 40, state: "default" },
  { height: "h-40", value: 72, state: "default" },
] as const;

export function SortingPreview() {
  return (
    <section
      aria-label="Sorting visualization preview"
      className="rounded-lg border border-border bg-surface-raised p-5 shadow-[var(--shadow-card)] sm:p-7"
    >
      <div className="flex items-start justify-between gap-4 border-b border-border pb-5">
        <div>
          <p className="text-sm font-semibold text-foreground">Bubble sort</p>
          <p className="mt-1 text-sm text-text-subtle">Comparing adjacent values</p>
        </div>
        <span className="rounded-full bg-success/15 px-3 py-1 text-xs font-semibold text-success">
          Step 4 of 12
        </span>
      </div>

      <div className="mt-8 flex h-56 items-end justify-between gap-2 sm:gap-3" aria-hidden="true">
        {bars.map((bar, index) => (
          <div key={bar.value} className="flex flex-1 flex-col items-center gap-3">
            <div
              className={`w-full max-w-12 rounded-t-md ${bar.height} ${bar.state === "active" ? "bg-accent-strong" : "bg-surface-hover"}`}
            />
            <span className="text-xs font-medium text-text-subtle">{index + 1}</span>
          </div>
        ))}
      </div>

      <div className="mt-6 grid grid-cols-2 gap-3 border-t border-border pt-5 text-sm">
        <p className="text-text-subtle">Comparing</p>
        <p className="text-right font-mono text-foreground">64 &lt; 91</p>
      </div>
    </section>
  );
}
