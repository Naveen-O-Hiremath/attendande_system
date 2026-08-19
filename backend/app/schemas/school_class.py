import uuid

from pydantic import BaseModel, Field


class SchoolClassCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    section: str | None = Field(default=None, max_length=32)
    year: str | None = Field(default=None, max_length=16)


class SchoolClassRead(BaseModel):
    id: uuid.UUID
    name: str
    section: str | None
    year: str | None
    student_count: int


class ClassAssignmentUpdate(BaseModel):
    school_class_id: uuid.UUID | None = None


class StudentSummary(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    roll_no: str
    enrollment_status: str
    school_class_id: uuid.UUID | None
    school_class_name: str | None
