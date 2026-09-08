import Link from "next/link";

import type { AlgorithmSummary } from "@/features/algorithms/mock-data";

const difficultyStyles = {
  Easy: "bg-success/15 text-success",
  Medium: "bg-warning/15 text-warning",
  Hard: "bg-danger/15 text-danger",
} as const;

export function AlgorithmCard({ algorithm }: { algorithm: AlgorithmSummary }) {
  return (
    <article className="flex min-h-56 flex-col rounded-lg border border-border bg-surface-raised p-5 transition-colors hover:bg-surface-hover">
      <div className="flex items-start justify-between gap-4">
        <p className="text-sm font-medium text-accent-strong">{algorithm.category}</p>
        <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${difficultyStyles[algorithm.difficulty]}`}>
          {algorithm.difficulty}
        </span>
      </div>
      <h2 className="mt-5 text-xl font-semibold text-foreground">{algorithm.name}</h2>
      <p className="mt-3 text-sm leading-6 text-text-muted">{algorithm.description}</p>
      <div className="mt-auto flex items-end justify-between gap-4 border-t border-border pt-5">
        <div>
          <p className="text-xs text-text-subtle">Average time</p>
          <p className="mt-1 font-mono text-sm text-foreground">{algorithm.timeComplexity}</p>
        </div>
        <Link
          className="rounded-md px-2 py-1 text-sm font-semibold text-accent-strong hover:bg-surface focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
          href={`/algorithms/${algorithm.slug}`}
        >
          Visualize
          <span aria-hidden="true"> →</span>
        </Link>
      </div>
    </article>
  );
}
