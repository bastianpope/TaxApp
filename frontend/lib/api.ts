import type {
  TaxReturn,
  TaxResult,
  TaxCalculationResponse,
  AggressivenessLevel,
  ScenarioResult,
  FederalResult,
  AuditRisk,
} from "./types";

export type { TaxCalculationResponse, AggressivenessLevel };

const API_BASE = "/api";

class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (!res.ok) {
    // Clone before reading to avoid "body stream already read" errors
    let detail: unknown;
    const cloned = res.clone();
    try {
      detail = await cloned.json();
    } catch {
      try {
        detail = await res.text();
      } catch {
        detail = `HTTP ${res.status}`;
      }
    }
    throw new ApiError(
      `API error ${res.status}: ${res.statusText}`,
      res.status,
      detail,
    );
  }

  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Auth-aware fetch: reads token from localStorage and adds Bearer header
// ---------------------------------------------------------------------------

const TOKEN_KEY = "taxapp_access_token";

function authFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem(TOKEN_KEY) : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return fetchJson<T>(path, { ...init, headers });
}

// ---------------------------------------------------------------------------
// Saved-return shape returned by the backend list/get endpoints
// ---------------------------------------------------------------------------

export interface SavedReturn {
  id: string;
  label: string;
  tax_year: number;
  status: "draft" | "complete";
  updated_at: string;
  return_data?: Record<string, unknown>;
}

export const api = {
  health(): Promise<{ status: string; service: string }> {
    return fetchJson("/health");
  },

  calculate(taxReturn: TaxReturn): Promise<TaxResult> {
    return fetchJson("/calculate", {
      method: "POST",
      body: JSON.stringify(taxReturn),
    });
  },

  // ── Auth ──────────────────────────────────────────────────────────────────

  auth: {
    register(email: string, password: string): Promise<{ access_token: string }> {
      return fetchJson("/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
    },

    login(
      email: string,
      password: string,
      totp_code?: string,
    ): Promise<{ access_token: string }> {
      return fetchJson("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password, totp_code }),
      });
    },

    logout(): Promise<void> {
      return authFetch("/auth/logout", { method: "POST" });
    },

    me(): Promise<{ id: string; email: string; totp_enabled: boolean }> {
      return authFetch("/auth/me");
    },

    totpSetup(): Promise<{ secret: string; uri: string }> {
      return authFetch("/auth/totp/setup", { method: "POST" });
    },

    totpConfirm(code: string): Promise<{ detail: string }> {
      return authFetch("/auth/totp/confirm", {
        method: "POST",
        body: JSON.stringify({ code }),
      });
    },

    totpDisable(): Promise<{ detail: string }> {
      return authFetch("/auth/totp", { method: "DELETE" });
    },
  },

  // ── Saved returns ─────────────────────────────────────────────────────────

  returns: {
    list(): Promise<SavedReturn[]> {
      return authFetch("/returns");
    },

    create(payload: {
      label: string;
      tax_year: number;
      return_data: Record<string, unknown>;
    }): Promise<SavedReturn> {
      return authFetch("/returns", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    },

    get(id: string): Promise<SavedReturn> {
      return authFetch(`/returns/${id}`);
    },

    update(
      id: string,
      payload: Partial<{
        label: string;
        status: string;
        return_data: Record<string, unknown>;
      }>,
    ): Promise<SavedReturn> {
      return authFetch(`/returns/${id}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
    },

    delete(id: string): Promise<void> {
      return authFetch(`/returns/${id}`, { method: "DELETE" });
    },
  },
};

export { ApiError };

// ---------------------------------------------------------------------------
// Backend input schema (mirrors tax_engine/models.py TaxReturn)
// Backend uses snake_case and different field names than the frontend types.
// ---------------------------------------------------------------------------

interface BackendW2 {
  employer_name?: string;
  wages: number;
  federal_tax_withheld: number;
  state_tax_withheld?: number;
  social_security_wages?: number;
  social_security_tax?: number;
  medicare_wages?: number;
  medicare_tax?: number;
}

interface BackendNEC {
  payer_name?: string;
  amount: number;
}

interface BackendINT {
  payer_name?: string;
  interest_income: number;
  tax_exempt_interest?: number;
}

interface BackendDIV {
  payer_name?: string;
  ordinary_dividends: number;
  qualified_dividends?: number;
  capital_gain_distributions?: number;
}

interface BackendB {
  description?: string;
  date_acquired?: string;
  date_sold?: string;
  proceeds: number;
  cost_basis: number;
  is_long_term: boolean;
}

interface BackendScheduleC {
  business_name?: string;
  gross_receipts: number;
  cost_of_goods_sold?: number;
  home_office_sqft?: number;
  vehicle_business_miles?: number;
  vehicle_total_miles?: number;
  expenses?: {
    advertising?: number;
    car_and_truck?: number;
    depreciation?: number;
    insurance?: number;
    legal_and_professional?: number;
    meals?: number;
    office_expense?: number;
    rent_or_lease?: number;
    repairs_and_maintenance?: number;
    supplies?: number;
    taxes_and_licenses?: number;
    travel?: number;
    utilities?: number;
    other_expenses?: number;
  };
}

interface BackendItemized {
  medical_and_dental?: number;
  state_and_local_taxes_paid?: number;
  real_estate_taxes?: number;
  mortgage_interest?: number;
  charitable_cash?: number;
  charitable_non_cash?: number;
  casualty_and_theft?: number;
  other_deductions?: number;
}

interface BackendDependent {
  name: string;
  relationship: string;
  age: number;
  is_qualifying_child?: boolean;
}

interface BackendStateResidency {
  state_code: string;
  property_tax_paid?: number;
  state_income_tax_paid?: number;
}

interface BackendTaxReturn {
  tax_year: number;
  filing_status: string;
  aggressiveness: string; // backend uses lowercase: "low" | "medium" | "high"
  dependents: BackendDependent[];
  w2s: BackendW2[];
  income_1099_nec: BackendNEC[];
  income_1099_int: BackendINT[];
  income_1099_div: BackendDIV[];
  income_1099_b: BackendB[];
  schedule_c?: BackendScheduleC;
  itemized_deductions?: BackendItemized;
  state_residencies: BackendStateResidency[];
  prior_audit: boolean;
}

// ---------------------------------------------------------------------------
// Map frontend TaxReturn → backend TaxReturn
// ---------------------------------------------------------------------------

function toBackendPayload(
  data: Partial<TaxReturn>,
  aggressiveness: AggressivenessLevel,
): BackendTaxReturn {
  // W-2s: key rename federal_withheld → federal_tax_withheld
  const w2s: BackendW2[] = (data.w2s ?? []).map((w) => ({
    employer_name: w.employer_name,
    wages: w.wages ?? 0,
    federal_tax_withheld: w.federal_withheld ?? 0,
    state_tax_withheld: w.state_withheld,
    social_security_tax: w.social_security_withheld,
    medicare_tax: w.medicare_withheld,
  }));

  // 1099-NEC: amount field matches
  const income_1099_nec: BackendNEC[] = (data.nec_1099s ?? []).map((n) => ({
    payer_name: n.payer_name,
    amount: n.amount ?? 0,
  }));

  // 1099-INT: interest → interest_income
  const income_1099_int: BackendINT[] = (data.int_1099s ?? []).map((n) => ({
    payer_name: n.payer_name,
    interest_income: n.interest ?? 0,
  }));

  // 1099-DIV: ordinary_dividends / qualified_dividends match
  const income_1099_div: BackendDIV[] = (data.div_1099s ?? []).map((d) => ({
    payer_name: d.payer_name,
    ordinary_dividends: d.ordinary_dividends ?? 0,
    qualified_dividends: d.qualified_dividends,
  }));

  // 1099-B: long_term → is_long_term
  const income_1099_b: BackendB[] = (data.capital_gains_1099b ?? []).map(
    (b) => ({
      description: b.description,
      proceeds: b.proceeds ?? 0,
      cost_basis: b.cost_basis ?? 0,
      is_long_term: b.long_term ?? false,
    }),
  );

  // Schedule C — only support first business (backend single ScheduleC)
  let schedule_c: BackendScheduleC | undefined;
  const bizzes = data.schedule_c_businesses ?? [];
  if (bizzes.length > 0) {
    const biz = bizzes[0];
    schedule_c = {
      business_name: biz.business_name,
      gross_receipts: biz.gross_income ?? 0,
      cost_of_goods_sold: 0,
      home_office_sqft: biz.home_office_sqft,
      vehicle_business_miles: biz.vehicle_business_miles,
      vehicle_total_miles: biz.vehicle_total_miles,
      expenses: {
        advertising: biz.advertising,
        car_and_truck: biz.car_truck,
        depreciation: biz.depreciation,
        insurance: biz.insurance,
        legal_and_professional: biz.legal_professional,
        meals: biz.meals,
        office_expense: biz.office_expense,
        rent_or_lease: biz.rent_lease,
        repairs_and_maintenance: biz.repairs,
        supplies: biz.supplies,
        taxes_and_licenses: biz.taxes_licenses,
        travel: biz.travel,
        utilities: biz.utilities,
        other_expenses: biz.other_expenses,
      },
    };
  }

  // Itemized deductions — rename fields
  let itemized_deductions: BackendItemized | undefined;
  if (data.itemized_deductions) {
    const id = data.itemized_deductions;
    itemized_deductions = {
      medical_and_dental: id.medical_expenses,
      state_and_local_taxes_paid: id.state_local_taxes,
      real_estate_taxes: id.real_estate_taxes,
      mortgage_interest: id.mortgage_interest,
      charitable_cash: id.charitable_cash,
      charitable_non_cash: id.charitable_non_cash,
      casualty_and_theft: id.casualty_losses,
    };
  }

  // Dependents — backend requires a name field
  const dependents: BackendDependent[] = (data.dependents ?? []).map(
    (d, i) => ({
      name: `Dependent ${i + 1}`,
      relationship: d.relationship ?? "child",
      age: d.age ?? 0,
      is_qualifying_child: true,
    }),
  );

  // State residencies — state → state_code
  const state_residencies: BackendStateResidency[] = (
    data.state_residencies ?? []
  ).map((s) => ({
    state_code: s.state,
    property_tax_paid: s.il_property_taxes_paid,
  }));

  return {
    tax_year: data.tax_year ?? 2025,
    filing_status: data.filing_status ?? "single",
    aggressiveness: aggressiveness.toLowerCase(), // frontend=UPPER, backend=lower
    dependents,
    w2s,
    income_1099_nec,
    income_1099_int,
    income_1099_div,
    income_1099_b,
    schedule_c,
    itemized_deductions,
    state_residencies,
    prior_audit: data.prior_audit ?? false,
  };
}

// ---------------------------------------------------------------------------
// Map flat backend response → ScenarioResult (frontend shape)
// ---------------------------------------------------------------------------

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function toScenarioResult(raw: any): ScenarioResult {
  const fed = raw.federal ?? {};
  const auditRaw = raw.audit_risk ?? {};

  const num = (v: unknown): number => {
    if (typeof v === "number") return v;
    if (typeof v === "string") return parseFloat(v) || 0;
    return 0;
  };

  // Extract high-weight risk factors as labels
  const riskFactors: string[] = Array.isArray(auditRaw.factors)
    ? (auditRaw.factors as { name: string; weighted_score: string | number }[])
        .filter((f) => num(f.weighted_score) > 0)
        .map((f) => f.name)
    : [];

  // Map string risk_level → uppercase AggressivenessLevel
  const riskLevelStr = (auditRaw.risk_level ?? "low") as string;
  const levelMap: Record<string, AggressivenessLevel> = {
    low: "LOW",
    medium: "MEDIUM",
    high: "HIGH",
  };
  const auditLevel: AggressivenessLevel =
    levelMap[riskLevelStr.toLowerCase()] ?? "LOW";

  const auditRisk: AuditRisk = {
    score: num(auditRaw.overall_score),
    level: auditLevel,
    risk_factors: riskFactors,
    recommendations: Array.isArray(auditRaw.recommendations)
      ? (auditRaw.recommendations as string[])
      : [],
  };

  const amtOwed = num(fed.amount_owed);
  const refund = num(fed.refund);
  // balance: positive = owed, negative = refund
  const balance = amtOwed > 0 ? amtOwed : -refund;

  const federal: FederalResult = {
    agi: num(fed.agi),
    taxable_income: num(fed.taxable_income),
    standard_deduction: num(fed.standard_deduction),
    itemized_deduction: num(fed.itemized_deduction_total),
    use_itemized: fed.used_standard_deduction === false,
    federal_tax: num(fed.total_tax),
    self_employment_tax: num(fed.self_employment_tax),
    effective_rate: num(raw.summary?.effective_federal_rate),
    total_withheld: num(fed.total_tax_withheld),
    balance,
    credits: {
      child_tax_credit: num(fed.child_tax_credit),
      earned_income_credit: num(fed.earned_income_credit),
      education_credits: num(fed.education_credits),
    },
  };

  // Build state result map from raw.states[]
  const state: Record<
    string,
    {
      taxable_income: number;
      state_tax: number;
      effective_rate: number;
      withheld: number;
      balance: number;
    }
  > = {};
  if (Array.isArray(raw.states)) {
    (raw.states as Record<string, unknown>[]).forEach((s) => {
      const stateCode = ((s.state_code ?? s.state ?? "unknown") as string);
      state[stateCode] = {
        taxable_income: num(s.taxable_income),
        state_tax: num(s.state_tax ?? s.total_tax),
        effective_rate: num(s.effective_rate),
        withheld: num(s.state_tax_withheld ?? s.withheld),
        balance: num(s.amount_owed ?? s.balance),
      };
    });
  }

  // Map DeductionRecommendation[] → DeductionRec[]
  const deductionRecs = Array.isArray(raw.aggressiveness?.recommendations)
    ? (
        raw.aggressiveness.recommendations as {
          item: string;
          explanation: string;
          suggested_adjustment?: string | number;
          recommended_level?: string;
          documentation_needed?: string[];
        }[]
      ).map((r) => ({
        description: r.item + (r.explanation ? ` — ${r.explanation}` : ""),
        estimated_savings: Math.abs(num(r.suggested_adjustment)),
        confidence: r.recommended_level ?? "medium",
        form: r.documentation_needed?.[0],
      }))
    : [];

  return {
    federal,
    state,
    audit_risk: auditRisk,
    deduction_recommendations: deductionRecs,
  };
}

// ---------------------------------------------------------------------------
// Public: calculateTaxes — 3 parallel calls, one per aggressiveness level
// ---------------------------------------------------------------------------

export async function calculateTaxes(
  data: Partial<TaxReturn>,
): Promise<TaxCalculationResponse> {
  const levels: AggressivenessLevel[] = ["LOW", "MEDIUM", "HIGH"];

  const payloads = levels.map((level) => toBackendPayload(data, level));

  const responses = await Promise.all(
    payloads.map((payload) =>
      fetchJson<unknown>("/calculate", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    ),
  );

  const [lowRaw, medRaw, highRaw] = responses;

  // Compute gross income from all income sources for the response envelope
  const grossIncome =
    (data.w2s ?? []).reduce((sum, w) => sum + (w.wages ?? 0), 0) +
    (data.nec_1099s ?? []).reduce((sum, n) => sum + (n.amount ?? 0), 0) +
    (data.int_1099s ?? []).reduce((sum, n) => sum + (n.interest ?? 0), 0) +
    (data.div_1099s ?? []).reduce(
      (sum, d) => sum + (d.ordinary_dividends ?? 0),
      0,
    ) +
    (data.schedule_c_businesses ?? []).reduce(
      (sum, b) => sum + (b.gross_income ?? 0),
      0,
    );

  return {
    tax_year: data.tax_year ?? 2025,
    filing_status: data.filing_status ?? "single",
    gross_income: grossIncome,
    scenarios: {
      LOW: toScenarioResult(lowRaw),
      MEDIUM: toScenarioResult(medRaw),
      HIGH: toScenarioResult(highRaw),
    },
  };
}

// ---------------------------------------------------------------------------
// Public: exportPdf — sends result data to backend and downloads the PDF
// ---------------------------------------------------------------------------

export async function exportPdf(
  result: TaxCalculationResponse,
  activeLevel: AggressivenessLevel,
): Promise<void> {
  const body = {
    tax_year: result.tax_year,
    filing_status: result.filing_status,
    gross_income: result.gross_income,
    active_level: activeLevel,
    scenarios: result.scenarios,
  };

  const res = await fetch(`${API_BASE}/export/pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    throw new Error(`PDF export failed: ${res.status} ${res.statusText}`);
  }

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `TaxApp_${result.tax_year}_${result.filing_status}_${activeLevel}.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
