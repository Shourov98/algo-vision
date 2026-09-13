import type { ElementView, VisualizationAdapter } from "@/features/visualization/adapters/types";
import { EngineInvariantError } from "@/features/visualization/errors";
import type { ElementId, MarkStatus } from "@/features/visualization/events";
import type { TreeNode } from "@/features/visualization/modules/types";

export interface TreeItem extends ElementView {
  value: unknown;
  leftId: ElementId | null;
  rightId: ElementId | null;
}

export interface TreeState {
  rootId: ElementId | null;
  nodes: TreeItem[];
}

function getItem(nodes: TreeItem[], id: ElementId): TreeItem {
  const item = nodes.find((candidate) => candidate.id === id);
  if (!item) throw new EngineInvariantError(`Unknown tree element ID: ${id}`);
  return item;
}

function setStatuses(nodes: TreeItem[], ids: ElementId[], status: MarkStatus) {
  for (const id of ids) getItem(nodes, id).status = status;
}

function createTreeState(input: unknown): TreeState {
  if (input === null) return { rootId: null, nodes: [] };
  if (typeof input !== "object") throw new TypeError("Tree adapter requires a tree root or null.");

  const nodes: TreeItem[] = [];
  const seenIds = new Set<ElementId>();
  const ancestors = new Set<TreeNode>();
  const visit = (node: TreeNode | null): ElementId | null => {
    if (node === null) return null;
    if (typeof node !== "object" || typeof node.id !== "string" || !node.id) {
      throw new EngineInvariantError("Tree nodes require a non-empty string ID.");
    }
    if (ancestors.has(node)) throw new EngineInvariantError("Tree input cannot contain cycles.");
    if (seenIds.has(node.id))
      throw new EngineInvariantError(`Duplicate tree element ID: ${node.id}`);

    ancestors.add(node);
    seenIds.add(node.id);
    const item: TreeItem = {
      id: node.id,
      status: "idle",
      value: node.value,
      leftId: null,
      rightId: null,
    };
    nodes.push(item);
    const leftId = visit(node.left);
    const rightId = visit(node.right);
    ancestors.delete(node);
    item.leftId = leftId;
    item.rightId = rightId;
    return node.id;
  };

  const rootId = visit(input as TreeNode);
  return { rootId, nodes };
}

export const TreeAdapter: VisualizationAdapter<TreeState> = {
  kind: "tree",

  createInitialState(input, seed) {
    if (seed) throw new EngineInvariantError("Tree adapter does not accept element ID seeds.");
    return createTreeState(input);
  },

  reduce(state, event) {
    const nodes = state.nodes.map((node) => ({ ...node }));
    let rootId = state.rootId;

    switch (event.type) {
      case "compare":
        setStatuses(nodes, event.ids, "comparing");
        break;
      case "swap":
        setStatuses(nodes, event.ids, "swapping");
        break;
      case "visit":
        setStatuses(nodes, [event.elementId], "visited");
        break;
      case "select":
        for (const node of nodes) if (node.status === "pivot") node.status = "idle";
        setStatuses(nodes, event.ids, "pivot");
        break;
      case "insert": {
        if (nodes.some((node) => node.id === event.elementId)) {
          throw new EngineInvariantError(`Tree element ID already exists: ${event.elementId}`);
        }
        if (event.parentId === undefined) {
          if (rootId !== null)
            throw new EngineInvariantError("Inserted tree nodes require a parent.");
          rootId = event.elementId;
        } else {
          if (!event.position)
            throw new EngineInvariantError("Inserted tree nodes require a position.");
          const parent = getItem(nodes, event.parentId);
          const childKey = event.position === "left" ? "leftId" : "rightId";
          if (parent[childKey] !== null) {
            throw new EngineInvariantError(`Tree parent already has a ${event.position} child.`);
          }
          parent[childKey] = event.elementId;
        }
        nodes.push({
          id: event.elementId,
          status: "active",
          value: event.value,
          leftId: null,
          rightId: null,
        });
        break;
      }
      case "delete": {
        const node = getItem(nodes, event.elementId);
        if (node.leftId !== null || node.rightId !== null) {
          throw new EngineInvariantError("Tree adapter can only delete leaf nodes.");
        }
        for (const parent of nodes) {
          if (parent.leftId === node.id) parent.leftId = null;
          if (parent.rightId === node.id) parent.rightId = null;
        }
        if (rootId === node.id) rootId = null;
        nodes.splice(nodes.indexOf(node), 1);
        break;
      }
      case "update":
        getItem(nodes, event.elementId).value = event.value;
        break;
      case "mark":
        setStatuses(nodes, [event.elementId], event.status);
        break;
      case "relax":
        getItem(nodes, event.from);
        getItem(nodes, event.to);
        break;
      case "found":
        setStatuses(nodes, event.ids, "found");
        break;
      case "enqueue":
      case "push":
        setStatuses(nodes, [event.elementId], "active");
        break;
      case "dequeue":
      case "pop":
        setStatuses(nodes, [event.elementId], "idle");
        break;
      case "complete":
        break;
    }

    return { rootId, nodes };
  },

  getElementIds(state) {
    return state.nodes.map((node) => node.id);
  },

  getElement(state, id) {
    return state.nodes.find((node) => node.id === id);
  },
};
