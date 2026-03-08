"""Tests for audit_risk.py — 15-factor weighted scoring engine."""

from decimal import Decimal

from tax_engine.audit_risk import compute_audit_risk
from tax_engine.federal import calculate_federal
from tax_engine.models import (
    Dependent,
    FilingStatus,
    Income1099NEC,
    ItemizedDeductions,
    ScheduleCBusiness,
    ScheduleCExpenses,
    TaxReturn,
    W2Income,
)


class TestAuditRiskScoring:
    """Test audit risk factor computations."""

    def test_simple_w2_low_risk(self):
        """A simple W-2 filer should have low audit risk."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(wages=Decimal("50000"))],
        )
        fed = calculate_federal(tr)
        result = compute_audit_risk(tr, fed)

        assert result.risk_level == "low"
        assert result.overall_score < Decimal("30")
        assert len(result.factors) == 15

    def test_schedule_c_loss_raises_risk(self):
        """Schedule C with a loss draws high scrutiny."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            schedule_c=ScheduleCBusiness(
                gross_receipts=Decimal("20000"),
                expenses=ScheduleCExpenses(
                    supplies=Decimal("15000"),
                    travel=Decimal("10000"),
                ),
            ),
        )
        fed = calculate_federal(tr)
        result = compute_audit_risk(tr, fed)

        # Schedule C factor should have elevated raw_score
        sc_factor = next(f for f in result.factors if f.name == "Schedule C Activity")
        assert sc_factor.raw_score >= Decimal("50")

    def test_cash_intensive_business(self):
        """Cash-intensive businesses get flagged."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            schedule_c=ScheduleCBusiness(
                gross_receipts=Decimal("100000"),
                is_cash_intensive=True,
            ),
        )
        fed = calculate_federal(tr)
        result = compute_audit_risk(tr, fed)

        cash_factor = next(f for f in result.factors if f.name == "Cash-Intensive Business")
        assert cash_factor.raw_score == Decimal("60")

    def test_high_charitable_raises_risk(self):
        """Charitable contributions >50% of AGI are highly risky."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(wages=Decimal("50000"))],
            itemized_deductions=ItemizedDeductions(
                charitable_cash=Decimal("30000"),
            ),
        )
        fed = calculate_federal(tr)
        result = compute_audit_risk(tr, fed)

        charity_factor = next(f for f in result.factors if f.name == "Charitable Contributions")
        assert charity_factor.raw_score >= Decimal("40")

    def test_hoh_filing_status_adds_risk(self):
        """Head of Household filing adds some audit risk."""
        tr = TaxReturn(
            filing_status=FilingStatus.HOH,
            w2s=[W2Income(wages=Decimal("50000"))],
            dependents=[Dependent(name="Child", relationship="child", age=5)],
        )
        fed = calculate_federal(tr)
        result = compute_audit_risk(tr, fed)

        hoh_factor = next(f for f in result.factors if f.name == "Filing Status (HOH)")
        assert hoh_factor.raw_score == Decimal("25")

    def test_prior_audit_raises_risk(self):
        """Prior audit history significantly raises risk."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(wages=Decimal("50000"))],
            prior_audit=True,
        )
        fed = calculate_federal(tr)
        result = compute_audit_risk(tr, fed)

        prior_factor = next(f for f in result.factors if f.name == "Prior Audit History")
        assert prior_factor.raw_score == Decimal("50")

    def test_high_income_raises_risk(self):
        """Very high income increases audit probability."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(wages=Decimal("2000000"))],
        )
        fed = calculate_federal(tr)
        result = compute_audit_risk(tr, fed)

        income_factor = next(f for f in result.factors if f.name == "Income Level")
        assert income_factor.raw_score == Decimal("75")

    def test_round_number_expenses_suspicious(self):
        """Many round-number expenses are suspicious."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            schedule_c=ScheduleCBusiness(
                gross_receipts=Decimal("100000"),
                expenses=ScheduleCExpenses(
                    advertising=Decimal("1000"),
                    insurance=Decimal("2000"),
                    office_expense=Decimal("3000"),
                    supplies=Decimal("4000"),
                    utilities=Decimal("5000"),
                ),
            ),
        )
        fed = calculate_federal(tr)
        result = compute_audit_risk(tr, fed)

        round_factor = next(f for f in result.factors if f.name == "Round-Number Expenses")
        assert round_factor.raw_score >= Decimal("40")

    def test_recommendations_generated_for_high_factors(self):
        """Recommendations appear for factors with raw_score >= 40."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(wages=Decimal("50000"))],
            prior_audit=True,  # raw_score 50
        )
        fed = calculate_federal(tr)
        result = compute_audit_risk(tr, fed)

        assert len(result.recommendations) > 0
        assert any("Prior Audit History" in r for r in result.recommendations)

    def test_multiple_1099_nec_increases_risk(self):
        """Many 1099-NEC payers increases risk."""
        necs = [Income1099NEC(amount=Decimal("5000")) for _ in range(12)]
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            income_1099_nec=necs,
        )
        fed = calculate_federal(tr)
        result = compute_audit_risk(tr, fed)

        nec_factor = next(f for f in result.factors if f.name == "1099-NEC Count")
        assert nec_factor.raw_score == Decimal("30")
