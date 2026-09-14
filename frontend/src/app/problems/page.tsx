import Link from "next/link";

import { problems, problemTopics, type ProblemTopic } from "@/features/problems/mock-data";

type SearchParams = Promise<{ difficulty?: string; q?: string; topic?: string }>;
function href(params: { difficulty?: string; q?: string | undefined; topic?: string }) {
  const query = new URLSearchParams();
  if (params.difficulty && params.difficulty !== "All") query.set("difficulty", params.difficulty);
  if (params.topic && params.topic !== "All") query.set("topic", params.topic);
  if (params.q) query.set("q", params.q);
  const value = query.toString();
  return value ? `/problems?${value}` : "/problems";
}
const tone = { Easy: "text-success", Medium: "text-warning", Hard: "text-danger" } as const;
export default async function ProblemsPage({ searchParams }: { searchParams: SearchParams }) {
  const params = await searchParams;
  const topic = problemTopics.includes(params.topic as (typeof problemTopics)[number])
    ? (params.topic as "All" | ProblemTopic)
    : "All";
  const difficulty = ["All", "Easy", "Medium", "Hard"].includes(params.difficulty ?? "")
    ? (params.difficulty as "All" | keyof typeof tone)
    : "All";
  const q = params.q?.trim().toLowerCase() ?? "";
  const visible = problems.filter(
    (problem) =>
      (topic === "All" || problem.topic === topic) &&
      (difficulty === "All" || problem.difficulty === difficulty) &&
      (!q || `${problem.title} ${problem.description} ${problem.topic}`.toLowerCase().includes(q)),
  );
  return (
    <div className="mx-auto w-full max-w-7xl px-6 py-12 lg:px-8 lg:py-16">
      <div className="max-w-2xl">
        <p className="text-sm font-semibold tracking-[0.18em] text-accent-strong uppercase">
          Interview preparation
        </p>
        <h1 className="mt-4 text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
          Practice with purpose.
        </h1>
        <p className="mt-5 text-lg leading-8 text-text-muted">
          Filter problems, read the approach, and visualize each solution.
        </p>
      </div>
      <div className="mt-12 grid gap-8 lg:grid-cols-[13rem_1fr]">
        <aside aria-label="Problem filters" className="lg:border-r lg:border-border lg:pr-8">
          <h2 className="text-sm font-semibold text-foreground">Topics</h2>
          <nav
            aria-label="Problem topics"
            className="mt-3 flex gap-2 overflow-x-auto pb-2 lg:flex-col"
          >
            {problemTopics.map((item) => (
              <Link
                className={`shrink-0 rounded-md px-3 py-2 text-sm font-medium ${item === topic ? "bg-accent-strong text-surface" : "text-text-muted hover:bg-surface-raised hover:text-foreground"}`}
                href={href({ difficulty, q: params.q, topic: item })}
                key={item}
              >
                {item}
              </Link>
            ))}
          </nav>
        </aside>
        <section aria-labelledby="problem-results">
          <form action="/problems" className="grid gap-3 sm:grid-cols-[1fr_10rem]">
            <input name="topic" type="hidden" value={topic === "All" ? "" : topic} />
            <label className="sr-only" htmlFor="problem-search">
              Search problems
            </label>
            <input
              className="h-11 rounded-md border border-border bg-surface-raised px-3 text-foreground"
              defaultValue={params.q}
              id="problem-search"
              name="q"
              placeholder="Search problems"
              type="search"
            />
            <label className="sr-only" htmlFor="problem-difficulty">
              Difficulty
            </label>
            <select
              className="h-11 rounded-md border border-border bg-surface-raised px-3 text-foreground"
              defaultValue={difficulty}
              id="problem-difficulty"
              name="difficulty"
            >
              <option>All</option>
              <option>Easy</option>
              <option>Medium</option>
              <option>Hard</option>
            </select>
          </form>
          <div className="mt-8 flex items-baseline justify-between">
            <h2 className="text-xl font-semibold text-foreground" id="problem-results">
              Problems
            </h2>
            <p className="text-sm text-text-subtle">{visible.length} available</p>
          </div>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            {visible.map((problem) => (
              <article
                className="rounded-lg border border-border bg-surface-raised p-5"
                key={problem.slug}
              >
                <p className={`text-sm font-semibold ${tone[problem.difficulty]}`}>
                  {problem.difficulty} · {problem.topic}
                </p>
                <h3 className="mt-3 text-xl font-semibold text-foreground">{problem.title}</h3>
                <p className="mt-2 text-sm leading-6 text-text-muted">{problem.description}</p>
                <Link
                  className="mt-5 inline-block text-sm font-semibold text-accent-strong hover:underline"
                  href={`/problems/${problem.slug}`}
                >
                  View problem →
                </Link>
              </article>
            ))}
          </div>
          {visible.length === 0 ? (
            <p className="mt-5 rounded-lg border border-border bg-surface-raised p-8 text-center text-text-muted">
              No problems match these filters.
            </p>
          ) : null}
        </section>
      </div>
    </div>
  );
}
