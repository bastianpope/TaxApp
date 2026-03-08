"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useReturn } from "@/context/ReturnContext";
import { useAuth } from "@/context/AuthContext";
import RiskGauge from "@/components/RiskGauge";
import ComparisonTable from "@/components/ComparisonTable";
import FederalCard from "@/components/FederalCard";
import StateCard from "@/components/StateCard";
import AggressivenessDial from "@/components/AggressivenessDial";
import type { TaxCalculationResponse, AggressivenessLevel } from "@/lib/types";
import { calculateTaxes, exportPdf, api } from "@/lib/api";

export default function ResultsPage() {
  const { state, dispatch } = useReturn();
  const { user } = useAuth();
  const router = useRouter();

  const [result, setResult] = useState<TaxCalculationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeLevel, setActiveLevel] = useState<AggressivenessLevel>(state.data.aggressiveness ?? "LOW");
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);

  // Freemium: any authenticated user = Pro (State + Audit cards unlocked)
  const isPro = !!user;

  // Calculate on mount only
  useEffect(() => {
    if (!state.data.filing_status) {
      router.push("/return/1");
      return;
    }
    calculateTaxes(state.data)
      .then(setResult)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-save once both result and a logged-in user are available
  const hasSaved = useRef(false);
  useEffect(() => {
    if (!result || !user || hasSaved.current) return;
    hasSaved.current = true;
    const taxYear = result.tax_year ?? new Date().getFullYear() - 1;
    const label = `${taxYear} Tax Return`;
    const payload = { label, tax_year: taxYear, return_data: state.data as Record<string, unknown> };
    const save = state.savedReturnId
      ? api.returns.update(state.savedReturnId, { return_data: state.data as Record<string, unknown>, status: "draft" })
      : api.returns.create(payload).then((saved) => { dispatch({ type: "SET_SAVED_ID", id: saved.id }); });
    save.catch(() => { /* non-fatal */ });
  }, [result, user]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleDownloadPdf() {
    if (!result) return;
    setPdfLoading(true);
    setPdfError(null);
    try {
      await exportPdf(result, activeLevel);
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      // Fallback to browser print if backend export fails
      setPdfError(`PDF generation failed: ${msg}. Falling back to browser print.`);
      window.print();
    } finally {
      setPdfLoading(false);
    }
  }

  // ── Loading ────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-6">
        <svg className="animate-spin w-12 h-12 text-sky-400" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.4 0 0 5.4 0 12h4z" />
        </svg>
        <p className="text-slate-400 text-sm">Calculating your taxes…</p>
      </div>
    );
  }

  // ── Error ──────────────────────────────────────────────────
  if (error || !result) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 px-4 text-center">
        <div className="text-5xl">⚠️</div>
        <h1 className="text-xl font-bold">Calculation Error</h1>
        <p className="text-slate-400 text-sm max-w-md">{error ?? "Could not reach the tax engine. Make sure the backend is running on port 8000."}</p>
        <button type="button" onClick={() => router.back()} className="btn-primary mt-2">← Go Back</button>
      </div>
    );
  }

  // ── Derive active scenario ──────────────────────────────────
  const scenarios = result.scenarios;
  const active = scenarios?.[activeLevel];

  // Guard: malformed API response
  if (!scenarios || !active) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 px-4 text-center">
        <div className="text-5xl">⚠️</div>
        <h1 className="text-xl font-bold">Unexpected Response</h1>
        <p className="text-slate-400 text-sm max-w-md">The tax engine returned an unexpected response. Please go back and try again.</p>
        <button type="button" onClick={() => router.back()} className="btn-primary mt-2">← Go Back</button>
      </div>
    );
  }

  // ── Render ─────────────────────────────────────────────────
  return (
    <div className="min-h-screen" style={{ background: "var(--bg-primary)" }}>
      {/* Header */}
      <header className="border-b no-print" style={{ borderColor: "var(--border)" }}>
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between gap-4 flex-wrap">
          <button
            type="button"
            onClick={() => router.push("/")}
            className="text-sm font-bold tracking-tight text-slate-300 hover:text-white transition-colors"
          >
            📊 TaxApp
          </button>
          <span className="text-xs text-slate-500">
            Tax Year {result.tax_year} · {result.filing_status.replace(/_/g, " ")}
          </span>
          <button
            type="button"
            id="print-results"
            onClick={handleDownloadPdf}
            disabled={pdfLoading}
            className="btn-ghost text-xs px-3 py-1.5 no-print"
            title={isPro ? "Download PDF" : "Sign in for PDF export"}
          >
            {pdfLoading ? "⏳ Generating…" : isPro ? "⬇️ Download PDF" : "🔒 PDF (Pro)"}
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8 space-y-8">
        {/* Summary headline */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-extrabold">Your Tax Summary</h1>
          <p className="text-slate-400 text-sm">
            Showing results for <strong className="text-white">{activeLevel === "LOW" ? "Conservative" : activeLevel === "MEDIUM" ? "Moderate" : "Aggressive"}</strong> strategy.
            Toggle below to compare scenarios.
          </p>
        </div>

        {/* Strategy selector chips */}
        <div className="flex justify-center gap-3 no-print flex-wrap">
          {(["LOW", "MEDIUM", "HIGH"] as AggressivenessLevel[]).map((l) => (
            <button
              key={l}
              id={`scenario-${l.toLowerCase()}`}
              type="button"
              onClick={() => setActiveLevel(l)}
              className="px-4 py-2 rounded-full text-sm font-medium transition-all"
              style={{
                background: activeLevel === l ? "rgba(14,165,233,0.15)" : "var(--bg-secondary)",
                border: `1px solid ${activeLevel === l ? "var(--accent)" : "var(--border)"}`,
                color: activeLevel === l ? "var(--accent)" : "var(--text-secondary)",
              }}
            >
              {l === "LOW" ? "🛡️ Conservative" : l === "MEDIUM" ? "⚖️ Moderate" : "🚀 Aggressive"}
            </button>
          ))}
        </div>

        {/* Aggressiveness dial */}
        <div className="flex justify-center">
          <div className="card inline-flex flex-col items-center py-6 px-10">
            <AggressivenessDial level={activeLevel} />
          </div>
        </div>

        {/* Federal + State cards */}
        <div className="grid md:grid-cols-2 gap-6">
          <FederalCard {...active.federal} grossIncome={result.gross_income} />

          {!isPro ? (
            <div className="card flex flex-col items-center justify-center py-10 text-center gap-3 relative overflow-hidden">
              <div className="absolute inset-0 backdrop-blur-sm rounded-xl flex flex-col items-center justify-center gap-3"
                style={{ background: "rgba(15,23,42,0.60)" }}>
                <div className="text-3xl">🔒</div>
                <p className="font-semibold text-sm">State Tax — Pro Feature</p>
                <p className="text-xs text-slate-400 max-w-[200px]">
                  Create a free account to unlock state-level calculations.
                </p>
                <button
                  type="button"
                  onClick={() => router.push("/auth")}
                  className="btn-primary text-xs px-4 py-2 mt-1"
                >
                  Sign Up Free
                </button>
              </div>
            </div>
          ) : Object.keys(active.state).length > 0 ? (
            <StateCard results={active.state} />
          ) : (
            <div className="card flex flex-col items-center justify-center py-10 text-center gap-3">
              <div className="text-3xl">📋</div>
              <p className="text-slate-400 text-sm">No state selected. Add a state in <button onClick={() => router.push("/return/5")} className="text-sky-400 underline">Step 5</button>.</p>
            </div>
          )}
        </div>

        {/* Audit risk */}
        <div className="card relative overflow-hidden">
          {!isPro && (
            <div className="absolute inset-0 backdrop-blur-sm rounded-xl flex flex-col items-center justify-center gap-3 z-10"
              style={{ background: "rgba(15,23,42,0.65)" }}>
              <div className="text-3xl">🔒</div>
              <p className="font-semibold text-sm">Audit Risk — Pro Feature</p>
              <p className="text-xs text-slate-400 max-w-[220px] text-center">
                Sign in to see your personalised audit risk score and recommendations.
              </p>
              <button type="button" onClick={() => router.push("/auth")} className="btn-primary text-xs px-4 py-2 mt-1">
                Sign Up Free
              </button>
            </div>
          )}
          <h2 className="font-semibold mb-4">Audit Risk Assessment</h2>
          <div className="flex flex-col md:flex-row items-center gap-6">
            <RiskGauge score={active.audit_risk.score} />
            <div className="flex-1 space-y-3">
              <div>
                <p className="text-sm font-semibold mb-1">Risk Factors</p>
                {active.audit_risk.risk_factors.length === 0 ? (
                  <p className="text-sm text-slate-500">No significant risk factors identified.</p>
                ) : (
                  <ul className="space-y-1">
                    {active.audit_risk.risk_factors.map((f, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-slate-400">
                        <span className="text-red-400 mt-0.5">●</span>
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              {active.audit_risk.recommendations.length > 0 && (
                <div>
                  <p className="text-sm font-semibold mb-1">Recommendations</p>
                  <ul className="space-y-1">
                    {active.audit_risk.recommendations.map((r, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-emerald-400">
                        <span className="mt-0.5">✓</span>
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Comparison table */}
        <div className="card">
          <h2 className="font-semibold mb-4">Scenario Comparison</h2>
          <ComparisonTable scenarios={scenarios} />
        </div>

        {/* Deduction recommendations */}
        {active.deduction_recommendations.length > 0 && (
          <div className="card">
            <h2 className="font-semibold mb-4">💡 Deduction Opportunities</h2>
            <div className="space-y-3">
              {active.deduction_recommendations.map((rec, i) => (
                <div
                  key={i}
                  className="rounded-lg p-4 flex items-start gap-3"
                  style={{ background: "rgba(16,185,129,0.05)", border: "1px solid rgba(16,185,129,0.15)" }}
                >
                  <span className="text-xl">💡</span>
                  <div>
                    <p className="text-sm font-semibold">{rec.description}</p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Potential Savings:{" "}
                      <strong className="text-emerald-400">${rec.estimated_savings.toLocaleString()}</strong>
                      {" · "}Confidence: <strong>{rec.confidence}</strong>
                    </p>
                    {rec.form && <p className="text-xs text-slate-500 mt-0.5">Form: {rec.form}</p>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Disclaimer */}
        <div className="rounded-lg p-5" style={{ background: "rgba(100,116,139,0.08)", border: "1px solid var(--border)" }}>
          <p className="text-xs text-slate-500 leading-relaxed">
            <strong className="text-slate-400">Disclaimer:</strong> This analysis is for informational and educational purposes only.
            It does not constitute legal, financial, or tax advice. TaxApp does not file tax returns.
            Tax laws are complex and subject to change. We strongly recommend consulting a qualified CPA
            or enrolled agent before filing. Results are estimates based on data you entered and may not
            reflect your actual tax liability. Always verify with official IRS publications and your state
            tax authority.
          </p>
        </div>

        {/* Export error toast */}
        {pdfError && (
          <div className="rounded-lg p-4 text-xs text-amber-300" style={{ background: "rgba(251,191,36,0.08)", border: "1px solid rgba(251,191,36,0.2)" }}>
            ⚠️ {pdfError}
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center no-print pb-8">
          <button type="button" id="edit-return" onClick={() => router.push("/return/1")} className="btn-ghost">
            ✏️ Edit Return
          </button>
          <button
            type="button"
            id="save-pdf"
            onClick={handleDownloadPdf}
            disabled={pdfLoading}
            className="btn-primary"
          >
            {pdfLoading ? "⏳ Generating PDF…" : "⬇️ Download PDF"}
          </button>
        </div>
      </main>
    </div>
  );
}
