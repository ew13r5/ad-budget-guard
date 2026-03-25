"""Budget rules CRUD — stub for split 03."""
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("")
async def list_rules():
    raise HTTPException(status_code=501, detail="Not yet implemented (split 03)")

@router.post("")
async def create_rule():
    raise HTTPException(status_code=501, detail="Not yet implemented (split 03)")
