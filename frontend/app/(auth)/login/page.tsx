"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error((body as { detail?: string }).detail ?? "Invalid credentials");
      }
      const { access_token } = await res.json() as { access_token: string };
      await login(access_token);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card w-full max-w-sm">
      <h1 className="text-xl font-bold mb-1">Sign in</h1>
      <p className="text-sm mb-6" style={{ color: "var(--text-muted)" }}>
        Access your saved returns and continue filing.
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
            autoComplete="current-password"
            required
            className="input"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        {error && (
          <p className="text-sm rounded-lg px-3 py-2" style={{ background: "rgba(239,68,68,0.1)", color: "var(--danger)" }}>
            {error}
          </p>
        )}

        <button type="submit" className="btn-primary w-full justify-center" disabled={loading}>
          {loading ? "Signing in…" : "Sign in"}
        </button>
      </form>

      <p className="mt-6 text-sm text-center" style={{ color: "var(--text-muted)" }}>
        Don&apos;t have an account?{" "}
        <Link href="/register" className="font-semibold" style={{ color: "var(--accent)" }}>
          Create one
        </Link>
      </p>
    </div>
  );
}
