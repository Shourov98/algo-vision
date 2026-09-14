"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { ApiError } from "@/lib/api/client";
import { useCurrentUser } from "@/lib/auth/auth-provider";
import { login, register } from "@/lib/auth/auth";

const schema = z.object({
  displayName: z.string().max(100, "Use 100 characters or fewer.").optional(),
  email: z.email("Enter a valid email address."),
  password: z.string().min(8, "Use at least 8 characters."),
});
type Values = z.infer<typeof schema>;

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const { refresh } = useCurrentUser();
  const {
    formState: { errors, isSubmitting },
    handleSubmit,
    register: field,
  } = useForm<Values>({ resolver: zodResolver(schema) });
  const submit = async (values: Values) => {
    try {
      if (mode === "login") await login({ email: values.email, password: values.password });
      else
        await register({
          ...(values.displayName ? { display_name: values.displayName } : {}),
          email: values.email,
          password: values.password,
        });
      await refresh();
      router.push("/dashboard");
    } catch (error) {
      const message =
        error instanceof ApiError ? error.message : "Unable to complete your request.";
      document.getElementById("auth-error")!.textContent = message;
    }
  };
  const creating = mode === "register";
  return (
    <form className="space-y-5" onSubmit={handleSubmit(submit)} noValidate>
      {creating ? (
        <label className="block text-sm text-text-muted">
          Display name
          <input
            className="mt-2 h-11 w-full rounded-md border border-border bg-surface-raised px-3 text-foreground"
            {...field("displayName")}
          />
          <span className="mt-1 block text-danger">{errors.displayName?.message}</span>
        </label>
      ) : null}
      <label className="block text-sm text-text-muted">
        Email
        <input
          className="mt-2 h-11 w-full rounded-md border border-border bg-surface-raised px-3 text-foreground"
          type="email"
          {...field("email")}
        />
        <span className="mt-1 block text-danger">{errors.email?.message}</span>
      </label>
      <label className="block text-sm text-text-muted">
        Password
        <input
          className="mt-2 h-11 w-full rounded-md border border-border bg-surface-raised px-3 text-foreground"
          type="password"
          {...field("password")}
        />
        <span className="mt-1 block text-danger">{errors.password?.message}</span>
      </label>
      <p aria-live="polite" className="text-sm text-danger" id="auth-error" />
      <button
        className="h-11 w-full rounded-md bg-accent-strong font-semibold text-surface disabled:opacity-60"
        disabled={isSubmitting}
        type="submit"
      >
        {isSubmitting ? "Please wait…" : creating ? "Create account" : "Sign in"}
      </button>
      <p className="text-center text-sm text-text-muted">
        {creating ? "Already have an account?" : "New to AlgoVision?"}{" "}
        <Link
          className="text-accent-strong hover:underline"
          href={creating ? "/sign-in" : "/sign-up"}
        >
          {creating ? "Sign in" : "Create account"}
        </Link>
      </p>
    </form>
  );
}
