import { ProtectedRoute } from "@/components/auth/protected-route";
import { DashboardContent } from "@/components/dashboard/dashboard-content";
export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <div className="mx-auto w-full max-w-7xl px-6 py-12 lg:px-8 lg:py-16">
        <p className="text-sm font-semibold tracking-[0.18em] text-accent-strong uppercase">
          Your progress
        </p>
        <h1 className="mt-4 text-4xl font-semibold tracking-tight text-foreground">
          Learning dashboard
        </h1>
        <p className="mt-4 text-lg text-text-muted">A focused view of your algorithm practice.</p>
        <div className="mt-10">
          <DashboardContent />
        </div>
      </div>
    </ProtectedRoute>
  );
}
