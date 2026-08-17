import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import EnrollmentStatus


class FaceEnrollmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    image_urls: list[str]
    status: EnrollmentStatus
    rejection_reason: str | None
    approved_by: uuid.UUID | None
    approved_at: datetime | None
    created_at: datetime


class RejectRequest(BaseModel):
    reason: str


class ResubmissionRequest(BaseModel):
    reason: str


class FaceMatchResponse(BaseModel):
    matched: bool
    needs_review: bool
    similarity: float
    attendance_record_id: uuid.UUID | None
    message: str
