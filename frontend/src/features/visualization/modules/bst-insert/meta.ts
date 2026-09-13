import type { AlgorithmMeta } from "@/features/visualization/modules/types";

export const bstInsertMeta: AlgorithmMeta = {
  name: "BST Insert",
  description:
    "Traverse an ordered binary search tree and attach a new leaf in its valid position.",
  difficulty: "medium",
  complexity: { best: "O(log n)", average: "O(log n)", worst: "O(n)", space: "O(1)" },
  topics: ["trees", "binary search tree", "insertion"],
};
