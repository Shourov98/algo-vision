import { ProtectedRoute } from "@/components/auth/protected-route";
import { RoadmapContent } from "@/components/roadmap/roadmap-content";
export default function RoadmapPage() {
  return (
    <ProtectedRoute>
      <div className="mx-auto w-full max-w-4xl px-6 py-12 lg:py-16">
        <p className="text-sm font-semibold tracking-[0.18em] text-accent-strong uppercase">
          Learning plan
        </p>
        <h1 className="mt-4 text-4xl font-semibold tracking-tight text-foreground">Your roadmap</h1>
        <p className="mt-4 text-lg text-text-muted">
          Follow a focused sequence of concepts and practice.
        </p>
        <div className="mt-10">
          <RoadmapContent />
        </div>
      </div>
    </ProtectedRoute>
  );
}
