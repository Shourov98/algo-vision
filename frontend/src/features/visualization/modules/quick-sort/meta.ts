import type { AlgorithmMeta } from "@/features/visualization/modules/types";

export const quickSortMeta: AlgorithmMeta = {
  name: "Quick Sort",
  description: "Partition values around a pivot, then recursively sort each partition.",
  difficulty: "medium",
  complexity: { best: "O(n log n)", average: "O(n log n)", worst: "O(n²)", space: "O(log n)" },
  topics: ["arrays", "divide and conquer", "sorting"],
};
