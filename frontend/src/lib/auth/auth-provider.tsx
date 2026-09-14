"use client";

import { useQuery } from "@tanstack/react-query";
import { createContext, useContext, type ReactNode } from "react";

import { ApiError } from "@/lib/api/client";
import { getCurrentUser, type CurrentUser } from "@/lib/auth/auth";

interface AuthContextValue {
  isAuthenticated: boolean;
  isLoading: boolean;
  refresh: () => Promise<unknown>;
  user: CurrentUser | null;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const query = useQuery({
    queryKey: ["auth", "current-user"],
    queryFn: getCurrentUser,
    retry: false,
  });
  const unauthenticated = query.error instanceof ApiError && query.error.status === 401;
  const user = unauthenticated ? null : (query.data ?? null);

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: user !== null,
        isLoading: query.isLoading,
        refresh: query.refetch,
        user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useCurrentUser() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useCurrentUser must be used within AuthProvider.");
  return context;
}
