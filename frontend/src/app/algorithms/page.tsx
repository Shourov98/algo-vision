import Link from "next/link";

import { AlgorithmCard } from "@/components/algorithms/algorithm-card";
import {
  algorithmCategories,
  algorithms,
  type AlgorithmCategory,
  type AlgorithmDifficulty,
} from "@/features/algorithms/mock-data";

type ExplorerSearchParams = Promise<{ category?: string; difficulty?: string; q?: string }>;

function buildExplorerHref(params: {
  category?: string | undefined;
  difficulty?: string | undefined;
  q?: string | undefined;
}) {
  const search = new URLSearchParams();
  if (params.category && params.category !== "All") search.set("category", params.category);
  if (params.difficulty && params.difficulty !== "All") search.set("difficulty", params.difficulty);
  if (params.q) search.set("q", params.q);
  const query = search.toString();
  return query ? `/algorithms?${query}` : "/algorithms";
}

export default async function AlgorithmsPage({
  searchParams,
}: {
  searchParams: ExplorerSearchParams;
}) {
  const params = await searchParams;
  const category = algorithmCategories.includes(
    params.category as (typeof algorithmCategories)[number],
  )
    ? (params.category as "All" | AlgorithmCategory)
    : "All";
  const difficulty = ["All", "Easy", "Medium", "Hard"].includes(params.difficulty ?? "")
    ? (params.difficulty as "All" | AlgorithmDifficulty)
    : "All";
  const query = params.q?.trim().toLowerCase() ?? "";
  const visibleAlgorithms = algorithms.filter(
    (algorithm) =>
      (category === "All" || algorithm.category === category) &&
      (difficulty === "All" || algorithm.difficulty === difficulty) &&
      (!query ||
        `${algorithm.name} ${algorithm.description} ${algorithm.category}`
          .toLowerCase()
          .includes(query)),
  );

  return (
    <div className="mx-auto w-full max-w-7xl px-6 py-12 lg:px-8 lg:py-16">
      <div className="max-w-2xl">
        <p className="text-sm font-semibold tracking-[0.18em] text-accent-strong uppercase">
          Algorithm explorer
        </p>
        <h1 className="mt-4 text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
          Learn one step at a time.
        </h1>
        <p className="mt-5 text-lg leading-8 text-text-muted">
          Choose an algorithm, follow its decisions, and build intuition through visual
          explanations.
        </p>
      </div>

      <div className="mt-12 grid gap-8 lg:grid-cols-[13rem_1fr]">
        <aside aria-label="Algorithm filters" className="lg:border-r lg:border-border lg:pr-8">
          <h2 className="text-sm font-semibold text-foreground">Topics</h2>
          <nav
            className="mt-3 flex gap-2 overflow-x-auto pb-2 lg:flex-col"
            aria-label="Algorithm categories"
          >
            {algorithmCategories.map((item) => {
              const active = item === category;
              return (
                <Link
                  className={`shrink-0 rounded-md px-3 py-2 text-sm font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring ${active ? "bg-accent-strong text-surface" : "text-text-muted hover:bg-surface-raised hover:text-foreground"}`}
                  href={buildExplorerHref({ category: item, difficulty, q: params.q })}
                  key={item}
                >
                  {item}
                </Link>
              );
            })}
          </nav>
        </aside>

        <section aria-labelledby="algorithm-results">
          <form className="grid gap-3 sm:grid-cols-[1fr_10rem]" action="/algorithms">
            <input type="hidden" name="category" value={category === "All" ? "" : category} />
            <label className="sr-only" htmlFor="algorithm-search">
              Search algorithms
            </label>
            <input
              className="h-11 rounded-md border border-border bg-surface-raised px-3 text-foreground placeholder:text-text-subtle focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
              defaultValue={params.q}
              id="algorithm-search"
              name="q"
              placeholder="Search algorithms"
              type="search"
            />
            <label className="sr-only" htmlFor="difficulty">
              Difficulty
            </label>
            <select
              className="h-11 rounded-md border border-border bg-surface-raised px-3 text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
              defaultValue={difficulty}
              id="difficulty"
              name="difficulty"
            >
              <option value="All">All difficulties</option>
              <option value="Easy">Easy</option>
              <option value="Medium">Medium</option>
              <option value="Hard">Hard</option>
            </select>
          </form>

          <div className="mt-8 flex items-baseline justify-between gap-4">
            <h2 id="algorithm-results" className="text-xl font-semibold text-foreground">
              Algorithms
            </h2>
            <p className="text-sm text-text-subtle">{visibleAlgorithms.length} available</p>
          </div>
          {visibleAlgorithms.length ? (
            <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {visibleAlgorithms.map((algorithm) => (
                <AlgorithmCard algorithm={algorithm} key={algorithm.slug} />
              ))}
            </div>
          ) : (
            <div className="mt-5 rounded-lg border border-border bg-surface-raised p-8 text-center">
              <p className="font-semibold text-foreground">No algorithms found</p>
              <p className="mt-2 text-sm text-text-muted">
                Try a different search or remove a filter.
              </p>
              <Link
                className="mt-4 inline-block text-sm font-semibold text-accent-strong hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
                href="/algorithms"
              >
                Clear filters
              </Link>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
