import { describe, expect, it, vi } from "vitest";

import { getAlgorithm } from "@/lib/api/algorithms";
import { apiFetch } from "@/lib/api/client";
import { reportAlgorithmCompletion, reportAlgorithmCompletionBySlug } from "@/lib/api/progress";

vi.mock("@/lib/api/algorithms", () => ({ getAlgorithm: vi.fn() }));
vi.mock("@/lib/api/client", () => ({ apiFetch: vi.fn() }));
const fetchMock = vi.mocked(apiFetch);
const getAlgorithmMock = vi.mocked(getAlgorithm);

describe("progress API client", () => {
  it("reports completed algorithm progress", async () => {
    fetchMock.mockResolvedValueOnce({});
    await reportAlgorithmCompletion("algorithm id");
    expect(fetchMock).toHaveBeenCalledWith("progress/algorithms/algorithm%20id", {
      body: JSON.stringify({ completion_percentage: 100, status: "completed" }),
      headers: { "Content-Type": "application/json" },
      method: "POST",
    });
  });
  it("resolves a slug before reporting completion", async () => {
    getAlgorithmMock.mockResolvedValueOnce({ id: "a1" } as never);
    fetchMock.mockResolvedValueOnce({});
    await reportAlgorithmCompletionBySlug("bubble-sort");
    expect(fetchMock).toHaveBeenCalledWith("progress/algorithms/a1", expect.anything());
  });
});
