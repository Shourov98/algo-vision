import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api/client";
export interface RoadmapItem {
  id: string;
  item_type: string;
  status?: string;
  title?: string;
}
export interface RoadmapStage {
  id: string;
  title: string;
  description?: string;
  items: RoadmapItem[];
  sort_order: number;
}
export function getRoadmap() {
  return apiFetch<RoadmapStage[]>("roadmap");
}
export function useRoadmap() {
  return useQuery({ queryKey: ["roadmap"], queryFn: getRoadmap });
}
