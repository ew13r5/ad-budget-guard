"""WebSocket endpoint for real-time monitoring updates."""
from __future__ import annotations

import asyncio
import json
from typing import Dict, Optional
from uuid import uuid4

import structlog
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

logger = structlog.get_logger(__name__)

MONITORING_PUBSUB_PATTERN = "monitoring:updates:*"
WS_QUEUE_MAX_SIZE = 100
WS_CLOSE_CODE_AUTH_FAILED = 4001

ws_monitoring_router = APIRouter()


class MonitoringConnectionManager:
    """WebSocket connection manager for monitoring updates with per-client queues."""

    def __init__(self, queue_max_size: int = WS_QUEUE_MAX_SIZE):
        self.active_connections: Dict[str, WebSocket] = {}
        self._queues: Dict[str, asyncio.Queue] = {}
        self._sender_tasks: Dict[str, asyncio.Task] = {}
        self._queue_max_size = queue_max_size

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self._queues[client_id] = asyncio.Queue()
        self._sender_tasks[client_id] = asyncio.create_task(
            self._client_sender(client_id)
        )

    async def disconnect(self, client_id: str) -> None:
        task = self._sender_tasks.pop(client_id, None)
        if task:
            task.cancel()
        self.active_connections.pop(client_id, None)
        self._queues.pop(client_id, None)

    async def broadcast(self, message: dict) -> None:
        for client_id, queue in list(self._queues.items()):
            if queue.qsize() >= self._queue_max_size:
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                pass

    async def _client_sender(self, client_id: str) -> None:
        ws = self.active_connections.get(client_id)
        queue = self._queues.get(client_id)
        if not ws or not queue:
            return

        try:
            while True:
                message = await queue.get()
                await ws.send_json(message)
        except (WebSocketDisconnect, Exception):
            await self.disconnect(client_id)


monitoring_manager = MonitoringConnectionManager()


async def monitoring_pubsub_subscriber(redis_url: str) -> None:
    """Background task: subscribe to monitoring:updates:*, broadcast to manager."""
    import redis.asyncio as aioredis

    backoff = 1
    while True:
        try:
            client = aioredis.from_url(redis_url)
            pubsub = client.pubsub()
            await pubsub.psubscribe(MONITORING_PUBSUB_PATTERN)
            backoff = 1

            while True:
                msg = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0,
                )
                if msg and msg["type"] == "pmessage":
                    data = json.loads(msg["data"])
                    data["type"] = "monitoring_update"
                    await monitoring_manager.broadcast(data)

        except asyncio.CancelledError:
            try:
                await pubsub.punsubscribe(MONITORING_PUBSUB_PATTERN)
                await client.close()
            except Exception:
                pass
            raise
        except Exception:
            logger.warning("monitoring_pubsub_reconnect", backoff=backoff)
            await asyncio.sleep(min(backoff, 30))
            backoff *= 2


@ws_monitoring_router.websocket("/ws/monitoring")
async def monitoring_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(default=None),
):
    if not token:
        await websocket.close(code=WS_CLOSE_CODE_AUTH_FAILED)
        return

    from app.services.token_service import verify_access_token

    user_id = verify_access_token(token)
    if not user_id:
        await websocket.close(code=WS_CLOSE_CODE_AUTH_FAILED)
        return

    client_id = f"mon:{user_id}:{uuid4().hex[:8]}"
    await monitoring_manager.connect(websocket, client_id)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        await monitoring_manager.disconnect(client_id)
