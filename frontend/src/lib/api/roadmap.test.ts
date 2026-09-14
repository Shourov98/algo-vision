import { describe, expect, it, vi } from "vitest";
import { getRoadmap } from "@/lib/api/roadmap";
import { apiFetch } from "@/lib/api/client";
vi.mock("@/lib/api/client", () => ({ apiFetch: vi.fn() }));
describe("roadmap API", () => {
  it("requests the roadmap", async () => {
    vi.mocked(apiFetch).mockResolvedValueOnce([]);
    await getRoadmap();
    expect(apiFetch).toHaveBeenCalledWith("roadmap");
  });
});
