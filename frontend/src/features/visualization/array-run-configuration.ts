import type {
  ArrayModuleCapabilities,
  SortDirection,
} from "@/features/visualization/modules/types";

export const ARRAY_MIN_ITEMS = 2;
export const ARRAY_MAX_ITEMS = 12;

const PRESET_VALUES = [5, 2, 8, 1, 4, 7, 3, 6, 9, 12, 10, 11] as const;

export interface ArrayRunConfiguration {
  values: number[];
  direction: SortDirection;
  target?: number;
}

export type ArrayRunConfigurationIssue =
  | "too_few_items"
  | "too_many_items"
  | "non_finite_value"
  | "missing_target"
  | "non_finite_target"
  | "unsorted_input";

export interface ArrayRunConfigurationValidation {
  valid: boolean;
  issues: ArrayRunConfigurationIssue[];
}

export function hasSameArrayRunConfiguration(
  left: ArrayRunConfiguration,
  right: ArrayRunConfiguration,
) {
  return (
    left.direction === right.direction &&
    left.target === right.target &&
    left.values.length === right.values.length &&
    left.values.every((value, index) => value === right.values[index])
  );
}

export function createDeterministicPreset(itemCount: number): number[] {
  if (!Number.isInteger(itemCount) || itemCount < ARRAY_MIN_ITEMS || itemCount > ARRAY_MAX_ITEMS)
    throw new RangeError(`Array size must be between ${ARRAY_MIN_ITEMS} and ${ARRAY_MAX_ITEMS}.`);
  return PRESET_VALUES.slice(0, itemCount);
}

export function isSortedForDirection(values: readonly number[], direction: SortDirection) {
  return values.every((value, index) => {
    if (index === 0) return true;
    const previous = values[index - 1]!;
    return direction === "ascending" ? previous <= value : previous >= value;
  });
}

export function validateArrayRunConfiguration(
  configuration: ArrayRunConfiguration,
  capabilities: ArrayModuleCapabilities,
): ArrayRunConfigurationValidation {
  const issues: ArrayRunConfigurationIssue[] = [];
  const { values } = configuration;
  if (values.length < capabilities.minItems) issues.push("too_few_items");
  if (values.length > capabilities.maxItems) issues.push("too_many_items");
  if (!values.every(Number.isFinite)) issues.push("non_finite_value");
  if (capabilities.supportsTarget && configuration.target === undefined)
    issues.push("missing_target");
  if (configuration.target !== undefined && !Number.isFinite(configuration.target))
    issues.push("non_finite_target");
  if (
    capabilities.requiresSortedInput &&
    values.every(Number.isFinite) &&
    !isSortedForDirection(values, configuration.direction)
  )
    issues.push("unsorted_input");
  return { valid: issues.length === 0, issues };
}

export function sortValuesForDirection(
  values: readonly number[],
  direction: SortDirection,
): number[] {
  return [...values].sort((left, right) =>
    direction === "ascending" ? left - right : right - left,
  );
}
