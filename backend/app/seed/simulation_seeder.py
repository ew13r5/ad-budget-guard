"""Seed data generator for simulation environment."""
from __future__ import annotations

import logging
import sys
import uuid

logger = logging.getLogger(__name__)
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List

import numpy as np
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.ad_account import AccountMode, AdAccount
from app.models.campaign import Campaign, CampaignStatus
from app.models.simulation_state import SimulationState
from app.models.spend_snapshot import SpendSnapshot, SpendSource

SEED_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def _deterministic_id(name: str) -> uuid.UUID:
    raw = uuid.uuid5(SEED_NAMESPACE, name)
    return uuid.UUID(str(raw))


@dataclass
class SeedResult:
    accounts_created: int
    campaigns_created: int
    snapshots_created: int
    ad_sets_created: int


ACCOUNT_DEFINITIONS = [
    {
        "name": "Client-Alpha — E-commerce Brand",
        "meta_account_id": "sim_act_847291035",
        "campaigns": [
            {"name": "Summer Sale 2024 — US", "daily_budget": Decimal("40.00")},
            {"name": "Retargeting — Cart Abandoners", "daily_budget": Decimal("25.00")},
            {"name": "Brand Awareness — 25-34", "daily_budget": Decimal("30.00")},
            {"name": "Lookalike — Top Customers", "daily_budget": Decimal("20.00")},
            {"name": "DPA — Product Catalog", "daily_budget": Decimal("15.00")},
            {"name": "Retargeting — Page Visitors", "daily_budget": Decimal("20.00")},
            {"name": "Holiday Promo — Black Friday", "daily_budget": Decimal("25.00")},
            {"name": "Video Views — Brand Story", "daily_budget": Decimal("15.00")},
            {"name": "Lead Gen — Free Consultation", "daily_budget": Decimal("10.00")},
            {"name": "App Install — iOS", "daily_budget": Decimal("20.00")},
        ],
    },
    {
        "name": "Client-Beta — SaaS Startup",
        "meta_account_id": "sim_act_293847561",
        "campaigns": [
            {"name": "Lead Gen — Free Trial", "daily_budget": Decimal("50.00")},
            {"name": "Webinar Signup — Q4", "daily_budget": Decimal("40.00")},
            {"name": "Retargeting — Demo Viewers", "daily_budget": Decimal("35.00")},
            {"name": "Lookalike — Paying Users", "daily_budget": Decimal("45.00")},
            {"name": "Brand Awareness — Tech Founders", "daily_budget": Decimal("30.00")},
            {"name": "Content Promo — Blog Posts", "daily_budget": Decimal("25.00")},
            {"name": "App Install — Desktop", "daily_budget": Decimal("60.00")},
            {"name": "Conversions — Annual Plan", "daily_budget": Decimal("65.00")},
        ],
    },
    {
        "name": "Client-Gamma — Real Estate Agency",
        "meta_account_id": "sim_act_571829364",
        "campaigns": [
            {"name": "New Listings — Miami", "daily_budget": Decimal("30.00")},
            {"name": "Open House — Weekend", "daily_budget": Decimal("25.00")},
            {"name": "Luxury Properties — High Net Worth", "daily_budget": Decimal("40.00")},
            {"name": "First-Time Buyers — Education", "daily_budget": Decimal("20.00")},
            {"name": "Retargeting — Property Viewers", "daily_budget": Decimal("25.00")},
            {"name": "Agent Branding — Local", "daily_budget": Decimal("15.00")},
            {"name": "Virtual Tours — Video Views", "daily_budget": Decimal("20.00")},
            {"name": "Seller Leads — Home Valuation", "daily_budget": Decimal("25.00")},
        ],
    },
    {
        "name": "Client-Delta — Restaurant Chain",
        "meta_account_id": "sim_act_684920173",
        "campaigns": [
            {"name": "Lunch Specials — Local", "daily_budget": Decimal("20.00")},
            {"name": "Delivery Promo — DoorDash", "daily_budget": Decimal("25.00")},
            {"name": "Happy Hour — 21-35", "daily_budget": Decimal("15.00")},
            {"name": "Catering — Corporate", "daily_budget": Decimal("30.00")},
            {"name": "New Menu Launch — Awareness", "daily_budget": Decimal("25.00")},
            {"name": "Weekend Brunch — Families", "daily_budget": Decimal("20.00")},
        ],
    },
    {
        "name": "Client-Epsilon — Online Education",
        "meta_account_id": "sim_act_395718264",
        "campaigns": [
            {"name": "Course Launch — Python Bootcamp", "daily_budget": Decimal("80.00")},
            {"name": "Retargeting — Free Lesson Viewers", "daily_budget": Decimal("60.00")},
            {"name": "Lookalike — Course Completers", "daily_budget": Decimal("100.00")},
            {"name": "Webinar Funnel — Data Science", "daily_budget": Decimal("120.00")},
            {"name": "Brand Awareness — Career Changers", "daily_budget": Decimal("70.00")},
            {"name": "Scholarship Program — Students", "daily_budget": Decimal("40.00")},
            {"name": "Corporate Training — B2B", "daily_budget": Decimal("90.00")},
        ],
    },
]


class SimulationSeeder:
    def __init__(self, session):
        self.session = session

    def seed(self, reset: bool = False) -> SeedResult:
        if reset:
            self._clear_simulation_data()

        # Check idempotency
        existing = self.session.execute(
            select(AdAccount).where(
                AdAccount.meta_account_id.in_(
                    [a["meta_account_id"] for a in ACCOUNT_DEFINITIONS]
                )
            )
        ).scalars().all()

        if len(existing) > 0 and not reset:
            return SeedResult(0, 0, 0, 0)

        accounts_created = 0
        campaigns_created = 0
        snapshots_created = 0

        for acct_def in ACCOUNT_DEFINITIONS:
            account = AdAccount(
                id=_deterministic_id(f"account:{acct_def['name']}"),
                meta_account_id=acct_def["meta_account_id"],
                name=acct_def["name"],
                mode=AccountMode.simulation,
                currency="USD",
                timezone="UTC",
            )
            self.session.add(account)
            accounts_created += 1

            for camp_def in acct_def["campaigns"]:
                campaign = Campaign(
                    id=_deterministic_id(f"campaign:{acct_def['name']}:{camp_def['name']}"),
                    account_id=account.id,
                    meta_campaign_id=f"sim_camp_{acct_def['meta_account_id']}_{camp_def['name'][:10].replace(' ', '_').lower()}",
                    name=camp_def["name"],
                    status=CampaignStatus.ACTIVE,
                    daily_budget=camp_def["daily_budget"],
                )
                self.session.add(campaign)
                campaigns_created += 1

            # Flush accounts + campaigns so FKs exist for snapshots
            self.session.flush()

            for camp_def in acct_def["campaigns"]:
                camp_id = _deterministic_id(f"campaign:{acct_def['name']}:{camp_def['name']}")
                # Generate 30 days of hourly snapshots
                snapshots = self._generate_snapshots(camp_id, camp_def["daily_budget"])
                for batch_start in range(0, len(snapshots), 1000):
                    batch = snapshots[batch_start:batch_start + 1000]
                    self.session.bulk_save_objects(batch)
                    snapshots_created += len(batch)

            # Create SimulationState for account
            sim_state = SimulationState(
                account_id=account.id,
                state_data={"ad_sets": self._generate_ad_sets(acct_def)},
                is_running=False,
            )
            self.session.add(sim_state)

        self.session.commit()
        return SeedResult(accounts_created, campaigns_created, snapshots_created, 0)

    def _clear_simulation_data(self):
        sim_accounts = self.session.execute(
            select(AdAccount.id).where(AdAccount.mode == AccountMode.simulation)
        ).scalars().all()

        if sim_accounts:
            # Delete snapshots for simulation campaigns
            sim_campaigns = self.session.execute(
                select(Campaign.id).where(Campaign.account_id.in_(sim_accounts))
            ).scalars().all()

            if sim_campaigns:
                self.session.execute(
                    delete(SpendSnapshot).where(SpendSnapshot.campaign_id.in_(sim_campaigns))
                )

            self.session.execute(
                delete(SimulationState).where(SimulationState.account_id.in_(sim_accounts))
            )
            self.session.execute(
                delete(Campaign).where(Campaign.account_id.in_(sim_accounts))
            )
            self.session.execute(
                delete(AdAccount).where(AdAccount.id.in_(sim_accounts))
            )

        # Clear simulation log
        try:
            from app.models.simulation_log import SimulationLog
            self.session.execute(delete(SimulationLog))
        except Exception:
            pass

        self.session.commit()

    def _generate_snapshots(self, campaign_id, daily_budget: Decimal) -> List[SpendSnapshot]:
        snapshots = []
        base_hourly = float(daily_budget) / 24.0
        now = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        for day_offset in range(30):
            day = now - timedelta(days=30 - day_offset)
            for hour in range(24):
                ts = day.replace(hour=hour)
                if 10 <= hour < 18:
                    rate = base_hourly * 1.5
                elif 18 <= hour < 22:
                    rate = base_hourly * 2.0
                elif 0 <= hour < 6:
                    rate = base_hourly * 0.3
                else:
                    rate = base_hourly

                spend = max(0.0, np.random.normal(rate, rate * 0.2))
                snapshots.append(SpendSnapshot(
                    campaign_id=campaign_id,
                    spend=Decimal(f"{spend:.2f}"),
                    source=SpendSource.simulator,
                    timestamp=ts,
                ))
        return snapshots

    def _generate_ad_sets(self, acct_def: dict) -> dict:
        ad_sets = {}
        targeting_options = [
            "Ages 25-45, Interest: Technology, Location: US",
            "Ages 18-34, Interest: Shopping, Location: EU",
            "Ages 35-55, Interest: Business, Location: US",
            "Lookalike: Top 1% Purchasers",
        ]
        for camp_def in acct_def["campaigns"]:
            cid = str(_deterministic_id(f"campaign:{acct_def['name']}:{camp_def['name']}"))
            num_sets = np.random.randint(2, 5)
            ad_sets[cid] = [
                {
                    "id": str(_deterministic_id(f"adset:{cid}:{i}")),
                    "name": f"{camp_def['name']} - Set {i+1}",
                    "targeting": targeting_options[i % len(targeting_options)],
                }
                for i in range(num_sets)
            ]
        return ad_sets


if __name__ == "__main__":
    from app.database import get_sync_session_factory

    session_factory = get_sync_session_factory()
    with session_factory() as session:
        seeder = SimulationSeeder(session)
        result = seeder.seed(reset="--reset" in sys.argv)
        logger.info("seed_complete", result=result)
