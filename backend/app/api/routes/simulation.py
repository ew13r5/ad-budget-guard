"""Simulation control API endpoints."""
from __future__ import annotations

import asyncio
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
from app.simulator.constants import (
    FORCED_ANOMALY_TTL,
    SIM_FORCED_ANOMALY_PREFIX,
    SIM_SPEND_PREFIX,
)
from app.simulator.scenarios import get_scenario_by_name
from app.simulator.state import SimulationStateManager

router = APIRouter()


def _get_state_manager() -> SimulationStateManager:
    """Create a StateManager connected to Redis."""
    import redis as sync_redis
    from app.config import get_settings

    settings = get_settings()
    client = sync_redis.from_url(settings.redis_url)
    return SimulationStateManager(redis=client)


@router.post("/start", response_model=SimulationStartResponse)
async def start_simulation(
    request: SimulationStartRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        get_scenario_by_name(request.scenario)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Unknown scenario: {request.scenario}")

    sm = _get_state_manager()
    await asyncio.to_thread(
        sm.set_simulation_state, status="running", scenario=request.scenario,
    )
    state = await asyncio.to_thread(sm.get_simulation_state)
    return SimulationStartResponse(
        status=state.status, scenario=state.scenario, speed=state.speed,
    )


@router.post("/pause", response_model=SimulationPauseResponse)
async def pause_simulation(
    current_user: User = Depends(get_current_user),
):
    sm = _get_state_manager()
    await asyncio.to_thread(sm.set_simulation_state, status="paused")
    return SimulationPauseResponse(status="paused")


@router.put("/speed", response_model=SimulationSpeedResponse)
async def set_speed(
    request: SimulationSpeedRequest,
    current_user: User = Depends(get_current_user),
):
    sm = _get_state_manager()
    await asyncio.to_thread(sm.set_simulation_state, speed=request.multiplier)
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

    sm = _get_state_manager()
    await asyncio.to_thread(sm.set_simulation_state, scenario=request.scenario)
    return SimulationScenarioResponse(scenario=request.scenario, status="running")


@router.post("/trigger-anomaly", response_model=SimulationTriggerAnomalyResponse)
async def trigger_anomaly(
    request: SimulationTriggerAnomalyRequest,
    current_user: User = Depends(get_current_user),
):
    sm = _get_state_manager()
    key = f"{SIM_FORCED_ANOMALY_PREFIX}{request.campaign_id}"
    await asyncio.to_thread(sm.redis.setex, key, FORCED_ANOMALY_TTL, "1")
    return SimulationTriggerAnomalyResponse(triggered=True, campaign_id=request.campaign_id)


@router.post("/reset", response_model=SimulationResetResponse)
async def reset_simulation(
    current_user: User = Depends(get_current_user),
):
    sm = _get_state_manager()
    await asyncio.to_thread(sm.reset_state)
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
    sm = _get_state_manager()
    state = await asyncio.to_thread(sm.get_simulation_state)

    # Count active campaigns
    try:
        keys = await asyncio.to_thread(
            sm.redis.keys, f"{SIM_SPEND_PREFIX}*",
        )
        campaign_count = len(keys)
    except Exception:
        campaign_count = 0

    return SimulationStatusResponse(
        status=state.status,
        sim_time=state.sim_time,
        speed=state.speed,
        scenario=state.scenario,
        tick_count=state.tick_count,
        campaign_count=campaign_count,
    )
