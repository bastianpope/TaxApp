"""TaxApp Tax Engine — Federal + State calculation with audit risk and aggressiveness dial."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from tax_engine.models import FederalResult, StateResidency, StateResult

__all__ = [
    "STATE_CALCULATORS",
    "StateCalculator",
    "get_state_calculator",
]


@runtime_checkable
class StateCalculator(Protocol):
    """Protocol for state tax calculators.

    Each state module (state_il, state_mn) implements this protocol.
    The API dispatches by residency via the STATE_CALCULATORS registry.
    """

    def calculate(self, federal_result: FederalResult, state_data: StateResidency) -> StateResult:
        """Calculate state tax given federal results and state-specific data."""
        ...

    def supported_state(self) -> str:
        """Return the two-letter state code this calculator handles (e.g. 'IL', 'MN')."""
        ...


# Registry populated after state modules are imported (avoids circular imports).
# state_il and state_mn register themselves here on import.
STATE_CALCULATORS: dict[str, StateCalculator] = {}


def get_state_calculator(state_code: str) -> StateCalculator:
    """Look up a state calculator by two-letter code. Raises KeyError if unsupported."""
    code = state_code.upper()
    if code not in STATE_CALCULATORS:
        supported = ", ".join(sorted(STATE_CALCULATORS.keys())) or "(none registered)"
        raise KeyError(f"No calculator for state '{code}'. Supported: {supported}")
    return STATE_CALCULATORS[code]
