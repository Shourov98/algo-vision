import type {
  AlgorithmEvent,
  AlgorithmEventDraft,
  ElementId,
} from "@/features/visualization/events";
import type { RunOptions } from "@/features/visualization/modules/types";
function line<E extends AlgorithmEventDraft>(event: E, value: number, options?: RunOptions) {
  return options?.highlightLines === false ? event : { ...event, line: value };
}
export function run(input: number[], options?: RunOptions): AlgorithmEvent[] {
  if (!input.every(Number.isFinite))
    throw new TypeError("Heap Sort requires finite number values.");
  const items = input.map((value, index) => ({ value, id: `element-${index + 1}` as ElementId }));
  const events: AlgorithmEvent[] = [];
  let step = 0;
  const emit = (event: AlgorithmEventDraft) => {
    events.push({ ...event, id: `heap-sort-${step}`, t: step });
    step += 1;
  };
  const sift = (root: number, size: number) => {
    let parent = root;
    while (true) {
      const left = parent * 2 + 1;
      const right = left + 1;
      let largest = parent;
      if (left < size) {
        emit(
          line(
            {
              type: "compare",
              ids: [items[largest]!.id, items[left]!.id],
              message: `Comparing heap nodes.`,
            },
            6,
            options,
          ),
        );
        if (items[left]!.value > items[largest]!.value) largest = left;
      }
      if (right < size) {
        emit(
          line(
            {
              type: "compare",
              ids: [items[largest]!.id, items[right]!.id],
              message: `Comparing heap nodes.`,
            },
            7,
            options,
          ),
        );
        if (items[right]!.value > items[largest]!.value) largest = right;
      }
      if (largest === parent) return;
      const a = items[parent]!,
        b = items[largest]!;
      [items[parent], items[largest]] = [b, a];
      emit(
        line({ type: "swap", ids: [a.id, b.id], message: `Restoring max-heap order.` }, 9, options),
      );
      parent = largest;
    }
  };
  for (let i = Math.floor(items.length / 2) - 1; i >= 0; i -= 1) sift(i, items.length);
  for (let end = items.length - 1; end > 0; end -= 1) {
    const a = items[0]!,
      b = items[end]!;
    [items[0], items[end]] = [b, a];
    emit(
      line(
        { type: "swap", ids: [a.id, b.id], message: `Moving maximum into its final position.` },
        13,
        options,
      ),
    );
    emit(
      line(
        { type: "mark", elementId: a.id, status: "sorted", message: `${a.value} is sorted.` },
        14,
        options,
      ),
    );
    sift(0, end);
  }
  if (items[0])
    emit(
      line(
        {
          type: "mark",
          elementId: items[0].id,
          status: "sorted",
          message: `${items[0].value} is sorted.`,
        },
        14,
        options,
      ),
    );
  emit(line({ type: "complete", message: "Sort complete." }, 16, options));
  return events;
}
