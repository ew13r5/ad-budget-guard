from __future__ import annotations

from dataclasses import dataclass, field

from app.simulator.constants import (
    PATTERN_ANOMALY,
    PATTERN_PEAK_HOURS,
    PATTERN_STEADY,
)


@dataclass
class CampaignScenarioConfig:
    campaign_filter: str
    pattern_type: str
    initial_spend_percent: float
    volatility: float = 1.0


@dataclass
class ScenarioConfig:
    name: str
    description: str
    campaign_configs: list[CampaignScenarioConfig] = field(default_factory=list)


SCENARIOS: dict[str, ScenarioConfig] = {
    "normal": ScenarioConfig(
        name="normal",
        description="All campaigns spending normally within budget",
        campaign_configs=[
            CampaignScenarioConfig("all", PATTERN_STEADY, 0.0, 1.0),
        ],
    ),
    "approaching_limit": ScenarioConfig(
        name="approaching_limit",
        description="Selected campaigns approaching daily budget limits",
        campaign_configs=[
            CampaignScenarioConfig("ShopNow E-commerce", PATTERN_PEAK_HOURS, 0.75, 1.2),
            CampaignScenarioConfig("all", PATTERN_STEADY, 0.0, 1.0),
        ],
    ),
    "budget_exceeded": ScenarioConfig(
        name="budget_exceeded",
        description="Campaigns will exceed budget, triggering auto-pause",
        campaign_configs=[
            CampaignScenarioConfig("NewBrand Startup", PATTERN_PEAK_HOURS, 0.9, 1.5),
            CampaignScenarioConfig("all", PATTERN_STEADY, 0.0, 1.0),
        ],
    ),
    "hack_simulation": ScenarioConfig(
        name="hack_simulation",
        description="Anomalous spend spikes simulating compromised campaigns",
        campaign_configs=[
            CampaignScenarioConfig("MegaCorp Enterprise", PATTERN_ANOMALY, 0.0, 2.0),
            CampaignScenarioConfig("all", PATTERN_STEADY, 0.0, 1.0),
        ],
    ),
}


def get_scenario_by_name(name: str) -> ScenarioConfig:
    """Return scenario config by name. Raises ValueError if not found."""
    if name not in SCENARIOS:
        available = ", ".join(SCENARIOS.keys())
        raise ValueError(f"Unknown scenario '{name}'. Available: {available}")
    return SCENARIOS[name]
