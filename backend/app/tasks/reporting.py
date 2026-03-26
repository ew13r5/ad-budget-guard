"""Celery tasks for report generation."""
from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.reporting.generate_daily_report")
def generate_daily_report():
    """Generate daily reports for all active accounts."""
    from app.database import get_sync_session_factory
    from app.models.ad_account import AdAccount
    from app.models.report import Report, ReportFormat, ReportType
    from app.services.report_service import ReportService

    session_factory = get_sync_session_factory()
    session = session_factory()

    try:
        accounts = (
            session.query(AdAccount)
            .filter(AdAccount.is_active.is_(True))
            .all()
        )

        results = []
        for account in accounts:
            try:
                service = ReportService(session)
                report_data = service.generate_daily(account.id)

                storage_dir = os.getenv("REPORT_STORAGE_DIR", "/app/reports")
                output_path = os.path.join(
                    storage_dir,
                    str(account.id),
                    f"daily_{date.today().isoformat()}.pdf",
                )

                file_path = None
                try:
                    from app.reports.pdf_formatter import render_pdf
                    file_path = render_pdf(report_data, output_path)
                except Exception:
                    logger.exception("pdf_render_failed", extra={"account_id": str(account.id)})

                report = Report(
                    account_id=account.id,
                    report_type=ReportType.daily,
                    report_format=ReportFormat.pdf,
                    date_from=datetime.combine(date.today(), datetime.min.time()),
                    date_to=datetime.combine(date.today(), datetime.max.time().replace(microsecond=0)),
                    file_path=file_path,
                    generated_at=datetime.now(timezone.utc),
                )
                session.add(report)
                session.commit()

                results.append({"account_id": str(account.id), "status": "ok"})
                logger.info("daily_report_generated", extra={"account_id": str(account.id)})

            except Exception:
                session.rollback()
                logger.exception("daily_report_error", extra={"account_id": str(account.id)})
                results.append({"account_id": str(account.id), "status": "error"})

        return {"status": "ok", "reports": len(results), "results": results}

    finally:
        session.close()


@celery_app.task(name="app.tasks.reporting.generate_weekly_report")
def generate_weekly_report():
    """Generate weekly reports for all active accounts."""
    from app.database import get_sync_session_factory
    from app.models.ad_account import AdAccount
    from app.models.report import Report, ReportFormat, ReportType
    from app.services.report_service import ReportService

    session_factory = get_sync_session_factory()
    session = session_factory()

    try:
        accounts = (
            session.query(AdAccount)
            .filter(AdAccount.is_active.is_(True))
            .all()
        )

        results = []
        today = date.today()
        week_start = today - timedelta(days=6)

        for account in accounts:
            try:
                service = ReportService(session)
                report_data = service.generate_weekly(account.id, today)

                storage_dir = os.getenv("REPORT_STORAGE_DIR", "/app/reports")
                output_path = os.path.join(
                    storage_dir,
                    str(account.id),
                    f"weekly_{week_start.isoformat()}_{today.isoformat()}.pdf",
                )

                file_path = None
                try:
                    from app.reports.pdf_formatter import render_pdf
                    file_path = render_pdf(report_data, output_path)
                except Exception:
                    logger.exception("pdf_render_failed")

                report = Report(
                    account_id=account.id,
                    report_type=ReportType.weekly,
                    report_format=ReportFormat.pdf,
                    date_from=datetime.combine(week_start, datetime.min.time()),
                    date_to=datetime.combine(today, datetime.max.time().replace(microsecond=0)),
                    file_path=file_path,
                    generated_at=datetime.now(timezone.utc),
                )
                session.add(report)
                session.commit()

                results.append({"account_id": str(account.id), "status": "ok"})

            except Exception:
                session.rollback()
                logger.exception("weekly_report_error")
                results.append({"account_id": str(account.id), "status": "error"})

        return {"status": "ok", "reports": len(results)}

    finally:
        session.close()


@celery_app.task(name="app.tasks.reporting.generate_monthly_report")
def generate_monthly_report():
    """Generate monthly reports for all active accounts."""
    from app.database import get_sync_session_factory
    from app.models.ad_account import AdAccount
    from app.models.report import Report, ReportFormat, ReportType
    from app.services.report_service import ReportService

    session_factory = get_sync_session_factory()
    session = session_factory()

    try:
        accounts = (
            session.query(AdAccount)
            .filter(AdAccount.is_active.is_(True))
            .all()
        )

        results = []
        today = date.today()
        month_start = today.replace(day=1)

        for account in accounts:
            try:
                service = ReportService(session)
                report_data = service.generate_monthly(account.id, today)

                storage_dir = os.getenv("REPORT_STORAGE_DIR", "/app/reports")
                output_path = os.path.join(
                    storage_dir,
                    str(account.id),
                    f"monthly_{month_start.isoformat()}_{today.isoformat()}.pdf",
                )

                file_path = None
                try:
                    from app.reports.pdf_formatter import render_pdf
                    file_path = render_pdf(report_data, output_path)
                except Exception:
                    logger.exception("pdf_render_failed")

                report = Report(
                    account_id=account.id,
                    report_type=ReportType.monthly,
                    report_format=ReportFormat.pdf,
                    date_from=datetime.combine(month_start, datetime.min.time()),
                    date_to=datetime.combine(today, datetime.max.time().replace(microsecond=0)),
                    file_path=file_path,
                    generated_at=datetime.now(timezone.utc),
                )
                session.add(report)
                session.commit()

                results.append({"account_id": str(account.id), "status": "ok"})

            except Exception:
                session.rollback()
                logger.exception("monthly_report_error")
                results.append({"account_id": str(account.id), "status": "error"})

        return {"status": "ok", "reports": len(results)}

    finally:
        session.close()


@celery_app.task(name="app.tasks.reporting.generate_report_async")
def generate_report_async(
    account_id: str,
    report_type: str = "daily",
    report_format: str = "pdf",
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """Generate a single report on demand (called from API)."""
    from app.database import get_sync_session_factory
    from app.models.report import Report, ReportFormat as RF, ReportType as RT
    from app.services.report_service import ReportService

    session_factory = get_sync_session_factory()
    session = session_factory()

    try:
        uid = UUID(account_id)
        service = ReportService(session)

        d_from = date.fromisoformat(date_from) if date_from else None
        d_to = date.fromisoformat(date_to) if date_to else None

        if report_type == "daily":
            report_data = service.generate_daily(uid, d_from)
        elif report_type == "weekly":
            report_data = service.generate_weekly(uid, d_to)
        elif report_type == "monthly":
            report_data = service.generate_monthly(uid, d_to)
        else:
            return {"status": "error", "message": f"Unknown report type: {report_type}"}

        file_path = None
        sheets_url = None

        if report_format == "pdf":
            storage_dir = os.getenv("REPORT_STORAGE_DIR", "/app/reports")
            output_path = os.path.join(
                storage_dir,
                account_id,
                f"{report_type}_{report_data.date_from.isoformat()}_{report_data.date_to.isoformat()}.pdf",
            )
            try:
                from app.reports.pdf_formatter import render_pdf
                file_path = render_pdf(report_data, output_path)
            except Exception:
                logger.exception("pdf_render_failed")
                return {"status": "error", "message": "PDF render failed"}

        elif report_format == "sheets":
            spreadsheet_id = os.getenv("GOOGLE_SPREADSHEET_ID", "")
            if not spreadsheet_id:
                return {"status": "error", "message": "No spreadsheet ID configured"}
            try:
                from app.reports.sheets_exporter import SheetsExporter
                exporter = SheetsExporter()
                sheets_url = exporter.export(report_data, spreadsheet_id)
            except Exception:
                logger.exception("sheets_export_failed")
                return {"status": "error", "message": "Sheets export failed"}

        report = Report(
            account_id=uid,
            report_type=RT(report_type),
            report_format=RF(report_format),
            date_from=datetime.combine(report_data.date_from, datetime.min.time()),
            date_to=datetime.combine(report_data.date_to, datetime.max.time().replace(microsecond=0)),
            file_path=file_path,
            sheets_url=sheets_url,
            generated_at=datetime.now(timezone.utc),
        )
        session.add(report)
        session.commit()

        return {"status": "ok", "report_id": str(report.id)}

    except Exception:
        session.rollback()
        logger.exception("generate_report_async_error")
        return {"status": "error", "message": "Report generation failed"}

    finally:
        session.close()


@celery_app.task(name="app.tasks.reporting.cleanup_old_reports")
def cleanup_old_reports(max_age_days: int = 90):
    """Delete report files older than max_age_days."""
    from app.database import get_sync_session_factory
    from app.models.report import Report

    session_factory = get_sync_session_factory()
    session = session_factory()

    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        old_reports = (
            session.query(Report)
            .filter(Report.generated_at < cutoff)
            .all()
        )

        deleted = 0
        for report in old_reports:
            if report.file_path and os.path.exists(report.file_path):
                try:
                    os.remove(report.file_path)
                    deleted += 1
                except OSError:
                    logger.exception("file_delete_failed", extra={"path": report.file_path})

            session.delete(report)

        session.commit()
        logger.info("cleanup_complete", extra={"deleted": deleted, "total": len(old_reports)})
        return {"status": "ok", "deleted": deleted}

    except Exception:
        session.rollback()
        logger.exception("cleanup_error")
        return {"status": "error"}

    finally:
        session.close()
