"""Minnesota state tax calculator — progressive bracket system.

MN has 4 progressive brackets and its own standard deduction.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from tax_engine.brackets import get_brackets
from tax_engine.federal import compute_tax_from_brackets
from tax_engine.models import FederalResult, FilingStatus, StateResult, TaxReturn

_ZERO = Decimal("0")
_PENNY = Decimal("0.01")


def _round(amount: Decimal) -> Decimal:
    return amount.quantize(_PENNY, rounding=ROUND_HALF_UP)


def _max0(amount: Decimal) -> Decimal:
    return max(_ZERO, amount)


def calculate_mn(tax_return: TaxReturn, federal: FederalResult) -> StateResult:
    """Calculate Minnesota state income tax.

    MN uses federal AGI, applies MN standard deduction and dependent
    exemptions, then progressive brackets.
    """
    constants = get_brackets(tax_return.tax_year)
    result = StateResult(state_code="MN")

    # MN starts from federal AGI
    mn_base = federal.agi

    # MN standard deduction
    mn_std_deduction = constants.mn_standard_deductions.get(
        tax_return.filing_status, constants.mn_standard_deductions[FilingStatus.SINGLE]
    )

    # Dependent exemption: $5,200 per dependent
    dependent_exemptions = constants.mn_dependent_exemption * len(tax_return.dependents)

    total_deductions = mn_std_deduction + dependent_exemptions
    result.state_taxable_income = _max0(mn_base - total_deductions)

    # Progressive brackets
    mn_brackets = constants.mn_brackets.get(
        tax_return.filing_status, constants.mn_brackets[FilingStatus.SINGLE]
    )
    result.state_tax = compute_tax_from_brackets(result.state_taxable_income, mn_brackets)

    # State tax withheld
    state_withheld = sum((w.state_tax_withheld for w in tax_return.w2s), _ZERO)

    # MN credits (simplified — no specific credits modeled beyond withholding)
    result.state_credits = _ZERO
    result.state_tax_after_credits = _max0(result.state_tax - result.state_credits)

    balance = result.state_tax_after_credits - state_withheld
    if balance > _ZERO:
        result.state_amount_owed = _round(balance)
    else:
        result.state_refund = _round(abs(balance))

    # Detail breakdown
    result.detail = {
        "federal_agi": mn_base,
        "mn_standard_deduction": mn_std_deduction,
        "dependent_exemptions": dependent_exemptions,
        "state_withheld": state_withheld,
    }

    return result
