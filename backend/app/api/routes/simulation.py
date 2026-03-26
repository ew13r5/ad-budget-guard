"""Simulation control API endpoints."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.simulation_log import SimulationLog
from app.models.user import User
from app.schemas.simulation import (
    SimulationLogEntry,
    SimulationLogResponse,
    SimulationPauseResponse,
    SimulationResetResponse,
    SimulationScenarioRequest,
    SimulationScenarioResponse,
    SimulationSpeedRequest,
    SimulationSpeedResponse,
    SimulationStartRequest,
    SimulationStartResponse,
    SimulationStatusResponse,
    SimulationTriggerAnomalyRequest,
    SimulationTriggerAnomalyResponse,
)
from app.simulator.scenarios import get_scenario_by_name

router = APIRouter()


def _get_engine():
    """Get simulator engine instance. Placeholder — wired in section-12."""
    from app.simulator.engine import SimulatorEngine
    # This will be replaced with proper DI in section-12
    raise HTTPException(status_code=503, detail="Simulation engine not initialized")


@router.post("/start", response_model=SimulationStartResponse)
async def start_simulation(
    request: SimulationStartRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        engine = _get_engine()
    except HTTPException:
        # Return mock response until engine is wired
        return SimulationStartResponse(status="running", scenario=request.scenario, speed=1)

    try:
        engine.start(scenario=request.scenario)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    state = engine.state_manager.get_simulation_state()
    return SimulationStartResponse(status=state.status, scenario=state.scenario, speed=state.speed)


@router.post("/pause", response_model=SimulationPauseResponse)
async def pause_simulation(
    current_user: User = Depends(get_current_user),
):
    return SimulationPauseResponse(status="paused")


@router.put("/speed", response_model=SimulationSpeedResponse)
async def set_speed(
    request: SimulationSpeedRequest,
    current_user: User = Depends(get_current_user),
):
    return SimulationSpeedResponse(speed=request.multiplier)


@router.put("/scenario", response_model=SimulationScenarioResponse)
async def set_scenario(
    request: SimulationScenarioRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        get_scenario_by_name(request.scenario)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Unknown scenario: {request.scenario}")

    return SimulationScenarioResponse(scenario=request.scenario, status="running")


@router.post("/trigger-anomaly", response_model=SimulationTriggerAnomalyResponse)
async def trigger_anomaly(
    request: SimulationTriggerAnomalyRequest,
    current_user: User = Depends(get_current_user),
):
    return SimulationTriggerAnomalyResponse(triggered=True, campaign_id=request.campaign_id)


@router.post("/reset", response_model=SimulationResetResponse)
async def reset_simulation(
    current_user: User = Depends(get_current_user),
):
    return SimulationResetResponse(status="stopped", message="Simulation reset complete")


@router.get("/log", response_model=SimulationLogResponse)
async def get_simulation_log(
    event_type: Optional[str] = None,
    campaign_id: Optional[UUID] = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(SimulationLog)
    count_query = select(func.count(SimulationLog.id))

    if event_type:
        query = query.where(SimulationLog.event_type == event_type)
        count_query = count_query.where(SimulationLog.event_type == event_type)
    if campaign_id:
        query = query.where(SimulationLog.campaign_id == campaign_id)
        count_query = count_query.where(SimulationLog.campaign_id == campaign_id)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(SimulationLog.real_time.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    rows = result.scalars().all()

    entries = [
        SimulationLogEntry(
            id=row.id,
            event_type=row.event_type,
            campaign_id=row.campaign_id,
            sim_time=row.sim_time,
            real_time=row.real_time,
            details=row.details,
        )
        for row in rows
    ]

    return SimulationLogResponse(entries=entries, total=total, limit=limit, offset=offset)


@router.get("/status", response_model=SimulationStatusResponse)
async def get_status(
    current_user: User = Depends(get_current_user),
):
    return SimulationStatusResponse(
        status="stopped",
        sim_time=None,
        speed=1,
        scenario="normal",
        tick_count=0,
        campaign_count=0,
    )
