import Link from "next/link";
import { AuthNav } from "@/components/AuthNav";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col">
      {/* Top nav */}
      <nav className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 border-b" style={{ background: "var(--bg-primary)", borderColor: "var(--border)" }}>
        <span className="font-bold tracking-tight text-lg">
          <span style={{ color: "var(--accent)" }}>Tax</span>App
        </span>
        <AuthNav />
      </nav>

      <section className="flex-1 flex flex-col items-center justify-center px-4 py-24 text-center">
        {/* Logo / wordmark */}
        <div className="mb-8 inline-flex items-center gap-3">
          <div
            className="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl"
            style={{ background: "linear-gradient(135deg, #0ea5e9, #6366f1)" }}
            aria-hidden
          >
            📊
          </div>
          <span className="text-3xl font-extrabold tracking-tight">TaxApp</span>
        </div>

        <h1 className="text-5xl sm:text-6xl font-extrabold tracking-tight mb-6 max-w-2xl leading-tight">
          Smart Tax Prep,{" "}
          <span style={{ background: "linear-gradient(135deg, #0ea5e9, #818cf8)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            Zero Surprises
          </span>
        </h1>

        <p className="text-lg text-slate-400 max-w-xl mb-10 leading-relaxed">
          Prepare your federal and state taxes with real-time audit risk scoring,
          smart deduction recommendations, and side-by-side scenario comparisons.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 items-center">
          <Link href="/return/1" id="start-cta" className="btn-primary text-base px-8 py-3">
            Start My Return →
          </Link>
          <Link href="#features" className="btn-ghost text-base px-8 py-3">
            See How It Works
          </Link>
        </div>

        <p className="mt-6 text-xs text-slate-500">
          ⓘ For informational purposes only. Not legal or tax advice.
          TaxApp does not e-file returns.
        </p>
      </section>

      {/* Feature highlights */}
      <section id="features" className="max-w-5xl mx-auto px-4 pb-24 grid sm:grid-cols-3 gap-6">
        {[
          {
            icon: "🔍",
            title: "Audit Risk Scoring",
            desc: "Our 15-factor model evaluates your return against IRS audit patterns and flags high-risk items before you file.",
          },
          {
            icon: "⚖️",
            title: "Aggressiveness Levels",
            desc: "Compare Conservative, Moderate, and Aggressive deduction strategies side-by-side to make an informed choice.",
          },
          {
            icon: "📑",
            title: "Federal + State",
            desc: "Supports Illinois and Minnesota state tax calculations — including IL property tax credit and MN renter's credit.",
          },
        ].map(({ icon, title, desc }) => (
          <div key={title} className="card space-y-3">
            <div className="text-3xl">{icon}</div>
            <h2 className="font-semibold text-base">{title}</h2>
            <p className="text-sm text-slate-400 leading-relaxed">{desc}</p>
          </div>
        ))}
      </section>

      {/* Footer scroll anchor */}
      <footer className="border-t py-6 text-center text-xs text-slate-500" style={{ borderColor: "var(--border)" }}>
        TaxApp {new Date().getFullYear()} · For informational purposes only · Not a substitute for professional tax advice
      </footer>
    </main>
  );
}
