import { ProtectedRoute } from "@/components/auth/protected-route";
import { SettingsContent } from "@/components/settings/settings-content";
export default function SettingsPage() {
  return (
    <ProtectedRoute>
      <div className="mx-auto w-full max-w-3xl px-6 py-12 lg:py-16">
        <p className="text-sm font-semibold tracking-[0.18em] text-accent-strong uppercase">
          Preferences
        </p>
        <h1 className="mt-4 text-4xl font-semibold tracking-tight text-foreground">Settings</h1>
        <p className="mt-4 text-lg text-text-muted">
          Control how algorithm visualizations are presented.
        </p>
        <div className="mt-10 rounded-lg border border-border bg-surface-raised p-6">
          <h2 className="text-xl font-semibold text-foreground">Visualization</h2>
          <div className="mt-5">
            <SettingsContent />
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
