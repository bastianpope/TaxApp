import type { StateResult } from "@/lib/types";
import { fmtDollar, fmtPct } from "@/lib/utils";

const STATE_NAMES: Record<string, string> = {
  IL: "Illinois",
  MN: "Minnesota",
};

function Row({ label, value }: { label: string; value: string }) {
  return (
    <tr className="border-t" style={{ borderColor: "var(--border)" }}>
      <td className="py-2 text-xs text-slate-400">{label}</td>
      <td className="py-2 text-xs text-right font-medium">{value}</td>
    </tr>
  );
}

export default function StateCard({ results }: { results: Record<string, StateResult> }) {
  const entries = Object.entries(results);

  return (
    <div className="card space-y-6">
      {entries.map(([stateCode, sr]) => {
        const balanceColor = sr.balance < 0 ? "text-emerald-400" : sr.balance > 0 ? "text-red-400" : "text-slate-300";

        return (
          <div key={stateCode} className="space-y-4">
            <div className="flex items-center gap-2">
              <span className="text-xl">🏛️</span>
              <h2 className="font-semibold">{STATE_NAMES[stateCode] ?? stateCode} Return</h2>
            </div>

            <div
              className="rounded-xl p-5 text-center"
              style={{
                background: sr.balance < 0 ? "rgba(16,185,129,0.08)" : "rgba(239,68,68,0.08)",
                border: `1px solid ${sr.balance < 0 ? "rgba(16,185,129,0.2)" : "rgba(239,68,68,0.2)"}`,
              }}
            >
              <p className="text-xs text-slate-400 mb-1">{sr.balance < 0 ? "Refund" : sr.balance > 0 ? "Amount Due" : "No Balance"}</p>
              <p className={`text-3xl font-extrabold ${balanceColor}`}>
                {sr.balance < 0 ? fmtDollar(-sr.balance) : fmtDollar(sr.balance)}
              </p>
              <p className="text-xs text-slate-500 mt-1">Rate: {fmtPct(sr.effective_rate)}</p>
            </div>

            <table className="w-full">
              <tbody>
                <Row label="State Taxable Income" value={fmtDollar(sr.taxable_income)} />
                <Row label="State Tax" value={fmtDollar(sr.state_tax)} />
                {(sr.credits_applied ?? 0) > 0 && (
                  <Row label="Credits Applied" value={`– ${fmtDollar(sr.credits_applied!)}`} />
                )}
                <Row label="Withheld" value={`– ${fmtDollar(sr.withheld)}`} />
              </tbody>
            </table>

            {sr.notes && sr.notes.length > 0 && (
              <ul className="space-y-1">
                {sr.notes.map((note, i) => (
                  <li key={i} className="text-xs text-slate-500 flex gap-2">
                    <span>ℹ️</span>
                    <span>{note}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        );
      })}
    </div>
  );
}
