import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDMixin
from app.models.enums import AttendanceMethod, AttendanceStatus


class AttendanceRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "attendance_records"

    student_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("student_profiles.user_id", ondelete="CASCADE"), nullable=False
    )
    school_class_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("school_classes.id", ondelete="CASCADE"), nullable=False
    )
    schedule_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("class_schedules.id", ondelete="SET NULL"), nullable=True
    )
    marked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[AttendanceStatus] = mapped_column(SAEnum(AttendanceStatus, name="attendance_status"), nullable=False)
    method: Mapped[AttendanceMethod] = mapped_column(SAEnum(AttendanceMethod, name="attendance_method"), nullable=False)
    geo_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    match_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    overridden_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    student: Mapped["StudentProfile"] = relationship()
    school_class: Mapped["SchoolClass"] = relationship()
    schedule: Mapped["ClassSchedule | None"] = relationship()
