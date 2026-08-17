import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDMixin


class Announcement(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "announcements"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    target_scope: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    attachments: Mapped[list["AnnouncementAttachment"]] = relationship(
        back_populates="announcement", cascade="all, delete-orphan"
    )


class AnnouncementAttachment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "announcement_attachments"

    announcement_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("announcements.id", ondelete="CASCADE"), nullable=False
    )
    file_url: Mapped[str] = mapped_column(String(512), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)

    announcement: Mapped["Announcement"] = relationship(back_populates="attachments")
