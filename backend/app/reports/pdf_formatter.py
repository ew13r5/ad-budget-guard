"""PDF report formatter using WeasyPrint + Jinja2."""
from __future__ import annotations

import logging
import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.schemas.report import ReportData

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "templates"


def render_pdf(report_data: ReportData, output_path: str) -> str:
    """Render report data to a PDF file. Returns the output path."""
    try:
        from weasyprint import HTML
    except ImportError:
        logger.error("weasyprint_not_installed")
        raise RuntimeError("WeasyPrint is not installed")

    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
    template = env.get_template("report.html")

    # Prepare chart data (SVG bar chart dimensions)
    max_spend = max((d.spend for d in report_data.daily_spends), default=1)
    if max_spend == 0:
        max_spend = 1

    chart_bars = []
    bar_width = 40
    gap = 10
    for i, d in enumerate(report_data.daily_spends):
        height = float(d.spend) / float(max_spend) * 200 if max_spend else 0
        chart_bars.append({
            "x": i * (bar_width + gap),
            "y": 200 - height,
            "width": bar_width,
            "height": max(height, 1),
            "spend": f"{d.spend:,.2f}",
            "label": d.date.strftime("%m/%d"),
        })

    chart_width = max(len(chart_bars) * (bar_width + gap), 100)

    html_content = template.render(
        report=report_data,
        chart_bars=chart_bars,
        chart_width=chart_width,
        agency_name=os.getenv("REPORT_AGENCY_NAME", "Ad Budget Guard"),
    )

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    HTML(string=html_content).write_pdf(output_path)
    logger.info("pdf_generated", extra={"path": output_path})
    return output_path
