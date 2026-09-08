import Link from "next/link";

import { SortingPreview } from "@/components/home/sorting-preview";

export default function Home() {
  return (
    <div className="overflow-hidden">
      <section className="mx-auto grid max-w-7xl gap-12 px-6 py-20 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:px-8 lg:py-28">
        <div className="max-w-2xl">
          <p className="mb-5 text-sm font-semibold tracking-[0.18em] text-accent-strong uppercase">
            Learn by seeing every step
          </p>
          <h1 className="text-4xl font-semibold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
            Make algorithms click.
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-8 text-text-muted">
            Explore interactive visualizations that turn complex algorithmic ideas into clear,
            memorable steps.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link
              className="inline-flex min-h-11 items-center justify-center rounded-md bg-accent-strong px-5 font-semibold text-surface transition-opacity hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
              href="/algorithms"
            >
              Explore algorithms
            </Link>
            <Link
              className="inline-flex min-h-11 items-center justify-center rounded-md border border-border bg-surface-raised px-5 font-semibold text-foreground transition-colors hover:bg-surface-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
              href="/problems"
            >
              Practice a problem
            </Link>
          </div>
        </div>

        <SortingPreview />
      </section>
    </div>
  );
}
