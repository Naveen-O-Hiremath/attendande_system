import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDMixin
from app.models.enums import EnrollmentStatus


class FaceEnrollment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "face_enrollments"

    student_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("student_profiles.user_id", ondelete="CASCADE"), nullable=False
    )
    image_urls: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    # Populated only on admin approval (never at submission time) so a pending
    # or rejected submission can never silently become the trusted embedding.
    embedding: Mapped[list[float] | None] = mapped_column(ARRAY(Float), nullable=True)
    capture_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[EnrollmentStatus] = mapped_column(
        SAEnum(EnrollmentStatus, name="face_enrollment_status"),
        nullable=False,
        default=EnrollmentStatus.PENDING,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    student: Mapped["StudentProfile"] = relationship(back_populates="face_enrollments")
