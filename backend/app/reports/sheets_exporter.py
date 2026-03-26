"""Google Sheets exporter using gspread."""
from __future__ import annotations

import json
import logging
import os
from typing import Optional

from app.schemas.report import ReportData

logger = logging.getLogger(__name__)


class SheetsExporter:
    """Export report data to a Google Sheets spreadsheet."""

    def __init__(self, service_account_json: Optional[str] = None):
        self._sa_json = service_account_json or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")

    def _get_client(self):
        import gspread
        from google.oauth2.service_account import Credentials

        if not self._sa_json:
            raise RuntimeError("Google service account JSON not configured")

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        creds_data = json.loads(self._sa_json)
        creds = Credentials.from_service_account_info(creds_data, scopes=scopes)
        return gspread.authorize(creds)

    def export(self, report_data: ReportData, spreadsheet_id: str) -> str:
        """Export report data to an existing Google Sheet. Returns the spreadsheet URL."""
        try:
            gc = self._get_client()
            sh = gc.open_by_key(spreadsheet_id)

            # Summary sheet
            try:
                summary_ws = sh.worksheet("Summary")
            except Exception:
                summary_ws = sh.add_worksheet(title="Summary", rows=20, cols=6)

            summary_ws.clear()
            summary_ws.update(
                "A1",
                [
                    ["Ad Budget Guard Report"],
                    [""],
                    ["Account", report_data.account_name],
                    ["Type", report_data.report_type],
                    ["Period", f"{report_data.date_from} to {report_data.date_to}"],
                    ["Currency", report_data.currency],
                    ["Total Spend", str(report_data.total_spend)],
                    ["Campaigns", str(len(report_data.campaigns))],
                    ["Incidents", str(len(report_data.incidents))],
                    ["Generated", report_data.generated_at.strftime("%Y-%m-%d %H:%M UTC")],
                ],
            )

            # Campaigns sheet
            if report_data.campaigns:
                try:
                    camp_ws = sh.worksheet("Campaigns")
                except Exception:
                    camp_ws = sh.add_worksheet(
                        title="Campaigns",
                        rows=len(report_data.campaigns) + 2,
                        cols=5,
                    )

                camp_ws.clear()
                rows = [["Campaign", "Spend", "Daily Budget", "Utilization %"]]
                for c in report_data.campaigns:
                    rows.append([
                        c.campaign_name,
                        str(c.spend),
                        str(c.daily_budget) if c.daily_budget else "",
                        str(c.utilization_pct) if c.utilization_pct else "",
                    ])
                camp_ws.update("A1", rows)

            # Daily Spend sheet
            if report_data.daily_spends:
                try:
                    daily_ws = sh.worksheet("Daily Spend")
                except Exception:
                    daily_ws = sh.add_worksheet(
                        title="Daily Spend",
                        rows=len(report_data.daily_spends) + 2,
                        cols=2,
                    )

                daily_ws.clear()
                rows = [["Date", "Spend"]]
                for d in report_data.daily_spends:
                    rows.append([str(d.date), str(d.spend)])
                daily_ws.update("A1", rows)

            # Incidents sheet
            if report_data.incidents:
                try:
                    inc_ws = sh.worksheet("Incidents")
                except Exception:
                    inc_ws = sh.add_worksheet(
                        title="Incidents",
                        rows=len(report_data.incidents) + 2,
                        cols=4,
                    )

                inc_ws.clear()
                rows = [["Timestamp", "Type", "Severity", "Message"]]
                for inc in report_data.incidents:
                    rows.append([
                        inc.timestamp.strftime("%Y-%m-%d %H:%M"),
                        inc.alert_type,
                        inc.severity,
                        inc.message,
                    ])
                inc_ws.update("A1", rows)

            url = sh.url
            logger.info("sheets_exported", extra={"spreadsheet_id": spreadsheet_id, "url": url})
            return url

        except Exception:
            logger.exception("sheets_export_failed")
            raise
