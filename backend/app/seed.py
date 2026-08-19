"""Idempotent first-run seeding: guarantees a working admin login exists on
a brand new database, so a fresh clone on another machine doesn't require
any manual SQL to get into the admin portal. Safe to run on every startup —
does nothing once the account already exists.
"""

import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.enums import UserRole
from app.models.user import User

DEFAULT_ADMIN_EMAIL = "portaladmin@example.com"
DEFAULT_ADMIN_PASSWORD = "password123"
DEFAULT_ADMIN_NAME = "Portal Admin"


async def seed_default_admin() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == DEFAULT_ADMIN_EMAIL))
        if result.scalar_one_or_none() is not None:
            print(f"  admin account already exists ({DEFAULT_ADMIN_EMAIL}), skipping.")
            return

        admin = User(
            email=DEFAULT_ADMIN_EMAIL,
            full_name=DEFAULT_ADMIN_NAME,
            hashed_password=hash_password(DEFAULT_ADMIN_PASSWORD),
            role=UserRole.ADMIN,
        )
        db.add(admin)
        await db.commit()
        print(f"  created default admin account: {DEFAULT_ADMIN_EMAIL} / {DEFAULT_ADMIN_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed_default_admin())
