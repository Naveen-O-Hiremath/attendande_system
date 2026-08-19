import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_admin
from app.crud import announcement as announcement_crud
from app.db.session import get_db
from app.models.announcement import Announcement
from app.models.user import User
from app.schemas.announcement import (
    AnnouncementCreate,
    AnnouncementRead,
    CommentCreate,
    CommentRead,
    LikeToggleResponse,
)

router = APIRouter()


@router.post("", response_model=AnnouncementRead, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    payload: AnnouncementCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> AnnouncementRead:
    """Admin-only: post an announcement, visible to every student immediately."""
    obj = await announcement_crud.create_announcement(db, payload, admin.id)
    # Built from known values rather than obj's relationships: obj was just
    # refreshed, and assigning/reading an unloaded relationship on it here
    # would trigger an implicit lazy-load, which AsyncSession can't do
    # outside an explicit await (raises a greenlet error).
    return AnnouncementRead(
        id=obj.id,
        title=obj.title,
        body=obj.body,
        created_by=obj.created_by,
        author_name=admin.full_name,
        created_at=obj.created_at,
        like_count=0,
        comment_count=0,
        liked_by_me=False,
        comments=[],
    )


@router.get("", response_model=list[AnnouncementRead])
async def list_announcements(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[AnnouncementRead]:
    """Every authenticated user (student or admin) sees the same feed, newest first."""
    items = await announcement_crud.list_announcements(db, limit, offset)
    ids = [i.id for i in items]
    counts = await announcement_crud.like_counts(db, ids)
    liked_ids = await announcement_crud.liked_announcement_ids(db, current_user.id, ids)
    return [
        AnnouncementRead(
            id=a.id,
            title=a.title,
            body=a.body,
            created_by=a.created_by,
            author_name=a.author.full_name if a.author else "Admin",
            created_at=a.created_at,
            like_count=counts.get(a.id, 0),
            comment_count=len(a.comments),
            liked_by_me=a.id in liked_ids,
            comments=[
                CommentRead(
                    id=c.id, user_id=c.user_id, author_name=c.user.full_name, body=c.body, created_at=c.created_at
                )
                for c in a.comments
            ],
        )
        for a in items
    ]


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(
    announcement_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    obj = await announcement_crud.get_announcement(db, announcement_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
    await announcement_crud.delete_announcement(db, announcement_id)


@router.post("/{announcement_id}/like", response_model=LikeToggleResponse)
async def toggle_like(
    announcement_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LikeToggleResponse:
    obj = await announcement_crud.get_announcement(db, announcement_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
    liked, count = await announcement_crud.toggle_like(db, announcement_id, current_user.id)
    return LikeToggleResponse(liked=liked, like_count=count)


@router.post("/{announcement_id}/comments", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
async def add_comment(
    announcement_id: uuid.UUID,
    payload: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommentRead:
    obj = await announcement_crud.get_announcement(db, announcement_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
    comment = await announcement_crud.add_comment(db, announcement_id, current_user.id, payload)
    return CommentRead(
        id=comment.id,
        user_id=comment.user_id,
        author_name=comment.user.full_name,
        body=comment.body,
        created_at=comment.created_at,
    )
