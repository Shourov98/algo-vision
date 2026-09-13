import { createDefaultBst } from "@/features/visualization/modules/bst/tree";
import { bstInsertMeta } from "@/features/visualization/modules/bst-insert/meta";
import { run } from "@/features/visualization/modules/bst-insert/run";
import type { TreeAlgorithmModule } from "@/features/visualization/modules/types";

export { bstInsertMeta } from "@/features/visualization/modules/bst-insert/meta";
export { DEFAULT_INSERT_VALUE, run } from "@/features/visualization/modules/bst-insert/run";

export const bstInsertModule: TreeAlgorithmModule = {
  slug: "bst-insert",
  visualizationKind: "tree",
  meta: bstInsertMeta,
  defaultRoot: createDefaultBst,
  run,
};
