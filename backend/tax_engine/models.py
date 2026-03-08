"""Pydantic data models for all tax data structures.

Covers income sources, deductions, state residency, and computed results.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class FilingStatus(StrEnum):
    """IRS filing status codes."""

    SINGLE = "single"
    MFJ = "married_filing_jointly"
    MFS = "married_filing_separately"
    HOH = "head_of_household"
    QSS = "qualifying_surviving_spouse"


class AggressivenessLevel(StrEnum):
    """3-level aggressiveness dial for deduction recommendations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class HomeOfficeMethod(StrEnum):
    """IRS home office deduction methods."""

    SIMPLIFIED = "simplified"
    ACTUAL = "actual"


# ---------------------------------------------------------------------------
# Income Models
# ---------------------------------------------------------------------------


class W2Income(BaseModel):
    """Form W-2 wage and tax statement."""

    employer_name: str = ""
    wages: Decimal = Decimal("0")
    federal_tax_withheld: Decimal = Decimal("0")
    state_tax_withheld: Decimal = Decimal("0")
    social_security_wages: Decimal = Decimal("0")
    social_security_tax: Decimal = Decimal("0")
    medicare_wages: Decimal = Decimal("0")
    medicare_tax: Decimal = Decimal("0")


class Income1099NEC(BaseModel):
    """Form 1099-NEC — Non-employee compensation."""

    payer_name: str = ""
    amount: Decimal = Decimal("0")


class Income1099INT(BaseModel):
    """Form 1099-INT — Interest income."""

    payer_name: str = ""
    interest_income: Decimal = Decimal("0")
    tax_exempt_interest: Decimal = Decimal("0")


class Income1099DIV(BaseModel):
    """Form 1099-DIV — Dividend income."""

    payer_name: str = ""
    ordinary_dividends: Decimal = Decimal("0")
    qualified_dividends: Decimal = Decimal("0")
    capital_gain_distributions: Decimal = Decimal("0")


class Income1099B(BaseModel):
    """Form 1099-B — Proceeds from broker/barter exchange."""

    description: str = ""
    date_acquired: str = ""
    date_sold: str = ""
    proceeds: Decimal = Decimal("0")
    cost_basis: Decimal = Decimal("0")
    is_long_term: bool = False

    @property
    def gain_or_loss(self) -> Decimal:
        return self.proceeds - self.cost_basis


# ---------------------------------------------------------------------------
# Schedule C
# ---------------------------------------------------------------------------


class ScheduleCExpenses(BaseModel):
    """Schedule C business expense categories."""

    advertising: Decimal = Decimal("0")
    car_and_truck: Decimal = Decimal("0")
    commissions_and_fees: Decimal = Decimal("0")
    contract_labor: Decimal = Decimal("0")
    depreciation: Decimal = Decimal("0")
    insurance: Decimal = Decimal("0")
    interest_mortgage: Decimal = Decimal("0")
    interest_other: Decimal = Decimal("0")
    legal_and_professional: Decimal = Decimal("0")
    office_expense: Decimal = Decimal("0")
    rent_or_lease: Decimal = Decimal("0")
    repairs_and_maintenance: Decimal = Decimal("0")
    supplies: Decimal = Decimal("0")
    taxes_and_licenses: Decimal = Decimal("0")
    travel: Decimal = Decimal("0")
    meals: Decimal = Decimal("0")  # 50% deductible
    utilities: Decimal = Decimal("0")
    wages: Decimal = Decimal("0")
    other_expenses: Decimal = Decimal("0")


class ScheduleCBusiness(BaseModel):
    """Schedule C — Profit or Loss from Business."""

    business_name: str = ""
    gross_receipts: Decimal = Decimal("0")
    cost_of_goods_sold: Decimal = Decimal("0")
    expenses: ScheduleCExpenses = Field(default_factory=ScheduleCExpenses)
    home_office_method: HomeOfficeMethod = HomeOfficeMethod.SIMPLIFIED
    home_office_sqft: Decimal = Decimal("0")  # for simplified method (max 300)
    home_office_actual_pct: Decimal = Decimal("0")  # for actual method
    home_office_actual_expenses: Decimal = Decimal("0")
    vehicle_business_miles: Decimal = Decimal("0")
    vehicle_total_miles: Decimal = Decimal("0")
    is_cash_intensive: bool = False  # e.g., restaurants, salons, vending


# ---------------------------------------------------------------------------
# Deductions
# ---------------------------------------------------------------------------


class ItemizedDeductions(BaseModel):
    """Schedule A — Itemized deductions."""

    medical_and_dental: Decimal = Decimal("0")
    state_and_local_taxes_paid: Decimal = Decimal("0")  # SALT cap $10,000
    real_estate_taxes: Decimal = Decimal("0")
    mortgage_interest: Decimal = Decimal("0")
    charitable_cash: Decimal = Decimal("0")
    charitable_non_cash: Decimal = Decimal("0")
    casualty_and_theft: Decimal = Decimal("0")
    other_deductions: Decimal = Decimal("0")


# ---------------------------------------------------------------------------
# State Residency
# ---------------------------------------------------------------------------


class StateResidency(BaseModel):
    """State-specific data (IL / MN)."""

    state_code: str  # "IL" or "MN"
    property_tax_paid: Decimal = Decimal("0")
    state_income_tax_paid: Decimal = Decimal("0")


# ---------------------------------------------------------------------------
# Tax Return (Top-Level Input)
# ---------------------------------------------------------------------------


class Dependent(BaseModel):
    """A qualifying dependent."""

    name: str
    relationship: str
    age: int
    is_qualifying_child: bool = True


class TaxReturn(BaseModel):
    """Top-level container for a tax return — all input data flows through this."""

    tax_year: int = 2025
    filing_status: FilingStatus = FilingStatus.SINGLE
    dependents: list[Dependent] = Field(default_factory=list)

    # Income sources
    w2s: list[W2Income] = Field(default_factory=list)
    income_1099_nec: list[Income1099NEC] = Field(default_factory=list)
    income_1099_int: list[Income1099INT] = Field(default_factory=list)
    income_1099_div: list[Income1099DIV] = Field(default_factory=list)
    income_1099_b: list[Income1099B] = Field(default_factory=list)

    # Business income
    schedule_c: ScheduleCBusiness | None = None

    # Deductions
    itemized_deductions: ItemizedDeductions | None = None

    # State
    state_residencies: list[StateResidency] = Field(default_factory=list)

    # History
    prior_audit: bool = False  # Was taxpayer audited in prior years?


# ---------------------------------------------------------------------------
# Computed Results
# ---------------------------------------------------------------------------


class FederalResult(BaseModel):
    """Computed federal tax result — line-by-line Form 1040 breakdown."""

    # Income
    total_wages: Decimal = Decimal("0")
    total_interest: Decimal = Decimal("0")
    total_dividends: Decimal = Decimal("0")
    qualified_dividends: Decimal = Decimal("0")
    total_capital_gains: Decimal = Decimal("0")
    schedule_c_net_profit: Decimal = Decimal("0")
    total_income: Decimal = Decimal("0")

    # Adjustments
    self_employment_tax_deduction: Decimal = Decimal("0")
    total_adjustments: Decimal = Decimal("0")
    agi: Decimal = Decimal("0")

    # Deductions
    standard_deduction: Decimal = Decimal("0")
    itemized_deduction_total: Decimal = Decimal("0")
    deduction_used: Decimal = Decimal("0")
    used_standard_deduction: bool = True
    taxable_income: Decimal = Decimal("0")

    # Tax computation
    tax_from_brackets: Decimal = Decimal("0")
    self_employment_tax: Decimal = Decimal("0")
    total_tax: Decimal = Decimal("0")

    # Credits
    child_tax_credit: Decimal = Decimal("0")
    earned_income_credit: Decimal = Decimal("0")
    education_credits: Decimal = Decimal("0")
    total_credits: Decimal = Decimal("0")

    # Payments & refund
    total_tax_withheld: Decimal = Decimal("0")
    tax_after_credits: Decimal = Decimal("0")
    amount_owed: Decimal = Decimal("0")
    refund: Decimal = Decimal("0")


class StateResult(BaseModel):
    """Computed state tax result."""

    state_code: str
    state_taxable_income: Decimal = Decimal("0")
    state_tax: Decimal = Decimal("0")
    state_credits: Decimal = Decimal("0")
    state_tax_after_credits: Decimal = Decimal("0")
    state_amount_owed: Decimal = Decimal("0")
    state_refund: Decimal = Decimal("0")

    # Breakdown details
    detail: dict[str, object] = Field(default_factory=dict)


class TaxResult(BaseModel):
    """Complete tax result — federal + state(s) combined."""

    federal: FederalResult
    states: list[StateResult] = Field(default_factory=list)
    total_tax: Decimal = Decimal("0")
    total_refund: Decimal = Decimal("0")
    total_owed: Decimal = Decimal("0")


# ---------------------------------------------------------------------------
# Audit Risk
# ---------------------------------------------------------------------------


class AuditRiskFactor(BaseModel):
    """A single audit risk factor with its contribution."""

    name: str
    weight: Decimal
    raw_score: Decimal  # 0–1 deviation from norm
    weighted_score: Decimal  # weight × raw_score
    description: str


class AuditRiskResult(BaseModel):
    """15-factor weighted composite audit risk score."""

    score: Decimal = Decimal("0")  # 0–100,
    risk_level: Literal["low", "moderate", "elevated", "high"] = "low"
    top_factors: list[AuditRiskFactor] = Field(default_factory=list)
    all_factors: list[AuditRiskFactor] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Aggressiveness
# ---------------------------------------------------------------------------


class DeductionRecommendation(BaseModel):
    """A single deduction recommendation from the aggressiveness engine."""

    category: str  # e.g., "home_office", "vehicle", "charitable"
    level: AggressivenessLevel
    eligible: bool = True
    estimated_amount: Decimal = Decimal("0")
    rationale: str = ""
    documentation_needed: list[str] = Field(default_factory=list)
    risk_note: str = ""  # only populated at HIGH level


class ComparisonScenario(BaseModel):
    """A single aggressiveness scenario result."""

    level: AggressivenessLevel
    tax_result: TaxResult
    risk_result: AuditRiskResult
    recommendations: list[DeductionRecommendation] = Field(default_factory=list)


class ComparisonResult(BaseModel):
    """Side-by-side comparison of all 3 aggressiveness levels."""

    scenarios: dict[str, ComparisonScenario] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Full Result (Orchestrator output)
# ---------------------------------------------------------------------------


class FullResult(BaseModel):
    """Complete computation result from the orchestrator.

    Uses Any for audit_risk/aggressiveness because those are dataclass-based
    (not Pydantic) — we store them directly but serialize via summary dict.
    """

    tax_year: int = 2025
    filing_status: FilingStatus = FilingStatus.SINGLE
    federal: FederalResult = Field(default_factory=FederalResult)
    states: list[StateResult] = Field(default_factory=list)
    audit_risk: object = None  # AuditRiskResult (dataclass)
    aggressiveness: object = None  # AggressivenessResult (dataclass)
    summary: dict = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)


# ---------------------------------------------------------------------------
# Error Models
# ---------------------------------------------------------------------------


class TaxValidationError(BaseModel):
    """Structured error model for 422 responses (beyond Pydantic defaults)."""

    field: str  # e.g., "w2s[0].wages"
    code: str  # e.g., "REQUIRED", "CONTRADICTION", "RANGE_EXCEEDED"
    message: str  # Human-readable description
    severity: Literal["error", "warning"] = "error"
