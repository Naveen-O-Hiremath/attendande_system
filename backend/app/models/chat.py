import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDMixin


class ChatGroup(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "chat_groups"

    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    school_class_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("school_classes.id", ondelete="CASCADE"), nullable=True
    )
    is_direct: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    members: Mapped[list["ChatGroupMember"]] = relationship(back_populates="group", cascade="all, delete-orphan")
    messages: Mapped[list["ChatMessage"]] = relationship(back_populates="group", cascade="all, delete-orphan")


class ChatGroupMember(Base, TimestampMixin):
    __tablename__ = "chat_group_members"

    group_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("chat_groups.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    is_muted: Mapped[bool] = mapped_column(Boolean, default=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    group: Mapped["ChatGroup"] = relationship(back_populates="members")


class ChatMessage(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "chat_messages"

    group_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("chat_groups.id", ondelete="CASCADE"), nullable=False
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_reported: Mapped[bool] = mapped_column(Boolean, default=False)
    is_removed: Mapped[bool] = mapped_column(Boolean, default=False)

    group: Mapped["ChatGroup"] = relationship(back_populates="messages")
