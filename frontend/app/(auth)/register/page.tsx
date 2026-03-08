"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

export default function RegisterPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const detail = (body as { detail?: string }).detail;
        throw new Error(detail ?? "Registration failed");
      }
      const { access_token } = await res.json() as { access_token: string };
      await login(access_token);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card w-full max-w-sm">
      <h1 className="text-xl font-bold mb-1">Create account</h1>
      <p className="text-sm mb-6" style={{ color: "var(--text-muted)" }}>
        Save your returns and access them from any device.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="label" htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            className="input"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div>
          <label className="label" htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={8}
            className="input"
            placeholder="Min. 8 characters"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        <div>
          <label className="label" htmlFor="confirm">Confirm password</label>
          <input
            id="confirm"
            type="password"
            autoComplete="new-password"
            required
            className="input"
            placeholder="••••••••"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
          />
        </div>

        {error && (
          <p className="text-sm rounded-lg px-3 py-2" style={{ background: "rgba(239,68,68,0.1)", color: "var(--danger)" }}>
            {error}
          </p>
        )}

        <button type="submit" className="btn-primary w-full justify-center" disabled={loading}>
          {loading ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p className="mt-6 text-sm text-center" style={{ color: "var(--text-muted)" }}>
        Already have an account?{" "}
        <Link href="/login" className="font-semibold" style={{ color: "var(--accent)" }}>
          Sign in
        </Link>
      </p>
    </div>
  );
}
