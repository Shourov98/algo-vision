import type { AlgorithmMeta } from "@/features/visualization/modules/types";

export const bubbleSortMeta: AlgorithmMeta = {
  name: "Bubble Sort",
  description: "Compare adjacent values and swap them until the array is sorted.",
  difficulty: "easy",
  complexity: {
    best: "O(n)",
    average: "O(n²)",
    worst: "O(n²)",
    space: "O(1)",
  },
  topics: ["arrays", "comparison sort", "sorting"],
};
