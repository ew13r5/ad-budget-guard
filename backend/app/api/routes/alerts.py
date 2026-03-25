"""Alerts — stub for split 05."""
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("")
async def list_alerts():
    raise HTTPException(status_code=501, detail="Not yet implemented (split 05)")

@router.post("/config")
async def configure_alerts():
    raise HTTPException(status_code=501, detail="Not yet implemented (split 05)")
