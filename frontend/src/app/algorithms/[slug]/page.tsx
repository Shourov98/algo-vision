import { notFound } from "next/navigation";

import { AlgorithmVisualizer } from "@/components/visualization/algorithm-visualizer";
import { VisualizationShell } from "@/components/visualization/visualization-shell";
import { bubbleSortModule } from "@/features/visualization/modules/bubble-sort";
import { bubbleSortCpp } from "@/features/visualization/modules/bubble-sort/code/cpp";
import { bubbleSortPython } from "@/features/visualization/modules/bubble-sort/code/python";
import { bubbleSortTypeScript } from "@/features/visualization/modules/bubble-sort/code/typescript";
import { quickSortModule } from "@/features/visualization/modules/quick-sort";
import { quickSortCpp } from "@/features/visualization/modules/quick-sort/code/cpp";
import { quickSortPython } from "@/features/visualization/modules/quick-sort/code/python";
import { quickSortTypeScript } from "@/features/visualization/modules/quick-sort/code/typescript";

const modules = {
  "bubble-sort": {
    module: bubbleSortModule,
    sources: { cpp: bubbleSortCpp, python: bubbleSortPython, typescript: bubbleSortTypeScript },
  },
  "quick-sort": {
    module: quickSortModule,
    sources: { cpp: quickSortCpp, python: quickSortPython, typescript: quickSortTypeScript },
  },
} as const;

export default async function AlgorithmPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const algorithm = modules[slug as keyof typeof modules];
  if (!algorithm) notFound();

  return (
    <VisualizationShell
      complexity={algorithm.module.meta.complexity ?? {}}
      description={algorithm.module.meta.description}
      slug={algorithm.module.slug}
      title={algorithm.module.meta.name}
    >
      <AlgorithmVisualizer module={algorithm.module} sources={algorithm.sources} />
    </VisualizationShell>
  );
}
