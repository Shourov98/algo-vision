import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ProtectedRoute } from "@/components/auth/protected-route";

const replace = vi.fn();
const useCurrentUser = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ replace }) }));
vi.mock("@/lib/auth/auth-provider", () => ({ useCurrentUser: () => useCurrentUser() }));

describe("ProtectedRoute", () => {
  it("shows a session loading state", () => {
    useCurrentUser.mockReturnValue({ isAuthenticated: false, isLoading: true });
    render(
      <ProtectedRoute>
        <p>Private</p>
      </ProtectedRoute>,
    );
    expect(screen.getByText("Checking your session…")).toBeInTheDocument();
  });
  it("redirects guests without rendering private content", () => {
    useCurrentUser.mockReturnValue({ isAuthenticated: false, isLoading: false });
    render(
      <ProtectedRoute>
        <p>Private</p>
      </ProtectedRoute>,
    );
    expect(replace).toHaveBeenCalledWith("/sign-in");
    expect(screen.queryByText("Private")).toBeNull();
  });
  it("renders children for an authenticated user", () => {
    useCurrentUser.mockReturnValue({ isAuthenticated: true, isLoading: false });
    render(
      <ProtectedRoute>
        <p>Private</p>
      </ProtectedRoute>,
    );
    expect(screen.getByText("Private")).toBeInTheDocument();
  });
});
