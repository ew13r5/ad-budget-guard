"""Reports API — generate, download, list reports."""
from __future__ import annotations

import os
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.ad_account import user_accounts
from app.models.report import Report
from app.models.user import User
from app.schemas.report import (
    ReportGenerateRequest,
    ReportListResponse,
    ReportResponse,
)

router = APIRouter()


async def _check_account_access(
    account_id: UUID, user: User, db: AsyncSession,
) -> None:
    result = await db.execute(
        select(user_accounts).where(
            user_accounts.c.user_id == user.id,
            user_accounts.c.account_id == account_id,
        )
    )
    if result.first() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="No access",
        )


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_report(
    body: ReportGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Enqueue report generation as a background task."""
    await _check_account_access(body.account_id, current_user, db)

    from app.tasks.reporting import generate_report_async

    task = generate_report_async.delay(
        account_id=str(body.account_id),
        report_type=body.report_type,
        report_format=body.report_format,
        date_from=body.date_from.isoformat() if body.date_from else None,
        date_to=body.date_to.isoformat() if body.date_to else None,
    )

    return {"status": "accepted", "task_id": task.id}


@router.get("/{report_id}/download")
async def download_report(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download a generated report PDF."""
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found",
        )

    await _check_account_access(report.account_id, current_user, db)

    if not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report file not found on disk",
        )

    filename = os.path.basename(report.file_path)
    return FileResponse(
        report.file_path,
        media_type="application/pdf",
        filename=filename,
    )


@router.get("/list", response_model=ReportListResponse)
async def list_reports(
    account_id: Optional[UUID] = Query(None),
    report_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List generated reports with pagination."""
    if account_id:
        await _check_account_access(account_id, current_user, db)

    query = select(Report)
    count_query = select(func.count(Report.id))

    if account_id:
        query = query.where(Report.account_id == account_id)
        count_query = count_query.where(Report.account_id == account_id)
    if report_type:
        query = query.where(Report.report_type == report_type)
        count_query = count_query.where(Report.report_type == report_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(Report.generated_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    reports = result.scalars().all()

    return ReportListResponse(
        reports=[ReportResponse.model_validate(r) for r in reports],
        total=total,
    )
