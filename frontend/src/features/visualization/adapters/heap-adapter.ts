import type { ElementView, VisualizationAdapter } from "@/features/visualization/adapters/types";
import { EngineInvariantError } from "@/features/visualization/errors";
import type { ElementId, MarkStatus } from "@/features/visualization/events";

export interface HeapItem extends ElementView {
  value: unknown;
}
export interface HeapState {
  items: HeapItem[];
  heapSize: number;
}
function item(items: HeapItem[], id: ElementId) {
  const result = items.find((candidate) => candidate.id === id);
  if (!result) throw new EngineInvariantError(`Unknown heap element ID: ${id}`);
  return result;
}
function statuses(items: HeapItem[], ids: ElementId[], status: MarkStatus) {
  ids.forEach((id) => {
    item(items, id).status = status;
  });
}

export const HeapAdapter: VisualizationAdapter<HeapState> = {
  kind: "heap",
  createInitialState(input, seed) {
    if (!Array.isArray(input)) throw new TypeError("Heap adapter requires an array input.");
    const ids = seed ?? input.map((_, index) => `element-${index + 1}`);
    if (ids.length !== input.length || new Set(ids).size !== ids.length)
      throw new EngineInvariantError("Heap seed must contain unique IDs matching the input.");
    return {
      items: input.map((value, index) => ({ id: ids[index]!, value, status: "idle" })),
      heapSize: input.length,
    };
  },
  reduce(state, event) {
    const items = state.items.map((entry) => ({ ...entry }));
    let heapSize = state.heapSize;
    if (event.type === "compare") statuses(items, event.ids, "comparing");
    else if (event.type === "swap") {
      const [a, b] = event.ids;
      const ai = items.findIndex((x) => x.id === a);
      const bi = items.findIndex((x) => x.id === b);
      if (ai < 0) item(items, a);
      if (bi < 0) item(items, b);
      [items[ai], items[bi]] = [items[bi]!, items[ai]!];
      statuses(items, event.ids, "swapping");
    } else if (event.type === "mark") {
      statuses(items, [event.elementId], event.status);
      if (event.status === "sorted") heapSize = Math.max(0, heapSize - 1);
    } else if (event.type === "visit") statuses(items, [event.elementId], "visited");
    else if (event.type === "found") statuses(items, event.ids, "found");
    else if (event.type === "select") statuses(items, event.ids, "pivot");
    return { items, heapSize };
  },
  getElementIds: (state) => state.items.map((entry) => entry.id),
  getElement: (state, id) => state.items.find((entry) => entry.id === id),
};
