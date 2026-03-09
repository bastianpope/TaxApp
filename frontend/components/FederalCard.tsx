import type { FederalResult } from "@/lib/types";
import { fmtDollar, fmtPctScaled } from "@/lib/utils";

type Props = FederalResult & { grossIncome: number };

function Row({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <tr className="border-t" style={{ borderColor: "var(--border)" }}>
      <td className="py-2 text-xs text-slate-400">
        {label}
        {sub && <span className="block text-slate-600 text-xs">{sub}</span>}
      </td>
      <td className="py-2 text-xs text-right font-medium">{value}</td>
    </tr>
  );
}

export default function FederalCard({
  grossIncome,
  agi,
  taxable_income,
  federal_tax,
  effective_rate,
  total_withheld,
  balance,
  standard_deduction,
  itemized_deduction,
  use_itemized,
  self_employment_tax,
  qbi_deduction,
}: Props) {
  const balanceColor = balance < 0 ? "text-emerald-400" : balance > 0 ? "text-red-400" : "text-slate-300";

  return (
    <div className="card space-y-4">
      <div className="flex items-center gap-2">
        <span className="text-xl">🇺🇸</span>
        <h2 className="font-semibold">Federal Return</h2>
      </div>

      {/* Balance highlight */}
      <div
        className="rounded-xl p-5 text-center"
        style={{
          background: balance < 0 ? "rgba(16,185,129,0.08)" : "rgba(239,68,68,0.08)",
          border: `1px solid ${balance < 0 ? "rgba(16,185,129,0.2)" : "rgba(239,68,68,0.2)"}`,
        }}
      >
        <p className="text-xs text-slate-400 mb-1">{balance < 0 ? "Refund" : balance > 0 ? "Amount Due" : "No Balance"}</p>
        <p className={`text-3xl font-extrabold ${balanceColor}`}>
          {balance < 0 ? fmtDollar(-balance) : fmtDollar(balance)}
        </p>
        <p className="text-xs text-slate-500 mt-1">Effective rate: {fmtPctScaled(effective_rate)}</p>
      </div>

      {/* Detail table */}
      <table className="w-full">
        <tbody>
          <Row label="Gross Income" value={fmtDollar(grossIncome)} />
          <Row label="Adjusted Gross Income (AGI)" value={fmtDollar(agi)} />
          <Row
            label={use_itemized ? "Itemized Deduction ✓" : "Standard Deduction ✓"}
            value={`– ${fmtDollar(use_itemized ? itemized_deduction : standard_deduction)}`}
            sub={use_itemized ? `Standard was ${fmtDollar(standard_deduction)}` : `Itemized was ${fmtDollar(itemized_deduction)}`}
          />
          {(qbi_deduction ?? 0) > 0 && (
            <Row label="QBI Deduction (20%)" value={`– ${fmtDollar(qbi_deduction!)}`} />
          )}
          <Row label="Taxable Income" value={fmtDollar(taxable_income)} />
          <Row label="Federal Income Tax" value={fmtDollar(federal_tax)} />
          {(self_employment_tax ?? 0) > 0 && (
            <Row label="Self-Employment Tax" value={fmtDollar(self_employment_tax!)} sub="15.3% on net SE income" />
          )}
          <Row label="Total Withheld" value={`– ${fmtDollar(total_withheld)}`} />
        </tbody>
      </table>
    </div>
  );
}
