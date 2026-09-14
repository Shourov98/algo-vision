import { AuthForm } from "@/components/auth/auth-form";
export default function SignInPage() {
  return (
    <section className="mx-auto w-full max-w-md px-6 py-16">
      <h1 className="text-3xl font-semibold text-foreground">Welcome back</h1>
      <p className="mt-2 text-text-muted">Sign in to continue learning.</p>
      <div className="mt-8 rounded-lg border border-border bg-surface p-6">
        <AuthForm mode="login" />
      </div>
    </section>
  );
}
