import Link from "next/link";
import { notFound } from "next/navigation";

import { problems } from "@/features/problems/mock-data";

export default async function ProblemDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const problem = problems.find((item) => item.slug === slug);
  if (!problem) notFound();

  return (
    <article className="mx-auto w-full max-w-3xl px-6 py-12 lg:py-16">
      <Link className="text-sm font-semibold text-accent-strong hover:underline" href="/problems">
        ← All problems
      </Link>
      <p className="mt-8 text-sm font-semibold text-text-muted">
        {problem.topic} · {problem.difficulty}
      </p>
      <h1 className="mt-3 text-4xl font-semibold tracking-tight text-foreground">
        {problem.title}
      </h1>
      <p className="mt-6 text-lg leading-8 text-text-muted">{problem.description}</p>
      <section className="mt-10 rounded-lg border border-border bg-surface-raised p-6">
        <h2 className="text-xl font-semibold text-foreground">Approach</h2>
        <p className="mt-3 leading-7 text-text-muted">
          Break the problem into small, observable decisions. The visualization shows how each input
          changes the algorithm state.
        </p>
        <Link
          className="mt-6 inline-flex rounded-md bg-accent-strong px-4 py-2 font-semibold text-surface hover:opacity-90"
          href={`/problems/${problem.slug}/visualize`}
        >
          Visualize solution <span aria-hidden="true">→</span>
        </Link>
      </section>
    </article>
  );
}
