from __future__ import annotations

from datetime import datetime
from typing import Any, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel


class SimulationStartRequest(BaseModel):
    scenario: str = "normal"


class SimulationStartResponse(BaseModel):
    status: str
    scenario: str
    speed: int


class SimulationPauseResponse(BaseModel):
    status: str


class SimulationSpeedRequest(BaseModel):
    multiplier: Literal[1, 5, 10]


class SimulationSpeedResponse(BaseModel):
    speed: int


class SimulationScenarioRequest(BaseModel):
    scenario: str


class SimulationScenarioResponse(BaseModel):
    scenario: str
    status: str


class SimulationTriggerAnomalyRequest(BaseModel):
    campaign_id: UUID


class SimulationTriggerAnomalyResponse(BaseModel):
    triggered: bool
    campaign_id: UUID


class SimulationResetResponse(BaseModel):
    status: str
    message: str


class SimulationStatusResponse(BaseModel):
    status: str
    sim_time: Optional[datetime] = None
    speed: int
    scenario: str
    tick_count: int
    campaign_count: int


class SimulationLogEntry(BaseModel):
    id: UUID
    event_type: str
    campaign_id: Optional[UUID] = None
    sim_time: datetime
    real_time: datetime
    details: Optional[dict[str, Any]] = None


class SimulationLogResponse(BaseModel):
    entries: List[SimulationLogEntry]
    total: int
    limit: int
    offset: int
