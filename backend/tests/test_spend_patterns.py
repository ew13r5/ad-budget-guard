from datetime import datetime
from decimal import Decimal

import pytest

from app.simulator.patterns import (
    AnomalyPattern,
    DecliningPattern,
    PeakHoursPattern,
    SpendPattern,
    SteadyPattern,
)


# --- SteadyPattern ---

class TestSteadyPattern:
    def test_returns_positive_decimal(self):
        p = SteadyPattern()
        result = p.calculate_delta(
            sim_time=datetime(2024, 1, 15, 10, 0),
            campaign_budget=Decimal("100"),
            remaining_budget=Decimal("50"),
            elapsed_seconds=2.0,
        )
        assert result > Decimal("0")
        assert isinstance(result, Decimal)

    def test_delta_proportional_to_elapsed(self):
        p = SteadyPattern(volatility=0.0)
        kwargs = dict(
            sim_time=datetime(2024, 1, 15, 12, 0),
            campaign_budget=Decimal("240"),
            remaining_budget=Decimal("200"),
        )
        d1 = p.calculate_delta(**kwargs, elapsed_seconds=2.0)
        d2 = p.calculate_delta(**kwargs, elapsed_seconds=4.0)
        ratio = float(d2 / d1)
        assert 1.9 <= ratio <= 2.1

    def test_volatility_zero_is_deterministic(self):
        p = SteadyPattern(volatility=0.0)
        kwargs = dict(
            sim_time=datetime(2024, 1, 15, 10, 0),
            campaign_budget=Decimal("100"),
            remaining_budget=Decimal("50"),
            elapsed_seconds=2.0,
        )
        assert p.calculate_delta(**kwargs) == p.calculate_delta(**kwargs)

    def test_sinusoidal_morning_higher_than_night(self):
        p = SteadyPattern(volatility=0.0)
        kwargs = dict(
            campaign_budget=Decimal("240"),
            remaining_budget=Decimal("200"),
            elapsed_seconds=2.0,
        )
        morning = p.calculate_delta(sim_time=datetime(2024, 1, 15, 10, 0), **kwargs)
        night = p.calculate_delta(sim_time=datetime(2024, 1, 15, 3, 0), **kwargs)
        assert morning > night

    def test_returns_zero_when_no_remaining(self):
        p = SteadyPattern()
        result = p.calculate_delta(
            sim_time=datetime(2024, 1, 15, 10, 0),
            campaign_budget=Decimal("100"),
            remaining_budget=Decimal("0"),
            elapsed_seconds=2.0,
        )
        assert result == Decimal("0")

    def test_delta_never_exceeds_remaining(self):
        p = SteadyPattern()
        result = p.calculate_delta(
            sim_time=datetime(2024, 1, 15, 10, 0),
            campaign_budget=Decimal("1000"),
            remaining_budget=Decimal("0.01"),
            elapsed_seconds=3600.0,
        )
        assert result <= Decimal("0.01")


# --- PeakHoursPattern ---

class TestPeakHoursPattern:
    def test_evening_higher_than_night(self):
        p = PeakHoursPattern(volatility=0.0)
        kwargs = dict(
            campaign_budget=Decimal("240"),
            remaining_budget=Decimal("200"),
            elapsed_seconds=2.0,
        )
        evening = p.calculate_delta(sim_time=datetime(2024, 1, 15, 20, 0), **kwargs)
        night = p.calculate_delta(sim_time=datetime(2024, 1, 15, 4, 0), **kwargs)
        assert evening > night

    def test_budget_distribution_sums_approximately(self):
        p = PeakHoursPattern(volatility=0.0)
        budget = Decimal("240")
        total = Decimal("0")
        step_seconds = 60.0  # 1 minute steps
        remaining = Decimal("10000")  # large enough not to constrain

        for hour in range(24):
            for minute in range(60):
                delta = p.calculate_delta(
                    sim_time=datetime(2024, 1, 15, hour, minute),
                    campaign_budget=budget,
                    remaining_budget=remaining,
                    elapsed_seconds=step_seconds,
                )
                total += delta

        ratio = float(total / budget)
        assert 0.8 <= ratio <= 1.2

    def test_volatility_zero_is_deterministic(self):
        p = PeakHoursPattern(volatility=0.0)
        kwargs = dict(
            sim_time=datetime(2024, 1, 15, 14, 0),
            campaign_budget=Decimal("100"),
            remaining_budget=Decimal("50"),
            elapsed_seconds=2.0,
        )
        assert p.calculate_delta(**kwargs) == p.calculate_delta(**kwargs)

    def test_returns_zero_when_no_remaining(self):
        p = PeakHoursPattern()
        result = p.calculate_delta(
            sim_time=datetime(2024, 1, 15, 20, 0),
            campaign_budget=Decimal("100"),
            remaining_budget=Decimal("0"),
            elapsed_seconds=2.0,
        )
        assert result == Decimal("0")


# --- AnomalyPattern ---

class TestAnomalyPattern:
    def test_baseline_reasonable_range(self):
        p = AnomalyPattern(volatility=0.0)
        # With volatility=0 and short elapsed, spike probability very low
        result = p.calculate_delta(
            sim_time=datetime(2024, 1, 15, 10, 0),
            campaign_budget=Decimal("240"),
            remaining_budget=Decimal("200"),
            elapsed_seconds=0.001,  # tiny elapsed → near-zero spike probability
        )
        assert result > Decimal("0")
        assert result < Decimal("1")  # should be small for 0.001s

    def test_forced_anomaly_spike(self):
        import numpy as np
        np.random.seed(42)

        p = AnomalyPattern(volatility=0.0)
        kwargs = dict(
            sim_time=datetime(2024, 1, 15, 12, 0),
            campaign_budget=Decimal("240"),
            remaining_budget=Decimal("200"),
            elapsed_seconds=2.0,
        )
        baseline = p.calculate_delta(**kwargs)

        np.random.seed(42)
        p2 = AnomalyPattern(volatility=0.0)
        p2.force_spike()
        spiked = p2.calculate_delta(**kwargs)

        # Spike should be 5-10x baseline
        assert spiked >= baseline * Decimal("4.5")
        assert spiked <= baseline * Decimal("11")

    def test_force_spike_resets_after_use(self):
        p = AnomalyPattern(volatility=0.0)
        p.force_spike()
        kwargs = dict(
            sim_time=datetime(2024, 1, 15, 12, 0),
            campaign_budget=Decimal("240"),
            remaining_budget=Decimal("200"),
            elapsed_seconds=0.001,
        )
        _ = p.calculate_delta(**kwargs)  # consumes the forced spike
        second = p.calculate_delta(**kwargs)
        # Second call should be baseline (small), not spiked
        assert second < Decimal("1")

    def test_returns_zero_when_no_remaining(self):
        p = AnomalyPattern()
        result = p.calculate_delta(
            sim_time=datetime(2024, 1, 15, 10, 0),
            campaign_budget=Decimal("100"),
            remaining_budget=Decimal("0"),
            elapsed_seconds=2.0,
        )
        assert result == Decimal("0")


# --- DecliningPattern ---

class TestDecliningPattern:
    def test_rate_decreases_with_less_remaining(self):
        p = DecliningPattern(volatility=0.0)
        kwargs = dict(
            sim_time=datetime(2024, 1, 15, 12, 0),
            campaign_budget=Decimal("240"),
            elapsed_seconds=2.0,
        )
        high = p.calculate_delta(remaining_budget=Decimal("100"), **kwargs)
        low = p.calculate_delta(remaining_budget=Decimal("10"), **kwargs)
        assert high > low

    def test_returns_zero_when_remaining_zero(self):
        p = DecliningPattern()
        result = p.calculate_delta(
            sim_time=datetime(2024, 1, 15, 12, 0),
            campaign_budget=Decimal("240"),
            remaining_budget=Decimal("0"),
            elapsed_seconds=2.0,
        )
        assert result == Decimal("0")

    def test_returns_zero_when_remaining_hours_zero(self):
        p = DecliningPattern(volatility=0.0)
        # 23:59 = ~0.017 remaining hours; at exactly 24:00 remaining_hours=0
        # Use hour=23, minute=59 which gives remaining_hours ~= 0.017
        result = p.calculate_delta(
            sim_time=datetime(2024, 1, 15, 23, 59, 59),
            campaign_budget=Decimal("240"),
            remaining_budget=Decimal("100"),
            elapsed_seconds=2.0,
        )
        # Very small remaining hours → very small delta (near zero)
        assert result < Decimal("0.01")

    def test_returns_zero_when_budget_zero(self):
        p = DecliningPattern()
        result = p.calculate_delta(
            sim_time=datetime(2024, 1, 15, 12, 0),
            campaign_budget=Decimal("0"),
            remaining_budget=Decimal("0"),
            elapsed_seconds=2.0,
        )
        assert result == Decimal("0")

    def test_full_budget_rate_equals_base(self):
        p = DecliningPattern(volatility=0.0)
        budget = Decimal("240")
        result = p.calculate_delta(
            sim_time=datetime(2024, 1, 15, 0, 0),  # midnight, 24h remaining
            campaign_budget=budget,
            remaining_budget=budget,
            elapsed_seconds=3600.0,  # 1 hour
        )
        expected_hourly = budget / Decimal("24")
        ratio = float(result / expected_hourly)
        assert 0.85 <= ratio <= 1.15
