import Link from "next/link";

const nodes = ["Head", "12", "24", "37", "null"];
export default function LinkedListPage() {
  return (
    <main className="mx-auto max-w-5xl px-6 py-12 lg:px-8">
      <p className="text-sm font-semibold tracking-[0.18em] text-accent-strong uppercase">
        Data structure
      </p>
      <h1 className="mt-3 text-4xl font-semibold text-foreground">Linked List</h1>
      <p className="mt-4 max-w-2xl text-lg leading-8 text-text-muted">
        A linked list stores values in nodes that point to the next node, making insertions and
        removals efficient once you reach the target position.
      </p>
      <section
        aria-labelledby="linked-list-flow"
        className="mt-10 rounded-lg border border-border bg-surface-raised p-6"
      >
        <h2 id="linked-list-flow" className="font-semibold text-foreground">
          Node chain
        </h2>
        <div aria-label="Linked list nodes" className="mt-6 flex flex-wrap items-center gap-3">
          {nodes.map((node, index) => (
            <div className="flex items-center gap-3" key={node}>
              <span
                className={`rounded-md border px-4 py-3 font-mono ${index === 0 ? "border-accent-strong text-accent-strong" : "border-border text-foreground"}`}
              >
                {node}
              </span>
              {index < nodes.length - 1 ? (
                <span aria-hidden="true" className="text-accent-strong">
                  →
                </span>
              ) : null}
            </div>
          ))}
        </div>
      </section>
      <section className="mt-6 grid gap-4 md:grid-cols-3">
        <article className="rounded-lg border border-border bg-surface-raised p-5">
          <h2 className="font-semibold text-foreground">Access</h2>
          <p className="mt-2 font-mono text-accent-strong">O(n)</p>
        </article>
        <article className="rounded-lg border border-border bg-surface-raised p-5">
          <h2 className="font-semibold text-foreground">Insert at head</h2>
          <p className="mt-2 font-mono text-accent-strong">O(1)</p>
        </article>
        <article className="rounded-lg border border-border bg-surface-raised p-5">
          <h2 className="font-semibold text-foreground">Search</h2>
          <p className="mt-2 font-mono text-accent-strong">O(n)</p>
        </article>
      </section>
      <Link
        className="mt-8 inline-flex rounded-md bg-accent-strong px-4 py-2 font-semibold text-surface"
        href="/data-structures"
      >
        Explore data structures
      </Link>
    </main>
  );
}
