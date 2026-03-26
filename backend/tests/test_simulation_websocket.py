"""Tests for SimulationConnectionManager."""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.simulator.websocket import SimulationConnectionManager


@pytest.fixture
def mgr():
    return SimulationConnectionManager(queue_max_size=5)


class TestConnectionManager:
    @pytest.mark.asyncio
    async def test_connect_adds_client(self, mgr):
        ws = AsyncMock()
        await mgr.connect(ws, "client1")
        assert "client1" in mgr.active_connections

    @pytest.mark.asyncio
    async def test_disconnect_removes_client(self, mgr):
        ws = AsyncMock()
        await mgr.connect(ws, "client1")
        await mgr.disconnect("client1")
        assert "client1" not in mgr.active_connections
        assert "client1" not in mgr._queues

    @pytest.mark.asyncio
    async def test_broadcast_enqueues_to_all(self, mgr):
        ws1 = AsyncMock()
        ws2 = AsyncMock()
        await mgr.connect(ws1, "c1")
        await mgr.connect(ws2, "c2")

        await mgr.broadcast({"type": "tick_update"})

        assert mgr._queues["c1"].qsize() == 1
        assert mgr._queues["c2"].qsize() == 1

    @pytest.mark.asyncio
    async def test_backpressure_drops_oldest(self, mgr):
        ws = AsyncMock()
        await mgr.connect(ws, "c1")

        for i in range(7):
            await mgr.broadcast({"i": i})

        # Max size is 5, so oldest should be dropped
        assert mgr._queues["c1"].qsize() == 5

    @pytest.mark.asyncio
    async def test_ws_router_importable(self):
        from app.simulator.websocket import ws_router
        assert ws_router is not None

    @pytest.mark.asyncio
    async def test_manager_singleton(self):
        from app.simulator.websocket import manager
        assert isinstance(manager, SimulationConnectionManager)
