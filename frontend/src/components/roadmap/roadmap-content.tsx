"use client";
import { useRoadmap } from "@/lib/api/roadmap";
export function RoadmapContent() {
  const { data, error, isLoading } = useRoadmap();
  if (isLoading)
    return (
      <p aria-live="polite" className="text-text-muted">
        Loading your roadmap…
      </p>
    );
  if (error)
    return (
      <p className="rounded-lg border border-danger/40 bg-danger/10 p-4 text-danger">
        Unable to load your roadmap. Please try again.
      </p>
    );
  if (!data?.length)
    return (
      <p className="rounded-lg border border-border bg-surface-raised p-6 text-text-muted">
        Your personalized roadmap will appear here soon.
      </p>
    );
  return (
    <ol className="space-y-5">
      {[...data]
        .sort((a, b) => a.sort_order - b.sort_order)
        .map((stage) => (
          <li className="rounded-lg border border-border bg-surface-raised p-6" key={stage.id}>
            <h2 className="text-xl font-semibold text-foreground">{stage.title}</h2>
            {stage.description ? <p className="mt-2 text-text-muted">{stage.description}</p> : null}
            <ul className="mt-4 space-y-2">
              {stage.items.map((item) => (
                <li
                  className="flex justify-between rounded-md bg-surface px-3 py-2 text-sm"
                  key={item.id}
                >
                  <span className="text-foreground">{item.title ?? item.item_type}</span>
                  <span className="text-text-subtle">{item.status ?? "Not started"}</span>
                </li>
              ))}
            </ul>
          </li>
        ))}
    </ol>
  );
}
