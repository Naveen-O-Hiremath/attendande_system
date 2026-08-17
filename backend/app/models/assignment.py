import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDMixin


class Assignment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "assignments"

    school_class_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("school_classes.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_marks: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    attachments: Mapped[list["AssignmentAttachment"]] = relationship(
        back_populates="assignment", cascade="all, delete-orphan"
    )
    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="assignment", cascade="all, delete-orphan"
    )


class AssignmentAttachment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "assignment_attachments"

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False
    )
    file_url: Mapped[str] = mapped_column(String(512), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)

    assignment: Mapped["Assignment"] = relationship(back_populates="attachments")


class Submission(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "submissions"

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("student_profiles.user_id", ondelete="CASCADE"), nullable=False
    )
    file_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    text_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    grade: Mapped[float | None] = mapped_column(Float, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    assignment: Mapped["Assignment"] = relationship(back_populates="submissions")
