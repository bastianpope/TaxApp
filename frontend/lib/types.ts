// ──────────────────────────────────────────────────────────────
// Tax-domain shared types (mirrors backend Pydantic models)
// ──────────────────────────────────────────────────────────────

export type FilingStatus = "single" | "married_filing_jointly" | "married_filing_separately" | "head_of_household" | "qualifying_surviving_spouse";
export type AggressivenessLevel = "LOW" | "MEDIUM" | "HIGH";

// ── Input models ──────────────────────────────────────────────

export interface W2Income {
  employer_name?: string;
  wages: number;
  federal_withheld: number;
  state_withheld?: number;
  state?: string;
  social_security_withheld?: number;
  medicare_withheld?: number;
  box12?: Record<string, number>;
}

export interface Income1099NEC {
  payer_name?: string;
  amount: number;
  federal_withheld?: number;
}

export interface Income1099INT {
  payer_name?: string;
  interest: number;
}

export interface Income1099DIV {
  payer_name?: string;
  ordinary_dividends: number;
  qualified_dividends?: number;
}

export interface Income1099B {
  description?: string;
  proceeds: number;
  cost_basis: number;
  long_term: boolean;
}

export interface ScheduleCBusiness {
  business_name?: string;
  business_type?: string;
  gross_income: number;
  advertising?: number;
  car_truck?: number;
  depreciation?: number;
  insurance?: number;
  legal_professional?: number;
  meals?: number;
  office_expense?: number;
  rent_lease?: number;
  repairs?: number;
  supplies?: number;
  taxes_licenses?: number;
  travel?: number;
  utilities?: number;
  other_expenses?: number;
  home_office_sqft?: number;
  home_total_sqft?: number;
  vehicle_business_miles?: number;
  vehicle_total_miles?: number;
}

export interface ItemizedDeductions {
  medical_expenses?: number;
  state_local_taxes?: number;
  real_estate_taxes?: number;
  mortgage_interest?: number;
  charitable_cash?: number;
  charitable_non_cash?: number;
  casualty_losses?: number;
}

export interface StateResidency {
  state: string;
  resident_full_year?: boolean;
  il_property_taxes_paid?: number;
  mn_school_district?: string;
}

export interface Dependent {
  relationship?: string;
  age: number;
  months_in_home?: number;
  full_time_student?: boolean;
}

export interface TaxReturn {
  tax_year?: number;
  filing_status: FilingStatus;
  aggressiveness?: AggressivenessLevel;
  dependents?: Dependent[];
  w2s?: W2Income[];
  nec_1099s?: Income1099NEC[];
  int_1099s?: Income1099INT[];
  div_1099s?: Income1099DIV[];
  capital_gains_1099b?: Income1099B[];
  schedule_c_businesses?: ScheduleCBusiness[];
  itemized_deductions?: ItemizedDeductions;
  state_residencies?: StateResidency[];
  prior_audit?: boolean;
  other_income?: number;
  other_income_description?: string;
  traditional_ira_contribution?: number;
  student_loan_interest?: number;
  tuition_fees?: number;
  health_savings_account?: number;
}

// ── Result models ─────────────────────────────────────────────

export interface FederalBreakdown {
  gross_income: string;
  agi: string;
  deduction_method: string;
  standard_deduction: string;
  itemized_total: string;
  deduction_used: string;
  taxable_income: string;
  income_tax: string;
  se_tax: string;
  se_deduction: string;
  child_tax_credit: string;
  eitc: string;
  total_credits: string;
  total_tax: string;
  total_withheld: string;
  refund_or_owed: string;
  effective_rate: string;
  marginal_rate: string;
}

export interface StateBreakdown {
  state: string;
  agi_adjustments: string;
  taxable_income: string;
  tax: string;
  credits: string;
  net_tax: string;
  withheld: string;
  refund_or_owed: string;
}

export interface AuditFactor {
  name: string;
  score: number;
  weight: number;
  description: string;
}

export interface AuditRiskResult {
  score: number;
  level: "LOW" | "MEDIUM" | "HIGH";
  top_factors: AuditFactor[];
  recommendations: string[];
}

export interface AggressivenessRecommendation {
  category: string;
  description: string;
  estimated_savings: string;
  risk_note?: string;
  documentation_needed: string[];
}

export interface AggressivenessBreakdown {
  level: AggressivenessLevel;
  recommendations: AggressivenessRecommendation[];
  total_additional_deductions: string;
}

export interface TaxResult {
  tax_year: number;
  filing_status: FilingStatus;
  federal: FederalBreakdown;
  states: StateBreakdown[];
  audit_risk: AuditRiskResult;
  aggressiveness: AggressivenessBreakdown;
  summary: {
    total_federal_tax: string;
    total_state_tax: string;
    total_tax: string;
    total_refund_or_owed: string;
    effective_federal_rate: string;
    total_income: string;
  };
}

// ── New rich result types (used by results page v2) ──────────

export type TaxReturnInput = TaxReturn;

export interface FederalResult {
  agi: number;
  taxable_income: number;
  standard_deduction: number;
  itemized_deduction: number;
  use_itemized: boolean;
  qbi_deduction?: number;
  federal_tax: number;
  self_employment_tax?: number;
  effective_rate: number;
  marginal_rate?: number;
  total_withheld: number;
  balance: number; // negative = refund, positive = owed
  credits?: Record<string, number>;
  qualified_dividends_tax?: number;
  capital_gains_tax?: number;
}

export interface StateResult {
  taxable_income: number;
  state_tax: number;
  effective_rate: number;
  withheld: number;
  balance: number;
  credits_applied?: number;
  notes?: string[];
}

export interface AuditRisk {
  score: number;
  level: AggressivenessLevel;
  risk_factors: string[];
  recommendations: string[];
}

export interface DeductionRec {
  description: string;
  estimated_savings: number;
  confidence: string;
  form?: string;
}

export interface ScenarioResult {
  federal: FederalResult;
  state: Record<string, StateResult>;
  audit_risk: AuditRisk;
  deduction_recommendations: DeductionRec[];
}

export type AllScenarios = Record<AggressivenessLevel, ScenarioResult>;

export interface TaxCalculationResponse {
  tax_year: number;
  filing_status: FilingStatus;
  gross_income: number;
  scenarios: AllScenarios;
}
