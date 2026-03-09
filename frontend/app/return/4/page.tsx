"use client";

import { useState } from "react";
import WizardShell from "@/components/WizardShell";
import { useReturn } from "@/context/ReturnContext";

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

export default function Step4Deductions() {
  const { state, dispatch } = useReturn();
  const d = state.data;
  const id = d.itemized_deductions;

  // Itemized deductions (nested under itemized_deductions in TaxReturn)
  const [mortgageInterest, setMortgageInterest] = useState<number>(id?.mortgage_interest ?? 0);
  const [realEstateTaxes, setRealEstateTaxes] = useState<number>(id?.real_estate_taxes ?? 0);
  const [charitableCash, setCharitableCash] = useState<number>(id?.charitable_cash ?? 0);
  const [charitableNonCash, setCharitableNonCash] = useState<number>(id?.charitable_non_cash ?? 0);
  const [medicalExpenses, setMedicalExpenses] = useState<number>(id?.medical_expenses ?? 0);

  // Above-the-line adjustments (top-level on TaxReturn)
  const [studentLoanInterest, setStudentLoanInterest] = useState<number>(d.student_loan_interest ?? 0);
  const [iraContribution, setIraContribution] = useState<number>(d.traditional_ira_contribution ?? 0);
  const [hsaContribution, setHsaContribution] = useState<number>(d.health_savings_account ?? 0);
  const [tuitionFees, setTuitionFees] = useState<number>(d.tuition_fees ?? 0);

  function handleNext() {
    dispatch({
      type: "PATCH",
      patch: {
        itemized_deductions: {
          mortgage_interest: mortgageInterest,
          real_estate_taxes: realEstateTaxes,
          charitable_cash: charitableCash,
          charitable_non_cash: charitableNonCash,
          medical_expenses: medicalExpenses,
          state_local_taxes: id?.state_local_taxes ?? 0,
        },
        student_loan_interest: studentLoanInterest,
        traditional_ira_contribution: iraContribution,
        health_savings_account: hsaContribution,
        tuition_fees: tuitionFees,
      },
    });
  }

  return (
    <WizardShell
      step={4}
      title="Deductions &amp; Adjustments"
      subtitle="Enter itemized deductions and above-the-line adjustments. We'll compare vs. your standard deduction automatically."
      onNext={handleNext}
    >
      {/* Homeowner */}
      <div className="card space-y-4">
        <h3 className="font-semibold text-sm text-sky-400">🏠 Home Ownership</h3>
        <NumInput id="mortgage-interest" label="Mortgage Interest (Form 1098 Box 1)" value={mortgageInterest} onChange={setMortgageInterest} />
        <NumInput id="real-estate-taxes" label="Property Taxes Paid" hint="Deductible up to $40,000 SALT cap (OBBBA 2025)" value={realEstateTaxes} onChange={setRealEstateTaxes} />
      </div>

      {/* Charitable */}
      <div className="card space-y-4">
        <h3 className="font-semibold text-sm text-sky-400">🤲 Charitable Contributions</h3>
        <NumInput id="charitable-cash" label="Cash Donations" hint="Bank records or receipts required" value={charitableCash} onChange={setCharitableCash} />
        <NumInput id="charitable-non-cash" label="Non-Cash Donations" hint="Clothing, goods, vehicles" value={charitableNonCash} onChange={setCharitableNonCash} />
      </div>

      {/* Medical */}
      <div className="card space-y-4">
        <h3 className="font-semibold text-sm text-sky-400">🏥 Medical Expenses</h3>
        <NumInput id="medical-expenses" label="Total Unreimbursed Medical Expenses" hint="Only the amount exceeding 7.5% of AGI is deductible" value={medicalExpenses} onChange={setMedicalExpenses} />
      </div>

      {/* Above the line */}
      <div className="card space-y-4">
        <h3 className="font-semibold text-sm text-sky-400">📉 Above-the-Line Adjustments</h3>
        <p className="text-xs text-slate-500">These reduce your AGI regardless of whether you itemize.</p>
        <div className="grid grid-cols-2 gap-3">
          <NumInput id="student-loan" label="Student Loan Interest" hint="Limited to $2,500" value={studentLoanInterest} onChange={setStudentLoanInterest} />
          <NumInput id="ira-contrib" label="Traditional IRA Contribution" hint="Max $7,000 (+ $1k catch-up 50+)" value={iraContribution} onChange={setIraContribution} />
          <NumInput id="hsa-contrib" label="HSA Contribution" hint="Self: $4,150 · Family: $8,300 (2024)" value={hsaContribution} onChange={setHsaContribution} />
          <NumInput id="tuition" label="Tuition & Fees Deduction" hint="Max $4,000 if income eligible" value={tuitionFees} onChange={setTuitionFees} />
        </div>
      </div>
    </WizardShell>
  );
}
