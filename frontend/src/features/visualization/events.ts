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
  | (BaseEvent & { type: "visit"; elementId: ElementId })
  | (BaseEvent & { type: "select"; ids: ElementId[] })
  | (BaseEvent & { type: "insert"; elementId: ElementId; value: unknown })
  | (BaseEvent & { type: "delete"; elementId: ElementId })
  | (BaseEvent & { type: "update"; elementId: ElementId; value: unknown })
  | (BaseEvent & { type: "mark"; elementId: ElementId; status: MarkStatus })
  | (BaseEvent & { type: "relax"; from: ElementId; to: ElementId; weight?: number })
  | (BaseEvent & { type: "found"; ids: ElementId[] })
  | (BaseEvent & { type: "enqueue"; elementId: ElementId })
  | (BaseEvent & { type: "dequeue"; elementId: ElementId })
  | (BaseEvent & { type: "push"; elementId: ElementId; value: unknown })
  | (BaseEvent & { type: "pop"; elementId: ElementId })
  | (BaseEvent & { type: "complete"; summary?: Record<string, unknown> });

type EventDraft<Event extends BaseEvent> = Event extends Event ? Omit<Event, "id" | "t"> : never;

export type AlgorithmEventDraft = EventDraft<AlgorithmEvent>;
