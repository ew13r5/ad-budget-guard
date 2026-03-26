from __future__ import annotations

import math
from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal

import numpy as np


class SpendPattern(ABC):
    """Base class for spend simulation patterns."""

    def __init__(self, volatility: float = 1.0):
        self.volatility = volatility

    @abstractmethod
    def calculate_delta(
        self,
        sim_time: datetime,
        campaign_budget: Decimal,
        remaining_budget: Decimal,
        elapsed_seconds: float,
    ) -> Decimal:
        """Calculate spend increment for this tick interval."""

    def _clamp(self, delta: Decimal, remaining_budget: Decimal) -> Decimal:
        if delta < Decimal("0"):
            return Decimal("0")
        if delta > remaining_budget:
            return remaining_budget
        return delta

    def _noise_multiplier(self, std: float = 0.15) -> float:
        if self.volatility == 0:
            return 1.0
        return float(np.random.normal(1.0, std * self.volatility))


class SteadyPattern(SpendPattern):
    """Constant hourly rate with Gaussian noise and sinusoidal time-of-day modifier."""

    def calculate_delta(
        self,
        sim_time: datetime,
        campaign_budget: Decimal,
        remaining_budget: Decimal,
        elapsed_seconds: float,
    ) -> Decimal:
        if remaining_budget <= 0:
            return Decimal("0")

        base_rate = campaign_budget / Decimal("24")
        rate_per_sec = base_rate / Decimal("3600")

        hour = sim_time.hour + sim_time.minute / 60.0
        # Period=12h: peaks at ~10 and ~22, troughs at ~4 and ~16
        sin_modifier = 1.0 + 0.2 * math.sin(2 * math.pi * (hour - 4) / 12)

        noise = self._noise_multiplier(0.15)

        delta = rate_per_sec * Decimal(str(elapsed_seconds)) * Decimal(str(sin_modifier)) * Decimal(str(noise))
        return self._clamp(delta, remaining_budget)


class PeakHoursPattern(SpendPattern):
    """Time-weighted distribution based on audience activity windows."""

    WINDOWS = [
        (0, 6, Decimal("0.10")),
        (6, 10, Decimal("0.15")),
        (10, 14, Decimal("0.25")),
        (14, 18, Decimal("0.15")),
        (18, 22, Decimal("0.30")),
        (22, 24, Decimal("0.05")),
    ]

    def calculate_delta(
        self,
        sim_time: datetime,
        campaign_budget: Decimal,
        remaining_budget: Decimal,
        elapsed_seconds: float,
    ) -> Decimal:
        if remaining_budget <= 0:
            return Decimal("0")

        hour = sim_time.hour
        fraction = Decimal("0.10")
        window_hours = Decimal("6")

        for start, end, frac in self.WINDOWS:
            if start <= hour < end:
                fraction = frac
                window_hours = Decimal(str(end - start))
                break

        window_rate = (campaign_budget * fraction) / window_hours
        rate_per_sec = window_rate / Decimal("3600")

        noise = self._noise_multiplier(0.15)

        delta = rate_per_sec * Decimal(str(elapsed_seconds)) * Decimal(str(noise))
        return self._clamp(delta, remaining_budget)


class AnomalyPattern(SpendPattern):
    """Steady baseline with random spend spikes."""

    def __init__(self, volatility: float = 1.0):
        super().__init__(volatility)
        self._forced_anomaly = False

    def force_spike(self) -> None:
        self._forced_anomaly = True

    def calculate_delta(
        self,
        sim_time: datetime,
        campaign_budget: Decimal,
        remaining_budget: Decimal,
        elapsed_seconds: float,
    ) -> Decimal:
        if remaining_budget <= 0:
            return Decimal("0")

        # Baseline like SteadyPattern
        base_rate = campaign_budget / Decimal("24")
        rate_per_sec = base_rate / Decimal("3600")

        hour = sim_time.hour + sim_time.minute / 60.0
        sin_modifier = 1.0 + 0.2 * math.sin(2 * math.pi * (hour - 4) / 12)
        noise = self._noise_multiplier(0.15)

        baseline = rate_per_sec * Decimal(str(elapsed_seconds)) * Decimal(str(sin_modifier)) * Decimal(str(noise))

        spike = False
        if self._forced_anomaly:
            spike = True
            self._forced_anomaly = False
        elif elapsed_seconds > 0:
            probability = elapsed_seconds / 3600.0
            if np.random.random() < probability:
                spike = True

        if spike:
            multiplier = Decimal(str(np.random.uniform(5, 10)))
            baseline = baseline * multiplier

        return self._clamp(baseline, remaining_budget)


class DecliningPattern(SpendPattern):
    """Spend rate decreases as remaining budget approaches zero."""

    def calculate_delta(
        self,
        sim_time: datetime,
        campaign_budget: Decimal,
        remaining_budget: Decimal,
        elapsed_seconds: float,
    ) -> Decimal:
        if remaining_budget <= 0:
            return Decimal("0")

        base_rate = campaign_budget / Decimal("24")
        if base_rate <= 0:
            return Decimal("0")

        remaining_hours = 24 - sim_time.hour - sim_time.minute / 60.0 - sim_time.second / 3600.0
        if remaining_hours <= 0:
            return Decimal("0")

        ratio = remaining_budget / (base_rate * Decimal(str(remaining_hours)))
        effective_rate = base_rate * min(Decimal("1"), ratio)
        rate_per_sec = effective_rate / Decimal("3600")

        noise = self._noise_multiplier(0.10)

        delta = rate_per_sec * Decimal(str(elapsed_seconds)) * Decimal(str(noise))
        return self._clamp(delta, remaining_budget)
