"use client";

import { formatDollar, formatPct } from "@/lib/utils";
import type { FederalBreakdown, StateBreakdown } from "@/lib/types";

interface FederalCardProps {
  data: FederalBreakdown;
  withheld: string;
}

export function FederalCard({ data, withheld }: FederalCardProps) {
  const refundOrOwed = parseFloat(data.refund_or_owed);
  const isRefund = refundOrOwed >= 0;

  return (
    <div className="card space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Federal Tax (1040)</h3>
        <span className="text-xs text-slate-400">TY {new Date().getFullYear() - 1}</span>
      </div>

      <div className="space-y-1">
        <div className="tax-row"><span className="label-col">Gross Income</span><span className="value-col">{formatDollar(data.gross_income)}</span></div>
        <div className="tax-row"><span className="label-col">AGI</span><span className="value-col">{formatDollar(data.agi)}</span></div>
        <div className="tax-row">
          <span className="label-col">{data.deduction_method === "standard" ? "Standard Deduction" : "Itemized Deductions"}</span>
          <span className="value-col text-emerald-400">−{formatDollar(data.deduction_used)}</span>
        </div>
        <div className="tax-row"><span className="label-col">Taxable Income</span><span className="value-col">{formatDollar(data.taxable_income)}</span></div>
        <div className="tax-row"><span className="label-col">Income Tax</span><span className="value-col">{formatDollar(data.income_tax)}</span></div>
        {parseFloat(data.se_tax) > 0 && (
          <div className="tax-row"><span className="label-col">Self-Employment Tax</span><span className="value-col">{formatDollar(data.se_tax)}</span></div>
        )}
        {parseFloat(data.child_tax_credit) > 0 && (
          <div className="tax-row"><span className="label-col">Child Tax Credit</span><span className="value-col text-emerald-400">−{formatDollar(data.child_tax_credit)}</span></div>
        )}
        {parseFloat(data.eitc) > 0 && (
          <div className="tax-row"><span className="label-col">EITC</span><span className="value-col text-emerald-400">−{formatDollar(data.eitc)}</span></div>
        )}
        <div className="tax-row"><span className="label-col">Total Withheld</span><span className="value-col text-emerald-400">−{formatDollar(withheld)}</span></div>
      </div>

      <div className="rounded-lg p-3 text-center" style={{ background: isRefund ? "rgba(16,185,129,0.08)" : "rgba(239,68,68,0.08)", border: `1px solid ${isRefund ? "rgba(16,185,129,0.2)" : "rgba(239,68,68,0.2)"}` }}>
        <p className="text-xs font-medium mb-0.5" style={{ color: isRefund ? "#10b981" : "#ef4444" }}>
          {isRefund ? "Federal Refund" : "Amount Owed"}
        </p>
        <p className="text-3xl font-bold tabular-nums" style={{ color: isRefund ? "#10b981" : "#ef4444" }}>
          {formatDollar(Math.abs(refundOrOwed))}
        </p>
        <p className="text-xs text-slate-400 mt-1">
          Effective rate: {formatPct(data.effective_rate)} · Marginal: {data.marginal_rate}%
        </p>
      </div>
    </div>
  );
}

interface StateCardProps {
  data: StateBreakdown;
}

const STATE_NAMES: Record<string, string> = {
  IL: "Illinois",
  MN: "Minnesota",
};

export function StateCard({ data }: StateCardProps) {
  const refundOrOwed = parseFloat(data.refund_or_owed);
  const isRefund = refundOrOwed >= 0;

  return (
    <div className="card space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">{STATE_NAMES[data.state] ?? data.state} State Tax</h3>
        <span className={`badge ${isRefund ? "badge-green" : "badge-red"}`}>
          {isRefund ? "Refund" : "Owed"}
        </span>
      </div>
      <div className="space-y-1">
        <div className="tax-row"><span className="label-col">State Taxable Income</span><span className="value-col">{formatDollar(data.taxable_income)}</span></div>
        <div className="tax-row"><span className="label-col">State Tax</span><span className="value-col">{formatDollar(data.tax)}</span></div>
        {parseFloat(data.credits) > 0 && (
          <div className="tax-row"><span className="label-col">Credits</span><span className="value-col text-emerald-400">−{formatDollar(data.credits)}</span></div>
        )}
        <div className="tax-row"><span className="label-col">Net State Tax</span><span className="value-col">{formatDollar(data.net_tax)}</span></div>
        <div className="tax-row"><span className="label-col">State Withheld</span><span className="value-col text-emerald-400">−{formatDollar(data.withheld)}</span></div>
      </div>
      <div className="rounded-lg p-3 text-center" style={{ background: isRefund ? "rgba(16,185,129,0.08)" : "rgba(239,68,68,0.08)", border: `1px solid ${isRefund ? "rgba(16,185,129,0.2)" : "rgba(239,68,68,0.2)"}` }}>
        <p className="text-2xl font-bold tabular-nums" style={{ color: isRefund ? "#10b981" : "#ef4444" }}>
          {formatDollar(Math.abs(refundOrOwed))}
        </p>
        <p className="text-xs text-slate-400 mt-1">{isRefund ? "State Refund" : "State Balance Due"}</p>
      </div>
    </div>
  );
}
