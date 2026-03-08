"""Tests for Illinois state tax calculator."""

from decimal import Decimal

from tax_engine.federal import calculate_federal
from tax_engine.models import (
    Dependent,
    FilingStatus,
    StateResidency,
    TaxReturn,
    W2Income,
)
from tax_engine.state_il import calculate_il


def d(val: str) -> Decimal:
    return Decimal(val)


class TestIllinoisTax:
    """Test IL flat-rate tax calculation."""

    def test_simple_single(self) -> None:
        """Single, $75k W-2 income — IL tax ~ ($75k - $2,625) × 4.95%."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(wages=d("75000"), state_tax_withheld=d("3000"))],
            state_residencies=[StateResidency(state_code="IL")],
        )
        fed = calculate_federal(tr)
        result = calculate_il(tr, fed)

        assert result.state_code == "IL"
        # AGI = 75,000; taxable = 75,000 - 2,625 = 72,375
        assert result.state_taxable_income == d("72375")
        # Tax = 72,375 × 0.0495 = 3,582.56
        expected_tax = d("3582.56")
        assert result.state_tax == expected_tax

    def test_mfj_two_exemptions(self) -> None:
        """MFJ gets two personal exemptions."""
        tr = TaxReturn(
            filing_status=FilingStatus.MFJ,
            w2s=[
                W2Income(wages=d("60000"), state_tax_withheld=d("2000")),
                W2Income(wages=d("40000"), state_tax_withheld=d("1500")),
            ],
            state_residencies=[StateResidency(state_code="IL")],
        )
        fed = calculate_federal(tr)
        result = calculate_il(tr, fed)

        # AGI = 100,000; taxable = 100,000 - 2×2,625 = 94,750
        assert result.state_taxable_income == d("94750")

    def test_dependents_reduce_taxable(self) -> None:
        """Two dependents reduce taxable income by $5,250."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(wages=d("80000"))],
            dependents=[
                Dependent(name="A", relationship="child", age=5),
                Dependent(name="B", relationship="child", age=8),
            ],
            state_residencies=[StateResidency(state_code="IL")],
        )
        fed = calculate_federal(tr)
        result = calculate_il(tr, fed)

        # taxable = 80,000 - 2,625 - 2×2,625 = 72,125
        assert result.state_taxable_income == d("72125")

    def test_property_tax_credit(self) -> None:
        """IL property tax credit = 5% of property taxes paid."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(wages=d("75000"))],
            state_residencies=[
                StateResidency(state_code="IL", property_tax_paid=d("6000")),
            ],
        )
        fed = calculate_federal(tr)
        result = calculate_il(tr, fed)

        assert result.state_credits == d("300.00")  # 6,000 × 5%

    def test_refund_with_withholding(self) -> None:
        """Over-withheld gets a refund."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(wages=d("40000"), state_tax_withheld=d("3000"))],
            state_residencies=[StateResidency(state_code="IL")],
        )
        fed = calculate_federal(tr)
        result = calculate_il(tr, fed)

        # Tax = (40,000 - 2,625) × 0.0495 = 1,850.06
        assert result.state_refund > d("0")

    def test_zero_income(self) -> None:
        """Zero income = zero tax."""
        tr = TaxReturn(
            state_residencies=[StateResidency(state_code="IL")],
        )
        fed = calculate_federal(tr)
        result = calculate_il(tr, fed)
        assert result.state_tax == d("0")
