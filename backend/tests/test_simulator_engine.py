"""Tests for SimulatorEngine."""
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import fakeredis
import pytest

from app.simulator.constants import SIM_FORCED_ANOMALY_PREFIX, SIM_STATE_KEY, SIM_TICK_LOCK_KEY
from app.simulator.engine import SimulatorEngine, TickResult
from app.simulator.state import SimulationStateManager


@pytest.fixture
def redis_client():
    return fakeredis.FakeRedis()


@pytest.fixture
def state_mgr(redis_client):
    return SimulationStateManager(redis=redis_client)


@pytest.fixture
def engine(state_mgr, redis_client):
    e = SimulatorEngine(state_manager=state_mgr, redis=redis_client)
    campaigns = [
        {"id": uuid4(), "daily_budget": Decimal("240"), "status": "ACTIVE", "account_name": "TechStart Agency"},
        {"id": uuid4(), "daily_budget": Decimal("100"), "status": "ACTIVE", "account_name": "ShopNow E-commerce"},
    ]
    e.set_campaigns(campaigns)
    return e


class TestTick:
    def test_advances_sim_time(self, engine, state_mgr):
        engine.start("normal")
        state_before = state_mgr.get_simulation_state()
        engine.tick()
        state_after = state_mgr.get_simulation_state()
        assert state_after.sim_time > state_before.sim_time

    def test_skips_paused_campaigns(self, engine, state_mgr):
        engine.start("normal")
        engine._campaigns[1]["status"] = "PAUSED"
        results = engine.tick()
        campaign_ids = {r.campaign_id for r in results}
        assert engine._campaigns[1]["id"] not in campaign_ids

    def test_publishes_to_pubsub(self, engine, redis_client):
        engine.start("normal")
        ps = redis_client.pubsub()
        ps.subscribe("simulation:updates")
        ps.get_message()  # subscribe confirmation

        engine.tick()
        msg = ps.get_message()
        assert msg is not None
        assert msg["type"] == "message"

    def test_increments_tick_count(self, engine, state_mgr):
        engine.start("normal")
        engine.tick()
        assert state_mgr.get_simulation_state().tick_count == 1
        engine.tick()
        assert state_mgr.get_simulation_state().tick_count == 2

    def test_lock_prevents_concurrent(self, engine, redis_client):
        engine.start("normal")
        redis_client.set(SIM_TICK_LOCK_KEY, "1", ex=5)
        results = engine.tick()
        assert results == []

    def test_per_campaign_error_isolation(self, engine, state_mgr):
        engine.start("normal")
        # Corrupt one campaign's budget to cause error
        engine._campaigns[0]["daily_budget"] = "not_a_decimal"
        results = engine.tick()
        # Second campaign should still process
        assert len(results) >= 1

    def test_returns_tick_results(self, engine):
        engine.start("normal")
        results = engine.tick()
        assert len(results) > 0
        assert isinstance(results[0], TickResult)
        assert results[0].delta >= Decimal("0")


class TestLifecycle:
    def test_start_sets_running(self, engine, state_mgr):
        engine.start("normal")
        assert state_mgr.get_simulation_state().status == "running"

    def test_start_default_scenario(self, engine, state_mgr):
        engine.start()
        assert state_mgr.get_simulation_state().scenario == "normal"

    def test_pause_preserves_state(self, engine, state_mgr):
        engine.start("normal")
        engine.tick()
        engine.pause()
        state = state_mgr.get_simulation_state()
        assert state.status == "paused"
        assert state.tick_count == 1

    def test_reset_clears_state(self, engine, state_mgr):
        engine.start("normal")
        engine.tick()
        engine.reset()
        state = state_mgr.get_simulation_state()
        assert state.status == "stopped"

    def test_set_speed_valid(self, engine, state_mgr):
        engine.start("normal")
        engine.set_speed(10)
        assert state_mgr.get_simulation_state().speed == 10

    def test_set_speed_invalid(self, engine):
        with pytest.raises(ValueError):
            engine.set_speed(3)

    def test_trigger_anomaly(self, engine, redis_client):
        cid = engine._campaigns[0]["id"]
        engine.trigger_anomaly(cid)
        key = f"{SIM_FORCED_ANOMALY_PREFIX}{cid}"
        assert redis_client.get(key) is not None
