"""Seed script to create admin account.

Usage:
    python -m src.scripts.seed_admin
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

from src.models import AdminUser
from src.config.settings import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed_admin_user():
    """Create admin account."""

    # Create async engine
    engine = create_async_engine(settings.database_url, echo=True)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Check if admin already exists
        result = await session.execute(
            select(AdminUser).where(AdminUser.email == "holden@flora-farms.com")
        )
        existing = result.scalar_one_or_none()

        if existing:
            print("✅ Admin account already exists (holden@flora-farms.com)")
            return

        # Hash password
        password_hash = pwd_context.hash("Satellite123!")

        # Create admin user
        admin = AdminUser(
            email="holden@flora-farms.com",
            password_hash=password_hash,
            full_name="Holden Greene",
            is_active=True,
        )

        session.add(admin)
        await session.commit()

        print("✅ Admin account created successfully!")
        print(f"   Email: holden@flora-farms.com")
        print(f"   Password: Satellite123!")
        print(f"   ID: {admin.id}")

    await engine.dispose()


if __name__ == "__main__":
    print("🌱 Seeding admin account...")
    asyncio.run(seed_admin_user())
    print("✅ Seeding complete!")
