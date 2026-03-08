"""Tests for federal tax calculator — core Form 1040 computation."""

from decimal import Decimal

from tax_engine.brackets import get_brackets
from tax_engine.federal import (
    calculate_federal,
    compute_child_tax_credit,
    compute_eitc,
    compute_schedule_c_profit,
    compute_se_tax,
    compute_tax_from_brackets,
)
from tax_engine.models import (
    Dependent,
    FilingStatus,
    Income1099B,
    Income1099DIV,
    Income1099INT,
    Income1099NEC,
    ItemizedDeductions,
    ScheduleCBusiness,
    ScheduleCExpenses,
    TaxReturn,
    W2Income,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def d(val: str) -> Decimal:
    """Shortcut for Decimal construction."""
    return Decimal(val)


def assert_close(actual: Decimal, expected: Decimal, tolerance: str = "1") -> None:
    """Assert two Decimals are within $tolerance of each other."""
    diff = abs(actual - expected)
    assert diff <= Decimal(tolerance), f"Expected ~{expected}, got {actual} (diff={diff})"


# ---------------------------------------------------------------------------
# Bracket computation
# ---------------------------------------------------------------------------


class TestBracketComputation:
    """Test progressive bracket tax calculation."""

    def test_zero_income(self) -> None:
        constants = get_brackets(2025)
        brackets = constants.federal_brackets[FilingStatus.SINGLE]
        assert compute_tax_from_brackets(d("0"), brackets) == d("0")

    def test_first_bracket_only(self) -> None:
        """$10,000 income, single — all in 10% bracket."""
        constants = get_brackets(2025)
        brackets = constants.federal_brackets[FilingStatus.SINGLE]
        tax = compute_tax_from_brackets(d("10000"), brackets)
        assert tax == d("1000.00")  # 10,000 × 10%

    def test_two_brackets(self) -> None:
        """$30,000 income, single — spans 10% and 12% brackets."""
        constants = get_brackets(2025)
        brackets = constants.federal_brackets[FilingStatus.SINGLE]
        tax = compute_tax_from_brackets(d("30000"), brackets)
        # 11,925 × 10% = 1,192.50
        # 18,075 × 12% = 2,169.00
        expected = d("1192.50") + d("2169.00")
        assert tax == expected

    def test_high_income(self) -> None:
        """$700,000 income, single — spans all brackets up to 37%."""
        constants = get_brackets(2025)
        brackets = constants.federal_brackets[FilingStatus.SINGLE]
        tax = compute_tax_from_brackets(d("700000"), brackets)
        # Should be a substantial amount
        assert tax > d("150000")
        assert tax < d("260000")

    def test_mfj_brackets(self) -> None:
        """$50,000 income, MFJ — wider brackets."""
        constants = get_brackets(2025)
        brackets = constants.federal_brackets[FilingStatus.MFJ]
        tax = compute_tax_from_brackets(d("50000"), brackets)
        # All in 10% + 12%
        # 23,850 × 10% = 2,385
        # 26,150 × 12% = 3,138
        expected = d("2385.00") + d("3138.00")
        assert tax == expected


# ---------------------------------------------------------------------------
# Self-employment tax
# ---------------------------------------------------------------------------


class TestSelfEmploymentTax:
    """Test SE tax computation."""

    def test_zero_se_income(self) -> None:
        constants = get_brackets(2025)
        se_tax, se_deduction = compute_se_tax(d("0"), constants)
        assert se_tax == d("0")
        assert se_deduction == d("0")

    def test_negative_se_income(self) -> None:
        constants = get_brackets(2025)
        se_tax, se_deduction = compute_se_tax(d("-5000"), constants)
        assert se_tax == d("0")
        assert se_deduction == d("0")

    def test_moderate_se_income(self) -> None:
        """$100,000 SE income — below SS wage base."""
        constants = get_brackets(2025)
        se_tax, se_deduction = compute_se_tax(d("100000"), constants)
        # SE base = 100,000 × 0.9235 = 92,350
        # SS: 92,350 × 0.124 = 11,451.40
        # Medicare: 92,350 × 0.029 = 2,678.15
        # Total: ~14,129.55
        assert se_tax > d("14000")
        assert se_tax < d("14300")
        # Deduction is half
        assert_close(se_deduction, se_tax / d("2"))


# ---------------------------------------------------------------------------
# Schedule C
# ---------------------------------------------------------------------------


class TestScheduleC:
    """Test Schedule C profit computation."""

    def test_no_schedule_c(self) -> None:
        tr = TaxReturn()
        constants = get_brackets(2025)
        assert compute_schedule_c_profit(tr, constants) == d("0")

    def test_basic_profit(self) -> None:
        tr = TaxReturn(
            schedule_c=ScheduleCBusiness(
                gross_receipts=d("100000"),
                expenses=ScheduleCExpenses(
                    supplies=d("5000"),
                    office_expense=d("3000"),
                ),
            )
        )
        constants = get_brackets(2025)
        profit = compute_schedule_c_profit(tr, constants)
        assert profit == d("92000")  # 100k - 5k - 3k

    def test_simplified_home_office(self) -> None:
        tr = TaxReturn(
            schedule_c=ScheduleCBusiness(
                gross_receipts=d("50000"),
                home_office_sqft=d("200"),  # 200 sqft × $5 = $1,000
            )
        )
        constants = get_brackets(2025)
        profit = compute_schedule_c_profit(tr, constants)
        assert profit == d("49000")  # 50k - 1k

    def test_home_office_capped_at_300_sqft(self) -> None:
        tr = TaxReturn(
            schedule_c=ScheduleCBusiness(
                gross_receipts=d("50000"),
                home_office_sqft=d("500"),  # Capped at 300 × $5 = $1,500
            )
        )
        constants = get_brackets(2025)
        profit = compute_schedule_c_profit(tr, constants)
        assert profit == d("48500")  # 50k - 1.5k

    def test_meals_50_pct_deductible(self) -> None:
        tr = TaxReturn(
            schedule_c=ScheduleCBusiness(
                gross_receipts=d("50000"),
                expenses=ScheduleCExpenses(meals=d("2000")),  # Only $1,000 deductible
            )
        )
        constants = get_brackets(2025)
        profit = compute_schedule_c_profit(tr, constants)
        assert profit == d("49000")  # 50k - 1k

    def test_vehicle_mileage(self) -> None:
        tr = TaxReturn(
            schedule_c=ScheduleCBusiness(
                gross_receipts=d("80000"),
                vehicle_business_miles=d("10000"),  # 10k × $0.70 = $7,000
            )
        )
        constants = get_brackets(2025)
        profit = compute_schedule_c_profit(tr, constants)
        assert profit == d("73000")  # 80k - 7k


# ---------------------------------------------------------------------------
# Credits
# ---------------------------------------------------------------------------


class TestChildTaxCredit:
    """Test CTC computation with phase-out."""

    def test_no_children(self) -> None:
        tr = TaxReturn(dependents=[])
        constants = get_brackets(2025)
        assert compute_child_tax_credit(tr, d("50000"), constants) == d("0")

    def test_one_qualifying_child(self) -> None:
        tr = TaxReturn(
            dependents=[Dependent(name="Child", relationship="son", age=5)],
        )
        constants = get_brackets(2025)
        credit = compute_child_tax_credit(tr, d("75000"), constants)
        assert credit == d("2000.00")

    def test_two_children(self) -> None:
        tr = TaxReturn(
            dependents=[
                Dependent(name="A", relationship="daughter", age=3),
                Dependent(name="B", relationship="son", age=10),
            ],
        )
        constants = get_brackets(2025)
        credit = compute_child_tax_credit(tr, d("75000"), constants)
        assert credit == d("4000.00")

    def test_phase_out_single(self) -> None:
        """AGI at $220,000 — $20k over threshold, reduces by $1,000."""
        tr = TaxReturn(
            dependents=[Dependent(name="A", relationship="son", age=5)],
        )
        constants = get_brackets(2025)
        credit = compute_child_tax_credit(tr, d("220000"), constants)
        assert credit == d("1000.00")  # $2,000 - $1,000 reduction

    def test_child_17_or_older_not_qualifying(self) -> None:
        """17-year-old doesn't qualify for CTC."""
        tr = TaxReturn(
            dependents=[Dependent(name="Teen", relationship="son", age=17)],
        )
        constants = get_brackets(2025)
        credit = compute_child_tax_credit(tr, d("75000"), constants)
        assert credit == d("0")


class TestEITC:
    """Test Earned Income Tax Credit."""

    def test_no_children_below_threshold(self) -> None:
        tr = TaxReturn()
        constants = get_brackets(2025)
        credit = compute_eitc(tr, d("15000"), constants)
        assert credit == d("632.00")

    def test_no_children_above_threshold(self) -> None:
        tr = TaxReturn()
        constants = get_brackets(2025)
        credit = compute_eitc(tr, d("20000"), constants)
        assert credit == d("0")

    def test_one_child(self) -> None:
        tr = TaxReturn(
            dependents=[Dependent(name="A", relationship="son", age=5)],
        )
        constants = get_brackets(2025)
        credit = compute_eitc(tr, d("35000"), constants)
        assert credit == d("4213.00")


# ---------------------------------------------------------------------------
# Full federal calculation
# ---------------------------------------------------------------------------


class TestFullFederal:
    """Integration tests for the full federal calculation pipeline."""

    def test_simple_w2_single(self) -> None:
        """Single filer, $75,000 W-2 income, no dependents."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(wages=d("75000"), federal_tax_withheld=d("9000"))],
        )
        result = calculate_federal(tr)

        assert result.total_wages == d("75000")
        assert result.agi == d("75000")
        assert result.standard_deduction == d("15000")
        assert result.used_standard_deduction is True
        assert result.taxable_income == d("60000")

        # Tax should be around $8,811
        # 11,925 × 10% = 1,192.50
        # 36,550 × 12% = 4,386.00
        # 11,525 × 22% = 2,535.50
        expected_tax = d("1192.50") + d("4386.00") + d("2535.50")
        assert result.tax_from_brackets == expected_tax

        # With $9,000 withheld, should get a refund
        assert result.refund > d("0")

    def test_self_employed_single(self) -> None:
        """Single filer with Schedule C income."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            schedule_c=ScheduleCBusiness(
                gross_receipts=d("100000"),
                expenses=ScheduleCExpenses(
                    supplies=d("5000"),
                    office_expense=d("3000"),
                ),
                home_office_sqft=d("200"),
            ),
        )
        result = calculate_federal(tr)

        assert result.schedule_c_net_profit == d("91000")
        assert result.self_employment_tax > d("0")
        assert result.self_employment_tax_deduction > d("0")
        assert result.agi < result.total_income  # SE deduction reduces AGI

    def test_mfj_with_children(self) -> None:
        """MFJ with two W-2s and two kids — CTC should apply."""
        tr = TaxReturn(
            filing_status=FilingStatus.MFJ,
            w2s=[
                W2Income(wages=d("60000"), federal_tax_withheld=d("5000")),
                W2Income(wages=d("50000"), federal_tax_withheld=d("4000")),
            ],
            dependents=[
                Dependent(name="A", relationship="daughter", age=5),
                Dependent(name="B", relationship="son", age=8),
            ],
        )
        result = calculate_federal(tr)

        assert result.total_wages == d("110000")
        assert result.child_tax_credit == d("4000")  # 2 kids × $2,000
        assert result.total_credits >= d("4000")

    def test_itemized_vs_standard(self) -> None:
        """Verify itemized is used when it exceeds standard deduction."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(wages=d("200000"), federal_tax_withheld=d("35000"))],
            itemized_deductions=ItemizedDeductions(
                mortgage_interest=d("12000"),
                state_and_local_taxes_paid=d("8000"),
                charitable_cash=d("5000"),
            ),
        )
        result = calculate_federal(tr)

        # Itemized = 12k + 8k + 5k = 25k > 15k standard
        assert not result.used_standard_deduction
        assert result.deduction_used == d("25000")

    def test_zero_income(self) -> None:
        """Zero income should produce zero tax."""
        tr = TaxReturn()
        result = calculate_federal(tr)
        assert result.total_tax == d("0")
        assert result.taxable_income == d("0")
        assert result.amount_owed == d("0")

    def test_capital_gains_included(self) -> None:
        """Capital gains add to total income."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(wages=d("50000"))],
            income_1099_b=[
                Income1099B(proceeds=d("20000"), cost_basis=d("10000"), is_long_term=True),
            ],
        )
        result = calculate_federal(tr)
        assert result.total_capital_gains == d("10000")
        assert result.total_income == d("60000")

    def test_interest_and_dividends(self) -> None:
        """Interest and dividend income included in total."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(wages=d("50000"))],
            income_1099_int=[Income1099INT(interest_income=d("500"))],
            income_1099_div=[Income1099DIV(ordinary_dividends=d("1000"))],
        )
        result = calculate_federal(tr)
        assert result.total_income == d("51500")

    def test_nec_income_adds_to_total_and_triggers_se_tax(self) -> None:
        """1099-NEC income triggers self-employment tax."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            income_1099_nec=[Income1099NEC(amount=d("50000"))],
        )
        result = calculate_federal(tr)
        assert result.total_income >= d("50000")
        assert result.self_employment_tax > d("0")
