import { describe, expect, it, vi } from "vitest";
import { getDashboard } from "@/lib/api/dashboard";
import { apiFetch } from "@/lib/api/client";
vi.mock("@/lib/api/client", () => ({ apiFetch: vi.fn() }));
describe("dashboard API", () => {
  it("requests the dashboard summary", async () => {
    vi.mocked(apiFetch).mockResolvedValueOnce({} as never);
    await getDashboard();
    expect(apiFetch).toHaveBeenCalledWith("dashboard");
  });
});
