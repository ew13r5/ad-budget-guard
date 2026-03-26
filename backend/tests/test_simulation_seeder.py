"""Tests for SimulationSeeder — basic validation without DB."""
import uuid
from decimal import Decimal

from app.seed.simulation_seeder import (
    ACCOUNT_DEFINITIONS,
    SEED_NAMESPACE,
    SeedResult,
    _deterministic_id,
)


class TestSeederDefinitions:
    def test_four_accounts_defined(self):
        assert len(ACCOUNT_DEFINITIONS) == 4

    def test_total_38_campaigns(self):
        total = sum(len(a["campaigns"]) for a in ACCOUNT_DEFINITIONS)
        assert total == 38

    def test_campaign_budgets_in_range(self):
        for acct in ACCOUNT_DEFINITIONS:
            for camp in acct["campaigns"]:
                assert Decimal("50") <= camp["daily_budget"] <= Decimal("500")

    def test_deterministic_uuids(self):
        id1 = _deterministic_id("test:name")
        id2 = _deterministic_id("test:name")
        assert id1 == id2

    def test_different_names_different_uuids(self):
        id1 = _deterministic_id("account:TechStart Agency")
        id2 = _deterministic_id("account:ShopNow E-commerce")
        assert id1 != id2

    def test_seed_result_dataclass(self):
        r = SeedResult(accounts_created=4, campaigns_created=38, snapshots_created=27000, ad_sets_created=0)
        assert r.accounts_created == 4

    def test_account_names_match_scenarios(self):
        names = {a["name"] for a in ACCOUNT_DEFINITIONS}
        assert "TechStart Agency" in names
        assert "ShopNow E-commerce" in names
        assert "NewBrand Startup" in names
        assert "MegaCorp Enterprise" in names

    def test_seeder_class_importable(self):
        from app.seed.simulation_seeder import SimulationSeeder
        assert SimulationSeeder is not None
