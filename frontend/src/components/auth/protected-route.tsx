"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";

import { useCurrentUser } from "@/lib/auth/auth-provider";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useCurrentUser();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) router.replace("/sign-in");
  }, [isAuthenticated, isLoading, router]);

  if (isLoading)
    return (
      <p aria-live="polite" className="p-6 text-text-muted">
        Checking your session…
      </p>
    );
  if (!isAuthenticated) return null;
  return <>{children}</>;
}
