import csv
import io
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin
from app.crud import attendance as attendance_crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.attendance import AttendanceRecordRead

router = APIRouter()


def _to_read(row: tuple) -> AttendanceRecordRead:
    record, user, profile, school_class = row
    return AttendanceRecordRead(
        id=record.id,
        student_id=user.id,
        student_name=user.full_name,
        roll_no=profile.roll_no,
        school_class_id=school_class.id,
        school_class_name=f"{school_class.name} - {school_class.section}" if school_class.section else school_class.name,
        marked_at=record.marked_at,
        status=record.status.value,
        method=record.method.value,
        geo_verified=record.geo_verified,
        match_confidence=record.match_confidence,
        device_id=record.device_id,
    )


@router.get("", response_model=list[AttendanceRecordRead])
async def list_attendance(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
    school_class_id: uuid.UUID | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
) -> list[AttendanceRecordRead]:
    """Admin-only: every attendance record marked via face match, newest first."""
    rows = await attendance_crud.list_records(db, school_class_id, date_from, date_to, limit, offset)
    return [_to_read(row) for row in rows]


@router.get("/export")
async def export_attendance(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
    school_class_id: uuid.UUID | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
) -> Response:
    """Admin-only: CSV export of every attendance record matching the same filters as the list view."""
    rows = await attendance_crud.list_all_records_for_export(db, school_class_id, date_from, date_to)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["Student", "Roll No", "Class", "Marked At", "Status", "Method", "Geo Verified", "Match Confidence", "Device"]
    )
    for row in rows:
        r = _to_read(row)
        writer.writerow(
            [
                r.student_name,
                r.roll_no,
                r.school_class_name,
                r.marked_at.isoformat(),
                r.status,
                r.method,
                r.geo_verified,
                f"{r.match_confidence:.4f}" if r.match_confidence is not None else "",
                r.device_id or "",
            ]
        )

    filename = f"attendance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
