"""FastAPI router for Authentication, Session Management, and Token Issuance."""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.security import (
    DEFAULT_TENANT_ID,
    VALID_ROLES,
    UserContext,
    generate_mock_token,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenRequest(BaseModel):
    role: str = Field(default="CPO", description="Target role (ANALYST, SUPPLY_CHAIN_PLANNER, PROCUREMENT_MANAGER, CATEGORY_DIRECTOR, CPO, ADMIN)")
    user_id: Optional[str] = Field(default=None, description="Optional user identifier (e.g. USR-CPO-01)")
    tenant_id: Optional[str] = Field(default=DEFAULT_TENANT_ID, description="Target tenant ID")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    tenant_id: str


@router.post("/token", response_model=TokenResponse)
def get_auth_token(req: TokenRequest) -> TokenResponse:
    """Issue a signed Bearer authentication token for a designated role."""
    norm_role = req.role.upper().strip()
    if norm_role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role '{req.role}'. Valid roles are: {', '.join(sorted(VALID_ROLES))}.",
        )
    uid = req.user_id or f"USR-{norm_role}"
    tenant = req.tenant_id or DEFAULT_TENANT_ID
    token = generate_mock_token(user_id=uid, role=norm_role, tenant_id=tenant)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=norm_role,
        user_id=uid,
        tenant_id=tenant,
    )


@router.get("/session", response_model=dict)
def get_session(current_user: UserContext = Depends(get_current_user)) -> dict:
    """Verify active token and return authenticated session identity."""
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "role": current_user.role,
        "tenant_id": current_user.tenant_id,
        "is_authenticated": current_user.is_authenticated,
    }
