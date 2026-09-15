"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  createDeterministicPreset,
  sortValuesForDirection,
  validateArrayRunConfiguration,
  type ArrayRunConfiguration,
} from "@/features/visualization/array-run-configuration";
import type { ArrayModuleCapabilities } from "@/features/visualization/modules/types";

const ISSUE_MESSAGES = {
  missing_target: "Enter a finite target value.",
  non_finite_target: "The target must be a finite number.",
  non_finite_value: "Every array value must be a finite number.",
  too_few_items: "Add more values before starting.",
  too_many_items: "Remove values before starting.",
  unsorted_input: "Sort the values for the selected search direction first.",
} as const;

export interface ArrayInputPanelProps {
  capabilities: ArrayModuleCapabilities;
  configuration: ArrayRunConfiguration;
  onChange(configuration: ArrayRunConfiguration): void;
  onStart(): void;
}

export function ArrayInputPanel({
  capabilities,
  configuration,
  onChange,
  onStart,
}: ArrayInputPanelProps) {
  const validation = validateArrayRunConfiguration(configuration, capabilities);
  const updateValues = (values: number[]) => onChange({ ...configuration, values });
  const updateValue = (index: number, rawValue: string) => {
    const values = [...configuration.values];
    values[index] = rawValue.trim() === "" ? Number.NaN : Number(rawValue);
    updateValues(values);
  };

  return (
    <section
      aria-labelledby="array-input-title"
      className="rounded-xl border border-border bg-surface-raised p-5"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 id="array-input-title" className="font-semibold text-foreground">
            Array input
          </h2>
          <p className="text-sm text-text-muted">Edit values, then start a fresh visualization.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            aria-label="Remove array value"
            disabled={configuration.values.length <= capabilities.minItems}
            onClick={() => updateValues(configuration.values.slice(0, -1))}
            size="sm"
            type="button"
            variant="outline"
          >
            −
          </Button>
          <output aria-label="Array element count" className="font-mono text-sm text-foreground">
            {configuration.values.length}
          </output>
          <Button
            aria-label="Add array value"
            disabled={configuration.values.length >= capabilities.maxItems}
            onClick={() => updateValues(createDeterministicPreset(configuration.values.length + 1))}
            size="sm"
            type="button"
            variant="outline"
          >
            +
          </Button>
        </div>
      </div>
      <div
        aria-label="Array values"
        className="mt-4 grid grid-cols-[repeat(auto-fit,minmax(4rem,1fr))] gap-2"
      >
        {configuration.values.map((value, index) => (
          <label className="text-xs text-text-subtle" key={index}>
            Value {index + 1}
            <Input
              aria-label={`Value ${index + 1}`}
              className="mt-1 font-mono"
              onChange={(event) => updateValue(index, event.target.value)}
              type="number"
              value={Number.isFinite(value) ? value : ""}
            />
          </label>
        ))}
      </div>
      <div className="mt-4 flex flex-wrap items-end gap-3">
        {capabilities.supportsDirection ? (
          <label className="text-sm text-text-muted">
            Order
            <select
              aria-label="Sort direction"
              className="ml-2 rounded-md border border-border bg-surface px-2 py-1.5 text-foreground"
              onChange={(event) =>
                onChange({
                  ...configuration,
                  direction: event.target.value as ArrayRunConfiguration["direction"],
                })
              }
              value={configuration.direction}
            >
              <option value="ascending">Ascending</option>
              <option value="descending">Descending</option>
            </select>
          </label>
        ) : null}
        {capabilities.supportsTarget ? (
          <label className="text-sm text-text-muted">
            Target
            <Input
              aria-label="Search target"
              className="ml-2 inline-block w-24 font-mono"
              onChange={(event) => {
                if (event.target.value.trim() === "") {
                  const { target, ...withoutTarget } = configuration;
                  void target;
                  onChange(withoutTarget);
                } else onChange({ ...configuration, target: Number(event.target.value) });
              }}
              type="number"
              value={configuration.target ?? ""}
            />
          </label>
        ) : null}
        {capabilities.requiresSortedInput ? (
          <Button
            onClick={() =>
              updateValues(sortValuesForDirection(configuration.values, configuration.direction))
            }
            size="sm"
            type="button"
            variant="outline"
          >
            Sort for search
          </Button>
        ) : null}
        <Button
          onClick={() => updateValues(createDeterministicPreset(configuration.values.length))}
          size="sm"
          type="button"
          variant="outline"
        >
          Reset values
        </Button>
        <Button disabled={!validation.valid} onClick={onStart} size="sm" type="button">
          Start over
        </Button>
      </div>
      <p aria-live="polite" className="mt-3 text-sm text-destructive">
        {validation.issues.map((issue) => ISSUE_MESSAGES[issue]).join(" ")}
      </p>
    </section>
  );
}
