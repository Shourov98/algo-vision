"use client";
import { useDashboard } from "@/lib/api/dashboard";
const cards = [
  { key: "algorithms_learned", label: "Algorithms learned" },
  { key: "problems_solved", label: "Problems solved" },
  { key: "current_streak", label: "Current streak" },
  { key: "interview_readiness", label: "Interview readiness" },
] as const;
export function DashboardContent() {
  const { data, error, isLoading } = useDashboard();
  if (isLoading)
    return (
      <p aria-live="polite" className="text-text-muted">
        Loading your dashboard…
      </p>
    );
  if (error || !data)
    return (
      <p className="rounded-lg border border-danger/40 bg-danger/10 p-4 text-danger">
        Unable to load your dashboard. Please try again.
      </p>
    );
  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <section className="rounded-lg border border-border bg-surface-raised p-5" key={card.key}>
            <p className="text-sm text-text-muted">{card.label}</p>
            <p className="mt-3 text-3xl font-semibold text-foreground">
              {data[card.key]}
              {card.key === "interview_readiness" ? "%" : ""}
            </p>
            {card.key === "algorithms_learned" ? (
              <p className="mt-2 text-sm text-text-subtle">of {data.algorithms_total} total</p>
            ) : null}
          </section>
        ))}
      </div>
      <section className="mt-6 rounded-lg border border-border bg-surface-raised p-6">
        <h2 className="text-xl font-semibold text-foreground">Keep your momentum</h2>
        <p className="mt-2 text-text-muted">
          Continue an algorithm visualization or practice your next interview problem.
        </p>
      </section>
    </>
  );
}
