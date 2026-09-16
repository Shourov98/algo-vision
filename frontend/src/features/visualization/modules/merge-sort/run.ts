import type {
  AlgorithmEvent,
  AlgorithmEventDraft,
  ElementId,
} from "@/features/visualization/events";
import type { RunOptions } from "@/features/visualization/modules/types";
import {
  resolveSortDirection,
  shouldTakeLeftForDirection,
} from "@/features/visualization/modules/sort-direction";

interface SortItem {
  id: ElementId;
  value: number;
}

function withLine<Event extends AlgorithmEventDraft>(
  event: Event,
  line: number,
  options?: RunOptions,
) {
  return options?.highlightLines === false ? event : { ...event, line };
}

export function run(input: number[], options?: RunOptions): AlgorithmEvent[] {
  if (!input.every(Number.isFinite))
    throw new TypeError("Merge Sort requires finite number values.");

  const items: SortItem[] = input.map((value, index) => ({ id: `element-${index + 1}`, value }));
  const direction = resolveSortDirection(options?.direction);
  const events: AlgorithmEvent[] = [];
  let step = 0;
  const emit = (event: AlgorithmEventDraft) => {
    events.push({ ...event, id: `merge-sort-${step}`, t: step });
    step += 1;
  };

  const merge = (low: number, middle: number, high: number) => {
    const left = items.slice(low, middle + 1);
    const right = items.slice(middle + 1, high + 1);
    const merged: SortItem[] = [];
    let leftIndex = 0;
    let rightIndex = 0;

    while (leftIndex < left.length && rightIndex < right.length) {
      const leftItem = left[leftIndex]!;
      const rightItem = right[rightIndex]!;
      emit(
        withLine(
          {
            type: "compare",
            ids: [leftItem.id, rightItem.id],
            message: `Compare ${leftItem.value} from the left half with ${rightItem.value} from the right half.`,
          },
          8,
          options,
        ),
      );
      if (shouldTakeLeftForDirection(leftItem.value, rightItem.value, direction)) {
        merged.push(leftItem);
        leftIndex += 1;
      } else {
        merged.push(rightItem);
        rightIndex += 1;
      }
    }
    merged.push(...left.slice(leftIndex), ...right.slice(rightIndex));

    for (let offset = 0; offset < merged.length; offset += 1) {
      const item = merged[offset]!;
      const targetIndex = low + offset;
      const fromIndex = items.findIndex((candidate) => candidate.id === item.id);
      if (fromIndex !== targetIndex) {
        emit(
          withLine(
            {
              type: "move",
              elementId: item.id,
              fromIndex,
              toIndex: targetIndex,
              message: `Move ${item.value} into position ${targetIndex} while merging the two sorted halves.`,
            },
            13,
            options,
          ),
        );
        items.splice(fromIndex, 1);
        items.splice(targetIndex, 0, item);
      }
    }
  };

  const sort = (low: number, high: number): void => {
    if (low >= high) return;
    const middle = Math.floor((low + high) / 2);
    sort(low, middle);
    sort(middle + 1, high);
    emit(
      withLine(
        {
          type: "select",
          ids: items.slice(low, high + 1).map((item) => item.id),
          leftIds: items.slice(low, middle + 1).map((item) => item.id),
          message: `Merge the sorted ranges from ${low} to ${middle} and ${middle + 1} to ${high}.`,
          rightIds: items.slice(middle + 1, high + 1).map((item) => item.id),
        },
        6,
        options,
      ),
    );
    merge(low, middle, high);
  };

  sort(0, items.length - 1);
  for (const item of items) {
    emit(
      withLine(
        {
          type: "mark",
          elementId: item.id,
          status: "sorted",
          message: `${item.value} is in its final sorted position.`,
        },
        16,
        options,
      ),
    );
  }
  emit(withLine({ type: "complete", message: "Merge Sort complete." }, 18, options));
  return events;
}
