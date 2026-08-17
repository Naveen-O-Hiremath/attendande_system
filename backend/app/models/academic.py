import uuid
from datetime import date, time

from sqlalchemy import Date, ForeignKey, String, Time
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDMixin
from app.models.enums import DayOfWeek


class Term(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "terms"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    school_classes: Mapped[list["SchoolClass"]] = relationship(back_populates="term")
    holidays: Mapped[list["Holiday"]] = relationship(back_populates="term", cascade="all, delete-orphan")


class Holiday(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "holidays"

    term_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("terms.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)

    term: Mapped["Term"] = relationship(back_populates="holidays")


class SchoolClass(Base, UUIDMixin, TimestampMixin):
    """A specific class/section (e.g. 'Grade 10 - Section B')."""

    __tablename__ = "school_classes"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    section: Mapped[str | None] = mapped_column(String(32), nullable=True)
    year: Mapped[str | None] = mapped_column(String(16), nullable=True)
    term_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("terms.id", ondelete="SET NULL"), nullable=True
    )

    term: Mapped["Term | None"] = relationship(back_populates="school_classes")
    students: Mapped[list["StudentProfile"]] = relationship(back_populates="school_class")
    schedules: Mapped[list["ClassSchedule"]] = relationship(
        back_populates="school_class", cascade="all, delete-orphan"
    )


class ClassSchedule(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "class_schedules"

    school_class_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("school_classes.id", ondelete="CASCADE"), nullable=False
    )
    day_of_week: Mapped[DayOfWeek] = mapped_column(SAEnum(DayOfWeek, name="day_of_week"), nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    room: Mapped[str | None] = mapped_column(String(64), nullable=True)
    geo_fence_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("geo_fences.id", ondelete="SET NULL"), nullable=True
    )

    school_class: Mapped["SchoolClass"] = relationship(back_populates="schedules")
    geo_fence: Mapped["GeoFence | None"] = relationship(back_populates="schedules")
