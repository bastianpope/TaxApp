"""Tax year constants — year-keyed registry.

Usage:
    constants = get_brackets(2025)
    rate = constants.federal_brackets[FilingStatus.SINGLE]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from tax_engine.models import FilingStatus

# ---------------------------------------------------------------------------
# Data structure for a single tax year's constants
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TaxYearConstants:
    """All constants for a single tax year — federal + state."""

    tax_year: int

    # Federal income tax brackets: {filing_status: [(upper_bound, rate), ...]}
    # upper_bound = Decimal("Infinity") for the top bracket
    federal_brackets: dict[FilingStatus, list[tuple[Decimal, Decimal]]]

    # Standard deduction by filing status
    standard_deductions: dict[FilingStatus, Decimal]

    # Self-employment tax
    se_tax_rate: Decimal
    se_medicare_rate: Decimal
    se_social_security_wage_base: Decimal

    # Additional Medicare surtax
    additional_medicare_threshold: dict[FilingStatus, Decimal]
    additional_medicare_rate: Decimal

    # Child Tax Credit
    child_tax_credit_amount: Decimal
    child_tax_credit_phase_out: dict[FilingStatus, Decimal]
    child_tax_credit_phase_out_rate: Decimal

    # EITC tables: {num_children: (max_income_single, max_income_mfj, max_credit)}
    eitc_table: dict[int, tuple[Decimal, Decimal, Decimal]]

    # Capital gains rates
    lt_capital_gains_rates: list[tuple[Decimal, Decimal]]  # (threshold, rate)

    # Schedule C
    standard_mileage_rate: Decimal
    simplified_home_office_rate: Decimal  # per sqft
    simplified_home_office_max_sqft: Decimal
    meals_deduction_pct: Decimal

    # SALT cap
    salt_cap: Decimal

    # Medical expense AGI threshold
    medical_expense_agi_pct: Decimal

    # Charitable deductions — AGI limits
    charitable_cash_agi_limit_pct: Decimal
    charitable_noncash_agi_limit_pct: Decimal

    # --- State: Illinois ---
    il_flat_rate: Decimal
    il_personal_exemption: Decimal
    il_dependent_exemption: Decimal

    # --- State: Minnesota ---
    mn_brackets: dict[FilingStatus, list[tuple[Decimal, Decimal]]]
    mn_standard_deductions: dict[FilingStatus, Decimal]
    mn_dependent_exemption: Decimal

    # Qualified dividends / LTCG preferential rate thresholds
    qualified_div_thresholds: dict[FilingStatus, list[tuple[Decimal, Decimal]]] = field(
        default_factory=dict
    )


# ---------------------------------------------------------------------------
# TY2025 Constants
# ---------------------------------------------------------------------------

_INF = Decimal("Infinity")

TY2025 = TaxYearConstants(
    tax_year=2025,
    # -------------------------------------------------------------------
    # Federal brackets (TY2025 — inflation adjusted)
    # -------------------------------------------------------------------
    federal_brackets={
        FilingStatus.SINGLE: [
            (Decimal("11925"), Decimal("0.10")),
            (Decimal("48475"), Decimal("0.12")),
            (Decimal("103350"), Decimal("0.22")),
            (Decimal("197300"), Decimal("0.24")),
            (Decimal("250525"), Decimal("0.32")),
            (Decimal("626350"), Decimal("0.35")),
            (_INF, Decimal("0.37")),
        ],
        FilingStatus.MFJ: [
            (Decimal("23850"), Decimal("0.10")),
            (Decimal("96950"), Decimal("0.12")),
            (Decimal("206700"), Decimal("0.22")),
            (Decimal("394600"), Decimal("0.24")),
            (Decimal("501050"), Decimal("0.32")),
            (Decimal("751600"), Decimal("0.35")),
            (_INF, Decimal("0.37")),
        ],
        FilingStatus.MFS: [
            (Decimal("11925"), Decimal("0.10")),
            (Decimal("48475"), Decimal("0.12")),
            (Decimal("103350"), Decimal("0.22")),
            (Decimal("197300"), Decimal("0.24")),
            (Decimal("250525"), Decimal("0.32")),
            (Decimal("375800"), Decimal("0.35")),
            (_INF, Decimal("0.37")),
        ],
        FilingStatus.HOH: [
            (Decimal("17000"), Decimal("0.10")),
            (Decimal("64850"), Decimal("0.12")),
            (Decimal("103350"), Decimal("0.22")),
            (Decimal("197300"), Decimal("0.24")),
            (Decimal("250500"), Decimal("0.32")),
            (Decimal("626350"), Decimal("0.35")),
            (_INF, Decimal("0.37")),
        ],
        FilingStatus.QSS: [  # Same as MFJ
            (Decimal("23850"), Decimal("0.10")),
            (Decimal("96950"), Decimal("0.12")),
            (Decimal("206700"), Decimal("0.22")),
            (Decimal("394600"), Decimal("0.24")),
            (Decimal("501050"), Decimal("0.32")),
            (Decimal("751600"), Decimal("0.35")),
            (_INF, Decimal("0.37")),
        ],
    },
    # -------------------------------------------------------------------
    # Standard deductions
    # -------------------------------------------------------------------
    standard_deductions={
        FilingStatus.SINGLE: Decimal("15000"),
        FilingStatus.MFJ: Decimal("30000"),
        FilingStatus.MFS: Decimal("15000"),
        FilingStatus.HOH: Decimal("22500"),
        FilingStatus.QSS: Decimal("30000"),
    },
    # -------------------------------------------------------------------
    # Self-employment tax
    # -------------------------------------------------------------------
    se_tax_rate=Decimal("0.153"),  # 12.4% SS + 2.9% Medicare
    se_medicare_rate=Decimal("0.029"),
    se_social_security_wage_base=Decimal("176100"),
    # -------------------------------------------------------------------
    # Additional Medicare
    # -------------------------------------------------------------------
    additional_medicare_threshold={
        FilingStatus.SINGLE: Decimal("200000"),
        FilingStatus.MFJ: Decimal("250000"),
        FilingStatus.MFS: Decimal("125000"),
        FilingStatus.HOH: Decimal("200000"),
        FilingStatus.QSS: Decimal("200000"),
    },
    additional_medicare_rate=Decimal("0.009"),
    # -------------------------------------------------------------------
    # Child Tax Credit
    # -------------------------------------------------------------------
    child_tax_credit_amount=Decimal("2000"),
    child_tax_credit_phase_out={
        FilingStatus.SINGLE: Decimal("200000"),
        FilingStatus.MFJ: Decimal("400000"),
        FilingStatus.MFS: Decimal("200000"),
        FilingStatus.HOH: Decimal("200000"),
        FilingStatus.QSS: Decimal("400000"),
    },
    child_tax_credit_phase_out_rate=Decimal("0.05"),  # per $1000 over threshold
    # -------------------------------------------------------------------
    # EITC (simplified — max credit for common scenarios)
    # (num_children: (max_income_single, max_income_mfj, max_credit))
    # -------------------------------------------------------------------
    eitc_table={
        0: (Decimal("18591"), Decimal("25511"), Decimal("632")),
        1: (Decimal("49084"), Decimal("56004"), Decimal("4213")),
        2: (Decimal("55768"), Decimal("62688"), Decimal("6960")),
        3: (Decimal("59899"), Decimal("66819"), Decimal("7830")),
    },
    # -------------------------------------------------------------------
    # Long-term capital gains rates (Single thresholds — simplified)
    # -------------------------------------------------------------------
    lt_capital_gains_rates=[
        (Decimal("48350"), Decimal("0.00")),
        (Decimal("533400"), Decimal("0.15")),
        (_INF, Decimal("0.20")),
    ],
    # -------------------------------------------------------------------
    # Schedule C constants
    # -------------------------------------------------------------------
    standard_mileage_rate=Decimal("0.70"),  # $0.70/mile for 2025
    simplified_home_office_rate=Decimal("5"),  # $5/sqft
    simplified_home_office_max_sqft=Decimal("300"),
    meals_deduction_pct=Decimal("0.50"),
    # -------------------------------------------------------------------
    # SALT cap
    # -------------------------------------------------------------------
    salt_cap=Decimal("10000"),
    # -------------------------------------------------------------------
    # Medical expense threshold
    # -------------------------------------------------------------------
    medical_expense_agi_pct=Decimal("0.075"),
    # -------------------------------------------------------------------
    # Charitable limits
    # -------------------------------------------------------------------
    charitable_cash_agi_limit_pct=Decimal("0.60"),
    charitable_noncash_agi_limit_pct=Decimal("0.30"),
    # -------------------------------------------------------------------
    # Illinois (flat rate state)
    # -------------------------------------------------------------------
    il_flat_rate=Decimal("0.0495"),
    il_personal_exemption=Decimal("2625"),
    il_dependent_exemption=Decimal("2625"),
    # -------------------------------------------------------------------
    # Minnesota (progressive brackets)
    # -------------------------------------------------------------------
    mn_brackets={
        FilingStatus.SINGLE: [
            (Decimal("31690"), Decimal("0.0535")),
            (Decimal("104090"), Decimal("0.068")),
            (Decimal("193240"), Decimal("0.0785")),
            (_INF, Decimal("0.0985")),
        ],
        FilingStatus.MFJ: [
            (Decimal("46330"), Decimal("0.0535")),
            (Decimal("184040"), Decimal("0.068")),
            (Decimal("321450"), Decimal("0.0785")),
            (_INF, Decimal("0.0985")),
        ],
        FilingStatus.MFS: [
            (Decimal("23165"), Decimal("0.0535")),
            (Decimal("92020"), Decimal("0.068")),
            (Decimal("160725"), Decimal("0.0785")),
            (_INF, Decimal("0.0985")),
        ],
        FilingStatus.HOH: [
            (Decimal("39010"), Decimal("0.0535")),
            (Decimal("155990"), Decimal("0.068")),
            (Decimal("193240"), Decimal("0.0785")),
            (_INF, Decimal("0.0985")),
        ],
        FilingStatus.QSS: [  # Same as MFJ
            (Decimal("46330"), Decimal("0.0535")),
            (Decimal("184040"), Decimal("0.068")),
            (Decimal("321450"), Decimal("0.0785")),
            (_INF, Decimal("0.0985")),
        ],
    },
    mn_standard_deductions={
        FilingStatus.SINGLE: Decimal("14575"),
        FilingStatus.MFJ: Decimal("29150"),
        FilingStatus.MFS: Decimal("14575"),
        FilingStatus.HOH: Decimal("21850"),
        FilingStatus.QSS: Decimal("29150"),
    },
    mn_dependent_exemption=Decimal("5200"),
    # -------------------------------------------------------------------
    # Qualified dividend / LTCG preferential rate thresholds
    # -------------------------------------------------------------------
    qualified_div_thresholds={
        FilingStatus.SINGLE: [
            (Decimal("48350"), Decimal("0.00")),
            (Decimal("533400"), Decimal("0.15")),
            (_INF, Decimal("0.20")),
        ],
        FilingStatus.MFJ: [
            (Decimal("96700"), Decimal("0.00")),
            (Decimal("600050"), Decimal("0.15")),
            (_INF, Decimal("0.20")),
        ],
        FilingStatus.MFS: [
            (Decimal("48350"), Decimal("0.00")),
            (Decimal("300025"), Decimal("0.15")),
            (_INF, Decimal("0.20")),
        ],
        FilingStatus.HOH: [
            (Decimal("64750"), Decimal("0.00")),
            (Decimal("566700"), Decimal("0.15")),
            (_INF, Decimal("0.20")),
        ],
        FilingStatus.QSS: [
            (Decimal("96700"), Decimal("0.00")),
            (Decimal("600050"), Decimal("0.15")),
            (_INF, Decimal("0.20")),
        ],
    },
)

# ---------------------------------------------------------------------------
# Year-keyed registry
# ---------------------------------------------------------------------------

_BRACKETS_REGISTRY: dict[int, TaxYearConstants] = {
    2025: TY2025,
}


def get_brackets(tax_year: int) -> TaxYearConstants:
    """Look up constants by tax year. Raises KeyError if unsupported."""
    if tax_year not in _BRACKETS_REGISTRY:
        supported = ", ".join(str(y) for y in sorted(_BRACKETS_REGISTRY.keys()))
        raise KeyError(f"No tax brackets for year {tax_year}. Supported: {supported}")
    return _BRACKETS_REGISTRY[tax_year]
