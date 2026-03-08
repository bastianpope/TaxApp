"""Illinois state tax calculator — flat rate system.

IL uses a simple flat rate (4.95% for 2025) with personal/dependent exemptions.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from tax_engine.brackets import get_brackets
from tax_engine.models import FederalResult, StateResult, TaxReturn

_ZERO = Decimal("0")
_PENNY = Decimal("0.01")


def _round(amount: Decimal) -> Decimal:
    return amount.quantize(_PENNY, rounding=ROUND_HALF_UP)


def _max0(amount: Decimal) -> Decimal:
    return max(_ZERO, amount)


def calculate_il(tax_return: TaxReturn, federal: FederalResult) -> StateResult:
    """Calculate Illinois state income tax.

    IL starts from federal AGI, applies exemptions, then flat rate.
    """
    constants = get_brackets(tax_return.tax_year)
    result = StateResult(state_code="IL")

    # IL uses federal AGI as starting point
    il_base = federal.agi

    # Personal exemption: $2,625 per filer
    filer_count = 2 if tax_return.filing_status.value in (
        "married_filing_jointly",
        "qualifying_surviving_spouse",
    ) else 1
    personal_exemptions = constants.il_personal_exemption * filer_count

    # Dependent exemptions: $2,625 per dependent
    dependent_exemptions = constants.il_dependent_exemption * len(tax_return.dependents)

    total_exemptions = personal_exemptions + dependent_exemptions
    result.state_taxable_income = _max0(il_base - total_exemptions)

    # Flat rate
    result.state_tax = _round(result.state_taxable_income * constants.il_flat_rate)

    # State tax withheld (from W-2s)
    state_withheld = sum((w.state_tax_withheld for w in tax_return.w2s), _ZERO)

    # IL credits: property tax credit (5% of property tax paid)
    property_tax_credit = _ZERO
    for sr in tax_return.state_residencies:
        if sr.state_code == "IL":
            property_tax_credit = _round(sr.property_tax_paid * Decimal("0.05"))
            break

    result.state_credits = property_tax_credit
    result.state_tax_after_credits = _max0(result.state_tax - result.state_credits)

    balance = result.state_tax_after_credits - state_withheld
    if balance > _ZERO:
        result.state_amount_owed = _round(balance)
    else:
        result.state_refund = _round(abs(balance))

    # Detail breakdown
    result.detail = {
        "federal_agi": il_base,
        "personal_exemptions": personal_exemptions,
        "dependent_exemptions": dependent_exemptions,
        "flat_rate": constants.il_flat_rate,
        "property_tax_credit": property_tax_credit,
        "state_withheld": state_withheld,
    }

    return result
