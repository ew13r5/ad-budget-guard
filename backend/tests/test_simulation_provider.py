"""Tests for SimulationProvider — basic import and interface compliance."""
from app.providers.simulation_provider import SimulationProvider, SyncSimulationProvider
from app.providers.base import AdDataProvider, SyncAdDataProvider


class TestSimulationProviderInterface:
    def test_implements_ad_data_provider(self):
        assert issubclass(SimulationProvider, AdDataProvider)

    def test_has_all_required_async_methods(self):
        methods = ["get_accounts", "get_campaigns", "get_current_spend",
                    "get_campaign_spend", "pause_campaign", "resume_campaign", "get_insights"]
        for m in methods:
            assert hasattr(SimulationProvider, m), f"Missing method: {m}"

    def test_sync_implements_sync_provider(self):
        assert issubclass(SyncSimulationProvider, SyncAdDataProvider)

    def test_sync_has_required_methods(self):
        methods = ["get_current_spend", "get_campaign_spend",
                    "pause_campaign", "resume_campaign", "get_insights"]
        for m in methods:
            assert hasattr(SyncSimulationProvider, m), f"Missing method: {m}"

    def test_constructor_accepts_db_and_redis(self):
        p = SimulationProvider(db=None, redis=None)
        assert p.db is None
        assert p.redis is None

    def test_sync_constructor_accepts_db_and_redis(self):
        p = SyncSimulationProvider(db=None, redis=None)
        assert p.db is None
        assert p.redis is None
