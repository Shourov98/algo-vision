import { quickSortMeta } from "@/features/visualization/modules/quick-sort/meta";
import { run } from "@/features/visualization/modules/quick-sort/run";
import type { ArrayAlgorithmModule } from "@/features/visualization/modules/types";
export { quickSortMeta } from "@/features/visualization/modules/quick-sort/meta";
export { run } from "@/features/visualization/modules/quick-sort/run";
export const quickSortModule: ArrayAlgorithmModule<number[]> = {
  slug: "quick-sort",
  visualizationKind: "array",
  meta: quickSortMeta,
  defaultInput: () => [5, 2, 8, 1, 4],
  run,
};
