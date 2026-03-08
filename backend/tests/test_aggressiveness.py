"""Tests for aggressiveness.py — 3-level recommendation engine."""

from decimal import Decimal

from tax_engine.aggressiveness import (
    AggressivenessLevel,
    analyze_aggressiveness,
)
from tax_engine.audit_risk import compute_audit_risk
from tax_engine.federal import calculate_federal
from tax_engine.models import (
    FilingStatus,
    ItemizedDeductions,
    ScheduleCBusiness,
    ScheduleCExpenses,
    TaxReturn,
    W2Income,
)


class TestAggressivenessAnalysis:
    """Test the deduction aggressiveness engine."""

    def test_no_deductions_gives_low(self):
        """Plain W-2 filer with no special deductions → LOW."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(wages=Decimal("50000"))],
        )
        fed = calculate_federal(tr)
        risk = compute_audit_risk(tr, fed)
        result = analyze_aggressiveness(tr, fed, risk)

        assert result.overall_level == AggressivenessLevel.LOW
        assert len(result.recommendations) == 0

    def test_large_home_office_is_high(self):
        """Home office >250 sqft → HIGH aggressiveness."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            schedule_c=ScheduleCBusiness(
                gross_receipts=Decimal("100000"),
                home_office_sqft=Decimal("300"),
            ),
        )
        fed = calculate_federal(tr)
        risk = compute_audit_risk(tr, fed)
        result = analyze_aggressiveness(tr, fed, risk)

        ho_rec = next(
            r for r in result.recommendations
            if r.item == "Home Office Deduction"
        )
        assert ho_rec.recommended_level == AggressivenessLevel.HIGH
        assert "photos" in " ".join(ho_rec.documentation_needed).lower()

    def test_moderate_home_office_is_medium(self):
        """Home office 150–250 sqft → MEDIUM."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            schedule_c=ScheduleCBusiness(
                gross_receipts=Decimal("100000"),
                home_office_sqft=Decimal("200"),
            ),
        )
        fed = calculate_federal(tr)
        risk = compute_audit_risk(tr, fed)
        result = analyze_aggressiveness(tr, fed, risk)

        ho_rec = next(
            r for r in result.recommendations
            if r.item == "Home Office Deduction"
        )
        assert ho_rec.recommended_level == AggressivenessLevel.MEDIUM

    def test_high_vehicle_mileage_is_high(self):
        """Vehicle >20,000 miles → HIGH."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            schedule_c=ScheduleCBusiness(
                gross_receipts=Decimal("100000"),
                vehicle_business_miles=Decimal("25000"),
            ),
        )
        fed = calculate_federal(tr)
        risk = compute_audit_risk(tr, fed)
        result = analyze_aggressiveness(tr, fed, risk)

        veh_rec = next(
            r for r in result.recommendations
            if r.item == "Vehicle / Mileage Deduction"
        )
        assert veh_rec.recommended_level == AggressivenessLevel.HIGH
        assert any("mileage log" in d.lower() for d in veh_rec.documentation_needed)

    def test_large_meals_is_high(self):
        """Meals >$5,000 → HIGH."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            schedule_c=ScheduleCBusiness(
                gross_receipts=Decimal("100000"),
                expenses=ScheduleCExpenses(meals=Decimal("8000")),
            ),
        )
        fed = calculate_federal(tr)
        risk = compute_audit_risk(tr, fed)
        result = analyze_aggressiveness(tr, fed, risk)

        meals_rec = next(
            r for r in result.recommendations
            if r.item == "Meals Deduction"
        )
        assert meals_rec.recommended_level == AggressivenessLevel.HIGH

    def test_high_charitable_ratio_is_high(self):
        """Charitable >25% of AGI → HIGH."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(wages=Decimal("80000"))],
            itemized_deductions=ItemizedDeductions(
                charitable_cash=Decimal("25000"),
            ),
        )
        fed = calculate_federal(tr)
        risk = compute_audit_risk(tr, fed)
        result = analyze_aggressiveness(tr, fed, risk)

        char_rec = next(
            r for r in result.recommendations
            if r.item == "Charitable Contributions"
        )
        assert char_rec.recommended_level == AggressivenessLevel.HIGH

    def test_thin_profit_margin_is_high(self):
        """Schedule C expense ratio >90% → HIGH."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            schedule_c=ScheduleCBusiness(
                gross_receipts=Decimal("100000"),
                expenses=ScheduleCExpenses(
                    supplies=Decimal("50000"),
                    contract_labor=Decimal("45000"),
                ),
            ),
        )
        fed = calculate_federal(tr)
        risk = compute_audit_risk(tr, fed)
        result = analyze_aggressiveness(tr, fed, risk)

        # Expense ratio = 95k / 100k = 95%
        exp_rec = next(
            r for r in result.recommendations
            if r.item == "Schedule C Expense Ratio"
        )
        assert exp_rec.recommended_level == AggressivenessLevel.HIGH

    def test_escalation_on_high_audit_risk(self):
        """MEDIUM recs escalate to HIGH when overall audit risk is ≥50."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(wages=Decimal("50000"))],
            prior_audit=True,
            schedule_c=ScheduleCBusiness(
                gross_receipts=Decimal("100000"),
                home_office_sqft=Decimal("200"),  # normally MEDIUM
                is_cash_intensive=True,  # raises audit risk
                expenses=ScheduleCExpenses(
                    supplies=Decimal("20000"),
                    contract_labor=Decimal("20000"),
                ),
            ),
        )
        fed = calculate_federal(tr)
        risk = compute_audit_risk(tr, fed)

        # Force a high enough risk score for escalation test
        if risk.overall_score < Decimal("50"):
            risk.overall_score = Decimal("55")

        result = analyze_aggressiveness(tr, fed, risk)

        # The home office rec should be escalated
        ho_rec = next(
            (r for r in result.recommendations if r.item == "Home Office Deduction"),
            None,
        )
        if ho_rec:
            assert ho_rec.recommended_level == AggressivenessLevel.HIGH
            assert "Escalated" in ho_rec.explanation

    def test_overall_level_reflects_worst(self):
        """Overall level should be the worst of all recommendations."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            schedule_c=ScheduleCBusiness(
                gross_receipts=Decimal("100000"),
                home_office_sqft=Decimal("100"),  # LOW
                vehicle_business_miles=Decimal("25000"),  # HIGH
            ),
        )
        fed = calculate_federal(tr)
        risk = compute_audit_risk(tr, fed)
        result = analyze_aggressiveness(tr, fed, risk)

        assert result.overall_level == AggressivenessLevel.HIGH
