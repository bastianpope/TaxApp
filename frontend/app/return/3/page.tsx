"use client";

import { useState } from "react";
import WizardShell from "@/components/WizardShell";
import { useReturn } from "@/context/ReturnContext";
import type { ScheduleCBusiness } from "@/lib/types";

function emptyBiz(): ScheduleCBusiness {
  return { gross_income: 0 };
}

function NumInput({ id, label, value, onChange }: { id: string; label: string; value: number; onChange: (v: number) => void }) {
  return (
    <div>
      <label className="label" htmlFor={id}>{label}</label>
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

export default function Step3Business() {
  const { state, dispatch } = useReturn();
  const [businesses, setBusinesses] = useState<ScheduleCBusiness[]>(
    state.data.schedule_c_businesses?.length ? state.data.schedule_c_businesses : []
  );

  function updateBiz(i: number, field: keyof ScheduleCBusiness, val: string | number) {
    setBusinesses(businesses.map((b, idx) => idx === i ? { ...b, [field]: val } : b));
  }

  function handleNext() {
    dispatch({ type: "PATCH", patch: { schedule_c_businesses: businesses } });
  }

  if (businesses.length === 0) {
    return (
      <WizardShell step={3} title="Business Income" subtitle="Add self-employment income if you freelanced, ran a business, or received 1099-NEC income." onNext={handleNext}>
        <div className="card flex flex-col items-center justify-center py-12 space-y-4">
          <div className="text-4xl">💼</div>
          <p className="text-slate-400 text-sm">No businesses added yet</p>
          <button type="button" id="add-business" onClick={() => setBusinesses([emptyBiz()])} className="btn-primary">
            + Add Schedule C Business
          </button>
        </div>
      </WizardShell>
    );
  }

  return (
    <WizardShell step={3} title="Business Income (Schedule C)" subtitle="Enter income and expenses for each self-employment activity." onNext={handleNext}>
      <div className="flex justify-end mb-2">
        <button type="button" id="add-business" onClick={() => setBusinesses([...businesses, emptyBiz()])} className="btn-ghost text-xs px-3 py-1.5">
          + Add Business
        </button>
      </div>

      {businesses.map((biz, i) => (
        <div key={i} className="card space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="font-semibold text-sm">Business {i + 1}</h3>
            <button type="button" onClick={() => setBusinesses(businesses.filter((_, idx) => idx !== i))} className="text-xs text-red-400">Remove</button>
          </div>

          {/* Name / type */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label" htmlFor={`biz-name-${i}`}>Business Name (optional)</label>
              <input id={`biz-name-${i}`} type="text" className="input" value={biz.business_name ?? ""} onChange={(e) => updateBiz(i, "business_name", e.target.value)} placeholder="e.g. Freelance Design" />
            </div>
            <div>
              <label className="label" htmlFor={`biz-type-${i}`}>Business Type (optional)</label>
              <select id={`biz-type-${i}`} className="input" value={biz.business_type ?? ""} onChange={(e) => updateBiz(i, "business_type", e.target.value)}>
                <option value="">— Select —</option>
                <option value="consulting">Consulting</option>
                <option value="freelance">Freelance / Creative</option>
                <option value="retail">Retail / E-commerce</option>
                <option value="rideshare">Rideshare / Delivery</option>
                <option value="real_estate">Real Estate</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          {/* Income */}
          <div className="pt-1">
            <p className="text-xs font-semibold text-sky-400 uppercase tracking-wider mb-3">Revenue</p>
            <NumInput id={`biz-income-${i}`} label="Gross Income / Revenue" value={biz.gross_income} onChange={(v) => updateBiz(i, "gross_income", v)} />
          </div>

          {/* Expenses */}
          <div>
            <p className="text-xs font-semibold text-sky-400 uppercase tracking-wider mb-3">Expenses</p>
            <div className="grid grid-cols-2 gap-3">
              <NumInput id={`biz-adv-${i}`} label="Advertising" value={biz.advertising ?? 0} onChange={(v) => updateBiz(i, "advertising", v)} />
              <NumInput id={`biz-car-${i}`} label="Car & Truck" value={biz.car_truck ?? 0} onChange={(v) => updateBiz(i, "car_truck", v)} />
              <NumInput id={`biz-ins-${i}`} label="Insurance" value={biz.insurance ?? 0} onChange={(v) => updateBiz(i, "insurance", v)} />
              <NumInput id={`biz-legal-${i}`} label="Legal & Professional" value={biz.legal_professional ?? 0} onChange={(v) => updateBiz(i, "legal_professional", v)} />
              <NumInput id={`biz-meals-${i}`} label="Meals (50%)" value={biz.meals ?? 0} onChange={(v) => updateBiz(i, "meals", v)} />
              <NumInput id={`biz-office-${i}`} label="Office Expense" value={biz.office_expense ?? 0} onChange={(v) => updateBiz(i, "office_expense", v)} />
              <NumInput id={`biz-rent-${i}`} label="Rent / Lease" value={biz.rent_lease ?? 0} onChange={(v) => updateBiz(i, "rent_lease", v)} />
              <NumInput id={`biz-supplies-${i}`} label="Supplies" value={biz.supplies ?? 0} onChange={(v) => updateBiz(i, "supplies", v)} />
              <NumInput id={`biz-travel-${i}`} label="Travel" value={biz.travel ?? 0} onChange={(v) => updateBiz(i, "travel", v)} />
              <NumInput id={`biz-utils-${i}`} label="Utilities" value={biz.utilities ?? 0} onChange={(v) => updateBiz(i, "utilities", v)} />
              <NumInput id={`biz-other-${i}`} label="Other Expenses" value={biz.other_expenses ?? 0} onChange={(v) => updateBiz(i, "other_expenses", v)} />
            </div>
          </div>

          {/* Home office */}
          <div>
            <p className="text-xs font-semibold text-sky-400 uppercase tracking-wider mb-3">Home Office (optional)</p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label" htmlFor={`biz-ho-sqft-${i}`}>Office Sq Ft</label>
                <input id={`biz-ho-sqft-${i}`} type="number" className="input" min={0} placeholder="0" value={biz.home_office_sqft ?? ""} onChange={(e) => updateBiz(i, "home_office_sqft", parseInt(e.target.value) || 0)} />
              </div>
              <div>
                <label className="label" htmlFor={`biz-home-sqft-${i}`}>Total Home Sq Ft</label>
                <input id={`biz-home-sqft-${i}`} type="number" className="input" min={0} placeholder="0" value={biz.home_total_sqft ?? ""} onChange={(e) => updateBiz(i, "home_total_sqft", parseInt(e.target.value) || 0)} />
              </div>
            </div>
          </div>

          {/* Vehicle */}
          <div>
            <p className="text-xs font-semibold text-sky-400 uppercase tracking-wider mb-3">Vehicle Mileage (optional)</p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label" htmlFor={`biz-biz-miles-${i}`}>Business Miles</label>
                <input id={`biz-biz-miles-${i}`} type="number" className="input" min={0} placeholder="0" value={biz.vehicle_business_miles ?? ""} onChange={(e) => updateBiz(i, "vehicle_business_miles", parseInt(e.target.value) || 0)} />
              </div>
              <div>
                <label className="label" htmlFor={`biz-tot-miles-${i}`}>Total Miles</label>
                <input id={`biz-tot-miles-${i}`} type="number" className="input" min={0} placeholder="0" value={biz.vehicle_total_miles ?? ""} onChange={(e) => updateBiz(i, "vehicle_total_miles", parseInt(e.target.value) || 0)} />
              </div>
            </div>
          </div>
        </div>
      ))}
    </WizardShell>
  );
}
