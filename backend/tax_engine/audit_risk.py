"""Audit risk scoring engine — 15-factor weighted composite (0–100).

Each factor contributes a sub-score; the weighted sum produces an overall
audit risk score that the aggressiveness engine uses for recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from tax_engine.models import FederalResult, FilingStatus, TaxReturn

_ZERO = Decimal("0")
_PENNY = Decimal("0.01")
_HUNDRED = Decimal("100")


def _round(v: Decimal) -> Decimal:
    return v.quantize(_PENNY, rounding=ROUND_HALF_UP)


def _clamp(v: Decimal, lo: Decimal = _ZERO, hi: Decimal = _HUNDRED) -> Decimal:
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class RiskFactor:
    """A single risk factor's contribution."""
    name: str
    raw_score: Decimal  # 0–100
    weight: Decimal  # 0.0–1.0
    weighted_score: Decimal  # raw × weight
    explanation: str = ""


@dataclass
class AuditRiskResult:
    """Overall audit risk assessment."""
    overall_score: Decimal = _ZERO  # 0–100
    risk_level: str = "low"  # low / medium / high
    factors: list[RiskFactor] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Individual risk factor computations
# ---------------------------------------------------------------------------


def _income_level_risk(agi: Decimal) -> Decimal:
    """Higher AGI ⇒ higher audit probability (IRS stats)."""
    if agi < Decimal("25000"):
        return Decimal("10")
    if agi < Decimal("50000"):
        return Decimal("15")
    if agi < Decimal("100000"):
        return Decimal("20")
    if agi < Decimal("200000"):
        return Decimal("25")
    if agi < Decimal("500000"):
        return Decimal("35")
    if agi < Decimal("1000000"):
        return Decimal("55")
    return Decimal("75")


def _schedule_c_risk(tr: TaxReturn, fed: FederalResult) -> Decimal:
    """Schedule C filers have elevated audit risk, especially with losses."""
    if fed.schedule_c_net_profit == _ZERO and tr.schedule_c is None:
        return _ZERO
    if fed.schedule_c_net_profit < _ZERO:
        return Decimal("70")  # Losses draw attention
    # High gross receipts with low profit margins
    if tr.schedule_c is not None and tr.schedule_c.gross_receipts > _ZERO:
        margin = fed.schedule_c_net_profit / tr.schedule_c.gross_receipts
        if margin < Decimal("0.10"):
            return Decimal("50")
        if margin < Decimal("0.20"):
            return Decimal("35")
    return Decimal("25")


def _cash_intensive_risk(tr: TaxReturn) -> Decimal:
    """Cash businesses face higher scrutiny."""
    if tr.schedule_c is not None and tr.schedule_c.is_cash_intensive:
        return Decimal("60")
    return _ZERO


def _home_office_risk(tr: TaxReturn) -> Decimal:
    """Home office deduction raises flags, especially large ones."""
    sc = tr.schedule_c
    if sc is None or sc.home_office_sqft == _ZERO:
        return _ZERO
    if sc.home_office_sqft > Decimal("250"):
        return Decimal("40")
    return Decimal("20")


def _vehicle_deduction_risk(tr: TaxReturn) -> Decimal:
    """High business mileage without commuting records is risky."""
    sc = tr.schedule_c
    if sc is None:
        return _ZERO
    if sc.vehicle_business_miles > Decimal("20000"):
        return Decimal("45")
    if sc.vehicle_business_miles > Decimal("10000"):
        return Decimal("25")
    return Decimal("10") if sc.vehicle_business_miles > _ZERO else _ZERO


def _charitable_risk(tr: TaxReturn, agi: Decimal) -> Decimal:
    """Charitable deductions that are unusually high relative to income."""
    it = tr.itemized_deductions
    if it is None:
        return _ZERO
    total_charity = it.charitable_cash + it.charitable_non_cash
    if agi <= _ZERO or total_charity <= _ZERO:
        return _ZERO
    ratio = total_charity / agi
    if ratio > Decimal("0.50"):
        return Decimal("70")
    if ratio > Decimal("0.25"):
        return Decimal("40")
    if ratio > Decimal("0.10"):
        return Decimal("15")
    return Decimal("5")


def _meals_entertainment_risk(tr: TaxReturn) -> Decimal:
    """Meals deductions draw scrutiny when large."""
    sc = tr.schedule_c
    if sc is None:
        return _ZERO
    if sc.expenses.meals > Decimal("5000"):
        return Decimal("35")
    if sc.expenses.meals > Decimal("2000"):
        return Decimal("20")
    return Decimal("5") if sc.expenses.meals > _ZERO else _ZERO


def _nec_count_risk(tr: TaxReturn) -> Decimal:
    """Multiple 1099-NEC payers increase reporting complexity risk."""
    count = len(tr.income_1099_nec)
    if count >= 10:
        return Decimal("30")
    if count >= 5:
        return Decimal("20")
    return Decimal("5") if count > 0 else _ZERO


def _capital_gains_risk(fed: FederalResult) -> Decimal:
    """Net capital losses or large gains increase scrutiny."""
    if fed.total_capital_gains < _ZERO:
        return Decimal("30")
    if fed.total_capital_gains > Decimal("100000"):
        return Decimal("25")
    return Decimal("5") if fed.total_capital_gains > _ZERO else _ZERO


def _filing_status_risk(tr: TaxReturn) -> Decimal:
    """HOH filing status is heavily audited for misuse."""
    if tr.filing_status == FilingStatus.HOH:
        return Decimal("25")
    return Decimal("5")


def _eitc_risk(fed: FederalResult) -> Decimal:
    """EITC claims have historically high audit rates."""
    if fed.earned_income_credit > _ZERO:
        return Decimal("35")
    return _ZERO


def _round_numbers_risk(tr: TaxReturn) -> Decimal:
    """Too many round-number expenses look suspicious."""
    sc = tr.schedule_c
    if sc is None:
        return _ZERO
    exp = sc.expenses
    amounts = [
        exp.advertising, exp.car_and_truck, exp.contract_labor,
        exp.insurance, exp.office_expense, exp.rent_or_lease,
        exp.supplies, exp.travel, exp.meals, exp.utilities,
    ]
    non_zero = [a for a in amounts if a > _ZERO]
    if not non_zero:
        return _ZERO
    round_count = sum(1 for a in non_zero if a % Decimal("100") == _ZERO)
    ratio = Decimal(round_count) / Decimal(len(non_zero))
    if ratio > Decimal("0.70"):
        return Decimal("40")
    if ratio > Decimal("0.40"):
        return Decimal("20")
    return _ZERO


def _deduction_ratio_risk(fed: FederalResult) -> Decimal:
    """Total deductions unusually high relative to income."""
    if fed.total_income <= _ZERO:
        return _ZERO
    ratio = fed.deduction_used / fed.total_income
    if ratio > Decimal("0.80"):
        return Decimal("50")
    if ratio > Decimal("0.50"):
        return Decimal("25")
    return _ZERO


def _missing_income_risk(tr: TaxReturn) -> Decimal:
    """W-2/1099 mismatch risk (simplified — if no income docs at all)."""
    has_income_docs = bool(
        tr.w2s or tr.income_1099_nec or tr.income_1099_int
        or tr.income_1099_div or tr.income_1099_b
    )
    if not has_income_docs and tr.schedule_c is not None:
        return Decimal("20")
    return _ZERO


def _prior_audit_risk(tr: TaxReturn) -> Decimal:
    """Prior audit history flag."""
    if tr.prior_audit:
        return Decimal("50")
    return _ZERO


# ---------------------------------------------------------------------------
# Factor registry with weights
# ---------------------------------------------------------------------------

_FACTORS: list[tuple[str, Decimal, Any]] = [
    ("Income Level", Decimal("0.10"), lambda tr, fed: _income_level_risk(fed.agi)),
    ("Schedule C Activity", Decimal("0.12"), lambda tr, fed: _schedule_c_risk(tr, fed)),
    ("Cash-Intensive Business", Decimal("0.06"), lambda tr, fed: _cash_intensive_risk(tr)),
    ("Home Office Deduction", Decimal("0.06"), lambda tr, fed: _home_office_risk(tr)),
    ("Vehicle Deduction", Decimal("0.06"), lambda tr, fed: _vehicle_deduction_risk(tr)),
    ("Charitable Contributions", Decimal("0.08"), lambda tr, fed: _charitable_risk(tr, fed.agi)),
    ("Meals & Entertainment", Decimal("0.05"), lambda tr, fed: _meals_entertainment_risk(tr)),
    ("1099-NEC Count", Decimal("0.04"), lambda tr, fed: _nec_count_risk(tr)),
    ("Capital Gains/Losses", Decimal("0.05"), lambda tr, fed: _capital_gains_risk(fed)),
    ("Filing Status (HOH)", Decimal("0.06"), lambda tr, fed: _filing_status_risk(tr)),
    ("EITC Claimed", Decimal("0.07"), lambda tr, fed: _eitc_risk(fed)),
    ("Round-Number Expenses", Decimal("0.05"), lambda tr, fed: _round_numbers_risk(tr)),
    ("High Deduction Ratio", Decimal("0.06"), lambda tr, fed: _deduction_ratio_risk(fed)),
    ("Missing Income Sources", Decimal("0.04"), lambda tr, fed: _missing_income_risk(tr)),
    ("Prior Audit History", Decimal("0.10"), lambda tr, fed: _prior_audit_risk(tr)),
]


# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------


def compute_audit_risk(tr: TaxReturn, fed: FederalResult) -> AuditRiskResult:
    """Compute the 15-factor audit risk score.

    Returns AuditRiskResult with overall 0–100 score, risk level, and
    per-factor breakdown.
    """
    result = AuditRiskResult()
    total_weighted = _ZERO

    for name, weight, fn in _FACTORS:
        raw = _clamp(fn(tr, fed))
        weighted = _round(raw * weight)
        total_weighted += weighted

        result.factors.append(
            RiskFactor(
                name=name,
                raw_score=raw,
                weight=weight,
                weighted_score=weighted,
            )
        )

    result.overall_score = _clamp(_round(total_weighted))

    # Risk level thresholds
    if result.overall_score >= Decimal("60"):
        result.risk_level = "high"
    elif result.overall_score >= Decimal("30"):
        result.risk_level = "medium"
    else:
        result.risk_level = "low"

    # Generate recommendations for high-scoring factors
    for f in result.factors:
        if f.raw_score >= Decimal("40"):
            result.recommendations.append(
                f"⚠️  {f.name}: Elevated risk (score {f.raw_score}). "
                f"Ensure thorough documentation and records."
            )

    return result
