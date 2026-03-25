"""Simulation controls — stub for split 02."""
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.post("/start")
async def start_simulation():
    raise HTTPException(status_code=501, detail="Not yet implemented (split 02)")

@router.post("/stop")
async def stop_simulation():
    raise HTTPException(status_code=501, detail="Not yet implemented (split 02)")

@router.get("/state")
async def get_simulation_state():
    raise HTTPException(status_code=501, detail="Not yet implemented (split 02)")
