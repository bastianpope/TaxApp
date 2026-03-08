"""Federal tax calculator — Form 1040 line-by-line computation.

Handles income aggregation, adjustments, deductions (standard vs. itemized),
bracket-based tax, SE tax, credits (CTC, EITC), and refund/owed.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from tax_engine.brackets import TaxYearConstants, get_brackets
from tax_engine.models import (
    FederalResult,
    FilingStatus,
    TaxReturn,
)

_ZERO = Decimal("0")
_TWO = Decimal("2")
_PENNY = Decimal("0.01")


def _round(amount: Decimal) -> Decimal:
    """Round to nearest cent (standard tax rounding)."""
    return amount.quantize(_PENNY, rounding=ROUND_HALF_UP)


def _max0(amount: Decimal) -> Decimal:
    """Return max(0, amount) — floors at zero."""
    return max(_ZERO, amount)


# ---------------------------------------------------------------------------
# Bracket computation
# ---------------------------------------------------------------------------


def compute_tax_from_brackets(
    taxable_income: Decimal,
    brackets: list[tuple[Decimal, Decimal]],
) -> Decimal:
    """Apply progressive tax brackets and return total tax.

    Each bracket is (upper_bound, rate). Income below the previous
    bracket's upper_bound is taxed at the bracket's rate.
    """
    tax = _ZERO
    prev_bound = _ZERO
    for upper_bound, rate in brackets:
        if taxable_income <= prev_bound:
            break
        taxable_in_bracket = min(taxable_income, upper_bound) - prev_bound
        tax += _round(taxable_in_bracket * rate)
        prev_bound = upper_bound
    return tax


# ---------------------------------------------------------------------------
# Self-employment tax
# ---------------------------------------------------------------------------


def compute_se_tax(
    net_se_income: Decimal,
    constants: TaxYearConstants,
) -> tuple[Decimal, Decimal]:
    """Compute self-employment tax and the above-the-line deduction.

    Returns (se_tax, se_deduction).
    """
    if net_se_income <= _ZERO:
        return _ZERO, _ZERO

    # 92.35% of net SE income is subject to SE tax
    se_base = _round(net_se_income * Decimal("0.9235"))

    # Social Security portion (12.4%) — capped at wage base
    ss_portion = min(se_base, constants.se_social_security_wage_base)
    ss_tax = _round(ss_portion * Decimal("0.124"))

    # Medicare portion (2.9%) — no cap
    medicare_tax = _round(se_base * constants.se_medicare_rate)

    se_tax = ss_tax + medicare_tax

    # Deductible half of SE tax (above-the-line adjustment)
    se_deduction = _round(se_tax / _TWO)

    return se_tax, se_deduction


# ---------------------------------------------------------------------------
# Schedule C Net Profit
# ---------------------------------------------------------------------------


def compute_schedule_c_profit(tax_return: TaxReturn, constants: TaxYearConstants) -> Decimal:
    """Compute Schedule C net profit from gross receipts minus expenses.

    Handles home office (simplified / actual) and vehicle deduction.
    """
    sc = tax_return.schedule_c
    if sc is None:
        return _ZERO

    gross_profit = sc.gross_receipts - sc.cost_of_goods_sold
    exp = sc.expenses

    # Sum all regular expenses
    total_expenses = (
        exp.advertising
        + exp.car_and_truck
        + exp.commissions_and_fees
        + exp.contract_labor
        + exp.depreciation
        + exp.insurance
        + exp.interest_mortgage
        + exp.interest_other
        + exp.legal_and_professional
        + exp.office_expense
        + exp.rent_or_lease
        + exp.repairs_and_maintenance
        + exp.supplies
        + exp.taxes_and_licenses
        + exp.travel
        + _round(exp.meals * constants.meals_deduction_pct)  # 50% deductible
        + exp.utilities
        + exp.wages
        + exp.other_expenses
    )

    # Home office deduction
    home_office = _ZERO
    if sc.home_office_method.value == "simplified":
        sqft = min(sc.home_office_sqft, constants.simplified_home_office_max_sqft)
        home_office = _round(sqft * constants.simplified_home_office_rate)
    elif sc.home_office_method.value == "actual":
        home_office = _round(sc.home_office_actual_expenses * sc.home_office_actual_pct)

    # Vehicle (standard mileage)
    vehicle_deduction = _round(sc.vehicle_business_miles * constants.standard_mileage_rate)

    net_profit = gross_profit - total_expenses - home_office - vehicle_deduction
    return net_profit  # Can be negative (net loss)


# ---------------------------------------------------------------------------
# Credits
# ---------------------------------------------------------------------------


def compute_child_tax_credit(
    tax_return: TaxReturn,
    agi: Decimal,
    constants: TaxYearConstants,
) -> Decimal:
    """Compute Child Tax Credit (CTC) with phase-out."""
    qualifying_children = sum(
        1 for d in tax_return.dependents if d.is_qualifying_child and d.age < 17
    )
    if qualifying_children == 0:
        return _ZERO

    base_credit = constants.child_tax_credit_amount * qualifying_children
    threshold = constants.child_tax_credit_phase_out[tax_return.filing_status]

    if agi > threshold:
        # Phase out by $50 per $1,000 (or fraction) above threshold
        excess = agi - threshold
        # Round up to nearest $1,000
        thousand_blocks = (excess / Decimal("1000")).to_integral_value(rounding="ROUND_CEILING")
        reduction = thousand_blocks * Decimal("50")
        base_credit = _max0(base_credit - reduction)

    return _round(base_credit)


def compute_eitc(
    tax_return: TaxReturn,
    agi: Decimal,
    constants: TaxYearConstants,
) -> Decimal:
    """Compute Earned Income Tax Credit (simplified lookup)."""
    # Count qualifying children (up to 3)
    num_children = min(
        sum(1 for d in tax_return.dependents if d.is_qualifying_child),
        3,
    )

    if num_children not in constants.eitc_table:
        return _ZERO

    max_single, max_mfj, max_credit = constants.eitc_table[num_children]

    if tax_return.filing_status in (FilingStatus.MFJ, FilingStatus.QSS):
        max_income = max_mfj
    else:
        max_income = max_single

    if agi > max_income:
        return _ZERO

    # Simplified: full credit if under threshold (real EITC has phase-in/out)
    return _round(max_credit)


# ---------------------------------------------------------------------------
# Itemized deductions
# ---------------------------------------------------------------------------


def compute_itemized_deductions(
    tax_return: TaxReturn, agi: Decimal, constants: TaxYearConstants,
) -> Decimal:
    """Compute total itemized deductions with limits applied."""
    itemized = tax_return.itemized_deductions
    if itemized is None:
        return _ZERO

    # Medical: only amount exceeding 7.5% of AGI
    medical = _max0(itemized.medical_and_dental - _round(agi * constants.medical_expense_agi_pct))

    # SALT: capped at $10,000
    salt = min(
        itemized.state_and_local_taxes_paid + itemized.real_estate_taxes,
        constants.salt_cap,
    )

    # Mortgage interest (no special cap applied here — simplified)
    mortgage = itemized.mortgage_interest

    # Charitable: cash limited to 60% AGI, non-cash to 30% AGI
    charitable_cash = min(
        itemized.charitable_cash,
        _round(agi * constants.charitable_cash_agi_limit_pct),
    )
    charitable_noncash = min(
        itemized.charitable_non_cash,
        _round(agi * constants.charitable_noncash_agi_limit_pct),
    )

    total = medical + salt + mortgage + charitable_cash + charitable_noncash
    total += itemized.casualty_and_theft + itemized.other_deductions

    return _round(total)


# ---------------------------------------------------------------------------
# Main computation
# ---------------------------------------------------------------------------


def calculate_federal(tax_return: TaxReturn) -> FederalResult:
    """Calculate complete federal tax liability from a TaxReturn.

    Returns a FederalResult with line-by-line 1040 breakdown.
    """
    constants = get_brackets(tax_return.tax_year)
    result = FederalResult()

    # ---------------------------------------------------------------
    # Step 1: Aggregate income
    # ---------------------------------------------------------------
    result.total_wages = sum((w.wages for w in tax_return.w2s), _ZERO)
    result.total_interest = sum(
        (i.interest_income for i in tax_return.income_1099_int), _ZERO
    )
    result.total_dividends = sum(
        (d.ordinary_dividends for d in tax_return.income_1099_div), _ZERO
    )
    result.qualified_dividends = sum(
        (d.qualified_dividends for d in tax_return.income_1099_div), _ZERO
    )
    result.total_capital_gains = sum(
        (b.gain_or_loss for b in tax_return.income_1099_b), _ZERO
    )

    # NEC income (Schedule C gross receipts handled separately)
    nec_income = sum((n.amount for n in tax_return.income_1099_nec), _ZERO)

    # Schedule C
    result.schedule_c_net_profit = compute_schedule_c_profit(tax_return, constants)

    result.total_income = (
        result.total_wages
        + result.total_interest
        + result.total_dividends
        + _max0(result.total_capital_gains)
        + result.schedule_c_net_profit
        + nec_income
    )

    # ---------------------------------------------------------------
    # Step 2: Adjustments to income (above-the-line)
    # ---------------------------------------------------------------
    se_income = result.schedule_c_net_profit + nec_income
    result.self_employment_tax, result.self_employment_tax_deduction = compute_se_tax(
        se_income, constants
    )

    result.total_adjustments = result.self_employment_tax_deduction
    result.agi = result.total_income - result.total_adjustments

    # ---------------------------------------------------------------
    # Step 3: Deductions (standard vs. itemized)
    # ---------------------------------------------------------------
    result.standard_deduction = constants.standard_deductions[tax_return.filing_status]
    result.itemized_deduction_total = compute_itemized_deductions(
        tax_return, result.agi, constants
    )

    if result.itemized_deduction_total > result.standard_deduction:
        result.deduction_used = result.itemized_deduction_total
        result.used_standard_deduction = False
    else:
        result.deduction_used = result.standard_deduction
        result.used_standard_deduction = True

    result.taxable_income = _max0(result.agi - result.deduction_used)

    # ---------------------------------------------------------------
    # Step 4: Tax computation (brackets)
    # ---------------------------------------------------------------
    brackets = constants.federal_brackets[tax_return.filing_status]
    result.tax_from_brackets = compute_tax_from_brackets(result.taxable_income, brackets)

    # Total tax = bracket tax + SE tax
    result.total_tax = result.tax_from_brackets + result.self_employment_tax

    # ---------------------------------------------------------------
    # Step 5: Credits
    # ---------------------------------------------------------------
    result.child_tax_credit = compute_child_tax_credit(tax_return, result.agi, constants)
    result.earned_income_credit = compute_eitc(tax_return, result.agi, constants)
    result.total_credits = (
        result.child_tax_credit + result.earned_income_credit + result.education_credits
    )

    # ---------------------------------------------------------------
    # Step 6: Payments / withholding
    # ---------------------------------------------------------------
    result.total_tax_withheld = sum(
        (w.federal_tax_withheld for w in tax_return.w2s), _ZERO
    )

    # ---------------------------------------------------------------
    # Step 7: Final — refund or owed
    # ---------------------------------------------------------------
    result.tax_after_credits = _max0(result.total_tax - result.total_credits)
    balance = result.tax_after_credits - result.total_tax_withheld

    if balance > _ZERO:
        result.amount_owed = _round(balance)
        result.refund = _ZERO
    else:
        result.amount_owed = _ZERO
        result.refund = _round(abs(balance))

    return result
