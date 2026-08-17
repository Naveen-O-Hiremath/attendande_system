import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EnrollmentStatus
from app.models.face_enrollment import FaceEnrollment


async def get(db: AsyncSession, enrollment_id: uuid.UUID) -> FaceEnrollment | None:
    result = await db.execute(select(FaceEnrollment).where(FaceEnrollment.id == enrollment_id))
    return result.scalar_one_or_none()


async def get_pending_for_student(db: AsyncSession, student_id: uuid.UUID) -> FaceEnrollment | None:
    result = await db.execute(
        select(FaceEnrollment).where(
            FaceEnrollment.student_id == student_id,
            FaceEnrollment.status == EnrollmentStatus.PENDING,
        )
    )
    return result.scalar_one_or_none()


async def get_latest_for_student(db: AsyncSession, student_id: uuid.UUID) -> FaceEnrollment | None:
    result = await db.execute(
        select(FaceEnrollment)
        .where(FaceEnrollment.student_id == student_id)
        .order_by(FaceEnrollment.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_latest_approved_for_student(db: AsyncSession, student_id: uuid.UUID) -> FaceEnrollment | None:
    result = await db.execute(
        select(FaceEnrollment)
        .where(
            FaceEnrollment.student_id == student_id,
            FaceEnrollment.status == EnrollmentStatus.APPROVED,
        )
        .order_by(FaceEnrollment.approved_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def list_enrollments(
    db: AsyncSession,
    status: EnrollmentStatus | None,
    limit: int,
    offset: int,
) -> list[FaceEnrollment]:
    query = select(FaceEnrollment).order_by(FaceEnrollment.created_at.desc()).offset(offset).limit(limit)
    if status is not None:
        query = query.where(FaceEnrollment.status == status)
    result = await db.execute(query)
    return list(result.scalars().all())
