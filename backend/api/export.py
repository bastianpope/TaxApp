"""PDF export endpoint.

POST /api/export/pdf  — accepts the same TaxCalculationResponse payload the
frontend already holds and returns a binary PDF with the tax summary.

No e-filing capability.  Every page carries a mandatory disclaimer.
"""

from __future__ import annotations

import io
import itertools
from datetime import date
from typing import Any

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

router = APIRouter(prefix="/api/export", tags=["export"])

# ---------------------------------------------------------------------------
# Request schema — mirrors TaxCalculationResponse on the frontend
# ---------------------------------------------------------------------------

DISCLAIMER = (
    "FOR INFORMATIONAL AND EDUCATIONAL PURPOSES ONLY. "
    "This document does not constitute legal, financial, or tax advice. "
    "TaxApp does not file tax returns. "
    "Tax laws are complex and subject to change. "
    "Always verify with official IRS publications and consult a qualified "
    "CPA or enrolled agent before filing."
)


class FederalIn(BaseModel):
    agi: float = 0
    taxable_income: float = 0
    standard_deduction: float = 0
    itemized_deduction: float = 0
    use_itemized: bool = False
    federal_tax: float = 0
    self_employment_tax: float = 0
    effective_rate: float = 0
    total_withheld: float = 0
    balance: float = 0
    credits: dict[str, float] = {}


class StateIn(BaseModel):
    taxable_income: float = 0
    state_tax: float = 0
    effective_rate: float = 0
    withheld: float = 0
    balance: float = 0


class AuditRiskIn(BaseModel):
    score: float = 0
    risk_factors: list[str] = []
    recommendations: list[str] = []


class DeductionRecIn(BaseModel):
    description: str
    estimated_savings: float = 0
    confidence: str = ""
    form: str | None = None


class ScenarioIn(BaseModel):
    federal: FederalIn = FederalIn()
    state: dict[str, StateIn] = {}
    audit_risk: AuditRiskIn = AuditRiskIn()
    deduction_recommendations: list[DeductionRecIn] = []


class PdfRequest(BaseModel):
    tax_year: int = 2025
    filing_status: str = "single"
    gross_income: float = 0
    active_level: str = "LOW"  # which scenario the user was viewing
    scenarios: dict[str, ScenarioIn]


# ---------------------------------------------------------------------------
# PDF builder
# ---------------------------------------------------------------------------

_BRAND_DARK = colors.HexColor("#0f172a")
_BRAND_ACCENT = colors.HexColor("#0ea5e9")
_BORDER_GREY = colors.HexColor("#334155")
_TEXT_MUTED = colors.HexColor("#94a3b8")
_SUCCESS = colors.HexColor("#10b981")
_DANGER = colors.HexColor("#ef4444")
_WARNING = colors.HexColor("#f59e0b")


def _dollar(v: float) -> str:
    if v < 0:
        return f"-${abs(v):,.0f}"
    return f"${v:,.0f}"


def _pct(v: float) -> str:
    return f"{v:.2f}%"


def _risk_color(score: float) -> Any:
    if score < 30:
        return _SUCCESS
    if score < 60:
        return _WARNING
    return _DANGER


def _level_label(level: str) -> str:
    return {"LOW": "Conservative", "MEDIUM": "Moderate", "HIGH": "Aggressive"}.get(
        level.upper(), level
    )


def _build_pdf(req: PdfRequest) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.85 * inch,
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=_BRAND_ACCENT,
        spaceAfter=4,
        leading=24,
    )
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.white,
        spaceBefore=14,
        spaceAfter=4,
        leading=17,
        backColor=_BRAND_DARK,
    )
    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#e2e8f0"),
        leading=13,
    )
    muted = ParagraphStyle(
        "Muted",
        parent=body,
        textColor=_TEXT_MUTED,
        fontSize=8,
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontSize=7.5,
        textColor=_TEXT_MUTED,
        leading=11,
        borderPad=6,
    )

    # -- Table style helpers --
    def _table_style(header_bg: Any = _BRAND_ACCENT) -> list[Any]:
        return [
            ("BACKGROUND", (0, 0), (-1, 0), header_bg),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [colors.HexColor("#1e293b"), colors.HexColor("#0f172a")],
            ),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#e2e8f0")),
            ("FONTSIZE", (0, 1), (-1, -1), 8.5),
            ("GRID", (0, 0), (-1, -1), 0.4, _BORDER_GREY),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ]

    active_level = req.active_level.upper()
    scenario = req.scenarios.get(active_level) or next(iter(req.scenarios.values()), ScenarioIn())
    fed = scenario.federal
    audit = scenario.audit_risk

    filing_label = req.filing_status.replace("_", " ").title()

    story: list[Any] = []

    # ── Header ──────────────────────────────────────────────────────────────
    story.append(Paragraph("📊 TaxApp — Tax Summary Report", h1))
    story.append(
        Paragraph(
            f"Tax Year {req.tax_year}  ·  {filing_label}  ·  "
            f"Strategy: <b>{_level_label(active_level)}</b>  ·  "
            f"Generated: {date.today().isoformat()}",
            muted,
        )
    )
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1, color=_BORDER_GREY))
    story.append(Spacer(1, 10))

    # ── Mandatory disclaimer (top) ───────────────────────────────────────────
    story.append(
        Paragraph(
            f"⚠️  <b>IMPORTANT:</b> {DISCLAIMER}",
            disclaimer_style,
        )
    )
    story.append(Spacer(1, 14))

    # ── Income overview ──────────────────────────────────────────────────────
    story.append(Paragraph(" Federal Income Overview", h2))
    story.append(Spacer(1, 4))
    income_data = [
        ["Line Item", "Amount"],
        ["Gross Income", _dollar(req.gross_income)],
        ["Adjusted Gross Income (AGI)", _dollar(fed.agi)],
        [
            f"Deduction ({'Itemized' if fed.use_itemized else 'Standard'})",
            _dollar(fed.itemized_deduction if fed.use_itemized else fed.standard_deduction),
        ],
        ["Taxable Income", _dollar(fed.taxable_income)],
    ]
    t = Table(income_data, colWidths=["65%", "35%"])
    t.setStyle(TableStyle(_table_style()))
    story.append(t)
    story.append(Spacer(1, 10))

    # ── Federal tax ──────────────────────────────────────────────────────────
    story.append(Paragraph(" Federal Tax Calculation", h2))
    story.append(Spacer(1, 4))

    credits_total = sum(fed.credits.values())
    balance_label = "Amount Owed" if fed.balance > 0 else "Refund"
    tax_data = [
        ["Line Item", "Amount"],
        ["Income Tax (before credits)", _dollar(fed.federal_tax)],
        ["Self-Employment Tax", _dollar(fed.self_employment_tax)],
        ["Total Credits", f"-{_dollar(credits_total)}"],
        ["Total Tax Withheld", f"-{_dollar(fed.total_withheld)}"],
        [balance_label, _dollar(abs(fed.balance))],
        ["Effective Federal Rate", _pct(fed.effective_rate * 100)],
    ]
    t2 = Table(tax_data, colWidths=["65%", "35%"])
    style2 = _table_style()
    # Highlight the balance row
    balance_row = len(tax_data) - 2
    balance_color = _DANGER if fed.balance > 0 else _SUCCESS
    style2.append(("TEXTCOLOR", (1, balance_row), (1, balance_row), balance_color))
    style2.append(("FONTNAME", (0, balance_row), (-1, balance_row), "Helvetica-Bold"))
    t2.setStyle(TableStyle(style2))
    story.append(t2)
    story.append(Spacer(1, 10))

    # ── State taxes ──────────────────────────────────────────────────────────
    if scenario.state:
        story.append(Paragraph(" State Tax Summary", h2))
        story.append(Spacer(1, 4))
        state_rows: list[list[str]] = [["State", "Taxable Income", "Tax", "Withheld", "Balance"]]
        for state_code, st in scenario.state.items():
            bal_label = _dollar(abs(st.balance))
            if st.balance < 0:
                bal_label = f"Refund {_dollar(abs(st.balance))}"
            state_rows.append(
                [
                    state_code,
                    _dollar(st.taxable_income),
                    _dollar(st.state_tax),
                    _dollar(st.withheld),
                    bal_label,
                ]
            )
        t3 = Table(state_rows, colWidths=["12%", "22%", "22%", "22%", "22%"])
        t3.setStyle(TableStyle(_table_style()))
        story.append(t3)
        story.append(Spacer(1, 10))

    # ── Audit risk ───────────────────────────────────────────────────────────
    story.append(Paragraph(" Audit Risk Assessment", h2))
    story.append(Spacer(1, 4))
    risk_score = audit.score
    risk_label = (
        "Low" if risk_score < 30 else "Medium" if risk_score < 60 else "High"
    )
    risk_color = _risk_color(risk_score)
    audit_data = [
        ["Overall Risk Score", f"{risk_score:.0f}/100"],
        ["Risk Level", risk_label],
    ]
    t_audit = Table(audit_data, colWidths=["65%", "35%"])
    audit_style = [
        (
            "ROWBACKGROUNDS",
            (0, 0),
            (-1, -1),
            [colors.HexColor("#1e293b"), colors.HexColor("#0f172a")],
        ),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#e2e8f0")),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.4, _BORDER_GREY),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("TEXTCOLOR", (1, 1), (1, 1), risk_color),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
    ]
    t_audit.setStyle(TableStyle(audit_style))
    story.append(t_audit)
    story.append(Spacer(1, 6))

    if audit.risk_factors:
        story.append(Paragraph("<b>Risk Factors:</b>", body))
        for f in audit.risk_factors:
            story.append(Paragraph(f"• {f}", body))
    if audit.recommendations:
        story.append(Spacer(1, 4))
        story.append(Paragraph("<b>Recommendations:</b>", body))
        for r in audit.recommendations:
            story.append(Paragraph(f"✓ {r}", body))
    story.append(Spacer(1, 10))

    # ── Deduction opportunities ──────────────────────────────────────────────
    if scenario.deduction_recommendations:
        story.append(Paragraph(" Deduction Opportunities", h2))
        story.append(Spacer(1, 4))
        rec_data = [["Opportunity", "Est. Savings", "Confidence"]]
        for rec in list(itertools.islice(scenario.deduction_recommendations, 10)):
            desc = rec.description[:80] + "…" if len(rec.description) > 80 else rec.description
            rec_data.append([desc, _dollar(rec.estimated_savings), rec.confidence])
        t_rec = Table(rec_data, colWidths=["55%", "25%", "20%"])
        t_rec.setStyle(TableStyle(_table_style(header_bg=_SUCCESS)))
        story.append(t_rec)
        story.append(Spacer(1, 10))

    # ── Scenario comparison ──────────────────────────────────────────────────
    story.append(Paragraph(" Scenario Comparison", h2))
    story.append(Spacer(1, 4))
    comp_levels = [("LOW", "Conservative 🛡️"), ("MEDIUM", "Moderate ⚖️"), ("HIGH", "Aggressive 🚀")]
    comp_rows = [["Metric", "Conservative", "Moderate", "Aggressive"]]
    metrics = [
        ("AGI", lambda s: _dollar(s.federal.agi)),
        ("Federal Tax", lambda s: _dollar(s.federal.federal_tax)),
        ("Balance", lambda s: _dollar(s.federal.balance)),
        ("Audit Risk", lambda s: f"{s.audit_risk.score:.0f}/100"),
    ]
    for label, fn in metrics:
        row = [label]
        for level, _ in comp_levels:
            sc = req.scenarios.get(level)
            row.append(fn(sc) if sc else "—")
        comp_rows.append(row)
    t_comp = Table(comp_rows, colWidths=["28%", "24%", "24%", "24%"])
    comp_style = _table_style()
    # Bold the active column
    col_idx = next(
        (i + 1 for i, (lvl, _) in enumerate(comp_levels) if lvl == active_level), 1
    )
    comp_style.append(("FONTNAME", (col_idx, 1), (col_idx, -1), "Helvetica-Bold"))
    comp_style.append(("TEXTCOLOR", (col_idx, 1), (col_idx, -1), _BRAND_ACCENT))
    t_comp.setStyle(TableStyle(comp_style))
    story.append(t_comp)
    story.append(Spacer(1, 16))

    # ── Footer disclaimer ────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=_BORDER_GREY))
    story.append(Spacer(1, 6))
    story.append(Paragraph(DISCLAIMER, disclaimer_style))

    doc.build(story)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("/pdf", summary="Generate a PDF tax summary")
async def export_pdf(req: PdfRequest) -> Response:
    """Generate and return a PDF of the tax summary.

    The caller should already have the TaxCalculationResponse in memory
    (from /api/calculate).  This endpoint does no further tax computation;
    it only formats and renders the data it receives.

    Returns: application/pdf binary stream.
    """
    pdf_bytes = _build_pdf(req)
    filename = f"TaxApp_{req.tax_year}_{req.filing_status}_{req.active_level}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
