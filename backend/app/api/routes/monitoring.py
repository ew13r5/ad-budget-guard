"""Monitoring — stub for split 03."""
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/spend")
async def get_spend():
    raise HTTPException(status_code=501, detail="Not yet implemented (split 03)")

@router.get("/forecast")
async def get_forecast():
    raise HTTPException(status_code=501, detail="Not yet implemented (split 03)")
