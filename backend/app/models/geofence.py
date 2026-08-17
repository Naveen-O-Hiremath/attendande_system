import uuid

from geoalchemy2 import Geography
from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin, UUIDMixin


class GeoFence(Base, UUIDMixin, TimestampMixin):
    """Either a simple circular fence (center + radius) or a polygon boundary."""

    __tablename__ = "geo_fences"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    center_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    center_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    radius_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    polygon: Mapped[str | None] = mapped_column(Geography(geometry_type="POLYGON", srid=4326), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    schedules: Mapped[list["ClassSchedule"]] = relationship(back_populates="geo_fence")
