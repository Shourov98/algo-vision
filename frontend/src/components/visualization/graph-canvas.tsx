import type { GraphState } from "@/features/visualization/adapters/graph-adapter";

const statusClass = {
  comparing: "fill-warning text-surface",
  found: "fill-success text-surface",
  frontier: "fill-accent-strong text-surface",
  visited: "fill-surface-raised text-foreground",
} as const;

export function GraphNode({ node }: { node: GraphState["nodes"][number] }) {
  const tone =
    statusClass[node.status as keyof typeof statusClass] ?? "fill-surface text-foreground";
  return (
    <g aria-label={`Node ${node.label ?? node.id}: ${node.status}`} className={tone}>
      <circle
        className="stroke-border"
        cx={node.position.x}
        cy={node.position.y}
        r="24"
        strokeWidth="2"
      />
      <text
        className="pointer-events-none fill-current text-xs font-semibold"
        dominantBaseline="middle"
        textAnchor="middle"
        x={node.position.x}
        y={node.position.y}
      >
        {node.label ?? node.id}
      </text>
    </g>
  );
}

export function GraphEdge({
  edge,
  nodes,
}: {
  edge: GraphState["edges"][number];
  nodes: GraphState["nodes"];
}) {
  const from = nodes.find((node) => node.id === edge.from);
  const to = nodes.find((node) => node.id === edge.to);
  if (!from || !to) return null;
  const x = (from.position.x + to.position.x) / 2;
  const y = (from.position.y + to.position.y) / 2;
  return (
    <g aria-label={`Edge ${edge.from} to ${edge.to}`}>
      <line
        className="stroke-border"
        strokeWidth="2"
        x1={from.position.x}
        x2={to.position.x}
        y1={from.position.y}
        y2={to.position.y}
      />
      {edge.weight === undefined ? null : (
        <text className="fill-text-muted text-xs" textAnchor="middle" x={x} y={y - 6}>
          {edge.weight}
        </text>
      )}
    </g>
  );
}

export function GraphCanvas({ state }: { state: GraphState }) {
  const width = Math.max(320, ...state.nodes.map((node) => node.position.x + 48));
  const height = Math.max(180, ...state.nodes.map((node) => node.position.y + 72));
  return (
    <section
      aria-label="Graph visualization"
      className="overflow-x-auto rounded-lg border border-border bg-surface-raised p-4"
    >
      <svg
        className="min-w-80"
        height={height}
        role="img"
        viewBox={`-32 -72 ${width} ${height + 72}`}
        width={width}
      >
        {state.edges.map((edge) => (
          <GraphEdge edge={edge} key={edge.id} nodes={state.nodes} />
        ))}
        {state.nodes.map((node) => (
          <GraphNode key={node.id} node={node} />
        ))}
      </svg>
    </section>
  );
}
