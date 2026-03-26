"""Tests for simulation API schemas and route imports."""
from uuid import uuid4

import pytest

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


class TestSchemas:
    def test_start_request_defaults(self):
        req = SimulationStartRequest()
        assert req.scenario == "normal"

    def test_speed_request_valid(self):
        req = SimulationSpeedRequest(multiplier=10)
        assert req.multiplier == 10

    def test_speed_request_invalid(self):
        with pytest.raises(Exception):
            SimulationSpeedRequest(multiplier=3)

    def test_start_response(self):
        resp = SimulationStartResponse(status="running", scenario="normal", speed=1)
        assert resp.status == "running"

    def test_status_response(self):
        resp = SimulationStatusResponse(
            status="stopped", speed=1, scenario="normal", tick_count=0, campaign_count=0
        )
        assert resp.status == "stopped"

    def test_log_entry(self):
        from datetime import datetime
        entry = SimulationLogEntry(
            id=uuid4(), event_type="pause", sim_time=datetime.now(), real_time=datetime.now()
        )
        assert entry.event_type == "pause"
        assert entry.campaign_id is None

    def test_log_response(self):
        resp = SimulationLogResponse(entries=[], total=0, limit=50, offset=0)
        assert resp.total == 0

    def test_trigger_anomaly_request(self):
        cid = uuid4()
        req = SimulationTriggerAnomalyRequest(campaign_id=cid)
        assert req.campaign_id == cid

    def test_scenario_request(self):
        req = SimulationScenarioRequest(scenario="hack_simulation")
        assert req.scenario == "hack_simulation"

    def test_reset_response(self):
        resp = SimulationResetResponse(status="stopped", message="done")
        assert resp.status == "stopped"


class TestRouteImports:
    def test_router_importable(self):
        from app.api.routes.simulation import router
        assert router is not None

    def test_router_has_expected_routes(self):
        from app.api.routes.simulation import router
        paths = {r.path for r in router.routes}
        assert "/start" in paths
        assert "/pause" in paths
        assert "/speed" in paths
        assert "/scenario" in paths
        assert "/trigger-anomaly" in paths
        assert "/reset" in paths
        assert "/log" in paths
        assert "/status" in paths
