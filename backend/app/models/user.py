import uuid

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDMixin
from app.models.enums import EnrollmentStatus, UserRole, UserStatus


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, name="user_role"), nullable=False)
    status: Mapped[UserStatus] = mapped_column(
        SAEnum(UserStatus, name="user_status"), nullable=False, default=UserStatus.ACTIVE
    )

    student_profile: Mapped["StudentProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class StudentProfile(Base, TimestampMixin):
    __tablename__ = "student_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    roll_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    school_class_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("school_classes.id", ondelete="SET NULL"), nullable=True
    )
    enrollment_status: Mapped[EnrollmentStatus] = mapped_column(
        SAEnum(EnrollmentStatus, name="enrollment_status"),
        nullable=False,
        default=EnrollmentStatus.PENDING,
    )

    user: Mapped["User"] = relationship(back_populates="student_profile")
    school_class: Mapped["SchoolClass | None"] = relationship(back_populates="students")
    face_enrollments: Mapped[list["FaceEnrollment"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
