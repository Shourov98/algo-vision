import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api/client";

export interface DashboardSummary {
  algorithms_learned: number;
  algorithms_total: number;
  current_streak: number;
  interview_readiness: number;
  problems_solved: number;
}
export function getDashboard() {
  return apiFetch<DashboardSummary>("dashboard");
}
export function useDashboard() {
  return useQuery({ queryKey: ["dashboard"], queryFn: getDashboard });
}
