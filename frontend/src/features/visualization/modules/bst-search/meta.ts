import type { AlgorithmMeta } from "@/features/visualization/modules/types";

export const bstSearchMeta: AlgorithmMeta = {
  name: "BST Search",
  description: "Follow ordered tree branches to locate a target value.",
  difficulty: "easy",
  complexity: { best: "O(1)", average: "O(log n)", worst: "O(n)", space: "O(1)" },
  topics: ["trees", "binary search tree", "searching"],
};
