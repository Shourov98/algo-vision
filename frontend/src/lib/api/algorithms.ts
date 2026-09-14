import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api/client";

export interface AlgorithmDetail {
  average_time: string | null;
  best_time: string | null;
  description: string;
  difficulty: string;
  id: string;
  name: string;
  slug: string;
  space_complexity: string | null;
  visualization_type: string;
  worst_time: string | null;
}

export interface AlgorithmPage {
  items: AlgorithmDetail[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface AlgorithmFilters {
  category?: string;
  difficulty?: string;
  page?: number;
  page_size?: number;
  search?: string;
  topic?: string;
}

function query(filters: AlgorithmFilters) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== "") params.set(key, String(value));
  });
  const value = params.toString();
  return value ? `algorithms?${value}` : "algorithms";
}

export function getAlgorithms(filters: AlgorithmFilters = {}) {
  return apiFetch<AlgorithmPage>(query(filters));
}

export function getAlgorithm(slug: string) {
  return apiFetch<AlgorithmDetail>(`algorithms/${encodeURIComponent(slug)}`);
}

export function useAlgorithms(filters: AlgorithmFilters = {}) {
  return useQuery({ queryKey: ["algorithms", filters], queryFn: () => getAlgorithms(filters) });
}

export function useAlgorithm(slug: string) {
  return useQuery({
    enabled: Boolean(slug),
    queryKey: ["algorithms", slug],
    queryFn: () => getAlgorithm(slug),
  });
}
