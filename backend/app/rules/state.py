"""Redis-backed consecutive trigger state manager."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from uuid import UUID

import redis

logger = logging.getLogger(__name__)

DEFAULT_TTL = 1800  # 30 minutes


class ConsecutiveStateManager:
    """Tracks consecutive rule trigger counts in Redis."""

    def __init__(self, client: redis.Redis, ttl: int = DEFAULT_TTL):
        self._client = client
        self._ttl = ttl

    def _key(self, rule_id: UUID, entity_id: UUID) -> str:
        return f"rule_state:{rule_id}:{entity_id}"

    def increment(self, rule_id: UUID, entity_id: UUID) -> int:
        key = self._key(rule_id, entity_id)
        try:
            raw = self._client.get(key)
            if raw:
                data = json.loads(raw)
                count = data.get("count", 0) + 1
            else:
                count = 1
            payload = json.dumps({
                "count": count,
                "last_checked": datetime.now(timezone.utc).isoformat(),
            })
            self._client.set(key, payload, ex=self._ttl)
            return count
        except (redis.ConnectionError, redis.RedisError):
            logger.exception("Redis error in increment for %s", key)
            return 0

    def reset(self, rule_id: UUID, entity_id: UUID) -> None:
        key = self._key(rule_id, entity_id)
        try:
            self._client.delete(key)
        except (redis.ConnectionError, redis.RedisError):
            logger.exception("Redis error in reset for %s", key)

    def get_count(self, rule_id: UUID, entity_id: UUID) -> int:
        key = self._key(rule_id, entity_id)
        try:
            raw = self._client.get(key)
            if not raw:
                return 0
            data = json.loads(raw)
            return data.get("count", 0)
        except (redis.ConnectionError, redis.RedisError):
            logger.exception("Redis error in get_count for %s", key)
            return 0
