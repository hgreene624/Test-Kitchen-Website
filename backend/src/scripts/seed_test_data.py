"""Seed script to create test candidate account.

Usage:
    python -m src.scripts.seed_test_data
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.models import Candidate, AccountStatus, SubmissionStatus
from src.config.settings import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_test_candidate():
    """Create test candidate account."""

    # Create async engine
    engine = create_async_engine(settings.database_url, echo=True)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Check if candidate already exists
        result = await session.execute(
            select(Candidate).where(Candidate.email == "test@candidate.com")
        )
        existing = result.scalar_one_or_none()

        if existing:
            print("✅ Test candidate account already exists (test@candidate.com)")
            return

        # Hash password
        password_hash = pwd_context.hash("TestCandidate123!")

        # Create candidate
        candidate = Candidate(
            email="test@candidate.com",
            password_hash=password_hash,
            full_name="Test Candidate",
            phone="555-0100",
            account_status=AccountStatus.ACTIVE,
            submission_status=SubmissionStatus.INCOMPLETE,
        )

        session.add(candidate)
        await session.commit()

        print("✅ Test candidate account created successfully!")
        print(f"   Email: test@candidate.com")
        print(f"   Password: TestCandidate123!")
        print(f"   ID: {candidate.id}")

    await engine.dispose()


if __name__ == "__main__":
    print("🌱 Seeding test candidate account...")
    asyncio.run(seed_test_candidate())
    print("✅ Seeding complete!")
