import uuid
from datetime import datetime

from pydantic import BaseModel


class AttendanceRecordRead(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    student_name: str
    roll_no: str
    school_class_id: uuid.UUID
    school_class_name: str
    marked_at: datetime
    status: str
    method: str
    geo_verified: bool
    match_confidence: float | None
    device_id: str | None
