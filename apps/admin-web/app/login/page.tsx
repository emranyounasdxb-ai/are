"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { AdminBrandLogo } from "../../components/admin-brand-logo";
import { useAuth } from "../../components/auth-provider";

const schema = z.object({ email: z.email(), password: z.string().min(10) });
type Values = z.infer<typeof schema>;

export default function LoginPage() {
  return <Suspense fallback={<main className="center-state">Loading secure sign in…</main>}><LoginForm /></Suspense>;
}

function LoginForm() {
  const { login } = useAuth(); const router = useRouter(); const params = useSearchParams(); const [error, setError] = useState("");
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<Values>();
  return <main className="login-page"><form className="login-card" onSubmit={handleSubmit(async (values) => { setError(""); const valid = schema.safeParse(values); if (!valid.success) { setError(valid.error.issues[0]?.message ?? "Review the submitted fields."); return; } try { await login(valid.data.email, valid.data.password); const target = params.get("returnTo"); router.replace(target?.startsWith("/") ? target : "/dashboard"); } catch (reason) { setError(reason instanceof Error ? reason.message : "Login failed."); } })}>
    <AdminBrandLogo className="login-brand-mark"/><h1>Secure sign in</h1><p>Authorized ALIYAS team members only.</p>
    {error ? <div className="form-error" role="alert">{error}</div> : null}
    <label>Email<input autoComplete="username" {...register("email", { required: "Email is required." })}/><small>{errors.email?.message}</small></label>
    <label>Password<input autoComplete="current-password" type="password" {...register("password", { required: "Password is required." })}/><small>{errors.password?.message}</small></label>
    <button disabled={isSubmitting} type="submit">{isSubmitting ? "Signing in…" : "Sign in"}</button>
  </form></main>;
}
