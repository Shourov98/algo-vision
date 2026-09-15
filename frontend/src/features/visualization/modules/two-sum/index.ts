import type { AlgorithmEvent, AlgorithmEventDraft } from "@/features/visualization/events";
import type { ArrayAlgorithmModule, RunOptions } from "@/features/visualization/modules/types";

export const TWO_SUM_TARGET = 9;

export function run(input: number[], options?: RunOptions): AlgorithmEvent[] {
  if (!input.every(Number.isFinite)) throw new TypeError("Two Sum requires finite number values.");
  const target = options?.target ?? TWO_SUM_TARGET;
  const seen = new Map<number, string>();
  const events: AlgorithmEvent[] = [];
  let step = 0;
  const emit = (event: AlgorithmEventDraft) => {
    events.push({ ...event, id: `two-sum-${step}`, t: step });
    step += 1;
  };
  for (let index = 0; index < input.length; index += 1) {
    const value = input[index]!;
    const id = `element-${index + 1}`;
    const match = seen.get(target - value);
    emit({
      type: "visit",
      elementId: id,
      line: 5,
      message: `Checking ${value}; need ${target - value}.`,
    });
    if (match) {
      emit({
        type: "found",
        ids: [match, id],
        line: 7,
        message: `Found ${target - value} + ${value} = ${target}.`,
      });
      emit({ type: "complete", line: 11, message: "Solution found.", summary: { target } });
      return events;
    }
    seen.set(value, id);
    emit({
      type: "mark",
      elementId: id,
      status: "visited",
      line: 9,
      message: `Remember ${value} for later.`,
    });
  }
  emit({ type: "complete", line: 11, message: `No pair adds to ${target}.`, summary: { target } });
  return events;
}

export const twoSumModule: ArrayAlgorithmModule<number[]> = {
  capabilities: {
    maxItems: 12,
    minItems: 2,
    requiresSortedInput: false,
    supportsDirection: false,
    supportsTarget: true,
  },
  slug: "two-sum",
  visualizationKind: "array",
  meta: {
    name: "Two Sum",
    description: "Track prior values to find a target pair.",
    difficulty: "easy",
    complexity: { best: "O(n)", average: "O(n)", worst: "O(n)", space: "O(n)" },
    topics: ["arrays", "hashing"],
  },
  defaultInput: () => [2, 7, 11, 15],
  run,
};
