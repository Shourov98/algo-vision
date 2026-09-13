import { createDefaultBst } from "@/features/visualization/modules/bst/tree";
import { bstSearchMeta } from "@/features/visualization/modules/bst-search/meta";
import { run } from "@/features/visualization/modules/bst-search/run";
import type { TreeAlgorithmModule } from "@/features/visualization/modules/types";

export { bstSearchMeta } from "@/features/visualization/modules/bst-search/meta";
export { DEFAULT_TARGET, run } from "@/features/visualization/modules/bst-search/run";

export const bstSearchModule: TreeAlgorithmModule = {
  slug: "bst-search",
  visualizationKind: "tree",
  meta: bstSearchMeta,
  defaultRoot: createDefaultBst,
  run,
};
