import type { SortDirection } from "@/features/visualization/modules/types";

export function resolveSortDirection(direction?: SortDirection): SortDirection {
  return direction ?? "ascending";
}

export function shouldSwapForDirection(left: number, right: number, direction: SortDirection) {
  return direction === "ascending" ? left > right : left < right;
}

export function shouldTakeLeftForDirection(left: number, right: number, direction: SortDirection) {
  return direction === "ascending" ? left <= right : left >= right;
}
