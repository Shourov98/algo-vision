import type { AlgorithmMeta } from "@/features/visualization/modules/types";

export const binarySearchMeta: AlgorithmMeta = {
  name: "Binary Search",
  description: "Find a target in a sorted array by repeatedly halving the search range.",
  difficulty: "easy",
  complexity: { best: "O(1)", average: "O(log n)", worst: "O(log n)", space: "O(1)" },
  topics: ["arrays", "searching", "divide and conquer"],
};
