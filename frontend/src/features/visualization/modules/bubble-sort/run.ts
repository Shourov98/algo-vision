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
    throw new TypeError("Bubble Sort requires finite number values.");

  const items: SortItem[] = input.map((value, index) => ({
    id: `element-${index + 1}`,
    value,
  }));
  const events: AlgorithmEvent[] = [];
  let step = 0;

  function emit(event: AlgorithmEventDraft) {
    events.push({ ...event, id: `bubble-sort-${step}`, t: step });
    step += 1;
  }

  for (let pass = 0; pass < items.length - 1; pass += 1) {
    for (let index = 0; index < items.length - pass - 1; index += 1) {
      const left = items[index]!;
      const right = items[index + 1]!;
      emit(
        withLine(
          {
            type: "compare",
            ids: [left.id, right.id],
            message: `Comparing ${left.value} and ${right.value}.`,
          },
          5,
          options,
        ),
      );

      if (left.value > right.value) {
        [items[index], items[index + 1]] = [right, left];
        emit(
          withLine(
            {
              type: "swap",
              ids: [left.id, right.id],
              message: `Swapping ${left.value} and ${right.value}.`,
            },
            6,
            options,
          ),
        );
      }
    }

    const sortedItem = items[items.length - pass - 1]!;
    emit(
      withLine(
        {
          type: "mark",
          elementId: sortedItem.id,
          status: "sorted",
          message: `${sortedItem.value} is in its final position.`,
        },
        8,
        options,
      ),
    );
  }

  if (items.length > 0) {
    const firstItem = items[0]!;
    emit(
      withLine(
        {
          type: "mark",
          elementId: firstItem.id,
          status: "sorted",
          message: `${firstItem.value} is in its final position.`,
        },
        8,
        options,
      ),
    );
  }

  emit(
    withLine(
      {
        type: "complete",
        message: "Sort complete.",
      },
      10,
      options,
    ),
  );
  return events;
}
