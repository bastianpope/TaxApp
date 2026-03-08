"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api, ApiError } from "@/lib/api";

export default function SettingsPage() {
  const { user, loading: authLoading, logout } = useAuth();
  const router = useRouter();

  const [totpEnabled, setTotpEnabled] = useState<boolean | null>(null);
  const [setupMode, setSetupMode] = useState<"idle" | "setup" | "confirm">(
    "idle",
  );
  const [qrUri, setQrUri] = useState<string | null>(null);
  const [secret, setSecret] = useState<string | null>(null);
  const [totpCode, setTotpCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{
    text: string;
    type: "ok" | "err";
  } | null>(null);

  // Sync totp_enabled from auth user
  useEffect(() => {
    if (user) setTotpEnabled(user.totp_enabled);
  }, [user]);

  // Redirect if not logged in
  useEffect(() => {
    if (!authLoading && !user) router.replace("/login");
  }, [authLoading, user, router]);

  async function handleSetupTotp() {
    try {
      setBusy(true);
      setMessage(null);
      const { uri, secret: s } = await api.auth.totpSetup();
      setQrUri(uri);
      setSecret(s);
      setSetupMode("setup");
    } catch (err) {
      setMessage({
        text:
          err instanceof ApiError ? String(err.detail) : "Setup failed.",
        type: "err",
      });
    } finally {
      setBusy(false);
    }
  }

  async function handleConfirmTotp() {
    if (!totpCode.trim()) return;
    try {
      setBusy(true);
      setMessage(null);
      await api.auth.totpConfirm(totpCode.trim());
      setTotpEnabled(true);
      setSetupMode("idle");
      setQrUri(null);
      setSecret(null);
      setTotpCode("");
      setMessage({ text: "Two-factor authentication enabled!", type: "ok" });
    } catch (err) {
      setMessage({
        text:
          err instanceof ApiError
            ? "Invalid code. Check your authenticator and try again."
            : "Confirmation failed.",
        type: "err",
      });
    } finally {
      setBusy(false);
    }
  }

  async function handleDisableTotp() {
    if (!confirm("Disable two-factor authentication? Your account will be less secure.")) return;
    try {
      setBusy(true);
      setMessage(null);
      await api.auth.totpDisable();
      setTotpEnabled(false);
      setMessage({ text: "Two-factor authentication disabled.", type: "ok" });
    } catch (err) {
      setMessage({
        text:
          err instanceof ApiError ? String(err.detail) : "Failed to disable 2FA.",
        type: "err",
      });
    } finally {
      setBusy(false);
    }
  }

  function cancelSetup() {
    setSetupMode("idle");
    setQrUri(null);
    setSecret(null);
    setTotpCode("");
    setMessage(null);
  }

  if (authLoading) {
    return (
      <div className="settings-loading">Authenticating…</div>
    );
  }
  if (!user) return null;

  return (
    <div className="settings-root">
      {/* Header */}
      <header className="settings-header">
        <div className="settings-header-inner">
          <button onClick={() => router.push("/dashboard")} className="settings-back">
            ← Dashboard
          </button>
          <span className="settings-logo">TaxApp</span>
        </div>
      </header>

      <main className="settings-main">
        <h1 className="settings-title">Account Settings</h1>

        {/* Account card */}
        <section className="settings-card">
          <h2 className="settings-section-title">Account</h2>
          <div className="settings-row">
            <span className="settings-label">Email</span>
            <span className="settings-value">{user.email}</span>
          </div>
        </section>

        {/* 2FA card */}
        <section className="settings-card">
          <h2 className="settings-section-title">Two-Factor Authentication</h2>
          <p className="settings-desc">
            Add an extra layer of security by requiring a one-time code from an
            authenticator app when you sign in.
          </p>

          {message && (
            <div
              className={`settings-msg ${message.type === "ok" ? "settings-msg-ok" : "settings-msg-err"}`}
              role="alert"
            >
              {message.text}
            </div>
          )}

          {setupMode === "idle" && (
            <div className="settings-2fa-status">
              <span
                className={`status-badge ${totpEnabled ? "status-on" : "status-off"}`}
              >
                {totpEnabled ? "Enabled" : "Disabled"}
              </span>
              {totpEnabled ? (
                <button
                  className="btn-danger-sm"
                  onClick={handleDisableTotp}
                  disabled={busy}
                >
                  {busy ? "Disabling…" : "Disable 2FA"}
                </button>
              ) : (
                <button
                  className="btn-primary-sm"
                  onClick={handleSetupTotp}
                  disabled={busy}
                >
                  {busy ? "Loading…" : "Enable 2FA"}
                </button>
              )}
            </div>
          )}

          {setupMode === "setup" && qrUri && (
            <div className="totp-setup">
              <p className="totp-instruction">
                Scan this QR code with your authenticator app (Google
                Authenticator, Authy, etc.), then enter the 6-digit code below
                to confirm.
              </p>

              {/* Inline QR code via Google Chart API — no external pkg needed */}
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                className="totp-qr"
                src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(qrUri)}`}
                alt="TOTP QR Code"
                width={200}
                height={200}
              />

              <details className="totp-manual">
                <summary>Can&apos;t scan? Enter the secret manually</summary>
                <code className="totp-secret">{secret}</code>
              </details>

              <div className="totp-confirm-row">
                <input
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  placeholder="6-digit code"
                  value={totpCode}
                  onChange={(e) => setTotpCode(e.target.value)}
                  className="totp-input"
                  autoComplete="one-time-code"
                />
                <button
                  className="btn-primary-sm"
                  onClick={handleConfirmTotp}
                  disabled={busy || totpCode.length !== 6}
                >
                  {busy ? "Verifying…" : "Verify & Enable"}
                </button>
                <button
                  className="btn-ghost-sm"
                  onClick={cancelSetup}
                  disabled={busy}
                >
                  Cancel
                </button>
              </div>

              {message && (
                <div
                  className={`settings-msg ${message.type === "ok" ? "settings-msg-ok" : "settings-msg-err"}`}
                  role="alert"
                >
                  {message.text}
                </div>
              )}
            </div>
          )}
        </section>

        {/* Danger zone */}
        <section className="settings-card settings-danger-zone">
          <h2 className="settings-section-title" style={{ color: "#ff6b7a" }}>
            Danger Zone
          </h2>
          <div className="settings-row">
            <div>
              <strong>Sign out of all devices</strong>
              <p className="settings-desc" style={{ margin: 0 }}>
                Revokes your current session immediately.
              </p>
            </div>
            <button
              className="btn-danger-sm"
              onClick={async () => {
                await logout();
                router.push("/");
              }}
            >
              Sign out
            </button>
          </div>
        </section>
      </main>

      <style>{settingsStyles}</style>
    </div>
  );
}

// ── Styles ──────────────────────────────────────────────────────────────────

const settingsStyles = `
.settings-root {
  min-height: 100vh;
  background: var(--color-bg);
  color: var(--color-text);
  font-family: var(--font-sans);
}
.settings-loading {
  display: flex; align-items: center; justify-content: center;
  min-height: 100vh; color: var(--color-text-muted);
}
.settings-header {
  position: sticky; top: 0; z-index: 50;
  border-bottom: 1px solid var(--color-border);
  background: rgba(10,10,20,0.85);
  backdrop-filter: blur(10px);
}
.settings-header-inner {
  max-width: 720px; margin: 0 auto; padding: 0 1.5rem;
  height: 56px; display: flex; align-items: center; justify-content: space-between;
}
.settings-back {
  background: none; border: none; color: var(--color-text-muted);
  cursor: pointer; font-size: 0.9rem; padding: 0.3rem 0.5rem;
  border-radius: 6px; transition: color 0.15s;
}
.settings-back:hover { color: var(--color-text); }
.settings-logo { font-size: 1.1rem; font-weight: 700; color: var(--color-accent); }
.settings-main { max-width: 720px; margin: 0 auto; padding: 2.5rem 1.5rem; display: flex; flex-direction: column; gap: 1.5rem; }
.settings-title { font-size: 1.75rem; font-weight: 700; margin: 0 0 0.5rem; }
.settings-card {
  border: 1px solid var(--color-border); border-radius: 12px;
  background: var(--color-surface); padding: 1.5rem;
}
.settings-danger-zone { border-color: rgba(220,53,69,0.35); }
.settings-section-title { font-size: 1.05rem; font-weight: 600; margin: 0 0 1rem; }
.settings-desc { font-size: 0.9rem; color: var(--color-text-muted); margin: 0 0 1rem; line-height: 1.5; }
.settings-row {
  display: flex; align-items: center; justify-content: space-between;
  gap: 1rem; flex-wrap: wrap;
}
.settings-label { font-size: 0.9rem; color: var(--color-text-muted); }
.settings-value { font-size: 0.95rem; }
.settings-msg {
  border-radius: 8px; padding: 0.65rem 1rem; font-size: 0.9rem; margin-bottom: 1rem;
}
.settings-msg-ok { background: rgba(34,197,94,0.1); border: 1px solid rgba(34,197,94,0.3); color: #4ade80; }
.settings-msg-err { background: rgba(220,53,69,0.1); border: 1px solid rgba(220,53,69,0.3); color: #ff6b7a; }
.settings-2fa-status { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }
.status-badge {
  padding: 0.3rem 0.75rem; border-radius: 100px; font-size: 0.8rem; font-weight: 600;
}
.status-on { background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }
.status-off { background: rgba(100,100,120,0.15); color: var(--color-text-muted); border: 1px solid var(--color-border); }
.totp-setup { display: flex; flex-direction: column; gap: 1rem; }
.totp-instruction { font-size: 0.9rem; color: var(--color-text-muted); margin: 0; line-height: 1.55; }
.totp-qr { border-radius: 8px; border: 4px solid #fff; align-self: flex-start; }
.totp-manual summary { font-size: 0.85rem; color: var(--color-text-muted); cursor: pointer; }
.totp-secret {
  display: block; margin-top: 0.5rem; font-family: monospace; font-size: 0.9rem;
  background: rgba(100,100,120,0.2); padding: 0.5rem 0.75rem; border-radius: 6px;
  word-break: break-all; user-select: all;
}
.totp-confirm-row { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
.totp-input {
  border: 1px solid var(--color-border); background: rgba(255,255,255,0.05);
  color: var(--color-text); border-radius: 8px; padding: 0.5rem 0.75rem;
  font-size: 1rem; width: 130px; text-align: center; letter-spacing: 0.15em;
  outline: none; transition: border-color 0.15s;
}
.totp-input:focus { border-color: var(--color-accent); }

/* Button variants */
.btn-primary-sm {
  background: var(--color-accent, #6366f1); color: #fff; border: none;
  border-radius: 8px; padding: 0.45rem 0.9rem; font-size: 0.88rem; font-weight: 600;
  cursor: pointer; transition: opacity 0.15s;
}
.btn-primary-sm:hover:not(:disabled) { opacity: 0.88; }
.btn-primary-sm:disabled { opacity: 0.4; cursor: default; }
.btn-danger-sm {
  background: transparent; color: #ff6b7a; border: 1px solid rgba(220,53,69,0.4);
  border-radius: 8px; padding: 0.45rem 0.9rem; font-size: 0.88rem; font-weight: 600;
  cursor: pointer; transition: background 0.15s;
}
.btn-danger-sm:hover:not(:disabled) { background: rgba(220,53,69,0.12); }
.btn-ghost-sm {
  background: transparent; color: var(--color-text-muted); border: none;
  border-radius: 8px; padding: 0.45rem 0.75rem; font-size: 0.88rem; cursor: pointer;
  transition: color 0.15s;
}
.btn-ghost-sm:hover { color: var(--color-text); }
`;
