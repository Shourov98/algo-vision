import { getAlgorithm } from "@/lib/api/algorithms";
import { apiFetch } from "@/lib/api/client";

export function reportAlgorithmCompletion(algorithmId: string) {
  return apiFetch(`progress/algorithms/${encodeURIComponent(algorithmId)}`, {
    body: JSON.stringify({ completion_percentage: 100, status: "completed" }),
    headers: { "Content-Type": "application/json" },
    method: "POST",
  });
}

export async function reportAlgorithmCompletionBySlug(slug: string) {
  const algorithm = await getAlgorithm(slug);
  await reportAlgorithmCompletion(algorithm.id);
}
