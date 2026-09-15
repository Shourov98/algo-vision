"use client";

import { DeferredAlgorithmVisualizer } from "@/components/visualization/deferred-algorithm-visualizer";
import { VisualizationShell } from "@/components/visualization/visualization-shell";
import { binarySearchModule } from "@/features/visualization/modules/binary-search";
import { binarySearchCpp } from "@/features/visualization/modules/binary-search/code/cpp";
import { binarySearchPython } from "@/features/visualization/modules/binary-search/code/python";
import { binarySearchTypeScript } from "@/features/visualization/modules/binary-search/code/typescript";
import { bubbleSortModule } from "@/features/visualization/modules/bubble-sort";
import { bubbleSortCpp } from "@/features/visualization/modules/bubble-sort/code/cpp";
import { bubbleSortPython } from "@/features/visualization/modules/bubble-sort/code/python";
import { bubbleSortTypeScript } from "@/features/visualization/modules/bubble-sort/code/typescript";
import { quickSortModule } from "@/features/visualization/modules/quick-sort";
import { quickSortCpp } from "@/features/visualization/modules/quick-sort/code/cpp";
import { quickSortPython } from "@/features/visualization/modules/quick-sort/code/python";
import { quickSortTypeScript } from "@/features/visualization/modules/quick-sort/code/typescript";

const modules = {
  "binary-search": {
    module: binarySearchModule,
    sources: {
      cpp: binarySearchCpp,
      python: binarySearchPython,
      typescript: binarySearchTypeScript,
    },
  },
  "bubble-sort": {
    module: bubbleSortModule,
    sources: { cpp: bubbleSortCpp, python: bubbleSortPython, typescript: bubbleSortTypeScript },
  },
  "quick-sort": {
    module: quickSortModule,
    sources: { cpp: quickSortCpp, python: quickSortPython, typescript: quickSortTypeScript },
  },
} as const;

export function AlgorithmVisualizerPage({ slug }: { slug: string }) {
  const algorithm = modules[slug as keyof typeof modules];

  return (
    <VisualizationShell
      complexity={algorithm.module.meta.complexity ?? {}}
      description={algorithm.module.meta.description}
      slug={algorithm.module.slug}
      title={algorithm.module.meta.name}
    >
      <DeferredAlgorithmVisualizer module={algorithm.module} sources={algorithm.sources} />
    </VisualizationShell>
  );
}
