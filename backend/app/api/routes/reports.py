"""Reports — stub for split 05."""
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/daily")
async def daily_report():
    raise HTTPException(status_code=501, detail="Not yet implemented (split 05)")

@router.get("/monthly")
async def monthly_report():
    raise HTTPException(status_code=501, detail="Not yet implemented (split 05)")
