"""Tests for simulation scenario presets."""
import pytest

from app.simulator.scenarios import (
    CampaignScenarioConfig,
    ScenarioConfig,
    SCENARIOS,
    get_scenario_by_name,
)


class TestScenarioConfig:
    def test_scenario_config_has_required_fields(self):
        sc = ScenarioConfig(name="test", description="desc", campaign_configs=[])
        assert sc.name == "test"
        assert sc.description == "desc"
        assert sc.campaign_configs == []

    def test_campaign_scenario_config_has_required_fields(self):
        c = CampaignScenarioConfig("all", "steady", 0.5, 1.2)
        assert c.campaign_filter == "all"
        assert c.pattern_type == "steady"
        assert c.initial_spend_percent == 0.5
        assert c.volatility == 1.2

    def test_campaign_scenario_config_defaults(self):
        c = CampaignScenarioConfig("all", "steady", 0.0)
        assert c.volatility == 1.0


class TestPresetScenarios:
    def test_normal_scenario_assigns_steady_or_peak_hours(self):
        sc = SCENARIOS["normal"]
        for cfg in sc.campaign_configs:
            assert cfg.pattern_type in ("steady", "peak_hours")

    def test_normal_scenario_initial_spend_zero(self):
        sc = SCENARIOS["normal"]
        for cfg in sc.campaign_configs:
            assert cfg.initial_spend_percent == 0.0

    def test_approaching_limit_initial_spend_70_to_80(self):
        sc = SCENARIOS["approaching_limit"]
        target = [c for c in sc.campaign_configs if c.campaign_filter != "all"]
        assert len(target) >= 1
        for cfg in target:
            assert 0.7 <= cfg.initial_spend_percent <= 0.8

    def test_budget_exceeded_initial_spend_90(self):
        sc = SCENARIOS["budget_exceeded"]
        target = [c for c in sc.campaign_configs if c.campaign_filter != "all"]
        assert len(target) >= 1
        for cfg in target:
            assert cfg.initial_spend_percent == 0.9

    def test_hack_simulation_assigns_anomaly_pattern(self):
        sc = SCENARIOS["hack_simulation"]
        target = [c for c in sc.campaign_configs if c.campaign_filter != "all"]
        assert len(target) >= 1
        for cfg in target:
            assert cfg.pattern_type == "anomaly"

    def test_all_scenarios_have_nonempty_campaign_configs(self):
        for name, sc in SCENARIOS.items():
            assert len(sc.campaign_configs) > 0, f"Scenario '{name}' has empty configs"

    def test_all_preset_scenario_names(self):
        expected = {"normal", "approaching_limit", "budget_exceeded", "hack_simulation"}
        assert set(SCENARIOS.keys()) == expected


class TestGetScenarioByName:
    def test_returns_correct_config_for_valid_name(self):
        sc = get_scenario_by_name("normal")
        assert sc.name == "normal"

    def test_raises_value_error_for_unknown_name(self):
        with pytest.raises(ValueError, match="Unknown scenario"):
            get_scenario_by_name("nonexistent")

    def test_name_lookup_is_case_sensitive(self):
        with pytest.raises(ValueError):
            get_scenario_by_name("Normal")
