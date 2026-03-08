"""Integration tests — end-to-end fixture-driven scenarios.

Load JSON fixtures from tests/fixtures/ty2025/, build TaxReturn,
run compute_full_return, and validate expectations.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from tax_engine.models import (
    Dependent,
    FilingStatus,
    Income1099NEC,
    ScheduleCBusiness,
    ScheduleCExpenses,
    StateResidency,
    TaxReturn,
    W2Income,
)
from tax_engine.orchestrator import compute_full_return

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "ty2025"


def _load_fixtures():
    """Yield (filename, fixture_data) for each JSON fixture."""
    for path in sorted(FIXTURES_DIR.glob("*.json")):
        with path.open() as f:
            yield path.stem, json.load(f)


def _build_tax_return(data: dict) -> TaxReturn:
    """Build a TaxReturn from fixture input dict."""
    inp = data["input"]
    d = Decimal

    w2s = [
        W2Income(
            employer_name=w["employer_name"],
            wages=d(w["wages"]),
            federal_withholding=d(w.get("federal_withholding", "0")),
            state_withholding=d(w.get("state_withholding", "0")),
        )
        for w in inp.get("w2s", [])
    ]

    nec_1099s = [
        Income1099NEC(payer_name=n["payer_name"], amount=d(n["amount"]))
        for n in inp.get("nec_1099s", [])
    ]

    dependents = [
        Dependent(
            name=dep["name"],
            age=dep["age"],
            relationship=dep["relationship"],
        )
        for dep in inp.get("dependents", [])
    ]

    state_residencies = [
        StateResidency(
            state_code=s["state_code"],
            state_withholding=d(s.get("state_withholding", "0")),
            property_tax_paid=d(s.get("property_tax_paid", "0")),
        )
        for s in inp.get("state_residencies", [])
    ]

    schedule_c = None
    if "schedule_c" in inp:
        sc = inp["schedule_c"]
        expenses = None
        if "expenses" in sc:
            exp = sc["expenses"]
            expenses = ScheduleCExpenses(
                advertising=d(exp.get("advertising", "0")),
                supplies=d(exp.get("supplies", "0")),
                travel=d(exp.get("travel", "0")),
                meals=d(exp.get("meals", "0")),
                other=d(exp.get("other", "0")),
            )
        schedule_c = ScheduleCBusiness(
            gross_receipts=d(sc["gross_receipts"]),
            expenses=expenses,
            home_office_sqft=d(sc.get("home_office_sqft", "0")),
            vehicle_business_miles=d(
                sc.get("vehicle_business_miles", "0")
            ),
        )

    return TaxReturn(
        tax_year=inp.get("tax_year", 2025),
        filing_status=FilingStatus[inp["filing_status"]],
        w2s=w2s,
        nec_1099s=nec_1099s,
        dependents=dependents,
        state_residencies=state_residencies,
        schedule_c=schedule_c,
    )


# -----------------------------------------------------------------------
# Parametrized fixture tests
# -----------------------------------------------------------------------


class TestIntegrationFixtures:
    """Run each JSON fixture through the full pipeline."""

    @pytest.fixture(
        params=list(_load_fixtures()),
        ids=[name for name, _ in _load_fixtures()],
    )
    def fixture_case(self, request):
        return request.param

    def test_fixture_runs_without_error(self, fixture_case):
        """Every fixture must produce a result without exceptions."""
        _name, data = fixture_case
        tr = _build_tax_return(data)
        result = compute_full_return(tr)
        assert result is not None
        assert result.federal is not None

    def test_fixture_expected_federal(self, fixture_case):
        """Validate federal expectations from fixture."""
        name, data = fixture_case
        expected = data.get("expected", {}).get("federal", {})
        if not expected:
            pytest.skip(f"No federal expectations for {name}")

        tr = _build_tax_return(data)
        result = compute_full_return(tr)
        fed = result.federal
        d = Decimal

        if "total_income_gte" in expected:
            assert fed.total_income >= d(expected["total_income_gte"])
        if "agi_gte" in expected:
            assert fed.agi >= d(expected["agi_gte"])
        if "child_tax_credit" in expected:
            assert fed.child_tax_credit == d(
                expected["child_tax_credit"]
            )
        if "se_tax_gt" in expected:
            assert fed.self_employment_tax > d(expected["se_tax_gt"])

    def test_fixture_expected_states(self, fixture_case):
        """Validate state expectations from fixture."""
        name, data = fixture_case
        expected = data.get("expected", {})
        if "states" not in expected and "states_count" not in expected:
            pytest.skip(f"No state expectations for {name}")

        tr = _build_tax_return(data)
        result = compute_full_return(tr)

        if "states_count" in expected:
            assert len(result.states) == expected["states_count"]

        for exp_state in expected.get("states", []):
            matches = [
                s
                for s in result.states
                if s.state_code == exp_state["state_code"]
            ]
            assert len(matches) == 1, (
                f"Expected state {exp_state['state_code']}"
            )
            state = matches[0]
            if "state_tax_gt" in exp_state:
                assert state.state_tax > Decimal(
                    exp_state["state_tax_gt"]
                )

    def test_fixture_expected_audit_risk(self, fixture_case):
        """Validate audit risk expectations from fixture."""
        name, data = fixture_case
        expected = data.get("expected", {}).get("audit_risk", {})
        if not expected:
            pytest.skip(f"No audit risk expectations for {name}")

        tr = _build_tax_return(data)
        result = compute_full_return(tr)
        risk = result.audit_risk

        if "risk_level" in expected:
            assert risk.risk_level == expected["risk_level"]
        if "risk_level_in" in expected:
            assert risk.risk_level in expected["risk_level_in"]
        if "overall_score_gte" in expected:
            assert risk.overall_score >= Decimal(
                expected["overall_score_gte"]
            )

    def test_fixture_expected_aggressiveness(self, fixture_case):
        """Validate aggressiveness expectations from fixture."""
        name, data = fixture_case
        expected = data.get("expected", {}).get(
            "aggressiveness", {}
        )
        if not expected:
            pytest.skip(f"No aggressiveness expectations for {name}")

        tr = _build_tax_return(data)
        result = compute_full_return(tr)
        agg = result.aggressiveness

        if expected.get("has_recommendations"):
            assert len(agg.recommendations) > 0

    def test_fixture_summary_keys(self, fixture_case):
        """Validate that expected summary keys are present."""
        name, data = fixture_case
        expected_keys = (
            data.get("expected", {}).get("summary_keys", [])
        )
        if not expected_keys:
            pytest.skip(f"No summary key expectations for {name}")

        tr = _build_tax_return(data)
        result = compute_full_return(tr)

        for key in expected_keys:
            assert key in result.summary, (
                f"Missing summary key: {key}"
            )


# -----------------------------------------------------------------------
# Cross-reference tests (independent of fixtures)
# -----------------------------------------------------------------------


class TestCrossReference:
    """Verify internal consistency across modules."""

    def _simple_return(self) -> TaxReturn:
        return TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(employer_name="X", wages=Decimal("80000"))],
            state_residencies=[StateResidency(state_code="IL")],
        )

    def test_summary_total_tax_equals_components(self):
        """total_tax_burden = federal_tax + total_state_tax."""
        result = compute_full_return(self._simple_return())
        assert result.summary["total_tax_burden"] == (
            result.summary["federal_tax"]
            + result.summary["total_state_tax"]
        )

    def test_effective_rate_is_reasonable(self):
        """Effective federal rate should be between 0% and 50%."""
        result = compute_full_return(self._simple_return())
        rate = result.summary["effective_federal_rate"]
        assert Decimal("0") <= rate <= Decimal("50")

    def test_audit_risk_score_range(self):
        """Audit risk score should be in [0, 100]."""
        result = compute_full_return(self._simple_return())
        assert (
            Decimal("0")
            <= result.audit_risk.overall_score
            <= Decimal("100")
        )

    def test_state_results_match_residencies(self):
        """One state result per state residency."""
        tr = TaxReturn(
            filing_status=FilingStatus.SINGLE,
            w2s=[W2Income(employer_name="X", wages=Decimal("90000"))],
            state_residencies=[
                StateResidency(state_code="IL"),
                StateResidency(state_code="MN"),
            ],
        )
        result = compute_full_return(tr)
        assert len(result.states) == 2
        codes = {s.state_code for s in result.states}
        assert codes == {"IL", "MN"}
