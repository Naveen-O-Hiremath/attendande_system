import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class CommentRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    author_name: str
    body: str
    created_at: datetime


class AnnouncementRead(BaseModel):
    id: uuid.UUID
    title: str
    body: str
    created_by: uuid.UUID
    author_name: str
    created_at: datetime
    like_count: int
    comment_count: int
    liked_by_me: bool
    comments: list[CommentRead]


class LikeToggleResponse(BaseModel):
    liked: bool
    like_count: int
