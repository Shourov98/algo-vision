import type { AlgorithmEvent, ElementId, MarkStatus } from "@/features/visualization/events";

export type VisualizationKind =
  | "array"
  | "linked-list"
  | "tree"
  | "graph"
  | "heap"
  | "dp-table"
  | "recursion-tree"
  | "stack-queue";

export interface ElementView {
  id: ElementId;
  label?: string;
  value?: unknown;
  status: MarkStatus;
  meta?: Record<string, unknown>;
}

export interface VisualizationAdapter<State> {
  readonly kind: VisualizationKind;
  createInitialState(input: unknown, seed?: ElementId[]): State;
  reduce(state: State, event: AlgorithmEvent): State;
  getElementIds(state: State): ElementId[];
  getElement(state: State, id: ElementId): ElementView | undefined;
}
