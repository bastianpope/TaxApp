import type { AllScenarios } from "@/lib/types";
import { fmtDollar, fmtPct } from "@/lib/utils";

const LABELS = {
  LOW: "🛡️ Conservative",
  MEDIUM: "⚖️ Moderate",
  HIGH: "🚀 Aggressive",
};

export default function ComparisonTable({ scenarios }: { scenarios: AllScenarios }) {
  const keys = ["LOW", "MEDIUM", "HIGH"] as const;

  return (
    <div className="overflow-x-auto -mx-1">
      <table className="w-full text-xs min-w-[440px]">
        <thead>
          <tr>
            <th className="text-left py-2 text-slate-400 font-medium w-36">Metric</th>
            {keys.map((k) => (
              <th key={k} className="text-right py-2 text-slate-300 font-semibold px-3">
                {LABELS[k]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {[
            {
              label: "Taxable Income",
              vals: keys.map((k) => fmtDollar(scenarios[k].federal.taxable_income)),
            },
            {
              label: "Deduction",
              vals: keys.map((k) =>
                scenarios[k].federal.use_itemized
                  ? `${fmtDollar(scenarios[k].federal.itemized_deduction)} (Itemized)`
                  : `${fmtDollar(scenarios[k].federal.standard_deduction)} (Standard)`
              ),
            },
            {
              label: "Federal Tax",
              vals: keys.map((k) => fmtDollar(scenarios[k].federal.federal_tax)),
            },
            {
              label: "SE Tax",
              vals: keys.map((k) => fmtDollar(scenarios[k].federal.self_employment_tax ?? 0)),
            },
            {
              label: "Effective Rate",
              vals: keys.map((k) => fmtPct(scenarios[k].federal.effective_rate)),
            },
            {
              label: "Federal Balance",
              vals: keys.map((k) => {
                const b = scenarios[k].federal.balance;
                return b < 0 ? `+${fmtDollar(-b)} refund` : b > 0 ? `-${fmtDollar(b)} due` : "Break even";
              }),
              colors: keys.map((k) => {
                const b = scenarios[k].federal.balance;
                return b < 0 ? "text-emerald-400" : b > 0 ? "text-red-400" : "";
              }),
            },
            {
              label: "Audit Risk",
              vals: keys.map((k) => {
                const s = scenarios[k].audit_risk.score;
                return `${s}/100`;
              }),
              colors: keys.map((k) => {
                const s = scenarios[k].audit_risk.score;
                return s >= 70 ? "text-red-400" : s >= 40 ? "text-amber-400" : "text-emerald-400";
              }),
            },
          ].map((row, i) => (
            <tr key={i} className="border-t" style={{ borderColor: "var(--border)" }}>
              <td className="py-2 text-slate-400">{row.label}</td>
              {keys.map((k, j) => (
                <td key={k} className={`py-2 text-right px-3 ${row.colors ? row.colors[j] : "text-slate-200"}`}>
                  {row.vals[j]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
