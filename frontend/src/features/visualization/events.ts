export type ElementId = string;
export type LineNumber = number;

export type MarkStatus =
  | "idle"
  | "active"
  | "comparing"
  | "swapping"
  | "sorted"
  | "pivot"
  | "visited"
  | "frontier"
  | "current"
  | "target"
  | "found";

export interface BaseEvent {
  id: string;
  t: number;
  line?: LineNumber;
  message: string;
}

export type AlgorithmEvent =
  | (BaseEvent & { type: "compare"; ids: ElementId[] })
  | (BaseEvent & { type: "swap"; ids: [ElementId, ElementId] })
  | (BaseEvent & { type: "visit"; id: ElementId })
  | (BaseEvent & { type: "select"; ids: ElementId[] })
  | (BaseEvent & { type: "insert"; id: ElementId; value: unknown })
  | (BaseEvent & { type: "delete"; id: ElementId })
  | (BaseEvent & { type: "update"; id: ElementId; value: unknown })
  | (BaseEvent & { type: "mark"; id: ElementId; status: MarkStatus })
  | (BaseEvent & { type: "relax"; from: ElementId; to: ElementId; weight?: number })
  | (BaseEvent & { type: "found"; ids: ElementId[] })
  | (BaseEvent & { type: "enqueue"; id: ElementId })
  | (BaseEvent & { type: "dequeue"; id: ElementId })
  | (BaseEvent & { type: "push"; id: ElementId; value: unknown })
  | (BaseEvent & { type: "pop"; id: ElementId })
  | (BaseEvent & { type: "complete"; summary?: Record<string, unknown> });

type EventDraft<Event extends BaseEvent> = Event extends Event ? Omit<Event, "id" | "t"> : never;

export type AlgorithmEventDraft = EventDraft<AlgorithmEvent>;
