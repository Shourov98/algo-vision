import { EngineInvariantError } from "@/features/visualization/errors";
import type { ElementId } from "@/features/visualization/events";
import type { TreeNode } from "@/features/visualization/modules/types";

export interface BstNode {
  id: ElementId;
  value: number;
  left: BstNode | null;
  right: BstNode | null;
}

export function createDefaultBst(): TreeNode {
  return {
    id: "node-8",
    value: 8,
    left: {
      id: "node-3",
      value: 3,
      left: { id: "node-1", value: 1, left: null, right: null },
      right: { id: "node-6", value: 6, left: null, right: null },
    },
    right: {
      id: "node-10",
      value: 10,
      left: null,
      right: { id: "node-14", value: 14, left: null, right: null },
    },
  };
}

export function assertBinarySearchTree(root: TreeNode | null): asserts root is BstNode | null {
  const ids = new Set<ElementId>();
  const ancestors = new Set<TreeNode>();
  const visit = (node: TreeNode | null, min: number, max: number) => {
    if (node === null) return;
    if (typeof node.id !== "string" || !node.id) {
      throw new EngineInvariantError("BST nodes require a non-empty string ID.");
    }
    if (typeof node.value !== "number" || !Number.isFinite(node.value)) {
      throw new TypeError("BST nodes require finite number values.");
    }
    if (node.value <= min || node.value >= max) {
      throw new EngineInvariantError("BST input must use strictly ordered values.");
    }
    if (ancestors.has(node)) throw new EngineInvariantError("BST input cannot contain cycles.");
    if (ids.has(node.id)) throw new EngineInvariantError(`Duplicate BST element ID: ${node.id}`);

    ancestors.add(node);
    ids.add(node.id);
    visit(node.left, min, node.value);
    visit(node.right, node.value, max);
    ancestors.delete(node);
  };

  visit(root, Number.NEGATIVE_INFINITY, Number.POSITIVE_INFINITY);
}

export function uniqueNodeId(root: TreeNode | null, value: number): ElementId {
  const ids = new Set<ElementId>();
  const collect = (node: TreeNode | null) => {
    if (node === null) return;
    ids.add(node.id);
    collect(node.left);
    collect(node.right);
  };
  collect(root);

  const base = `node-${value}`;
  let suffix = 1;
  let candidate = base;
  while (ids.has(candidate)) {
    candidate = `${base}-${suffix}`;
    suffix += 1;
  }
  return candidate;
}
