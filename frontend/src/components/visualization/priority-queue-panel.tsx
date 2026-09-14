export interface PriorityQueueEntry {
  id: string;
  priority: number;
  label?: string;
}
export function PriorityQueuePanel({ entries }: { entries: PriorityQueueEntry[] }) {
  const ordered = [...entries].sort((a, b) => a.priority - b.priority || a.id.localeCompare(b.id));
  return (
    <section aria-label="Priority queue" className="rounded-lg border border-border bg-surface p-4">
      <h2 className="font-semibold text-foreground">Priority queue</h2>
      <ol className="mt-3 space-y-2 font-mono text-sm">
        {ordered.length ? (
          ordered.map((entry) => (
            <li className="flex justify-between text-text-muted" key={entry.id}>
              <span>{entry.label ?? entry.id}</span>
              <span>{entry.priority}</span>
            </li>
          ))
        ) : (
          <li className="text-text-subtle">Empty</li>
        )}
      </ol>
    </section>
  );
}
