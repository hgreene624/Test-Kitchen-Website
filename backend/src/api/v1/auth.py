"""Authentication endpoints for candidate and admin login/signup."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.services.auth_service import AuthService
from src.api.middleware.auth_middleware import get_current_candidate, get_current_admin
from src.models import Candidate, AdminUser, AccountStatus


router = APIRouter()


# Request/Response Models
class SignupRequest(BaseModel):
    """Candidate signup request."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)


class LoginRequest(BaseModel):
    """Login request for both candidates and admins."""

    email: EmailStr
    password: str


class VerifyEmailRequest(BaseModel):
    """Email verification request."""

    candidate_id: str


class AuthResponse(BaseModel):
    """Authentication response with JWT token."""

    access_token: str
    token_type: str = "bearer"
    user: dict


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str


# Candidate Authentication Endpoints


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Candidate Auth"],
)
async def candidate_signup(
    request: SignupRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new candidate account.

    Creates a new candidate account with UNVERIFIED status.
    Email verification is required before the account becomes ACTIVE.

    **Functional Requirements**: FR-001, FR-002, FR-003

    Args:
        request: Signup request with email, password, and optional profile info
        db: Database session

    Returns:
        AuthResponse with JWT token and candidate info

    Raises:
        HTTPException 400: If email already registered
        HTTPException 422: If validation fails
    """
    auth_service = AuthService(db)

    try:
        candidate = await auth_service.signup_candidate(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            phone=request.phone,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Generate access token
    from src.lib.auth import create_access_token

    token_data = {
        "sub": str(candidate.id),
        "email": candidate.email,
        "role": "candidate",
    }
    access_token = create_access_token(token_data)

    return AuthResponse(
        access_token=access_token,
        user={
            "id": str(candidate.id),
            "email": candidate.email,
            "full_name": candidate.full_name,
            "phone": candidate.phone,
            "account_status": candidate.account_status.value,
            "submission_status": candidate.submission_status.value,
        },
    )


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    tags=["Candidate Auth"],
)
async def verify_email(
    request: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify candidate email address.

    Marks the candidate's account as ACTIVE after email verification.

    **Functional Requirements**: FR-002

    Args:
        request: Verification request with candidate_id
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException 404: If candidate not found
        HTTPException 400: If email already verified
    """
    auth_service = AuthService(db)

    try:
        candidate = await auth_service.verify_email(request.candidate_id)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return MessageResponse(
        message=f"Email verified successfully for {candidate.email}"
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    tags=["Candidate Auth"],
)
async def candidate_login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate candidate and issue JWT token.

    Validates credentials and returns JWT token for authenticated requests.
    Account must not be SUSPENDED to log in.

    **Functional Requirements**: FR-001, FR-004

    Args:
        request: Login credentials
        db: Database session

    Returns:
        AuthResponse with JWT token and candidate info

    Raises:
        HTTPException 401: If credentials are invalid
        HTTPException 403: If account is suspended
    """
    auth_service = AuthService(db)

    try:
        candidate, access_token = await auth_service.login_candidate(
            email=request.email,
            password=request.password,
        )
    except ValueError as e:
        if "suspended" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthResponse(
        access_token=access_token,
        user={
            "id": str(candidate.id),
            "email": candidate.email,
            "full_name": candidate.full_name,
            "phone": candidate.phone,
            "account_status": candidate.account_status.value,
            "submission_status": candidate.submission_status.value,
            "email_verified_at": (
                candidate.email_verified_at.isoformat()
                if candidate.email_verified_at
                else None
            ),
        },
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    tags=["Candidate Auth"],
)
async def candidate_logout(
    current_candidate: Candidate = Depends(get_current_candidate),
):
    """
    Logout current candidate.

    Client should discard the JWT token after calling this endpoint.
    Server-side token invalidation is handled by token expiration.

    Args:
        current_candidate: Authenticated candidate from JWT token

    Returns:
        Success message
    """
    return MessageResponse(
        message="Logged out successfully. Please discard your access token."
    )


@router.get(
    "/me",
    response_model=dict,
    tags=["Candidate Auth"],
)
async def get_current_user(
    current_candidate: Candidate = Depends(get_current_candidate),
):
    """
    Get current authenticated candidate information.

    Returns the profile of the currently authenticated candidate.

    Args:
        current_candidate: Authenticated candidate from JWT token

    Returns:
        Candidate profile information
    """
    return {
        "id": str(current_candidate.id),
        "email": current_candidate.email,
        "full_name": current_candidate.full_name,
        "phone": current_candidate.phone,
        "account_status": current_candidate.account_status.value,
        "submission_status": current_candidate.submission_status.value,
        "email_verified_at": (
            current_candidate.email_verified_at.isoformat()
            if current_candidate.email_verified_at
            else None
        ),
        "submitted_at": (
            current_candidate.submitted_at.isoformat()
            if current_candidate.submitted_at
            else None
        ),
        "created_at": current_candidate.created_at.isoformat(),
    }


# Admin Authentication Endpoints


@router.post(
    "/admin/login",
    response_model=AuthResponse,
    tags=["Admin Auth"],
)
async def admin_login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate admin user and issue JWT token.

    Validates admin credentials and returns JWT token.
    Admin account must be active to log in.

    **Functional Requirements**: FR-004

    Args:
        request: Admin login credentials
        db: Database session

    Returns:
        AuthResponse with JWT token and admin info

    Raises:
        HTTPException 401: If credentials are invalid
        HTTPException 403: If admin account is inactive
    """
    auth_service = AuthService(db)

    try:
        admin, access_token = await auth_service.login_admin(
            email=request.email,
            password=request.password,
        )
    except ValueError as e:
        if "inactive" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthResponse(
        access_token=access_token,
        user={
            "id": str(admin.id),
            "email": admin.email,
            "full_name": admin.full_name,
            "is_active": admin.is_active,
            "last_login_at": (
                admin.last_login_at.isoformat() if admin.last_login_at else None
            ),
        },
    )


@router.get(
    "/admin/me",
    response_model=dict,
    tags=["Admin Auth"],
)
async def get_current_admin_user(
    current_admin: AdminUser = Depends(get_current_admin),
):
    """
    Get current authenticated admin information.

    Returns the profile of the currently authenticated admin.

    Args:
        current_admin: Authenticated admin from JWT token

    Returns:
        Admin profile information
    """
    return {
        "id": str(current_admin.id),
        "email": current_admin.email,
        "full_name": current_admin.full_name,
        "is_active": current_admin.is_active,
        "last_login_at": (
            current_admin.last_login_at.isoformat()
            if current_admin.last_login_at
            else None
        ),
        "created_at": current_admin.created_at.isoformat(),
    }
