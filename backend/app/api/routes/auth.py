"""Facebook OAuth and JWT authentication routes."""
from __future__ import annotations

import asyncio
import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from urllib.parse import urlencode
from uuid import UUID

import httpx
import redis as sync_redis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.config import get_settings
from app.models.ad_account import AccountMode, AdAccount, UserRole, user_accounts
from app.models.campaign import Campaign, CampaignStatus
from app.models.user import User
from app.schemas.auth import (
    FacebookAuthRequest, RefreshRequest, TokenResponse, UserResponse,
)
from app.services.crypto import decrypt_token, encrypt_token
from app.services.token_service import (
    create_access_token, create_refresh_token, verify_refresh_token,
)

router = APIRouter()

GRAPH_API_BASE = "https://graph.facebook.com"
FACEBOOK_DIALOG_BASE = "https://www.facebook.com"
OAUTH_SCOPES = "ads_management,ads_read,business_management"


def _get_redis():
    settings = get_settings()
    return sync_redis.from_url(settings.redis_url)


# ─── OAuth Login ────────────────────────────────────────────

@router.get("/facebook/login")
async def facebook_login():
    """Generate Facebook OAuth authorization URL with CSRF state parameter."""
    settings = get_settings()

    state = secrets.token_urlsafe(32)

    r = _get_redis()
    await asyncio.to_thread(r.setex, f"oauth:state:{state}", 600, "1")

    params = {
        "client_id": settings.meta_app_id,
        "redirect_uri": settings.facebook_redirect_uri,
        "state": state,
        "scope": OAUTH_SCOPES,
        "response_type": "code",
    }
    auth_url = f"{FACEBOOK_DIALOG_BASE}/{settings.meta_api_version}/dialog/oauth?{urlencode(params)}"

    return {"auth_url": auth_url}


# ─── OAuth Token Exchange ───────────────────────────────────

@router.post("/facebook", response_model=TokenResponse)
async def facebook_auth(
    body: FacebookAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    """Exchange Facebook authorization code for JWT tokens."""
    settings = get_settings()

    # 1. Validate state (atomic GETDEL)
    if body.state:
        r = _get_redis()
        result = await asyncio.to_thread(r.getdel, f"oauth:state:{body.state}")
        if result is None:
            raise HTTPException(status_code=400, detail="Invalid state parameter")

    graph_base = f"{GRAPH_API_BASE}/{settings.meta_api_version}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        # 2. Exchange code for short-lived token
        resp = await client.get(
            f"{graph_base}/oauth/access_token",
            params={
                "client_id": settings.meta_app_id,
                "redirect_uri": settings.facebook_redirect_uri,
                "client_secret": settings.meta_app_secret,
                "code": body.code,
            },
        )
        data = resp.json()
        if "error" in data:
            raise HTTPException(status_code=401, detail=data["error"].get("message", "Invalid authorization code"))
        short_token = data.get("access_token")
        if not short_token:
            raise HTTPException(status_code=401, detail="No access token returned")

        # 3. Exchange for long-lived token
        resp2 = await client.get(
            f"{graph_base}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": settings.meta_app_id,
                "client_secret": settings.meta_app_secret,
                "fb_exchange_token": short_token,
            },
        )
        data2 = resp2.json()
        long_token = data2.get("access_token", short_token)
        expires_in = int(data2.get("expires_in", 5184000))

        # 4. Fetch user profile
        resp3 = await client.get(
            f"{graph_base}/me",
            params={"fields": "id,name,email", "access_token": long_token},
        )
        profile = resp3.json()
        if "error" in profile:
            raise HTTPException(status_code=502, detail="Failed to fetch Facebook profile")

    fb_id = profile["id"]
    name = profile.get("name", "Facebook User")
    email = profile.get("email")

    # 5. Create or update User
    result = await db.execute(select(User).where(User.facebook_id == fb_id))
    user = result.scalar_one_or_none()

    encrypted = encrypt_token(long_token, settings.encryption_key)
    token_expires = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    if user:
        user.name = name
        user.email = email
        user.access_token = encrypted
        user.token_expires_at = token_expires
        user.needs_reauth = False
    else:
        user = User(
            facebook_id=fb_id,
            name=name,
            email=email,
            access_token=encrypted,
            token_expires_at=token_expires,
            needs_reauth=False,
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    # 6. Return JWT tokens
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


# ─── Account Discovery ─────────────────────────────────────

@router.post("/facebook/discover-accounts")
async def discover_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch ad accounts from Meta API and create/link AdAccount records."""
    settings = get_settings()

    if not current_user.access_token:
        raise HTTPException(status_code=401, detail="No Facebook token. Connect your account first.")

    try:
        token = decrypt_token(current_user.access_token, settings.encryption_key)
    except ValueError:
        raise HTTPException(status_code=401, detail="Token decryption failed. Please reconnect.")

    graph_base = f"{GRAPH_API_BASE}/{settings.meta_api_version}"
    all_accounts = []

    async with httpx.AsyncClient(timeout=15.0) as client:
        url = f"{graph_base}/me/adaccounts"
        params = {
            "fields": "account_id,name,currency,timezone_name,account_status,business",
            "access_token": token,
            "limit": "100",
        }
        max_pages = 20

        for _ in range(max_pages):
            resp = await client.get(url, params=params)
            data = resp.json()
            if "error" in data:
                raise HTTPException(status_code=502, detail=data["error"].get("message", "Meta API error"))

            all_accounts.extend(data.get("data", []))

            next_url = data.get("paging", {}).get("next")
            if not next_url:
                break
            url = next_url
            params = {}  # next URL has params embedded

    discovered = []
    for acct in all_accounts:
        meta_id = acct.get("account_id", "")
        if not meta_id:
            continue

        result = await db.execute(
            select(AdAccount).where(AdAccount.meta_account_id == meta_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            is_new = False
            account = existing
        else:
            is_new = True
            account_status = acct.get("account_status", 0)
            mode = AccountMode.production if account_status == 1 else AccountMode.sandbox
            account = AdAccount(
                meta_account_id=meta_id,
                name=acct.get("name", meta_id),
                mode=mode,
                currency=acct.get("currency", "USD"),
                timezone=acct.get("timezone_name", "UTC"),
                is_active=True,
            )
            db.add(account)
            await db.flush()

        # Link user if not already linked
        link_result = await db.execute(
            select(user_accounts).where(
                user_accounts.c.user_id == current_user.id,
                user_accounts.c.account_id == account.id,
            )
        )
        if link_result.first() is None:
            await db.execute(
                insert(user_accounts).values(
                    user_id=current_user.id,
                    account_id=account.id,
                    role=UserRole.owner,
                )
            )

        discovered.append({
            "id": str(account.id),
            "meta_account_id": meta_id,
            "name": account.name,
            "currency": account.currency,
            "timezone": account.timezone,
            "is_new": is_new,
        })

    await db.commit()

    return {"accounts": discovered, "total": len(discovered)}


# ─── Campaign Import ────────────────────────────────────────

def _cents_to_dollars(value: Optional[str]) -> Optional[Decimal]:
    """Convert Meta API budget value (cents string) to Decimal dollars."""
    if not value or value == "0":
        return None
    return Decimal(value) / 100


@router.post("/facebook/import-campaigns")
async def import_campaigns(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch campaigns from Meta API and create/update Campaign records."""
    settings = get_settings()
    account_id = UUID(body.get("account_id", ""))

    # Verify access
    link_result = await db.execute(
        select(user_accounts).where(
            user_accounts.c.user_id == current_user.id,
            user_accounts.c.account_id == account_id,
        )
    )
    if link_result.first() is None:
        raise HTTPException(status_code=403, detail="No access to this account")

    result = await db.execute(select(AdAccount).where(AdAccount.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        token = decrypt_token(current_user.access_token, settings.encryption_key)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Token error")

    graph_base = f"{GRAPH_API_BASE}/{settings.meta_api_version}"
    all_campaigns = []

    async with httpx.AsyncClient(timeout=15.0) as client:
        url = f"{graph_base}/act_{account.meta_account_id}/campaigns"
        params = {
            "fields": "name,status,daily_budget,lifetime_budget",
            "access_token": token,
            "limit": "100",
        }

        for _ in range(20):
            resp = await client.get(url, params=params)
            data = resp.json()
            if "error" in data:
                break
            all_campaigns.extend(data.get("data", []))
            next_url = data.get("paging", {}).get("next")
            if not next_url:
                break
            url = next_url
            params = {}

    imported = 0
    updated = 0

    for camp in all_campaigns:
        meta_campaign_id = camp.get("id", "")
        if not meta_campaign_id:
            continue

        result = await db.execute(
            select(Campaign).where(
                Campaign.account_id == account_id,
                Campaign.meta_campaign_id == meta_campaign_id,
            )
        )
        existing = result.scalar_one_or_none()

        raw_status = camp.get("status", "PAUSED")
        try:
            campaign_status = CampaignStatus(raw_status)
        except ValueError:
            campaign_status = CampaignStatus.PAUSED

        if existing:
            existing.name = camp.get("name", existing.name)
            existing.status = campaign_status
            existing.daily_budget = _cents_to_dollars(camp.get("daily_budget"))
            existing.lifetime_budget = _cents_to_dollars(camp.get("lifetime_budget"))
            updated += 1
        else:
            new_campaign = Campaign(
                account_id=account_id,
                meta_campaign_id=meta_campaign_id,
                name=camp.get("name", "Unnamed Campaign"),
                status=campaign_status,
                daily_budget=_cents_to_dollars(camp.get("daily_budget")),
                lifetime_budget=_cents_to_dollars(camp.get("lifetime_budget")),
            )
            db.add(new_campaign)
            imported += 1

    await db.commit()

    return {"imported": imported, "updated": updated, "total": imported + updated}


# ─── Token Refresh ──────────────────────────────────────────

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Exchange refresh token for new access token."""
    user_id = verify_refresh_token(body.refresh_token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


# ─── User Profile ───────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        needs_reauth=current_user.needs_reauth,
    )
