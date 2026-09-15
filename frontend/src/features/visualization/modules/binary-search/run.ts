import type {
  AlgorithmEvent,
  AlgorithmEventDraft,
  ElementId,
} from "@/features/visualization/events";
import type { RunOptions } from "@/features/visualization/modules/types";

export const DEFAULT_TARGET = 7;

function withLine<Event extends AlgorithmEventDraft>(
  event: Event,
  line: number,
  options?: RunOptions,
) {
  return options?.highlightLines === false ? event : { ...event, line };
}

function assertSorted(values: number[], direction: "ascending" | "descending") {
  if (!values.every(Number.isFinite))
    throw new TypeError("Binary Search requires finite number values.");
  const sorted = values.every((value, index) => {
    if (index === 0) return true;
    const previous = values[index - 1]!;
    return direction === "ascending" ? previous <= value : previous >= value;
  });
  if (!sorted) throw new RangeError(`Binary Search requires values in ${direction} order.`);
}

export function run(input: number[], options?: RunOptions): AlgorithmEvent[] {
  const direction = options?.direction ?? "ascending";
  assertSorted(input, direction);
  const target = options?.target ?? DEFAULT_TARGET;
  if (!Number.isFinite(target)) throw new TypeError("Binary Search requires a finite target.");

  const ids: ElementId[] = input.map((_, index) => `element-${index + 1}`);
  const events: AlgorithmEvent[] = [];
  let step = 0;
  const emit = (event: AlgorithmEventDraft) => {
    events.push({ ...event, id: `binary-search-${step}`, t: step });
    step += 1;
  };

  let low = 0;
  let high = input.length - 1;
  while (low <= high) {
    const middle = low + Math.floor((high - low) / 2);
    const value = input[middle]!;
    const elementId = ids[middle]!;
    emit(
      withLine(
        {
          type: "mark",
          elementId,
          status: "current",
          message: `Checking ${value} at index ${middle}.`,
        },
        5,
        options,
      ),
    );
    emit(
      withLine(
        { type: "compare", ids: [elementId], message: `Comparing ${value} with target ${target}.` },
        7,
        options,
      ),
    );

    if (value === target) {
      emit(
        withLine(
          { type: "found", ids: [elementId], message: `Found ${target} at index ${middle}.` },
          8,
          options,
        ),
      );
      emit(
        withLine(
          {
            type: "complete",
            message: "Search complete.",
            summary: { found: true, index: middle, target },
          },
          15,
          options,
        ),
      );
      return events;
    }

    emit(
      withLine(
        {
          type: "visit",
          elementId,
          message: `${value} is not the target; removing it from the range.`,
        },
        10,
        options,
      ),
    );
    const discardLeft = direction === "ascending" ? value < target : value > target;
    if (discardLeft) low = middle + 1;
    else high = middle - 1;
  }

  emit(
    withLine(
      {
        type: "complete",
        message: `${target} is not in the array.`,
        summary: { found: false, index: -1, target },
      },
      15,
      options,
    ),
  );
  return events;
}
