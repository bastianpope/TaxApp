"use client";

import { useState } from "react";
import WizardShell from "@/components/WizardShell";
import { useReturn } from "@/context/ReturnContext";
import type { FilingStatus, Dependent } from "@/lib/types";
import { FILING_STATUS_LABELS } from "@/lib/utils";

export default function Step1Personal() {
  const { state, dispatch } = useReturn();
  const { data } = state;

  const [dependents, setDependents] = useState<Dependent[]>(data.dependents ?? []);
  const [filingStatus, setFilingStatus] = useState<FilingStatus>(data.filing_status ?? "single");
  const [taxYear, setTaxYear] = useState<number>(data.tax_year ?? 2025);
  const [priorAudit, setPriorAudit] = useState<boolean>(data.prior_audit ?? false);

  function addDependent() {
    setDependents([...dependents, { age: 0, relationship: "child", months_in_home: 12 }]);
  }

  function removeDependent(i: number) {
    setDependents(dependents.filter((_, idx) => idx !== i));
  }

  function updateDependent(i: number, field: keyof Dependent, value: string | number | boolean) {
    setDependents(dependents.map((d, idx) => idx === i ? { ...d, [field]: value } : d));
  }

  function handleNext() {
    dispatch({
      type: "PATCH",
      patch: {
        filing_status: filingStatus,
        tax_year: taxYear,
        prior_audit: priorAudit,
        dependents,
      },
    });
  }

  return (
    <WizardShell
      step={1}
      title="Personal Information"
      subtitle="Tell us about yourself and your household."
      onNext={handleNext}
    >
      <div className="card space-y-5">
        {/* Tax Year */}
        <div>
          <label className="label" htmlFor="tax-year">Tax Year</label>
          <select
            id="tax-year"
            className="input"
            value={taxYear}
            onChange={(e) => setTaxYear(parseInt(e.target.value))}
          >
            <option value={2025}>2025</option>
            <option value={2024}>2024</option>
          </select>
        </div>

        {/* Filing status */}
        <div>
          <label className="label" htmlFor="filing-status">Filing Status</label>
          <select
            id="filing-status"
            className="input"
            value={filingStatus}
            onChange={(e) => setFilingStatus(e.target.value as FilingStatus)}
          >
            {Object.entries(FILING_STATUS_LABELS).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </select>
        </div>

        {/* Prior audit */}
        <div className="flex items-center gap-3">
          <input
            id="prior-audit"
            type="checkbox"
            className="w-4 h-4 accent-sky-500"
            checked={priorAudit}
            onChange={(e) => setPriorAudit(e.target.checked)}
          />
          <label htmlFor="prior-audit" className="text-sm cursor-pointer">
            I have been audited by the IRS in the past 3 years
            <span className="text-xs text-slate-500 block">This increases your audit risk score if checked</span>
          </label>
        </div>
      </div>

      {/* Dependents */}
      <div className="card space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-sm">Dependents</h3>
          <button type="button" id="add-dependent" onClick={addDependent} className="btn-ghost text-xs px-3 py-1.5">
            + Add Dependent
          </button>
        </div>

        {dependents.length === 0 && (
          <p className="text-sm text-slate-500 py-2 text-center">No dependents added</p>
        )}

        {dependents.map((dep, i) => (
          <div key={i} className="rounded-lg p-4 space-y-3" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)" }}>
            <div className="flex justify-between items-center">
              <span className="text-xs font-semibold text-slate-400">Dependent {i + 1}</span>
              <button type="button" onClick={() => removeDependent(i)} className="text-xs text-red-400 hover:text-red-300">
                Remove
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label" htmlFor={`dep-rel-${i}`}>Relationship</label>
                <select
                  id={`dep-rel-${i}`}
                  className="input"
                  value={dep.relationship ?? "child"}
                  onChange={(e) => updateDependent(i, "relationship", e.target.value)}
                >
                  <option value="child">Child</option>
                  <option value="parent">Parent</option>
                  <option value="sibling">Sibling</option>
                  <option value="other">Other Relative</option>
                </select>
              </div>
              <div>
                <label className="label" htmlFor={`dep-age-${i}`}>Age</label>
                <input
                  id={`dep-age-${i}`}
                  type="number"
                  className="input"
                  min={0}
                  max={100}
                  value={dep.age}
                  onChange={(e) => updateDependent(i, "age", parseInt(e.target.value) || 0)}
                />
              </div>
              <div>
                <label className="label" htmlFor={`dep-months-${i}`}>Months in Home</label>
                <input
                  id={`dep-months-${i}`}
                  type="number"
                  className="input"
                  min={0}
                  max={12}
                  value={dep.months_in_home ?? 12}
                  onChange={(e) => updateDependent(i, "months_in_home", parseInt(e.target.value) || 0)}
                />
              </div>
              <div className="flex items-end pb-2">
                <label className="flex items-center gap-2 cursor-pointer text-sm">
                  <input
                    type="checkbox"
                    className="w-4 h-4 accent-sky-500"
                    checked={dep.full_time_student ?? false}
                    onChange={(e) => updateDependent(i, "full_time_student", e.target.checked)}
                  />
                  Full-time student
                </label>
              </div>
            </div>
          </div>
        ))}
      </div>
    </WizardShell>
  );
}
