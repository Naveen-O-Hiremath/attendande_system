import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.enums import EnrollmentStatus, UserRole
from app.models.user import StudentProfile, User
from app.schemas.user import UserCreate


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, payload: UserCreate) -> User:
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        phone=payload.phone,
        role=payload.role,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.flush()

    if payload.role == UserRole.STUDENT:
        if not payload.roll_no:
            raise ValueError("roll_no is required for student accounts")
        db.add(
            StudentProfile(
                user_id=user.id,
                roll_no=payload.roll_no,
                enrollment_status=EnrollmentStatus.PENDING,
            )
        )

    await db.commit()
    await db.refresh(user)
    return user


async def authenticate(db: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user
