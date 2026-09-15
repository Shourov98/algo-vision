import { run } from "@/features/visualization/modules/heap-sort/run";
import type { ArrayAlgorithmModule } from "@/features/visualization/modules/types";
export { run } from "@/features/visualization/modules/heap-sort/run";
export const heapSortModule: ArrayAlgorithmModule<number[]> = {
  capabilities: {
    maxItems: 12,
    minItems: 2,
    requiresSortedInput: false,
    supportsDirection: true,
    supportsTarget: false,
  },
  slug: "heap-sort",
  visualizationKind: "heap",
  meta: {
    name: "Heap Sort",
    description: "Build a max heap, then extract its maximum values.",
    difficulty: "medium",
    complexity: { best: "O(n log n)", average: "O(n log n)", worst: "O(n log n)", space: "O(1)" },
    topics: ["arrays", "heaps", "sorting"],
  },
  defaultInput: () => [5, 2, 8, 1, 4],
  run,
};
