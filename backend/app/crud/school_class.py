import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.academic import SchoolClass
from app.models.user import StudentProfile, User
from app.schemas.school_class import SchoolClassCreate


async def create_class(db: AsyncSession, payload: SchoolClassCreate) -> SchoolClass:
    obj = SchoolClass(name=payload.name, section=payload.section, year=payload.year)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def list_classes(db: AsyncSession) -> list[SchoolClass]:
    result = await db.execute(
        select(SchoolClass).options(selectinload(SchoolClass.students)).order_by(SchoolClass.name)
    )
    return list(result.scalars().all())


async def get_class(db: AsyncSession, class_id: uuid.UUID) -> SchoolClass | None:
    result = await db.execute(select(SchoolClass).where(SchoolClass.id == class_id))
    return result.scalar_one_or_none()


async def list_students_with_class(
    db: AsyncSession,
) -> list[tuple[User, StudentProfile, SchoolClass | None]]:
    result = await db.execute(
        select(User, StudentProfile, SchoolClass)
        .join(StudentProfile, StudentProfile.user_id == User.id)
        .outerjoin(SchoolClass, SchoolClass.id == StudentProfile.school_class_id)
        .order_by(User.full_name)
    )
    return [(row[0], row[1], row[2]) for row in result.all()]
