"""Authentication middleware with JWT validation and role-based access control."""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.lib.auth import decode_access_token
from src.models import Candidate, AdminUser

# Bearer token security scheme
security = HTTPBearer()


async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Extract and validate JWT token from request headers.

    Args:
        credentials: HTTP authorization credentials from request

    Returns:
        Decoded token payload dictionary

    Raises:
        HTTPException: If token is invalid or missing
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def get_current_candidate(
    payload: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> Candidate:
    """Get current authenticated candidate from token.

    Args:
        payload: Decoded JWT token payload
        db: Database session

    Returns:
        Authenticated Candidate object

    Raises:
        HTTPException: If candidate not found or role mismatch
    """
    role = payload.get("role")
    user_id = payload.get("sub")

    if role != "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions - candidate access required",
        )

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID",
        )

    # Fetch candidate from database
    result = await db.execute(
        select(Candidate).where(Candidate.id == user_id)
    )
    candidate = result.scalar_one_or_none()

    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    # Check if account is suspended
    if candidate.account_status == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account suspended",
        )

    return candidate


async def get_current_admin(
    payload: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    """Get current authenticated admin from token.

    Args:
        payload: Decoded JWT token payload
        db: Database session

    Returns:
        Authenticated AdminUser object

    Raises:
        HTTPException: If admin not found or role mismatch
    """
    role = payload.get("role")
    user_id = payload.get("sub")

    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions - admin access required",
        )

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID",
        )

    # Fetch admin from database
    result = await db.execute(
        select(AdminUser).where(AdminUser.id == user_id)
    )
    admin = result.scalar_one_or_none()

    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found",
        )

    # Check if admin is active
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account inactive",
        )

    return admin


# Dependency aliases for route decorators
require_candidate = Depends(get_current_candidate)
require_admin = Depends(get_current_admin)
