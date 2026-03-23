"""Authentication service for signup, login, and email verification."""

from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.lib.auth import hash_password, verify_password, create_access_token
from src.models import Candidate, AdminUser, AccountStatus, SubmissionStatus


class AuthService:
    """Service for handling authentication operations."""

    def __init__(self, db: AsyncSession):
        """Initialize auth service with database session.

        Args:
            db: Async database session
        """
        self.db = db

    async def signup_candidate(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> Candidate:
        """Register a new candidate account.

        Args:
            email: Candidate email address
            password: Plain text password
            full_name: Optional full name
            phone: Optional phone number

        Returns:
            Created Candidate object

        Raises:
            ValueError: If email already exists
        """
        # Check if email already exists
        result = await self.db.execute(
            select(Candidate).where(Candidate.email == email)
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError(f"Email {email} is already registered")

        # Hash password
        password_hash = hash_password(password)

        # Create candidate
        candidate = Candidate(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            phone=phone,
            account_status=AccountStatus.UNVERIFIED,
            submission_status=SubmissionStatus.INCOMPLETE,
        )

        self.db.add(candidate)
        await self.db.commit()
        await self.db.refresh(candidate)

        return candidate

    async def login_candidate(
        self,
        email: str,
        password: str,
    ) -> tuple[Candidate, str]:
        """Authenticate candidate and generate access token.

        Args:
            email: Candidate email address
            password: Plain text password

        Returns:
            Tuple of (Candidate object, JWT token string)

        Raises:
            ValueError: If credentials are invalid
        """
        # Find candidate by email
        result = await self.db.execute(
            select(Candidate).where(Candidate.email == email)
        )
        candidate = result.scalar_one_or_none()

        if not candidate:
            raise ValueError("Invalid email or password")

        # Verify password
        if not verify_password(password, candidate.password_hash):
            raise ValueError("Invalid email or password")

        # Check account status
        if candidate.account_status == AccountStatus.SUSPENDED:
            raise ValueError("Account is suspended")

        # Generate JWT token
        token_data = {
            "sub": str(candidate.id),
            "email": candidate.email,
            "role": "candidate",
        }
        access_token = create_access_token(token_data)

        return candidate, access_token

    async def login_admin(
        self,
        email: str,
        password: str,
    ) -> tuple[AdminUser, str]:
        """Authenticate admin and generate access token.

        Args:
            email: Admin email address
            password: Plain text password

        Returns:
            Tuple of (AdminUser object, JWT token string)

        Raises:
            ValueError: If credentials are invalid
        """
        # Find admin by email
        result = await self.db.execute(
            select(AdminUser).where(AdminUser.email == email)
        )
        admin = result.scalar_one_or_none()

        if not admin:
            raise ValueError("Invalid email or password")

        # Verify password
        if not verify_password(password, admin.password_hash):
            raise ValueError("Invalid email or password")

        # Check if admin is active
        if not admin.is_active:
            raise ValueError("Admin account is inactive")

        # Update last login timestamp
        admin.last_login_at = datetime.utcnow()
        await self.db.commit()

        # Generate JWT token
        token_data = {
            "sub": str(admin.id),
            "email": admin.email,
            "role": "admin",
        }
        access_token = create_access_token(token_data)

        return admin, access_token

    async def verify_email(
        self,
        candidate_id: str,
    ) -> Candidate:
        """Mark candidate email as verified.

        Args:
            candidate_id: Candidate UUID

        Returns:
            Updated Candidate object

        Raises:
            ValueError: If candidate not found
        """
        result = await self.db.execute(
            select(Candidate).where(Candidate.id == candidate_id)
        )
        candidate = result.scalar_one_or_none()

        if not candidate:
            raise ValueError("Candidate not found")

        if candidate.account_status != AccountStatus.UNVERIFIED:
            raise ValueError("Email already verified")

        # Update account status
        candidate.account_status = AccountStatus.ACTIVE
        candidate.email_verified_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(candidate)

        return candidate

    async def get_candidate_by_id(self, candidate_id: str) -> Optional[Candidate]:
        """Get candidate by ID.

        Args:
            candidate_id: Candidate UUID

        Returns:
            Candidate object if found, None otherwise
        """
        result = await self.db.execute(
            select(Candidate).where(Candidate.id == candidate_id)
        )
        return result.scalar_one_or_none()

    async def get_admin_by_id(self, admin_id: str) -> Optional[AdminUser]:
        """Get admin by ID.

        Args:
            admin_id: Admin UUID

        Returns:
            AdminUser object if found, None otherwise
        """
        result = await self.db.execute(
            select(AdminUser).where(AdminUser.id == admin_id)
        )
        return result.scalar_one_or_none()
