import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AuthProvider, useCurrentUser } from "@/lib/auth/auth-provider";
import { ApiError } from "@/lib/api/client";
import { getCurrentUser } from "@/lib/auth/auth";

vi.mock("@/lib/auth/auth", () => ({ getCurrentUser: vi.fn() }));
const mockedCurrentUser = vi.mocked(getCurrentUser);
function Consumer() {
  const { isAuthenticated, isLoading, user } = useCurrentUser();
  return <p>{isLoading ? "loading" : `${isAuthenticated}:${user?.email ?? "guest"}`}</p>;
}
function renderAuth() {
  return render(
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      <AuthProvider>
        <Consumer />
      </AuthProvider>
    </QueryClientProvider>,
  );
}
describe("AuthProvider", () => {
  it("exposes the current cookie-authenticated user", async () => {
    mockedCurrentUser.mockResolvedValueOnce({ id: "u1", email: "user@example.com" });
    renderAuth();
    expect(await screen.findByText("true:user@example.com")).toBeInTheDocument();
  });
  it("treats an unauthorized session as a guest", async () => {
    mockedCurrentUser.mockRejectedValueOnce(new ApiError("UNAUTHORIZED", "Sign in required", 401));
    renderAuth();
    expect(await screen.findByText("false:guest")).toBeInTheDocument();
  });
});
