import { notFound } from "next/navigation";

import { AlgorithmVisualizerPage } from "@/components/visualization/algorithm-visualizer-page";

const algorithmSlugs = new Set(["binary-search", "bubble-sort", "quick-sort"]);

export default async function AlgorithmPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  if (!algorithmSlugs.has(slug)) notFound();

  return <AlgorithmVisualizerPage slug={slug} />;
}
