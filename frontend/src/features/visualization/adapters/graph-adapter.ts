import type { ElementView, VisualizationAdapter } from "@/features/visualization/adapters/types";
import { EngineInvariantError } from "@/features/visualization/errors";
import type { ElementId, MarkStatus } from "@/features/visualization/events";
import type { GraphEdge, GraphNode } from "@/features/visualization/modules/types";

export interface GraphItem extends ElementView {
  position: { x: number; y: number };
}

export interface GraphState {
  nodes: GraphItem[];
  edges: GraphEdge[];
}

interface GraphInput {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

function node(nodes: GraphItem[], id: ElementId) {
  const result = nodes.find((candidate) => candidate.id === id);
  if (!result) throw new EngineInvariantError(`Unknown graph element ID: ${id}`);
  return result;
}

function setStatus(nodes: GraphItem[], ids: ElementId[], status: MarkStatus) {
  ids.forEach((id) => {
    node(nodes, id).status = status;
  });
}

function validate(input: unknown): GraphInput {
  if (
    !input ||
    typeof input !== "object" ||
    !Array.isArray((input as GraphInput).nodes) ||
    !Array.isArray((input as GraphInput).edges)
  ) {
    throw new TypeError("Graph adapter requires nodes and edges.");
  }
  const graph = input as GraphInput;
  const ids = new Set<string>();
  for (const graphNode of graph.nodes) {
    if (!graphNode.id || ids.has(graphNode.id))
      throw new EngineInvariantError("Graph node IDs must be unique.");
    if (
      !graphNode.position ||
      !Number.isFinite(graphNode.position.x) ||
      !Number.isFinite(graphNode.position.y)
    ) {
      throw new EngineInvariantError(
        `Graph node ${graphNode.id} requires a finite static position.`,
      );
    }
    ids.add(graphNode.id);
  }
  for (const edge of graph.edges) {
    if (!ids.has(edge.from) || !ids.has(edge.to))
      throw new EngineInvariantError(`Graph edge ${edge.id} references an unknown node.`);
  }
  return graph;
}

export const GraphAdapter: VisualizationAdapter<GraphState> = {
  kind: "graph",
  createInitialState(input, seed) {
    if (seed) throw new EngineInvariantError("Graph adapter does not accept element ID seeds.");
    const graph = validate(input);
    return {
      nodes: graph.nodes.map((entry) => ({
        id: entry.id,
        position: { ...entry.position! },
        status: "idle",
        ...(entry.label === undefined ? {} : { label: entry.label }),
        ...(entry.value === undefined ? {} : { value: entry.value }),
      })),
      edges: graph.edges.map((edge) => ({ ...edge })),
    };
  },
  reduce(state, event) {
    const nodes = state.nodes.map((entry) => ({ ...entry, position: { ...entry.position } }));
    switch (event.type) {
      case "compare":
        setStatus(nodes, event.ids, "comparing");
        break;
      case "visit":
        setStatus(nodes, [event.elementId], "visited");
        break;
      case "select":
        setStatus(nodes, event.ids, "current");
        break;
      case "mark":
        setStatus(nodes, [event.elementId], event.status);
        break;
      case "found":
        setStatus(nodes, event.ids, "found");
        break;
      case "relax":
        node(nodes, event.from);
        setStatus(nodes, [event.to], "frontier");
        break;
      case "enqueue":
      case "push":
        setStatus(nodes, [event.elementId], "frontier");
        break;
      case "dequeue":
      case "pop":
        setStatus(nodes, [event.elementId], "visited");
        break;
      default:
        break;
    }
    return { nodes, edges: state.edges.map((edge) => ({ ...edge })) };
  },
  getElementIds: (state) => state.nodes.map((entry) => entry.id),
  getElement: (state, id) => state.nodes.find((entry) => entry.id === id),
};
