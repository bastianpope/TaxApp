"""Aggressiveness engine — 3-level recommendation taxonomy.

Analyzes each deduction/credit and provides Low / Medium / High
aggressiveness recommendations based on documentation strength,
IRS enforcement history, and audit risk.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tax_engine.audit_risk import AuditRiskResult
    from tax_engine.models import FederalResult, TaxReturn

_ZERO = Decimal("0")
_PENNY = Decimal("0.01")


def _round(v: Decimal) -> Decimal:
    return v.quantize(_PENNY, rounding=ROUND_HALF_UP)


class AggressivenessLevel(StrEnum):
    """Three-tier aggressiveness classification."""
    LOW = "low"          # Conservative — minimal audit risk
    MEDIUM = "medium"    # Standard — some documentation needed
    HIGH = "high"        # Aggressive — strong records required


@dataclass
class DeductionRecommendation:
    """A single deduction/credit recommendation."""
    item: str
    current_amount: Decimal = _ZERO
    recommended_level: AggressivenessLevel = AggressivenessLevel.MEDIUM
    explanation: str = ""
    suggested_adjustment: Decimal = _ZERO  # positive = reduce, negative = increase
    documentation_needed: list[str] = field(default_factory=list)


@dataclass
class AggressivenessResult:
    """Complete aggressiveness assessment."""
    overall_level: AggressivenessLevel = AggressivenessLevel.MEDIUM
    recommendations: list[DeductionRecommendation] = field(default_factory=list)
    potential_savings: Decimal = _ZERO
    potential_risk_reduction: Decimal = _ZERO


# ---------------------------------------------------------------------------
# Recommendation generators
# ---------------------------------------------------------------------------


def _assess_home_office(tr: TaxReturn) -> DeductionRecommendation | None:
    """Assess home office deduction aggressiveness."""
    sc = tr.schedule_c
    if sc is None or sc.home_office_sqft == _ZERO:
        return None

    rec = DeductionRecommendation(
        item="Home Office Deduction",
        current_amount=sc.home_office_sqft * Decimal("5"),  # simplified
    )

    if sc.home_office_sqft > Decimal("250"):
        rec.recommended_level = AggressivenessLevel.HIGH
        rec.explanation = (
            "Large home office (>250 sqft) draws IRS scrutiny. "
            "Ensure the space is used regularly and exclusively for business."
        )
        rec.documentation_needed = [
            "Floor plan showing dedicated office space",
            "Photos of the office area",
            "Records showing exclusive business use",
        ]
    elif sc.home_office_sqft > Decimal("150"):
        rec.recommended_level = AggressivenessLevel.MEDIUM
        rec.explanation = "Standard home office size. Keep documentation."
        rec.documentation_needed = ["Floor plan or measurement records"]
    else:
        rec.recommended_level = AggressivenessLevel.LOW
        rec.explanation = "Small home office — low audit risk."

    return rec


def _assess_vehicle(tr: TaxReturn) -> DeductionRecommendation | None:
    """Assess vehicle business mileage deduction."""
    sc = tr.schedule_c
    if sc is None or sc.vehicle_business_miles <= _ZERO:
        return None

    rec = DeductionRecommendation(
        item="Vehicle / Mileage Deduction",
        current_amount=_round(sc.vehicle_business_miles * Decimal("0.70")),
    )

    if sc.vehicle_business_miles > Decimal("20000"):
        rec.recommended_level = AggressivenessLevel.HIGH
        rec.explanation = (
            "Very high business mileage (>20,000 mi). "
            "IRS expects detailed contemporaneous mileage logs."
        )
        rec.documentation_needed = [
            "Contemporaneous mileage log (date, destination, purpose, miles)",
            "Vehicle maintenance records showing odometer",
            "Calendar/appointment records corroborating travel",
        ]
    elif sc.vehicle_business_miles > Decimal("10000"):
        rec.recommended_level = AggressivenessLevel.MEDIUM
        rec.explanation = "Moderate business mileage. Keep a mileage log."
        rec.documentation_needed = ["Mileage log app or written records"]
    else:
        rec.recommended_level = AggressivenessLevel.LOW
        rec.explanation = "Reasonable business mileage — low risk."
        rec.documentation_needed = ["Basic mileage records"]

    return rec


def _assess_meals(tr: TaxReturn) -> DeductionRecommendation | None:
    """Assess meals deduction."""
    sc = tr.schedule_c
    if sc is None or sc.expenses.meals <= _ZERO:
        return None

    rec = DeductionRecommendation(
        item="Meals Deduction",
        current_amount=_round(sc.expenses.meals * Decimal("0.50")),
    )

    if sc.expenses.meals > Decimal("5000"):
        rec.recommended_level = AggressivenessLevel.HIGH
        rec.explanation = (
            "Meals over $5,000 draw attention. Each meal must have "
            "documented business purpose, attendees, and topics discussed."
        )
        rec.documentation_needed = [
            "Receipts for each meal",
            "Business purpose notes (who, what, why)",
            "Calendar entries for business meals",
        ]
    elif sc.expenses.meals > Decimal("2000"):
        rec.recommended_level = AggressivenessLevel.MEDIUM
        rec.explanation = "Moderate meals expense. Keep receipts."
        rec.documentation_needed = ["Receipts with business notations"]
    else:
        rec.recommended_level = AggressivenessLevel.LOW

    return rec


def _assess_charitable(tr: TaxReturn, agi: Decimal) -> DeductionRecommendation | None:
    """Assess charitable contribution levels."""
    it = tr.itemized_deductions
    if it is None:
        return None

    total_charity = it.charitable_cash + it.charitable_non_cash
    if total_charity <= _ZERO:
        return None

    rec = DeductionRecommendation(
        item="Charitable Contributions",
        current_amount=total_charity,
    )

    if agi > _ZERO:
        ratio = total_charity / agi
        if ratio > Decimal("0.25"):
            rec.recommended_level = AggressivenessLevel.HIGH
            rec.explanation = (
                f"Charitable giving is {_round(ratio * Decimal('100'))}% of AGI — "
                f"well above average. Strong documentation required."
            )
            rec.documentation_needed = [
                "Written acknowledgment from charities (>$250 per donation)",
                "Qualified appraisals for non-cash donations >$5,000",
                "Form 8283 for non-cash contributions >$500",
                "Bank/credit card statements for cash donations",
            ]
        elif ratio > Decimal("0.10"):
            rec.recommended_level = AggressivenessLevel.MEDIUM
            rec.explanation = "Above-average charitable giving. Keep donation receipts."
            rec.documentation_needed = ["Donation receipts and acknowledgments"]
        else:
            rec.recommended_level = AggressivenessLevel.LOW

    if it.charitable_non_cash > _ZERO:
        rec.documentation_needed.append(
            "Fair market value documentation for non-cash donations"
        )

    return rec


def _assess_schedule_c_expenses(
    tr: TaxReturn, fed: FederalResult,
) -> DeductionRecommendation | None:
    """Assess overall Schedule C expense level."""
    sc = tr.schedule_c
    if sc is None or sc.gross_receipts <= _ZERO:
        return None

    total_expenses = sc.gross_receipts - fed.schedule_c_net_profit
    if total_expenses <= _ZERO:
        return None

    expense_ratio = total_expenses / sc.gross_receipts

    rec = DeductionRecommendation(
        item="Schedule C Expense Ratio",
        current_amount=total_expenses,
    )

    if expense_ratio > Decimal("0.90"):
        rec.recommended_level = AggressivenessLevel.HIGH
        rec.explanation = (
            f"Expenses are {_round(expense_ratio * Decimal('100'))}% of gross receipts. "
            f"Very thin margin — IRS may question if business is for profit."
        )
        rec.documentation_needed = [
            "Business plan showing profit intent",
            "Records of all expense categories",
            "Receipts for all deductions claimed",
        ]
    elif expense_ratio > Decimal("0.70"):
        rec.recommended_level = AggressivenessLevel.MEDIUM
        rec.explanation = "Moderate expense ratio. Maintain organized records."
        rec.documentation_needed = ["Organized expense receipts by category"]
    else:
        rec.recommended_level = AggressivenessLevel.LOW

    return rec


# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------


def analyze_aggressiveness(
    tr: TaxReturn,
    fed: FederalResult,
    risk: AuditRiskResult,
) -> AggressivenessResult:
    """Analyze tax return aggressiveness and generate recommendations.

    Considers audit risk score to calibrate recommendations.
    """
    result = AggressivenessResult()
    assessors = [
        _assess_home_office(tr),
        _assess_vehicle(tr),
        _assess_meals(tr),
        _assess_charitable(tr, fed.agi),
        _assess_schedule_c_expenses(tr, fed),
    ]

    for rec in assessors:
        if rec is not None:
            # If overall audit risk is already high, escalate medium→high
            if (
                risk.overall_score >= Decimal("50")
                and rec.recommended_level == AggressivenessLevel.MEDIUM
            ):
                rec.recommended_level = AggressivenessLevel.HIGH
                rec.explanation += (
                    " [Escalated due to elevated overall audit risk score.]"
                )
            result.recommendations.append(rec)

    # Determine overall level
    if not result.recommendations:
        result.overall_level = AggressivenessLevel.LOW
    else:
        levels = [r.recommended_level for r in result.recommendations]
        if AggressivenessLevel.HIGH in levels:
            result.overall_level = AggressivenessLevel.HIGH
        elif AggressivenessLevel.MEDIUM in levels:
            result.overall_level = AggressivenessLevel.MEDIUM
        else:
            result.overall_level = AggressivenessLevel.LOW

    return result
