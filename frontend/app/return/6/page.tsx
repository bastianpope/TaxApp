"use client";

import { useState } from "react";
import WizardShell from "@/components/WizardShell";
import AggressivenessDial from "@/components/AggressivenessDial";
import { useReturn } from "@/context/ReturnContext";
import type { AggressivenessLevel } from "@/lib/types";

const LEVELS: { level: AggressivenessLevel; label: string; emoji: string; desc: string }[] = [
  {
    level: "LOW",
    emoji: "🛡️",
    label: "Conservative",
    desc: "Only clearly documented, well-established deductions. Minimal audit risk. Best if you want peace of mind and are unsure about certain deductions.",
  },
  {
    level: "MEDIUM",
    emoji: "⚖️",
    label: "Moderate",
    desc: "Common deductions with reasonable documentation. Balanced approach suitable for most filers. May include home office, vehicle, and unreimbursed business expenses.",
  },
  {
    level: "HIGH",
    emoji: "🚀",
    label: "Aggressive",
    desc: "Maximum legal deductions including gray-area items. Higher audit risk. Consider only if you have records to substantiate all claims and understand the implications.",
  },
];

export default function Step6Strategy() {
  const { state, dispatch } = useReturn();
  const [level, setLevel] = useState<AggressivenessLevel>(state.data.aggressiveness ?? "LOW");

  function handleCalculate() {
    dispatch({ type: "SET_AGGRESSIVENESS", level });
    dispatch({ type: "SET_STEP", step: 6 });
    // WizardShell will navigate to /results after calling onNext()
  }

  return (
    <WizardShell
      step={6}
      title="Tax Strategy"
      subtitle="Choose how aggressively you'd like to approach deductions. You can compare all three scenarios on the results page."
      onNext={handleCalculate}
      nextLabel="Calculate My Taxes →"
    >
      {/* Visual dial */}
      <div className="card flex flex-col items-center py-8">
        <AggressivenessDial level={level} />
      </div>

      {/* Level selector cards */}
      <div className="space-y-3">
        {LEVELS.map(({ level: l, emoji, label, desc }) => (
          <button
            key={l}
            id={`agg-level-${l.toLowerCase()}`}
            type="button"
            onClick={() => setLevel(l)}
            className="w-full text-left rounded-xl p-4 transition-all"
            style={{
              background: level === l ? "rgba(14,165,233,0.08)" : "var(--bg-secondary)",
              border: `2px solid ${level === l ? "var(--accent)" : "var(--border)"}`,
            }}
          >
            <div className="flex items-start gap-3">
              <span className="text-2xl mt-0.5">{emoji}</span>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-sm">{label}</span>
                  {level === l && (
                    <span className="text-xs px-2 py-0.5 rounded-full font-medium" style={{ background: "rgba(14,165,233,0.15)", color: "var(--accent)" }}>
                      Selected
                    </span>
                  )}
                </div>
                <p className="text-sm text-slate-400 leading-relaxed">{desc}</p>
              </div>
            </div>
          </button>
        ))}
      </div>

      <div className="rounded-lg p-4" style={{ background: "rgba(251,191,36,0.05)", border: "1px solid rgba(251,191,36,0.15)" }}>
        <p className="text-xs text-amber-300">
          ⚠️ The results page shows all three scenarios side-by-side. Your selected level is the default but you can explore others on the results page.
        </p>
      </div>
    </WizardShell>
  );
}
