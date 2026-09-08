import type { ReactNode } from "react";

export interface VisualizationShellProps {
  slug: string;
  title: string;
  description?: string;
  complexity: { best?: string; average?: string; worst?: string; space?: string };
  children: ReactNode;
}

export function VisualizationShell({
  slug,
  title,
  description,
  complexity,
  children,
}: VisualizationShellProps) {
  return (
    <section aria-labelledby={`${slug}-title`} className="mx-auto max-w-7xl px-6 py-10 lg:px-8">
      <header className="border-b border-border pb-6">
        <p className="text-sm font-semibold text-accent-strong">Algorithm visualization</p>
        <h1 id={`${slug}-title`} className="mt-2 text-3xl font-semibold text-foreground">
          {title}
        </h1>
        {description ? <p className="mt-3 max-w-2xl text-text-muted">{description}</p> : null}
        <dl className="mt-5 flex flex-wrap gap-5 text-sm">
          {Object.entries(complexity).map(([label, value]) =>
            value ? (
              <div key={label}>
                <dt className="text-text-subtle">{label}</dt>
                <dd className="mt-1 font-mono text-foreground">{value}</dd>
              </div>
            ) : null,
          )}
        </dl>
      </header>
      <div className="mt-6 space-y-6">{children}</div>
    </section>
  );
}
