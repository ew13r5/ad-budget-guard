"""Tests for SimulationStateManager."""
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import fakeredis
import pytest

from app.simulator.state import SimulationStateManager, SimState, CampaignSpendState
from app.simulator.constants import SIM_STATE_KEY, SIM_SPEND_PREFIX


@pytest.fixture
def redis_client():
    return fakeredis.FakeRedis()


@pytest.fixture
def state_mgr(redis_client):
    return SimulationStateManager(redis=redis_client)


class TestGetSimulationState:
    def test_reads_from_redis(self, redis_client, state_mgr):
        redis_client.hset(SIM_STATE_KEY, mapping={
            "sim_time": "2024-01-15T14:30:00",
            "speed": "10",
            "status": "running",
            "tick_count": "42",
            "scenario": "normal",
        })
        state = state_mgr.get_simulation_state()
        assert state.speed == 10
        assert state.status == "running"
        assert state.tick_count == 42
        assert state.scenario == "normal"

    def test_defaults_when_empty(self, state_mgr):
        state = state_mgr.get_simulation_state()
        assert state.status == "stopped"
        assert state.speed == 1
        assert state.tick_count == 0


class TestSetSimulationState:
    def test_sets_fields(self, redis_client, state_mgr):
        state_mgr.set_simulation_state(status="running", speed=5)
        data = redis_client.hgetall(SIM_STATE_KEY)
        decoded = {k.decode(): v.decode() for k, v in data.items()}
        assert decoded["status"] == "running"
        assert decoded["speed"] == "5"


class TestUpdateCampaignSpend:
    def test_atomic_increment(self, redis_client, state_mgr):
        cid = uuid4()
        key = f"{SIM_SPEND_PREFIX}{cid}"
        redis_client.hset(key, mapping={"total_cents": "10000", "total_today": "100.00"})

        result = state_mgr.update_campaign_spend(cid, Decimal("25.50"))
        assert result.total_today == Decimal("125.50")

    def test_preserves_decimal_precision(self, state_mgr):
        cid = uuid4()
        for _ in range(100):
            state_mgr.update_campaign_spend(cid, Decimal("0.01"))
        result = state_mgr.get_campaign_spend(cid)
        assert result.total_today == Decimal("1.00")

    def test_initializes_from_zero(self, state_mgr):
        cid = uuid4()
        result = state_mgr.update_campaign_spend(cid, Decimal("50.00"))
        assert result.total_today == Decimal("50.00")


class TestGetCampaignSpend:
    def test_returns_none_when_missing(self, state_mgr):
        assert state_mgr.get_campaign_spend(uuid4()) is None

    def test_reads_existing(self, redis_client, state_mgr):
        cid = uuid4()
        key = f"{SIM_SPEND_PREFIX}{cid}"
        redis_client.hset(key, mapping={
            "total_today": "75.50",
            "total_cents": "7550",
            "last_delta": "2.30",
            "last_tick": "2024-01-15T14:30:00",
        })
        result = state_mgr.get_campaign_spend(cid)
        assert result.total_today == Decimal("75.50")
        assert result.last_delta == Decimal("2.30")


class TestResetState:
    def test_clears_all_simulation_keys(self, redis_client, state_mgr):
        redis_client.set("simulation:state", "x")
        redis_client.set(f"simulation:spend:{uuid4()}", "y")
        redis_client.set("other:key", "z")

        state_mgr.reset_state()

        # simulation keys gone
        keys = [k.decode() for k in redis_client.keys("simulation:*")]
        assert len(keys) == 0
        # other keys preserved
        assert redis_client.get("other:key") is not None
