from __future__ import annotations

from app.models.ad_account import AccountMode, AdAccount
from app.models.user import User
from app.providers.base import AdDataProvider


def get_provider_for_account(account: AdAccount, user: User) -> AdDataProvider:
    """Create provider based on account.mode, injecting user token for Meta API."""
    if account.mode == AccountMode.simulation:
        raise NotImplementedError("SimulationProvider not yet implemented (split 02)")

    # meta_sandbox or production
    from app.providers.meta_api_provider import MetaApiProvider
    return MetaApiProvider(access_token=user.access_token or "")
