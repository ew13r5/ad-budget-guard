"""Seed data generator for simulation environment."""
from __future__ import annotations

import sys
import uuid
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
    return uuid.uuid5(SEED_NAMESPACE, name)


@dataclass
class SeedResult:
    accounts_created: int
    campaigns_created: int
    snapshots_created: int
    ad_sets_created: int


ACCOUNT_DEFINITIONS = [
    {
        "name": "TechStart Agency",
        "meta_account_id": "sim_act_techstart",
        "campaigns": [
            {"name": "Brand Awareness - US", "daily_budget": Decimal("200.00")},
            {"name": "Brand Awareness - EU", "daily_budget": Decimal("180.00")},
            {"name": "Retargeting - Website Visitors", "daily_budget": Decimal("150.00")},
            {"name": "Retargeting - Cart Abandoners", "daily_budget": Decimal("120.00")},
            {"name": "Lookalike - Top Purchasers", "daily_budget": Decimal("250.00")},
            {"name": "App Install - iOS", "daily_budget": Decimal("300.00")},
            {"name": "App Install - Android", "daily_budget": Decimal("280.00")},
            {"name": "Lead Gen - Whitepaper", "daily_budget": Decimal("100.00")},
            {"name": "Lead Gen - Webinar", "daily_budget": Decimal("90.00")},
            {"name": "Video Views - Product Demo", "daily_budget": Decimal("160.00")},
            {"name": "Engagement - Social Posts", "daily_budget": Decimal("75.00")},
            {"name": "Conversions - Free Trial", "daily_budget": Decimal("350.00")},
            {"name": "Conversions - Premium", "daily_budget": Decimal("400.00")},
            {"name": "Dynamic Ads - Catalog", "daily_budget": Decimal("220.00")},
            {"name": "Reach - Local Markets", "daily_budget": Decimal("130.00")},
        ],
    },
    {
        "name": "ShopNow E-commerce",
        "meta_account_id": "sim_act_shopnow",
        "campaigns": [
            {"name": "Spring Sale - All Products", "daily_budget": Decimal("180.00")},
            {"name": "Flash Deal - Electronics", "daily_budget": Decimal("150.00")},
            {"name": "Retargeting - Browse Abandon", "daily_budget": Decimal("120.00")},
            {"name": "Lookalike - Repeat Buyers", "daily_budget": Decimal("200.00")},
            {"name": "New Arrivals - Fashion", "daily_budget": Decimal("100.00")},
            {"name": "Clearance - Winter Stock", "daily_budget": Decimal("80.00")},
            {"name": "Bundle Promo - Accessories", "daily_budget": Decimal("90.00")},
            {"name": "Gift Guide - Holiday", "daily_budget": Decimal("160.00")},
            {"name": "VIP Customers - Exclusive", "daily_budget": Decimal("250.00")},
            {"name": "Cart Recovery - High Value", "daily_budget": Decimal("140.00")},
        ],
    },
    {
        "name": "NewBrand Startup",
        "meta_account_id": "sim_act_newbrand",
        "campaigns": [
            {"name": "Launch Campaign - Awareness", "daily_budget": Decimal("100.00")},
            {"name": "Early Adopters - Signup", "daily_budget": Decimal("80.00")},
            {"name": "Influencer Collab - Reach", "daily_budget": Decimal("60.00")},
            {"name": "Product Hunt - Traffic", "daily_budget": Decimal("50.00")},
            {"name": "Beta Users - Conversions", "daily_budget": Decimal("70.00")},
        ],
    },
    {
        "name": "MegaCorp Enterprise",
        "meta_account_id": "sim_act_megacorp",
        "campaigns": [
            {"name": "Enterprise Solutions - Awareness", "daily_budget": Decimal("500.00")},
            {"name": "B2B Lead Gen - Decision Makers", "daily_budget": Decimal("450.00")},
            {"name": "Retargeting - Demo Requests", "daily_budget": Decimal("350.00")},
            {"name": "Account Based - Fortune 500", "daily_budget": Decimal("400.00")},
            {"name": "Webinar Series - Thought Leadership", "daily_budget": Decimal("300.00")},
            {"name": "Content Syndication - Whitepapers", "daily_budget": Decimal("250.00")},
            {"name": "Event Promo - Annual Conference", "daily_budget": Decimal("200.00")},
            {"name": "Brand Safety - Premium", "daily_budget": Decimal("380.00")},
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

                # Generate 30 days of hourly snapshots
                snapshots = self._generate_snapshots(campaign.id, camp_def["daily_budget"])
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
        print(f"Seeded: {result}")
