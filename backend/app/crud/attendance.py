import uuid
from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.academic import SchoolClass
from app.models.attendance import AttendanceRecord
from app.models.user import StudentProfile, User


def _base_query() -> Select:
    return (
        select(AttendanceRecord, User, StudentProfile, SchoolClass)
        .join(StudentProfile, StudentProfile.user_id == AttendanceRecord.student_id)
        .join(User, User.id == StudentProfile.user_id)
        .join(SchoolClass, SchoolClass.id == AttendanceRecord.school_class_id)
    )


def _apply_filters(
    query: Select,
    school_class_id: uuid.UUID | None,
    date_from: datetime | None,
    date_to: datetime | None,
) -> Select:
    if school_class_id is not None:
        query = query.where(AttendanceRecord.school_class_id == school_class_id)
    if date_from is not None:
        query = query.where(AttendanceRecord.marked_at >= date_from)
    if date_to is not None:
        query = query.where(AttendanceRecord.marked_at <= date_to)
    return query


async def list_records(
    db: AsyncSession,
    school_class_id: uuid.UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[tuple[AttendanceRecord, User, StudentProfile, SchoolClass]]:
    query = _apply_filters(_base_query(), school_class_id, date_from, date_to)
    query = query.order_by(AttendanceRecord.marked_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return [tuple(row) for row in result.all()]


async def list_all_records_for_export(
    db: AsyncSession,
    school_class_id: uuid.UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> list[tuple[AttendanceRecord, User, StudentProfile, SchoolClass]]:
    query = _apply_filters(_base_query(), school_class_id, date_from, date_to)
    query = query.order_by(AttendanceRecord.marked_at.desc())
    result = await db.execute(query)
    return [tuple(row) for row in result.all()]
