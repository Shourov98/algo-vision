import { describe, expect, it, vi } from "vitest";

import { getAlgorithm, getAlgorithms } from "@/lib/api/algorithms";
import { apiFetch } from "@/lib/api/client";

vi.mock("@/lib/api/client", () => ({ apiFetch: vi.fn() }));
const fetchMock = vi.mocked(apiFetch);

describe("algorithms API client", () => {
  it("serializes list filters as query parameters", async () => {
    fetchMock.mockResolvedValueOnce({
      items: [],
      page: 1,
      page_size: 20,
      total: 0,
      total_pages: 0,
    });
    await getAlgorithms({ difficulty: "easy", page: 2, search: "sort" });
    expect(fetchMock).toHaveBeenCalledWith("algorithms?difficulty=easy&page=2&search=sort");
  });
  it("encodes algorithm slugs", async () => {
    fetchMock.mockResolvedValueOnce({} as never);
    await getAlgorithm("a/b");
    expect(fetchMock).toHaveBeenCalledWith("algorithms/a%2Fb");
  });
});
