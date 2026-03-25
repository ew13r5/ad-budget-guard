from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class FacebookAuthRequest(BaseModel):
    code: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: Optional[str] = None
    needs_reauth: bool = False


class TokenHealthStatus(BaseModel):
    account_id: UUID
    status: str  # valid | expiring_soon | expired | error


class TokenHealthResponse(BaseModel):
    statuses: List[TokenHealthStatus]
