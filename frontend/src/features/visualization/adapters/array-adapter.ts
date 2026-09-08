import type { ElementView, VisualizationAdapter } from "@/features/visualization/adapters/types";
import { EngineInvariantError } from "@/features/visualization/errors";
import type { ElementId, MarkStatus } from "@/features/visualization/events";

export interface ArrayItem extends ElementView {
  value: unknown;
}

export interface ArrayState {
  items: ArrayItem[];
}

function createElementIds(length: number, seed?: ElementId[]): ElementId[] {
  const ids = seed ?? Array.from({ length }, (_, index) => `element-${index + 1}`);
  if (ids.length !== length)
    throw new EngineInvariantError("Array seed must match the input length.");
  if (new Set(ids).size !== ids.length)
    throw new EngineInvariantError("Array element IDs must be unique.");
  return ids;
}

function getItem(items: ArrayItem[], id: ElementId): ArrayItem {
  const item = items.find((candidate) => candidate.id === id);
  if (!item) throw new EngineInvariantError(`Unknown array element ID: ${id}`);
  return item;
}

function setStatuses(items: ArrayItem[], ids: ElementId[], status: MarkStatus) {
  for (const id of ids) getItem(items, id).status = status;
}

export const ArrayAdapter: VisualizationAdapter<ArrayState> = {
  kind: "array",

  createInitialState(input, seed) {
    if (!Array.isArray(input)) throw new TypeError("Array adapter requires an array input.");
    const ids = createElementIds(input.length, seed);
    return {
      items: input.map((value, index) => ({ id: ids[index]!, status: "idle", value })),
    };
  },

  reduce(state, event) {
    const items = state.items.map((item) => ({ ...item }));

    switch (event.type) {
      case "compare":
        setStatuses(items, event.ids, "comparing");
        break;
      case "swap": {
        const [firstId, secondId] = event.ids;
        const firstIndex = items.findIndex((item) => item.id === firstId);
        const secondIndex = items.findIndex((item) => item.id === secondId);
        if (firstIndex === -1) getItem(items, firstId);
        if (secondIndex === -1) getItem(items, secondId);
        [items[firstIndex], items[secondIndex]] = [items[secondIndex]!, items[firstIndex]!];
        setStatuses(items, event.ids, "swapping");
        break;
      }
      case "visit":
        setStatuses(items, [event.elementId], "visited");
        break;
      case "select":
        for (const item of items) if (item.status === "pivot") item.status = "idle";
        setStatuses(items, event.ids, "pivot");
        break;
      case "insert":
        if (items.some((item) => item.id === event.elementId)) {
          throw new EngineInvariantError(`Array element ID already exists: ${event.elementId}`);
        }
        items.push({ id: event.elementId, status: "active", value: event.value });
        break;
      case "delete": {
        const itemIndex = items.findIndex((item) => item.id === event.elementId);
        if (itemIndex === -1) getItem(items, event.elementId);
        items.splice(itemIndex, 1);
        break;
      }
      case "update":
        getItem(items, event.elementId).value = event.value;
        break;
      case "mark":
        setStatuses(items, [event.elementId], event.status);
        break;
      case "relax":
        getItem(items, event.from);
        getItem(items, event.to);
        break;
      case "found":
        setStatuses(items, event.ids, "found");
        break;
      case "enqueue":
      case "push":
        setStatuses(items, [event.elementId], "active");
        break;
      case "dequeue":
      case "pop":
        setStatuses(items, [event.elementId], "idle");
        break;
      case "complete":
        for (const item of items) {
          if (["active", "comparing", "swapping"].includes(item.status)) item.status = "sorted";
        }
        break;
    }

    return { items };
  },

  getElementIds(state) {
    return state.items.map((item) => item.id);
  },

  getElement(state, id) {
    return state.items.find((item) => item.id === id);
  },
};
