import { describe, expect, it, vi } from "vitest";

import { problems } from "@/features/problems/mock-data";
import { run as runTwoSum } from "@/features/visualization/modules/two-sum";
import { getDashboard } from "@/lib/api/dashboard";
import { apiFetch } from "@/lib/api/client";
import { getRoadmap } from "@/lib/api/roadmap";

vi.mock("@/lib/api/client", () => ({ apiFetch: vi.fn() }));
const fetchMock = vi.mocked(apiFetch);

describe("Phase 6 page invariants", () => {
  it("keeps problem catalog routes unique and exposes the Two Sum visualizer", () => {
    expect(new Set(problems.map((problem) => problem.slug))).toHaveLength(problems.length);
    expect(problems.find((problem) => problem.slug === "two-sum")).toBeDefined();
    const events = runTwoSum([2, 7, 11, 15]);
    expect(runTwoSum([2, 7, 11, 15])).toEqual(events);
    expect(events.at(-1)?.type).toBe("complete");
    expect(events.some((event) => event.type === "found")).toBe(true);
  });

  it("uses the protected-page API boundaries for dashboard and roadmap data", async () => {
    fetchMock.mockResolvedValueOnce({} as never).mockResolvedValueOnce([]);
    await getDashboard();
    await getRoadmap();
    expect(fetchMock).toHaveBeenNthCalledWith(1, "dashboard");
    expect(fetchMock).toHaveBeenNthCalledWith(2, "roadmap");
  });
});
