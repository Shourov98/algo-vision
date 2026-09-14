import { describe, expect, it } from "vitest";

import {
  isArrayModule,
  isGraphModule,
  isTreeModule,
  type AlgorithmModule,
} from "@/features/visualization/modules/types";

const meta = {
  description: "A test algorithm.",
  difficulty: "easy" as const,
  name: "Test Algorithm",
  topics: ["testing"],
};

describe("algorithm module contracts", () => {
  it("narrows modules by their specialized input capability", () => {
    const modules: AlgorithmModule[] = [
      {
        defaultInput: () => [3, 1],
        meta,
        run: () => [],
        slug: "array-test",
        visualizationKind: "array",
      },
      {
        defaultRoot: () => null,
        meta,
        run: () => [],
        slug: "tree-test",
        visualizationKind: "tree",
      },
      {
        defaultGraph: () => ({ edges: [], nodes: [] }),
        meta,
        run: () => [],
        slug: "graph-test",
        visualizationKind: "graph",
      },
    ];

    expect(modules.filter(isArrayModule)).toHaveLength(1);
    expect(modules.filter(isTreeModule)).toHaveLength(1);
    expect(modules.filter(isGraphModule)).toHaveLength(1);
  });
});
