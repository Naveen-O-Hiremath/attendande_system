import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole, UserStatus


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    phone: str | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.STUDENT
    roll_no: str | None = Field(default=None, description="Required when role=student")


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: UserRole
    status: UserStatus
