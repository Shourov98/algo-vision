import { bubbleSortMeta } from "@/features/visualization/modules/bubble-sort/meta";
import { run } from "@/features/visualization/modules/bubble-sort/run";
import type { ArrayAlgorithmModule } from "@/features/visualization/modules/types";

export { bubbleSortMeta } from "@/features/visualization/modules/bubble-sort/meta";
export { run } from "@/features/visualization/modules/bubble-sort/run";

export const bubbleSortModule: ArrayAlgorithmModule<number[]> = {
  slug: "bubble-sort",
  visualizationKind: "array",
  meta: bubbleSortMeta,
  defaultInput: () => [5, 2, 8, 1, 4],
  run,
};
