import { mergeSortMeta } from "@/features/visualization/modules/merge-sort/meta";
import { run } from "@/features/visualization/modules/merge-sort/run";
import type { ArrayAlgorithmModule } from "@/features/visualization/modules/types";

export { mergeSortMeta } from "@/features/visualization/modules/merge-sort/meta";
export { run } from "@/features/visualization/modules/merge-sort/run";

export const mergeSortModule: ArrayAlgorithmModule<number[]> = {
  slug: "merge-sort",
  visualizationKind: "array",
  meta: mergeSortMeta,
  defaultInput: () => [8, 3, 6, 1, 7, 2],
  run,
};
