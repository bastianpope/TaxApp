"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useReturn } from "@/context/ReturnContext";
import { api, type SavedReturn, ApiError } from "@/lib/api";

export default function DashboardPage() {
  const { user, loading: authLoading, logout } = useAuth();
  const { dispatch } = useReturn();
  const router = useRouter();

  const [returns, setReturns] = useState<SavedReturn[]>([]);
  const [listLoading, setListLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !user) {
      router.replace("/login");
    }
  }, [authLoading, user, router]);

  const loadReturns = useCallback(async () => {
    try {
      setListLoading(true);
      const data = await api.returns.list();
      setReturns(data);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        router.replace("/login");
      } else {
        setError("Failed to load your returns. Please try again.");
      }
    } finally {
      setListLoading(false);
    }
  }, [router]);

  useEffect(() => {
    if (user) loadReturns();
  }, [user, loadReturns]);

  async function handleContinue(savedReturn: SavedReturn) {
    try {
      const full = await api.returns.get(savedReturn.id);
      // Merge saved return_data into ReturnContext
      if (full.return_data) {
        dispatch({
          type: "LOAD",
          state: {
            currentStep: 1,
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            data: full.return_data as any,
            savedReturnId: full.id,
          },
        });
      }
      router.push("/return/1");
    } catch {
      setError("Could not load return data. Please try again.");
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this return? This cannot be undone.")) return;
    try {
      setDeletingId(id);
      await api.returns.delete(id);
      setReturns((prev) => prev.filter((r) => r.id !== id));
    } catch {
      setError("Failed to delete return.");
    } finally {
      setDeletingId(null);
    }
  }

  async function handleNew() {
    dispatch({ type: "RESET" });
    router.push("/return/1");
  }

  function formatDate(iso: string) {
    return new Date(iso).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  }

  if (authLoading) return <LoadingScreen message="Authenticating…" />;
  if (!user) return null; // will redirect

  return (
    <div className="dashboard-root">
      {/* Header */}
      <header className="dashboard-header">
        <div className="dashboard-header-inner">
          <span className="dashboard-logo">TaxApp</span>
          <nav className="dashboard-nav">
            <button
              onClick={() => router.push("/settings")}
              className="btn-ghost"
            >
              Settings
            </button>
            <button
              onClick={async () => {
                await logout();
                router.push("/");
              }}
              className="btn-ghost"
            >
              Sign out
            </button>
          </nav>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="dashboard-top">
          <div>
            <h1 className="dashboard-title">Your Tax Returns</h1>
            <p className="dashboard-subtitle">{user.email}</p>
          </div>
          <button onClick={handleNew} className="btn-primary">
            + Start new return
          </button>
        </div>

        {error && (
          <div className="dashboard-error" role="alert">
            {error}
            <button onClick={() => setError(null)} aria-label="Dismiss">
              ×
            </button>
          </div>
        )}

        {listLoading ? (
          <LoadingScreen message="Loading your returns…" />
        ) : returns.length === 0 ? (
          <EmptyState onNew={handleNew} />
        ) : (
          <ul className="return-list">
            {returns.map((r) => (
              <li key={r.id} className="return-card">
                <div className="return-card-info">
                  <span className="return-card-label">{r.label}</span>
                  <span className="return-card-meta">
                    TY {r.tax_year} · {r.status} · saved{" "}
                    {formatDate(r.updated_at)}
                  </span>
                </div>
                <div className="return-card-actions">
                  <button
                    onClick={() => handleContinue(r)}
                    className="btn-secondary"
                  >
                    Continue
                  </button>
                  <button
                    onClick={() => handleDelete(r.id)}
                    className="btn-danger"
                    disabled={deletingId === r.id}
                  >
                    {deletingId === r.id ? "…" : "Delete"}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </main>

      <style>{dashboardStyles}</style>
    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────

function LoadingScreen({ message }: { message: string }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "40vh",
        color: "var(--color-text-muted)",
        fontSize: "1rem",
      }}
    >
      {message}
    </div>
  );
}

function EmptyState({ onNew }: { onNew: () => void }) {
  return (
    <div className="empty-state">
      <div className="empty-icon">📄</div>
      <h2 className="empty-title">No returns yet</h2>
      <p className="empty-desc">
        Start your first tax return and we&apos;ll save your progress
        automatically.
      </p>
      <button onClick={onNew} className="btn-primary">
        Start your first return
      </button>
    </div>
  );
}

// ── Styles ─────────────────────────────────────────────────────────────────

const dashboardStyles = `
.dashboard-root {
  min-height: 100vh;
  background: var(--color-bg);
  color: var(--color-text);
  font-family: var(--font-sans);
}
.dashboard-header {
  position: sticky;
  top: 0;
  z-index: 50;
  border-bottom: 1px solid var(--color-border);
  background: rgba(10, 10, 20, 0.85);
  backdrop-filter: blur(10px);
}
.dashboard-header-inner {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 1.5rem;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.dashboard-logo {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--color-accent);
  letter-spacing: -0.02em;
}
.dashboard-nav { display: flex; gap: 0.5rem; }
.dashboard-main {
  max-width: 900px;
  margin: 0 auto;
  padding: 2.5rem 1.5rem;
}
.dashboard-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}
.dashboard-title {
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0 0 0.25rem;
}
.dashboard-subtitle {
  color: var(--color-text-muted);
  margin: 0;
  font-size: 0.95rem;
}
.dashboard-error {
  background: rgba(220,53,69,0.12);
  border: 1px solid rgba(220,53,69,0.35);
  color: #ff6b7a;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}
.dashboard-error button {
  background: none;
  border: none;
  color: inherit;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0 0.25rem;
  line-height: 1;
}
.return-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.return-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.1rem 1.25rem;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  background: var(--color-surface);
  transition: border-color 0.15s;
  flex-wrap: wrap;
}
.return-card:hover { border-color: var(--color-accent); }
.return-card-info { display: flex; flex-direction: column; gap: 0.25rem; }
.return-card-label { font-weight: 600; font-size: 1rem; }
.return-card-meta { font-size: 0.85rem; color: var(--color-text-muted); text-transform: capitalize; }
.return-card-actions { display: flex; gap: 0.5rem; }

/* Empty state */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  border: 2px dashed var(--color-border);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}
.empty-icon { font-size: 2.5rem; }
.empty-title { font-size: 1.3rem; font-weight: 600; margin: 0; }
.empty-desc { color: var(--color-text-muted); max-width: 360px; margin: 0; }

/* Shared button styles (reuse globals if defined, else fallback) */
.btn-primary {
  background: var(--color-accent, #6366f1);
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 0.55rem 1.1rem;
  font-size: 0.92rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
  white-space: nowrap;
}
.btn-primary:hover { opacity: 0.88; }
.btn-secondary {
  background: transparent;
  color: var(--color-accent, #6366f1);
  border: 1px solid var(--color-accent, #6366f1);
  border-radius: 8px;
  padding: 0.45rem 0.9rem;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-secondary:hover { background: rgba(99,102,241,0.1); }
.btn-danger {
  background: transparent;
  color: #ff6b7a;
  border: 1px solid rgba(220,53,69,0.4);
  border-radius: 8px;
  padding: 0.45rem 0.9rem;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}
.btn-danger:hover { background: rgba(220,53,69,0.12); }
.btn-danger:disabled { opacity: 0.4; cursor: default; }
.btn-ghost {
  background: transparent;
  color: var(--color-text-muted, #888);
  border: none;
  border-radius: 8px;
  padding: 0.4rem 0.75rem;
  font-size: 0.9rem;
  cursor: pointer;
  transition: color 0.15s;
}
.btn-ghost:hover { color: var(--color-text, #fff); }
`;
