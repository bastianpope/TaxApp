"use client";

import { useState } from "react";
import WizardShell from "@/components/WizardShell";
import { useReturn } from "@/context/ReturnContext";
import type { W2Income, Income1099NEC, Income1099INT, Income1099DIV } from "@/lib/types";

function emptyW2(): W2Income {
  return { wages: 0, federal_withheld: 0 };
}
function emptyNEC(): Income1099NEC {
  return { amount: 0 };
}
function emptyINT(): Income1099INT {
  return { interest: 0 };
}
function emptyDIV(): Income1099DIV {
  return { ordinary_dividends: 0 };
}

function NumInput({
  id, label, value, onChange, prefix = "$", placeholder = "0",
}: {
  id: string; label: string; value: number; onChange: (v: number) => void; prefix?: string; placeholder?: string;
}) {
  return (
    <div>
      <label className="label" htmlFor={id}>{label}</label>
      <div className="relative">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm">{prefix}</span>
        <input
          id={id}
          type="number"
          className="input pl-7"
          min={0}
          step={1}
          placeholder={placeholder}
          value={value || ""}
          onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        />
      </div>
    </div>
  );
}

export default function Step2Income() {
  const { state, dispatch } = useReturn();
  const { data } = state;

  const [w2s, setW2s] = useState<W2Income[]>(data.w2s?.length ? data.w2s : [emptyW2()]);
  const [necs, setNecs] = useState<Income1099NEC[]>(data.nec_1099s ?? []);
  const [ints, setInts] = useState<Income1099INT[]>(data.int_1099s ?? []);
  const [divs, setDivs] = useState<Income1099DIV[]>(data.div_1099s ?? []);
  const [otherIncome, setOtherIncome] = useState<number>(data.other_income ?? 0);
  const [otherDesc, setOtherDesc] = useState<string>(data.other_income_description ?? "");

  function handleNext() {
    dispatch({
      type: "PATCH",
      patch: {
        w2s,
        nec_1099s: necs,
        int_1099s: ints,
        div_1099s: divs,
        other_income: otherIncome,
        other_income_description: otherDesc,
      },
    });
  }

  function updateW2(i: number, field: keyof W2Income, val: string | number) {
    setW2s(w2s.map((w, idx) => idx === i ? { ...w, [field]: val } : w));
  }
  function updateNEC(i: number, field: keyof Income1099NEC, val: string | number) {
    setNecs(necs.map((n, idx) => idx === i ? { ...n, [field]: val } : n));
  }
  function updateINT(i: number, field: keyof Income1099INT, val: string | number) {
    setInts(ints.map((n, idx) => idx === i ? { ...n, [field]: val } : n));
  }
  function updateDIV(i: number, field: keyof Income1099DIV, val: string | number) {
    setDivs(divs.map((n, idx) => idx === i ? { ...n, [field]: val } : n));
  }

  return (
    <WizardShell
      step={2}
      title="Income"
      subtitle="Enter all income sources. Add multiple W-2s or 1099s as needed."
      onNext={handleNext}
    >
      {/* W-2s */}
      <div className="card space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-sm">W-2 Wages</h3>
          <button type="button" id="add-w2" onClick={() => setW2s([...w2s, emptyW2()])} className="btn-ghost text-xs px-3 py-1.5">
            + Add W-2
          </button>
        </div>
        {w2s.map((w, i) => (
          <div key={i} className="rounded-lg p-4 space-y-3" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)" }}>
            <div className="flex justify-between">
              <span className="text-xs font-semibold text-slate-400">Employer {i + 1}</span>
              {w2s.length > 1 && (
                <button type="button" onClick={() => setW2s(w2s.filter((_, idx) => idx !== i))} className="text-xs text-red-400">Remove</button>
              )}
            </div>
            <div>
              <label className="label" htmlFor={`w2-employer-${i}`}>Employer Name (optional)</label>
              <input
                id={`w2-employer-${i}`}
                type="text"
                className="input"
                placeholder="e.g. Acme Corp"
                value={w.employer_name ?? ""}
                onChange={(e) => updateW2(i, "employer_name", e.target.value)}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <NumInput id={`w2-wages-${i}`} label="Box 1 — Wages" value={w.wages} onChange={(v) => updateW2(i, "wages", v)} />
              <NumInput id={`w2-fed-${i}`} label="Box 2 — Federal Withheld" value={w.federal_withheld} onChange={(v) => updateW2(i, "federal_withheld", v)} />
              <NumInput id={`w2-ss-${i}`} label="Box 4 — Social Security" value={w.social_security_withheld ?? 0} onChange={(v) => updateW2(i, "social_security_withheld", v)} />
              <NumInput id={`w2-med-${i}`} label="Box 6 — Medicare" value={w.medicare_withheld ?? 0} onChange={(v) => updateW2(i, "medicare_withheld", v)} />
              <NumInput id={`w2-state-${i}`} label="State Tax Withheld" value={w.state_withheld ?? 0} onChange={(v) => updateW2(i, "state_withheld", v)} />
            </div>
          </div>
        ))}
      </div>

      {/* 1099-NEC */}
      <div className="card space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-sm">1099-NEC (Freelance / Contract)</h3>
          <button type="button" id="add-nec" onClick={() => setNecs([...necs, emptyNEC()])} className="btn-ghost text-xs px-3 py-1.5">
            + Add 1099-NEC
          </button>
        </div>
        {necs.length === 0 && <p className="text-sm text-slate-500">None added</p>}
        {necs.map((n, i) => (
          <div key={i} className="rounded-lg p-4 grid grid-cols-2 gap-3" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)" }}>
            <div className="col-span-2 flex justify-between">
              <span className="text-xs font-semibold text-slate-400">1099-NEC {i + 1}</span>
              <button type="button" onClick={() => setNecs(necs.filter((_, idx) => idx !== i))} className="text-xs text-red-400">Remove</button>
            </div>
            <div className="col-span-2">
              <label className="label" htmlFor={`nec-payer-${i}`}>Payer Name (optional)</label>
              <input id={`nec-payer-${i}`} type="text" className="input" value={n.payer_name ?? ""} onChange={(e) => updateNEC(i, "payer_name", e.target.value)} />
            </div>
            <NumInput id={`nec-amt-${i}`} label="Box 1 — Nonemployee Comp" value={n.amount} onChange={(v) => updateNEC(i, "amount", v)} />
            <NumInput id={`nec-fed-${i}`} label="Box 4 — Federal Withheld" value={n.federal_withheld ?? 0} onChange={(v) => updateNEC(i, "federal_withheld", v)} />
          </div>
        ))}
      </div>

      {/* 1099-INT */}
      <div className="card space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-sm">1099-INT (Interest Income)</h3>
          <button type="button" id="add-int" onClick={() => setInts([...ints, emptyINT()])} className="btn-ghost text-xs px-3 py-1.5">
            + Add 1099-INT
          </button>
        </div>
        {ints.map((n, i) => (
          <div key={i} className="grid grid-cols-2 gap-3 rounded-lg p-3" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)" }}>
            <div className="col-span-2 flex justify-between">
              <span className="text-xs font-semibold text-slate-400">1099-INT {i + 1}</span>
              <button type="button" onClick={() => setInts(ints.filter((_, idx) => idx !== i))} className="text-xs text-red-400">Remove</button>
            </div>
            <NumInput id={`int-amt-${i}`} label="Interest" value={n.interest} onChange={(v) => updateINT(i, "interest", v)} />
          </div>
        ))}
      </div>

      {/* 1099-DIV */}
      <div className="card space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-sm">1099-DIV (Dividend Income)</h3>
          <button type="button" id="add-div" onClick={() => setDivs([...divs, emptyDIV()])} className="btn-ghost text-xs px-3 py-1.5">
            + Add 1099-DIV
          </button>
        </div>
        {divs.map((n, i) => (
          <div key={i} className="grid grid-cols-2 gap-3 rounded-lg p-3" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border)" }}>
            <div className="col-span-2 flex justify-between">
              <span className="text-xs font-semibold text-slate-400">1099-DIV {i + 1}</span>
              <button type="button" onClick={() => setDivs(divs.filter((_, idx) => idx !== i))} className="text-xs text-red-400">Remove</button>
            </div>
            <NumInput id={`div-ord-${i}`} label="Ordinary Dividends" value={n.ordinary_dividends} onChange={(v) => updateDIV(i, "ordinary_dividends", v)} />
            <NumInput id={`div-qual-${i}`} label="Qualified Dividends" value={n.qualified_dividends ?? 0} onChange={(v) => updateDIV(i, "qualified_dividends", v)} />
          </div>
        ))}
      </div>

      {/* Other income */}
      <div className="card space-y-3">
        <h3 className="font-semibold text-sm">Other Income</h3>
        <NumInput id="other-income" label="Other Income Amount" value={otherIncome} onChange={setOtherIncome} />
        <div>
          <label className="label" htmlFor="other-desc">Description</label>
          <input id="other-desc" type="text" className="input" placeholder="e.g. Rental income, alimony..." value={otherDesc} onChange={(e) => setOtherDesc(e.target.value)} />
        </div>
      </div>
    </WizardShell>
  );
}
