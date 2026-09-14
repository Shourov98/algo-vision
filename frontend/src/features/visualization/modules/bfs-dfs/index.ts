import type { AlgorithmEvent, AlgorithmEventDraft } from "@/features/visualization/events";
import type {
  GraphEdge,
  GraphNode,
  GraphAlgorithmModule,
  RunOptions,
} from "@/features/visualization/modules/types";

export interface GraphInput {
  nodes: GraphNode[];
  edges: GraphEdge[];
  source: string;
}
export const defaultGraph = (): GraphInput => ({
  source: "a",
  nodes: [
    { id: "a", label: "A", position: { x: 0, y: 0 } },
    { id: "b", label: "B", position: { x: 100, y: -40 } },
    { id: "c", label: "C", position: { x: 100, y: 40 } },
    { id: "d", label: "D", position: { x: 200, y: 0 } },
  ],
  edges: [
    { id: "a-b", from: "a", to: "b" },
    { id: "a-c", from: "a", to: "c" },
    { id: "b-d", from: "b", to: "d" },
    { id: "c-d", from: "c", to: "d" },
  ],
});

function adjacency(input: GraphInput) {
  const ids = new Set(input.nodes.map((node) => node.id));
  if (!ids.has(input.source)) throw new TypeError("Graph source must be a node.");
  const graph = new Map(input.nodes.map((node) => [node.id, [] as string[]]));
  input.edges.forEach((edge) => {
    if (!ids.has(edge.from) || !ids.has(edge.to))
      throw new TypeError("Graph edges must reference nodes.");
    graph.get(edge.from)!.push(edge.to);
  });
  return graph;
}
function emitters(name: string, options?: RunOptions) {
  const events: AlgorithmEvent[] = [];
  let step = 0;
  const emit = (event: AlgorithmEventDraft) => {
    events.push({
      ...event,
      id: `${name}-${step}`,
      t: step,
      ...(options?.highlightLines === false ? {} : { line: 6 }),
    } as AlgorithmEvent);
    step += 1;
  };
  return { events, emit };
}
export function runBfs(input: GraphInput, options?: RunOptions): AlgorithmEvent[] {
  const graph = adjacency(input);
  const { events, emit } = emitters("bfs", options);
  const queue = [input.source],
    seen = new Set(queue);
  emit({ type: "enqueue", elementId: input.source, message: `Enqueue ${input.source}.` });
  while (queue.length) {
    const id = queue.shift()!;
    emit({ type: "dequeue", elementId: id, message: `Dequeue ${id}.` });
    emit({ type: "visit", elementId: id, message: `Visit ${id}.` });
    for (const next of graph.get(id)!) {
      if (!seen.has(next)) {
        seen.add(next);
        queue.push(next);
        emit({ type: "enqueue", elementId: next, message: `Enqueue ${next}.` });
      }
    }
  }
  emit({ type: "complete", message: "BFS complete.", summary: { visited: [...seen] } });
  return events;
}
export function runDfs(input: GraphInput, options?: RunOptions): AlgorithmEvent[] {
  const graph = adjacency(input);
  const { events, emit } = emitters("dfs", options);
  const seen = new Set<string>();
  const visit = (id: string) => {
    seen.add(id);
    emit({ type: "visit", elementId: id, message: `Visit ${id}.` });
    for (const next of graph.get(id)!) {
      if (!seen.has(next)) {
        emit({ type: "select", ids: [next], message: `Explore ${next} from ${id}.` });
        visit(next);
      }
    }
  };
  visit(input.source);
  emit({ type: "complete", message: "DFS complete.", summary: { visited: [...seen] } });
  return events;
}
export const bfsModule: GraphAlgorithmModule = {
  slug: "breadth-first-search",
  visualizationKind: "graph",
  meta: {
    name: "Breadth-First Search",
    description: "Visit graph neighbors layer by layer.",
    difficulty: "medium",
    complexity: { best: "O(V + E)", average: "O(V + E)", worst: "O(V + E)", space: "O(V)" },
    topics: ["graphs", "searching", "queues"],
  },
  defaultGraph: () => {
    const { nodes, edges } = defaultGraph();
    return { nodes, edges };
  },
  run: runBfs,
};
export const dfsModule: GraphAlgorithmModule = {
  slug: "depth-first-search",
  visualizationKind: "graph",
  meta: {
    name: "Depth-First Search",
    description: "Explore each graph branch before backtracking.",
    difficulty: "medium",
    complexity: { best: "O(V + E)", average: "O(V + E)", worst: "O(V + E)", space: "O(V)" },
    topics: ["graphs", "searching", "recursion"],
  },
  defaultGraph: () => {
    const { nodes, edges } = defaultGraph();
    return { nodes, edges };
  },
  run: runDfs,
};
