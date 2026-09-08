import type { VisualizationAdapter } from "@/features/visualization/adapters/types";
import type { AlgorithmEvent, ElementId } from "@/features/visualization/events";

export interface AlgorithmMeta {
  name: string;
  description: string;
  difficulty: "easy" | "medium" | "hard";
  complexity?: {
    best?: string;
    average?: string;
    worst?: string;
    space?: string;
  };
  topics: string[];
}

export interface RunOptions {
  seed?: number;
  highlightLines?: boolean;
}

export interface TreeNode {
  id: ElementId;
  value: unknown;
  left: TreeNode | null;
  right: TreeNode | null;
}

export interface GraphNode {
  id: ElementId;
  label?: string;
  value?: unknown;
}

export interface GraphEdge {
  id: string;
  from: ElementId;
  to: ElementId;
  weight?: number;
}

export interface AlgorithmModuleBase {
  slug: string;
  visualizationKind: VisualizationAdapter<unknown>["kind"];
  meta: AlgorithmMeta;
  run(input: unknown, options?: RunOptions): AlgorithmEvent[];
}

export interface HasDefaultInput<Input> {
  defaultInput: () => Input;
}

export interface HasRootInput {
  defaultRoot: () => TreeNode | null;
}

export interface HasGraphInput {
  defaultGraph: () => { nodes: GraphNode[]; edges: GraphEdge[] };
}

export type ArrayAlgorithmModule<Input = number[]> = AlgorithmModuleBase & HasDefaultInput<Input>;
export type TreeAlgorithmModule = AlgorithmModuleBase & HasRootInput;
export type GraphAlgorithmModule = AlgorithmModuleBase & HasGraphInput;
export type AlgorithmModule = ArrayAlgorithmModule | TreeAlgorithmModule | GraphAlgorithmModule;

export function isArrayModule(module: AlgorithmModule): module is ArrayAlgorithmModule {
  return "defaultInput" in module;
}

export function isTreeModule(module: AlgorithmModule): module is TreeAlgorithmModule {
  return "defaultRoot" in module;
}

export function isGraphModule(module: AlgorithmModule): module is GraphAlgorithmModule {
  return "defaultGraph" in module;
}
