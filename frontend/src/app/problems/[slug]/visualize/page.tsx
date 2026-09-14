import { notFound } from "next/navigation";

import { AlgorithmVisualizer } from "@/components/visualization/algorithm-visualizer";
import { VisualizationShell } from "@/components/visualization/visualization-shell";
import { twoSumModule } from "@/features/visualization/modules/two-sum";
import { twoSumCpp } from "@/features/visualization/modules/two-sum/code/cpp";
import { twoSumPython } from "@/features/visualization/modules/two-sum/code/python";
import { twoSumTypeScript } from "@/features/visualization/modules/two-sum/code/typescript";

export default async function ProblemVisualizationPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  if (slug !== "two-sum") notFound();
  return (
    <VisualizationShell
      complexity={twoSumModule.meta.complexity ?? {}}
      description={twoSumModule.meta.description}
      slug={twoSumModule.slug}
      title={twoSumModule.meta.name}
    >
      <AlgorithmVisualizer
        module={twoSumModule}
        sources={{ cpp: twoSumCpp, python: twoSumPython, typescript: twoSumTypeScript }}
      />
    </VisualizationShell>
  );
}
