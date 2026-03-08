"use client";

import { useState } from "react";
import WizardShell from "@/components/WizardShell";
import { useReturn } from "@/context/ReturnContext";
import type { StateResidency } from "@/lib/types";

function emptyResidency(): StateResidency {
  return { state: "IL", resident_full_year: true };
}

function NumInput({ id, label, value, onChange, hint }: { id: string; label: string; value: number; onChange: (v: number) => void; hint?: string }) {
  return (
    <div>
      <label className="label" htmlFor={id}>{label}</label>
      {hint && <p className="text-xs text-slate-500 mb-1">{hint}</p>}
      <div className="relative">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm">$</span>
        <input
          id={id}
          type="number"
          className="input pl-7"
          min={0}
          step={1}
          placeholder="0"
          value={value || ""}
          onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        />
      </div>
    </div>
  );
}

export default function Step5State() {
  const { state, dispatch } = useReturn();
  const d = state.data;

  const [residencies, setResidencies] = useState<StateResidency[]>(
    d.state_residencies?.length ? d.state_residencies : [emptyResidency()]
  );

  // Per-residency IL property tax is stored inside each StateResidency entry
  function updateRes(i: number, field: keyof StateResidency, val: string | number | boolean) {
    setResidencies(residencies.map((r, idx) => idx === i ? { ...r, [field]: val } : r));
  }

  const hasIL = residencies.some(r => r.state === "IL");
  const hasMN = residencies.some(r => r.state === "MN");

  // MN school district (stored in the MN residency entry)
  const mnIdx = residencies.findIndex(r => r.state === "MN");

  function handleNext() {
    dispatch({
      type: "PATCH",
      patch: {
        state_residencies: residencies,
      },
    });
  }

  return (
    <WizardShell step={5} title="State Taxes" subtitle="We support Illinois (IL) and Minnesota (MN) state returns." onNext={handleNext}>

      {/* State residency */}
      <div className="card space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-sm">State Residency</h3>
          {residencies.length < 2 && (
            <button type="button" onClick={() => setResidencies([...residencies, emptyResidency()])} className="btn-ghost text-xs px-3 py-1.5">
              + Part-year / Multi-state
            </button>
          )}
        </div>

        {residencies.map((res, i) => (
          <div key={i} className="space-y-3 rounded-lg p-3" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)" }}>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label" htmlFor={`res-state-${i}`}>State</label>
                <select
                  id={`res-state-${i}`}
                  className="input"
                  value={res.state}
                  onChange={(e) => updateRes(i, "state", e.target.value)}
                >
                  <option value="IL">Illinois</option>
                  <option value="MN">Minnesota</option>
                </select>
              </div>
              <div className="flex flex-col justify-end">
                <label className="flex items-center gap-2 cursor-pointer pt-1">
                  <input
                    id={`res-full-${i}`}
                    type="checkbox"
                    className="rounded"
                    checked={res.resident_full_year ?? true}
                    onChange={(e) => updateRes(i, "resident_full_year", e.target.checked)}
                  />
                  <span className="text-sm text-slate-300">Full-year resident</span>
                </label>
              </div>
            </div>
            {residencies.length > 1 && (
              <div className="flex justify-end">
                <button type="button" onClick={() => setResidencies(residencies.filter((_, idx) => idx !== i))} className="text-xs text-red-400">Remove</button>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* IL Credits */}
      {hasIL && (
        <div className="card space-y-4">
          <h3 className="font-semibold text-sm text-blue-400">🔵 Illinois — Property Tax Credit</h3>
          <NumInput
            id="il-prop-tax"
            label="IL Property Tax Paid"
            hint="5% credit on IL property taxes paid"
            value={residencies.find(r => r.state === "IL")?.il_property_taxes_paid ?? 0}
            onChange={(v) => {
              const ilIdx = residencies.findIndex(r => r.state === "IL");
              if (ilIdx >= 0) updateRes(ilIdx, "il_property_taxes_paid", v);
            }}
          />
        </div>
      )}

      {/* MN School District */}
      {hasMN && mnIdx >= 0 && (
        <div className="card space-y-4">
          <h3 className="font-semibold text-sm text-purple-400">🟣 Minnesota — School District</h3>
          <div>
            <label className="label" htmlFor="mn-school">School District Code</label>
            <input
              id="mn-school"
              type="text"
              className="input"
              placeholder="e.g. 0621"
              maxLength={6}
              value={residencies[mnIdx]?.mn_school_district ?? ""}
              onChange={(e) => updateRes(mnIdx, "mn_school_district", e.target.value)}
            />
            <p className="text-xs text-slate-500 mt-1">Find your district at <span className="text-purple-400">revenue.state.mn.us</span></p>
          </div>
        </div>
      )}

      <div className="rounded-lg p-4" style={{ background: "rgba(16,185,129,0.05)", border: "1px solid rgba(16,185,129,0.15)" }}>
        <p className="text-xs text-emerald-300">
          ℹ️ State income tax withheld should be entered in the W-2 section (Step 2).
          We apply it automatically when calculating your state balance.
        </p>
      </div>
    </WizardShell>
  );
}
