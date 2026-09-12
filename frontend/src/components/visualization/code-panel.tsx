"use client";

export const sourceLanguages = ["typescript", "python", "cpp"] as const;
export type SourceLanguage = (typeof sourceLanguages)[number];

export interface CodePanelProps {
  sources: Record<SourceLanguage, string>;
  currentLine?: number;
  language: SourceLanguage;
  onLanguageChange(language: SourceLanguage): void;
}

const languageLabels: Record<SourceLanguage, string> = {
  typescript: "TypeScript",
  python: "Python",
  cpp: "C++",
};

export function CodePanel({ sources, currentLine, language, onLanguageChange }: CodePanelProps) {
  const lines = sources[language].split("\n");

  return (
    <section
      aria-labelledby="code-panel-title"
      className="overflow-hidden rounded-lg border border-border bg-surface-raised"
    >
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3">
        <h2 id="code-panel-title" className="font-semibold text-foreground">
          Code
        </h2>
        <div aria-label="Source language" className="flex rounded-md bg-surface p-1" role="tablist">
          {sourceLanguages.map((item) => (
            <button
              aria-controls="source-code"
              aria-selected={language === item}
              className={`rounded px-3 py-1.5 text-sm font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring ${language === item ? "bg-accent-strong text-surface" : "text-text-muted hover:text-foreground"}`}
              id={`${item}-tab`}
              key={item}
              onClick={() => onLanguageChange(item)}
              role="tab"
              type="button"
            >
              {languageLabels[item]}
            </button>
          ))}
        </div>
      </div>
      <pre
        aria-labelledby={`${language}-tab`}
        className="overflow-x-auto p-4 text-sm leading-6"
        id="source-code"
        role="tabpanel"
      >
        <code>
          {lines.map((line, index) => {
            const lineNumber = index + 1;
            const active = lineNumber === currentLine;
            return (
              <span
                className={`grid grid-cols-[2.5rem_1fr] px-2 font-mono ${active ? "-mx-2 bg-accent/35 text-foreground" : "text-text-muted"}`}
                data-current={active || undefined}
                key={lineNumber}
              >
                <span aria-hidden="true" className="select-none text-text-subtle">
                  {lineNumber}
                </span>
                <span>{line || " "}</span>
              </span>
            );
          })}
        </code>
      </pre>
    </section>
  );
}
