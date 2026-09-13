import { binarySearchMeta } from "@/features/visualization/modules/binary-search/meta";
import { run } from "@/features/visualization/modules/binary-search/run";
import type { ArrayAlgorithmModule } from "@/features/visualization/modules/types";

export { binarySearchMeta } from "@/features/visualization/modules/binary-search/meta";
export { DEFAULT_TARGET, run } from "@/features/visualization/modules/binary-search/run";

export const binarySearchModule: ArrayAlgorithmModule<number[]> = {
  slug: "binary-search",
  visualizationKind: "array",
  meta: binarySearchMeta,
  defaultInput: () => [1, 3, 5, 7, 9, 11],
  run,
};
