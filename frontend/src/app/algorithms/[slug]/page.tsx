import { notFound } from "next/navigation";

import { AlgorithmVisualizer } from "@/components/visualization/algorithm-visualizer";
import { VisualizationShell } from "@/components/visualization/visualization-shell";
import { bubbleSortModule } from "@/features/visualization/modules/bubble-sort";
import { bubbleSortCpp } from "@/features/visualization/modules/bubble-sort/code/cpp";
import { bubbleSortPython } from "@/features/visualization/modules/bubble-sort/code/python";
import { bubbleSortTypeScript } from "@/features/visualization/modules/bubble-sort/code/typescript";

const modules = { "bubble-sort": bubbleSortModule } as const;

export default async function AlgorithmPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const algorithmModule = modules[slug as keyof typeof modules];
  if (!algorithmModule) notFound();

  return (
    <VisualizationShell
      complexity={algorithmModule.meta.complexity ?? {}}
      description={algorithmModule.meta.description}
      slug={algorithmModule.slug}
      title={algorithmModule.meta.name}
    >
      <AlgorithmVisualizer
        module={algorithmModule}
        sources={{ cpp: bubbleSortCpp, python: bubbleSortPython, typescript: bubbleSortTypeScript }}
      />
    </VisualizationShell>
  );
}
