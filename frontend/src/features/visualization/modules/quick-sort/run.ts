import type {
  AlgorithmEvent,
  AlgorithmEventDraft,
  ElementId,
} from "@/features/visualization/events";
import type { RunOptions } from "@/features/visualization/modules/types";

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
    throw new TypeError("Quick Sort requires finite number values.");
  const items: SortItem[] = input.map((value, index) => ({ id: `element-${index + 1}`, value }));
  const events: AlgorithmEvent[] = [];
  let step = 0;
  const emit = (event: AlgorithmEventDraft) => {
    events.push({ ...event, id: `quick-sort-${step}`, t: step });
    step += 1;
  };
  const partition = (low: number, high: number) => {
    const pivot = items[high]!;
    emit(
      withLine(
        { type: "select", ids: [pivot.id], message: `Selecting ${pivot.value} as the pivot.` },
        4,
        options,
      ),
    );
    let pivotIndex = low;
    for (let index = low; index < high; index += 1) {
      const item = items[index]!;
      emit(
        withLine(
          {
            type: "compare",
            ids: [item.id, pivot.id],
            message: `Comparing ${item.value} with pivot ${pivot.value}.`,
          },
          6,
          options,
        ),
      );
      if (item.value <= pivot.value) {
        if (pivotIndex !== index) {
          const swapWith = items[pivotIndex]!;
          [items[pivotIndex], items[index]] = [item, swapWith];
          emit(
            withLine(
              {
                type: "swap",
                ids: [item.id, swapWith.id],
                message: `Swapping ${item.value} and ${swapWith.value}.`,
              },
              8,
              options,
            ),
          );
        }
        pivotIndex += 1;
      }
    }
    if (pivotIndex !== high) {
      const swapWith = items[pivotIndex]!;
      [items[pivotIndex], items[high]] = [pivot, swapWith];
      emit(
        withLine(
          {
            type: "swap",
            ids: [pivot.id, swapWith.id],
            message: `Moving pivot ${pivot.value} into position.`,
          },
          11,
          options,
        ),
      );
    }
    emit(
      withLine(
        {
          type: "mark",
          elementId: pivot.id,
          status: "sorted",
          message: `${pivot.value} is in its final position.`,
        },
        12,
        options,
      ),
    );
    return pivotIndex;
  };
  const sort = (low: number, high: number) => {
    if (low >= high) return;
    const pivotIndex = partition(low, high);
    sort(low, pivotIndex - 1);
    sort(pivotIndex + 1, high);
  };
  sort(0, items.length - 1);
  if (items.length === 1)
    emit(
      withLine(
        {
          type: "mark",
          elementId: items[0]!.id,
          status: "sorted",
          message: `${items[0]!.value} is in its final position.`,
        },
        12,
        options,
      ),
    );
  emit(withLine({ type: "complete", message: "Sort complete." }, 15, options));
  return events;
}
