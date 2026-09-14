import { afterEach, describe, expect, it, vi } from "vitest";

import { apiFetch } from "@/lib/api/client";

afterEach(() => vi.unstubAllGlobals());

describe("apiFetch", () => {
  it("includes cookie credentials and a default JSON accept header", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify({ ok: true }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(apiFetch<{ ok: boolean }>("/auth/me")).resolves.toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/auth/me",
      expect.objectContaining({ credentials: "include" }),
    );
    expect(new Headers(fetchMock.mock.calls[0]?.[1]?.headers).get("Accept")).toBe(
      "application/json",
    );
  });

  it("normalizes a structured backend error", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response(
            JSON.stringify({ error: { code: "UNAUTHORIZED", message: "Sign in required" } }),
            { status: 401, statusText: "Unauthorized" },
          ),
        ),
    );

    await expect(apiFetch("auth/me")).rejects.toMatchObject({
      code: "UNAUTHORIZED",
      message: "Sign in required",
      status: 401,
    });
  });

  it("normalizes network failures without leaking transport errors", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    await expect(apiFetch("algorithms")).rejects.toMatchObject({
      code: "NETWORK_ERROR",
      status: 0,
    });
  });
});
