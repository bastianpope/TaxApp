"""Tests for orchestrator.py — full pipeline integration."""

from decimal import Decimal

from tax_engine.models import (
    Dependent,
    FilingStatus,
    Income1099NEC,
    ItemizedDeductions,
    ScheduleCBusiness,
    ScheduleCExpenses,
    StateResidency,
    TaxReturn,
    W2Income,
)
from tax_engine.orchestrator import compute_full_return


class TestOrchestrator:
    """Test the full return pipeline."""

    def test_simple_w2_single_il(self):
        """Simple W-2 single filer in Illinois."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(wages=Decimal("75000"), federal_tax_withheld=Decimal("10000"))],
            state_residencies=[StateResidency(state_code="IL")],
        )
        result = compute_full_return(tr)

        assert result.tax_year == 2025
        assert result.filing_status == FilingStatus.SINGLE
        assert result.federal.total_income == Decimal("75000")
        assert result.federal.agi == Decimal("75000")
        assert len(result.states) == 1
        assert result.states[0].state_code == "IL"
        assert result.states[0].state_tax > Decimal("0")
        assert result.audit_risk is not None
        assert result.aggressiveness is not None
        assert "total_income" in result.summary
        assert "effective_federal_rate" in result.summary

    def test_mfj_with_children_mn(self):
        """MFJ filer with children in Minnesota."""
        tr = TaxReturn(
            filing_status=FilingStatus.MFJ,
            w2s=[
                W2Income(wages=Decimal("80000"), federal_tax_withheld=Decimal("8000")),
                W2Income(wages=Decimal("60000"), federal_tax_withheld=Decimal("5000")),
            ],
            dependents=[
                Dependent(name="Child 1", relationship="child", age=8),
                Dependent(name="Child 2", relationship="child", age=12),
            ],
            state_residencies=[StateResidency(state_code="MN")],
        )
        result = compute_full_return(tr)

        assert result.federal.child_tax_credit == Decimal("4000")
        assert len(result.states) == 1
        assert result.states[0].state_code == "MN"
        assert result.summary["audit_risk_level"] in ("low", "medium", "high")

    def test_self_employed_dual_state(self):
        """Self-employed filer with both IL and MN residency."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            schedule_c=ScheduleCBusiness(
                gross_receipts=Decimal("120000"),
                expenses=ScheduleCExpenses(
                    supplies=Decimal("10000"),
                    travel=Decimal("5000"),
                ),
                home_office_sqft=Decimal("200"),
                vehicle_business_miles=Decimal("12000"),
            ),
            state_residencies=[
                StateResidency(state_code="IL"),
                StateResidency(state_code="MN"),
            ],
        )
        result = compute_full_return(tr)

        assert len(result.states) == 2
        assert result.federal.schedule_c_net_profit > Decimal("0")
        assert result.federal.self_employment_tax > Decimal("0")
        # Both states should compute taxes
        assert all(s.state_tax >= Decimal("0") for s in result.states)

    def test_unsupported_state_placeholder(self):
        """Unsupported state code gets a placeholder result."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(wages=Decimal("50000"))],
            state_residencies=[StateResidency(state_code="TX")],
        )
        result = compute_full_return(tr)

        assert len(result.states) == 1
        assert result.states[0].state_code == "TX"
        assert "error" in result.states[0].detail

    def test_summary_contains_all_keys(self):
        """Summary dict has all expected keys."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(wages=Decimal("50000"))],
        )
        result = compute_full_return(tr)

        expected_keys = {
            "total_income", "agi", "federal_taxable_income",
            "federal_tax", "federal_refund", "federal_owed",
            "total_state_tax", "total_tax_burden",
            "effective_federal_rate", "audit_risk_score",
            "audit_risk_level", "aggressiveness_level",
        }
        assert expected_keys.issubset(set(result.summary.keys()))

    def test_zero_income(self):
        """Zero income produces valid result with no errors."""
        tr = TaxReturn(filing_status=FilingStatus.SINGLE)
        result = compute_full_return(tr)

        assert result.federal.total_income == Decimal("0")
        assert result.federal.tax_after_credits == Decimal("0")
        assert result.summary["effective_federal_rate"] == Decimal("0")
        assert result.summary["audit_risk_level"] == "low"

    def test_complex_scenario(self):
        """Complex scenario: W-2 + 1099 + Schedule C + itemized + IL."""
        tr = TaxReturn(
            filing_status=FilingStatus.MFJ,
            w2s=[
                W2Income(wages=Decimal("100000"), federal_tax_withheld=Decimal("15000")),
            ],
            income_1099_nec=[
                Income1099NEC(amount=Decimal("30000")),
            ],
            schedule_c=ScheduleCBusiness(
                gross_receipts=Decimal("80000"),
                expenses=ScheduleCExpenses(
                    supplies=Decimal("10000"),
                    travel=Decimal("5000"),
                    meals=Decimal("6000"),
                ),
                home_office_sqft=Decimal("250"),
                vehicle_business_miles=Decimal("15000"),
            ),
            dependents=[
                Dependent(name="Child", relationship="child", age=10),
            ],
            itemized_deductions=ItemizedDeductions(
                mortgage_interest=Decimal("18000"),
                state_and_local_taxes_paid=Decimal("12000"),  # capped at $10k
                charitable_cash=Decimal("8000"),
            ),
            state_residencies=[
                StateResidency(state_code="IL", property_tax_paid=Decimal("5000")),
            ],
        )
        result = compute_full_return(tr)

        # Everything should produce positive numbers
        assert result.federal.total_income > Decimal("0")
        assert result.federal.agi > Decimal("0")
        assert result.federal.tax_after_credits > Decimal("0")
        assert result.states[0].state_tax > Decimal("0")
        # Aggressiveness should flag the meals and mileage
        assert result.aggressiveness is not None
        assert len(result.aggressiveness.recommendations) > 0
