import type { AlgorithmMeta } from "@/features/visualization/modules/types";

export const mergeSortMeta: AlgorithmMeta = {
  name: "Merge Sort",
  description: "Split the array into smaller lists, then merge each sorted pair back together.",
  difficulty: "medium",
  complexity: { best: "O(n log n)", average: "O(n log n)", worst: "O(n log n)", space: "O(n)" },
  topics: ["arrays", "sorting", "divide and conquer"],
};
