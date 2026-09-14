export const algorithmCategories = ["All", "Sorting", "Searching", "Graphs", "Trees"] as const;

export type AlgorithmCategory = Exclude<(typeof algorithmCategories)[number], "All">;
export type AlgorithmDifficulty = "Easy" | "Medium" | "Hard";

export interface AlgorithmSummary {
  slug: string;
  name: string;
  description: string;
  category: AlgorithmCategory;
  difficulty: AlgorithmDifficulty;
  timeComplexity: string;
}

export const algorithms: readonly AlgorithmSummary[] = [
  {
    slug: "bubble-sort",
    name: "Bubble Sort",
    description: "Compare adjacent values and swap them into order.",
    category: "Sorting",
    difficulty: "Easy",
    timeComplexity: "O(n²)",
  },
  {
    slug: "merge-sort",
    name: "Merge Sort",
    description: "Divide a list, sort its halves, then merge them together.",
    category: "Sorting",
    difficulty: "Medium",
    timeComplexity: "O(n log n)",
  },
  {
    slug: "quick-sort",
    name: "Quick Sort",
    description: "Partition values around a pivot and recursively sort each side.",
    category: "Sorting",
    difficulty: "Medium",
    timeComplexity: "O(n log n)",
  },
  {
    slug: "binary-search",
    name: "Binary Search",
    description: "Repeatedly halve a sorted search space to find a target.",
    category: "Searching",
    difficulty: "Easy",
    timeComplexity: "O(log n)",
  },
  {
    slug: "breadth-first-search",
    name: "Breadth-First Search",
    description: "Visit graph neighbors layer by layer using a queue.",
    category: "Graphs",
    difficulty: "Medium",
    timeComplexity: "O(V + E)",
  },
  {
    slug: "dijkstra",
    name: "Dijkstra’s Algorithm",
    description: "Find shortest paths from a source in a weighted graph.",
    category: "Graphs",
    difficulty: "Hard",
    timeComplexity: "O((V + E) log V)",
  },
  {
    slug: "binary-search-tree",
    name: "Binary Search Tree",
    description: "Navigate an ordered tree to search, insert, and remove values.",
    category: "Trees",
    difficulty: "Medium",
    timeComplexity: "O(log n)",
  },
];
