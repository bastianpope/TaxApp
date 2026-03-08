"""Tax calculation API routes.

POST /api/calculate — accepts TaxReturn JSON, returns FullResult.
POST /api/health — health check.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from tax_engine.models import TaxReturn  # noqa: TC001 — FastAPI needs at runtime
from tax_engine.orchestrator import FullResult, compute_full_return

router = APIRouter(prefix="/api", tags=["tax"])


@router.post("/calculate", response_model=None)
async def calculate_tax(tax_return: TaxReturn) -> dict:
    """Compute full tax return and return JSON result.

    Accepts a TaxReturn payload, runs the full pipeline
    (federal + state + audit risk + aggressiveness), and
    returns the assembled FullResult as a JSON dict.
    """
    try:
        result: FullResult = compute_full_return(tax_return)
        return _serialize_result(result)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Tax computation failed: {exc}",
        ) from exc


@router.get("/health")
async def health_check() -> dict:
    """Simple health check endpoint."""
    return {"status": "ok", "service": "taxapp"}


def _serialize_result(result: FullResult) -> dict:
    """Convert FullResult to a JSON-safe dict.

    Pydantic models serialize via .model_dump(); dataclasses
    need manual conversion for Decimal fields.
    """
    from dataclasses import asdict

    def _convert(obj: object) -> object:
        """Recursively convert Decimals to strings for JSON."""
        from decimal import Decimal

        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, dict):
            return {k: _convert(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_convert(v) for v in obj]
        return obj

    # Federal & states are Pydantic
    fed_dict = _convert(result.federal.model_dump())
    states_dict = [_convert(s.model_dump()) for s in result.states]

    # Audit risk & aggressiveness are dataclasses
    audit_dict = _convert(asdict(result.audit_risk))
    agg_dict = _convert(asdict(result.aggressiveness))

    return {
        "tax_year": result.tax_year,
        "filing_status": result.filing_status.value,
        "federal": fed_dict,
        "states": states_dict,
        "audit_risk": audit_dict,
        "aggressiveness": agg_dict,
        "summary": _convert(result.summary),
    }
