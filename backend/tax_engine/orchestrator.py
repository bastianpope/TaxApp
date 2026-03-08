"""Orchestrator — ties all tax engine modules together.

Entry point: `compute_full_return(TaxReturn) → FullResult`
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from tax_engine.aggressiveness import analyze_aggressiveness
from tax_engine.audit_risk import compute_audit_risk
from tax_engine.federal import calculate_federal
from tax_engine.models import (
    FullResult,
    StateResult,
    TaxReturn,
)
from tax_engine.state_il import calculate_il
from tax_engine.state_mn import calculate_mn

if TYPE_CHECKING:
    from collections.abc import Callable

# ---------------------------------------------------------------------------
# State calculator registry
# ---------------------------------------------------------------------------

_STATE_CALCULATORS: dict[str, Callable[..., StateResult]] = {
    "IL": calculate_il,
    "MN": calculate_mn,
}


def compute_full_return(tax_return: TaxReturn) -> FullResult:
    """Run the complete tax computation pipeline.

    1. Federal calculation (Form 1040)
    2. State calculations (per residency)
    3. Audit risk scoring
    4. Aggressiveness analysis
    5. Assemble full result with summary

    Returns FullResult with all components.
    """
    # Step 1: Federal
    federal = calculate_federal(tax_return)

    # Step 2: States
    state_results: list[StateResult] = []
    for residency in tax_return.state_residencies:
        state_code = residency.state_code.upper()
        if state_code in _STATE_CALCULATORS:
            calc_fn = _STATE_CALCULATORS[state_code]
            state_result = calc_fn(tax_return, federal)
            state_results.append(state_result)
        else:
            # Unsupported state — include a placeholder
            state_results.append(
                StateResult(
                    state_code=state_code,
                    detail={"error": f"State '{state_code}' not yet supported"},
                )
            )

    # Step 3: Audit risk
    audit_risk = compute_audit_risk(tax_return, federal)

    # Step 4: Aggressiveness
    aggressiveness = analyze_aggressiveness(tax_return, federal, audit_risk)

    # Step 5: Assemble
    total_state_taxes = sum(
        (s.state_tax_after_credits for s in state_results), Decimal("0")
    )

    return FullResult(
        tax_year=tax_return.tax_year,
        filing_status=tax_return.filing_status,
        federal=federal,
        states=state_results,
        audit_risk=audit_risk,
        aggressiveness=aggressiveness,
        summary={
            "total_income": federal.total_income,
            "agi": federal.agi,
            "federal_taxable_income": federal.taxable_income,
            "federal_tax": federal.tax_after_credits,
            "federal_refund": federal.refund,
            "federal_owed": federal.amount_owed,
            "total_state_tax": total_state_taxes,
            "total_tax_burden": federal.tax_after_credits + total_state_taxes,
            "effective_federal_rate": (
                federal.tax_after_credits / federal.agi * Decimal("100")
                if federal.agi > Decimal("0")
                else Decimal("0")
            ),
            "audit_risk_score": audit_risk.overall_score,
            "audit_risk_level": audit_risk.risk_level,
            "aggressiveness_level": aggressiveness.overall_level.value,
        },
    )
