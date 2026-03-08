"""Tests for Minnesota state tax calculator."""

from decimal import Decimal

from tax_engine.federal import calculate_federal
from tax_engine.models import (
    Dependent,
    FilingStatus,
    TaxReturn,
    W2Income,
)
from tax_engine.state_mn import calculate_mn


def d(val: str) -> Decimal:
    return Decimal(val)


def assert_close(actual: Decimal, expected: Decimal, tolerance: str = "2") -> None:
    diff = abs(actual - expected)
    assert diff <= Decimal(tolerance), f"Expected ~{expected}, got {actual} (diff={diff})"


class TestMinnesotaTax:
    """Test MN progressive bracket tax calculation."""

    def test_simple_single(self) -> None:
        """Single, $75k W-2 — MN progressive tax."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(wages=d("75000"), state_tax_withheld=d("3500"))],
        )
        fed = calculate_federal(tr)
        result = calculate_mn(tr, fed)

        assert result.state_code == "MN"
        # AGI = 75,000; MN deduction = 14,575; taxable = 60,425
        assert result.state_taxable_income == d("60425")
        # Tax: 31,690 × 5.35% + 28,735 × 6.80%
        expected = d("1695.42") + d("1953.98")
        assert_close(result.state_tax, expected)

    def test_mfj_wider_brackets(self) -> None:
        """MFJ gets wider brackets and higher standard deduction."""
        tr = TaxReturn(
            filing_status=FilingStatus.MFJ,
            w2s=[
                W2Income(wages=d("80000"), state_tax_withheld=d("3000")),
                W2Income(wages=d("70000"), state_tax_withheld=d("2500")),
            ],
        )
        fed = calculate_federal(tr)
        result = calculate_mn(tr, fed)

        # AGI = 150,000; MN deduction = 29,150; taxable = 120,850
        assert result.state_taxable_income == d("120850")

    def test_dependents_reduce_taxable(self) -> None:
        """Dependents reduce MN taxable income by $5,200 each."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(wages=d("80000"))],
            dependents=[
                Dependent(name="A", relationship="child", age=5),
            ],
        )
        fed = calculate_federal(tr)
        result = calculate_mn(tr, fed)

        # taxable = 80,000 - 14,575 - 5,200 = 60,225
        assert result.state_taxable_income == d("60225")

    def test_high_income_top_bracket(self) -> None:
        """High income reaches 9.85% top bracket."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(wages=d("250000"))],
        )
        fed = calculate_federal(tr)
        result = calculate_mn(tr, fed)

        # Taxable = 250,000 - 14,575 = 235,425
        assert result.state_taxable_income == d("235425")
        # Reaches all 4 brackets
        assert result.state_tax > d("15000")

    def test_zero_income(self) -> None:
        tr = TaxReturn()
        fed = calculate_federal(tr)
        result = calculate_mn(tr, fed)
        assert result.state_tax == d("0")
        assert result.state_taxable_income == d("0")

    def test_refund_with_withholding(self) -> None:
        """Over-withheld gets a refund."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(wages=d("40000"), state_tax_withheld=d("3000"))],
        )
        fed = calculate_federal(tr)
        result = calculate_mn(tr, fed)

        # Taxable = 40,000 - 14,575 = 25,425
        # Tax: 25,425 × 5.35% = 1,360.24 (all in first bracket)
        assert result.state_refund > d("0")
