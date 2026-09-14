import { AuthForm } from "@/components/auth/auth-form";
export default function SignUpPage() {
  return (
    <section className="mx-auto w-full max-w-md px-6 py-16">
      <h1 className="text-3xl font-semibold text-foreground">Create your account</h1>
      <p className="mt-2 text-text-muted">Track your progress as you learn.</p>
      <div className="mt-8 rounded-lg border border-border bg-surface p-6">
        <AuthForm mode="register" />
      </div>
    </section>
  );
}
