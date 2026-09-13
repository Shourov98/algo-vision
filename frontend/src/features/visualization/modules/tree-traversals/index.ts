import {
  createDefaultBst,
  type BstNode,
  assertBinarySearchTree,
} from "@/features/visualization/modules/bst/tree";
import type { AlgorithmEvent } from "@/features/visualization/events";
import type {
  AlgorithmMeta,
  RunOptions,
  TreeAlgorithmModule,
  TreeNode,
} from "@/features/visualization/modules/types";

type TraversalOrder = "in-order" | "pre-order" | "post-order";

const metadata: Record<TraversalOrder, AlgorithmMeta> = {
  "in-order": {
    name: "In-Order Traversal",
    description: "Visit left subtree, node, then right subtree.",
    difficulty: "easy",
    complexity: { best: "O(n)", average: "O(n)", worst: "O(n)", space: "O(h)" },
    topics: ["trees", "traversal"],
  },
  "pre-order": {
    name: "Pre-Order Traversal",
    description: "Visit node before its left and right subtrees.",
    difficulty: "easy",
    complexity: { best: "O(n)", average: "O(n)", worst: "O(n)", space: "O(h)" },
    topics: ["trees", "traversal"],
  },
  "post-order": {
    name: "Post-Order Traversal",
    description: "Visit child subtrees before their parent node.",
    difficulty: "easy",
    complexity: { best: "O(n)", average: "O(n)", worst: "O(n)", space: "O(h)" },
    topics: ["trees", "traversal"],
  },
};

function runTraversal(
  order: TraversalOrder,
  root: TreeNode | null,
  options?: RunOptions,
): AlgorithmEvent[] {
  assertBinarySearchTree(root);
  const events: AlgorithmEvent[] = [];
  let step = 0;
  const emitVisit = (node: BstNode) => {
    events.push({
      id: `${order}-${step}`,
      t: step,
      type: "visit",
      elementId: node.id,
      message: `Visiting ${node.value}.`,
      ...(options?.highlightLines === false ? {} : { line: 6 }),
    });
    step += 1;
  };
  const traverse = (node: BstNode | null) => {
    if (node === null) return;
    if (order === "pre-order") emitVisit(node);
    traverse(node.left);
    if (order === "in-order") emitVisit(node);
    traverse(node.right);
    if (order === "post-order") emitVisit(node);
  };
  traverse(root);
  events.push({
    id: `${order}-${step}`,
    t: step,
    type: "complete",
    message: "Traversal complete.",
    summary: { order, visited: step },
    ...(options?.highlightLines === false ? {} : { line: 8 }),
  });
  return events;
}

export const runInOrder = (root: TreeNode | null, options?: RunOptions) =>
  runTraversal("in-order", root, options);
export const runPreOrder = (root: TreeNode | null, options?: RunOptions) =>
  runTraversal("pre-order", root, options);
export const runPostOrder = (root: TreeNode | null, options?: RunOptions) =>
  runTraversal("post-order", root, options);

function moduleFor(
  order: TraversalOrder,
  run: (root: TreeNode | null, options?: RunOptions) => AlgorithmEvent[],
): TreeAlgorithmModule {
  return {
    slug: order,
    visualizationKind: "tree",
    meta: metadata[order],
    defaultRoot: createDefaultBst,
    run,
  };
}

export const inOrderModule = moduleFor("in-order", runInOrder);
export const preOrderModule = moduleFor("pre-order", runPreOrder);
export const postOrderModule = moduleFor("post-order", runPostOrder);
