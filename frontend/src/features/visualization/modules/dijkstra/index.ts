import type { AlgorithmEvent, AlgorithmEventDraft } from "@/features/visualization/events";
import type {
  GraphEdge,
  GraphNode,
  GraphAlgorithmModule,
  RunOptions,
} from "@/features/visualization/modules/types";
export interface DijkstraInput {
  nodes: GraphNode[];
  edges: GraphEdge[];
  source: string;
}
export const defaultDijkstraGraph = (): DijkstraInput => ({
  source: "a",
  nodes: [
    { id: "a", label: "A", position: { x: 0, y: 0 } },
    { id: "b", label: "B", position: { x: 100, y: -40 } },
    { id: "c", label: "C", position: { x: 100, y: 40 } },
    { id: "d", label: "D", position: { x: 200, y: 0 } },
  ],
  edges: [
    { id: "a-b", from: "a", to: "b", weight: 4 },
    { id: "a-c", from: "a", to: "c", weight: 1 },
    { id: "c-b", from: "c", to: "b", weight: 2 },
    { id: "b-d", from: "b", to: "d", weight: 1 },
    { id: "c-d", from: "c", to: "d", weight: 5 },
  ],
});
export function run(input: DijkstraInput, options?: RunOptions): AlgorithmEvent[] {
  const ids = new Set(input.nodes.map((n) => n.id));
  if (!ids.has(input.source)) throw new TypeError("Dijkstra source must be a node.");
  const adj = new Map(input.nodes.map((n) => [n.id, [] as GraphEdge[]]));
  for (const e of input.edges) {
    if (!ids.has(e.from) || !ids.has(e.to) || e.weight === undefined || e.weight < 0)
      throw new TypeError("Dijkstra requires non-negative weighted edges.");
    adj.get(e.from)!.push(e);
  }
  const distances = Object.fromEntries(input.nodes.map((n) => [n.id, Infinity])) as Record<
    string,
    number
  >;
  distances[input.source] = 0;
  const events: AlgorithmEvent[] = [];
  let step = 0;
  const emit = (event: AlgorithmEventDraft) => {
    events.push({
      ...event,
      id: `dijkstra-${step}`,
      t: step,
      ...(options?.highlightLines === false ? {} : { line: 8 }),
    } as AlgorithmEvent);
    step += 1;
  };
  const queue: [string, number][] = [[input.source, 0]];
  emit({
    type: "enqueue",
    elementId: input.source,
    message: `Queue ${input.source} at distance 0.`,
  });
  while (queue.length) {
    queue.sort((a, b) => a[1] - b[1] || a[0].localeCompare(b[0]));
    const [id, d] = queue.shift()!;
    if (d !== distances[id]) continue;
    emit({ type: "dequeue", elementId: id, message: `Dequeue ${id} at distance ${d}.` });
    for (const e of adj.get(id)!) {
      const weight = e.weight!;
      const next = d + weight;
      if (next < (distances[e.to] ?? Number.POSITIVE_INFINITY)) {
        distances[e.to] = next;
        emit({
          type: "relax",
          from: id,
          to: e.to,
          weight,
          message: `Update ${e.to} to distance ${next}.`,
        });
        queue.push([e.to, next]);
        emit({ type: "enqueue", elementId: e.to, message: `Queue ${e.to} at distance ${next}.` });
      }
    }
    emit({ type: "visit", elementId: id, message: `Finalize ${id}.` });
  }
  emit({ type: "complete", message: "Dijkstra complete.", summary: { distances } });
  return events;
}
export const dijkstraModule: GraphAlgorithmModule = {
  slug: "dijkstra",
  visualizationKind: "graph",
  meta: {
    name: "Dijkstra’s Algorithm",
    description: "Find shortest paths from a source using a priority queue.",
    difficulty: "hard",
    complexity: {
      best: "O((V + E) log V)",
      average: "O((V + E) log V)",
      worst: "O((V + E) log V)",
      space: "O(V)",
    },
    topics: ["graphs", "shortest path", "priority queue"],
  },
  defaultGraph: () => {
    const { nodes, edges } = defaultDijkstraGraph();
    return { nodes, edges };
  },
  run,
};
