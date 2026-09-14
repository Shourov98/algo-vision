"use client";

import { useUIStore } from "@/stores/ui-store";

function Toggle({
  checked,
  label,
  onChange,
}: {
  checked: boolean;
  label: string;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between gap-4 rounded-md border border-border bg-surface px-4 py-3 text-foreground">
      <span>{label}</span>
      <input
        aria-label={label}
        checked={checked}
        className="h-4 w-4 accent-accent-strong"
        onChange={(event) => onChange(event.target.checked)}
        type="checkbox"
      />
    </label>
  );
}

export function SettingsContent() {
  const {
    isCodePanelOpen,
    isCompactLayout,
    isExplanationOpen,
    setCompactLayout,
    toggleCodePanel,
    toggleExplanationPanel,
  } = useUIStore();
  return (
    <section className="space-y-3">
      <Toggle
        checked={isCompactLayout}
        label="Use compact visualization layout"
        onChange={setCompactLayout}
      />
      <Toggle
        checked={isCodePanelOpen}
        label="Show code panel by default"
        onChange={(checked) => {
          if (checked !== isCodePanelOpen) toggleCodePanel();
        }}
      />
      <Toggle
        checked={isExplanationOpen}
        label="Show step explanations by default"
        onChange={(checked) => {
          if (checked !== isExplanationOpen) toggleExplanationPanel();
        }}
      />
    </section>
  );
}
