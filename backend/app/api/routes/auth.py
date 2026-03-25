"""Facebook OAuth and JWT authentication routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import (
    FacebookAuthRequest, RefreshRequest, TokenResponse, UserResponse,
)
from app.services.token_service import (
    create_access_token, create_refresh_token, verify_refresh_token,
)

router = APIRouter()


@router.post("/facebook", response_model=TokenResponse)
async def facebook_auth(
    body: FacebookAuthRequest,
    db: AsyncSession = Depends(get_db),
):
    """Exchange Facebook authorization code for JWT tokens.

    In a full implementation, this would:
    1. Exchange code for short-lived token with Facebook
    2. Exchange short-lived -> long-lived token
    3. Fetch user profile and ad accounts
    4. Create/update user record

    For now, this is a stub that creates a test user.
    """
    # TODO: Implement actual Facebook OAuth flow (httpx calls to Graph API)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Facebook OAuth not yet fully implemented",
    )


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

    from uuid import UUID
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        needs_reauth=current_user.needs_reauth,
    )
