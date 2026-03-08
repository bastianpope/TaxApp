/**
 * Minimal centered layout for auth pages (login, register).
 * No nav, no sidebar — just a branded card on the dark bg.
 */
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-12">
      {/* Brand */}
      <div className="mb-8 text-center">
        <span className="text-2xl font-bold tracking-tight" style={{ color: "var(--accent)" }}>
          Tax
          <span style={{ color: "var(--text-primary)" }}>App</span>
        </span>
        <p className="mt-1 text-sm" style={{ color: "var(--text-muted)" }}>
          Smart federal &amp; state tax preparation
        </p>
      </div>

      {children}
    </div>
  );
}
