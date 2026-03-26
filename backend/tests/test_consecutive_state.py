"""Tests for ConsecutiveStateManager (Redis-backed)."""
from uuid import uuid4

import pytest

from app.rules.state import ConsecutiveStateManager

pytestmark = pytest.mark.usefixtures("redis_client")


@pytest.fixture
def state_manager(redis_client):
    return ConsecutiveStateManager(redis_client, ttl=1800)


class TestConsecutiveStateManager:
    def test_increment_returns_1_on_first_call(self, state_manager):
        rule_id, entity_id = uuid4(), uuid4()
        assert state_manager.increment(rule_id, entity_id) == 1

    def test_increment_returns_2_on_second_call(self, state_manager):
        rule_id, entity_id = uuid4(), uuid4()
        state_manager.increment(rule_id, entity_id)
        assert state_manager.increment(rule_id, entity_id) == 2

    def test_reset_sets_count_to_zero(self, state_manager):
        rule_id, entity_id = uuid4(), uuid4()
        state_manager.increment(rule_id, entity_id)
        state_manager.increment(rule_id, entity_id)
        state_manager.reset(rule_id, entity_id)
        assert state_manager.get_count(rule_id, entity_id) == 0

    def test_get_count_returns_0_for_nonexistent_key(self, state_manager):
        assert state_manager.get_count(uuid4(), uuid4()) == 0

    def test_increment_resets_ttl(self, state_manager, redis_client):
        rule_id, entity_id = uuid4(), uuid4()
        state_manager.increment(rule_id, entity_id)
        key = f"rule_state:{rule_id}:{entity_id}"
        ttl1 = redis_client.ttl(key)
        assert ttl1 > 0

        state_manager.increment(rule_id, entity_id)
        ttl2 = redis_client.ttl(key)
        assert ttl2 > 0
        assert ttl2 >= ttl1 - 1  # TTL refreshed

    def test_different_pairs_tracked_independently(self, state_manager):
        rule_a, rule_b = uuid4(), uuid4()
        entity_x, entity_y = uuid4(), uuid4()

        state_manager.increment(rule_a, entity_x)
        state_manager.increment(rule_a, entity_x)

        assert state_manager.get_count(rule_a, entity_x) == 2
        assert state_manager.get_count(rule_b, entity_x) == 0
        assert state_manager.get_count(rule_a, entity_y) == 0
