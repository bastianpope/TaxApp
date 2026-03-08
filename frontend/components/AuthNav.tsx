"use client";

import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";

export function AuthNav() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  async function handleLogout() {
    await logout();
    router.refresh();
  }

  if (loading) return null;

  return (
    <div className="flex items-center gap-3">
      {user ? (
        <>
          <span className="text-sm hidden sm:block" style={{ color: "var(--text-muted)" }}>
            {user.email}
          </span>
          <button
            onClick={handleLogout}
            className="btn-ghost text-sm px-4 py-2"
            id="auth-logout-btn"
          >
            Sign out
          </button>
        </>
      ) : (
        <>
          <Link href="/login" className="btn-ghost text-sm px-4 py-2" id="auth-login-link">
            Sign in
          </Link>
          <Link href="/register" className="btn-primary text-sm px-4 py-2" id="auth-register-link">
            Get started
          </Link>
        </>
      )}
    </div>
  );
}
