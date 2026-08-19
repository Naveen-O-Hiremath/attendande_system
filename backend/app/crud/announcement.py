import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.announcement import Announcement, AnnouncementComment, AnnouncementLike
from app.models.user import User
from app.schemas.announcement import AnnouncementCreate, CommentCreate


async def create_announcement(db: AsyncSession, payload: AnnouncementCreate, author_id: uuid.UUID) -> Announcement:
    obj = Announcement(
        title=payload.title,
        body=payload.body,
        target_scope={},
        created_by=author_id,
        sent_at=datetime.now(timezone.utc),
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def list_announcements(db: AsyncSession, limit: int, offset: int) -> list[Announcement]:
    result = await db.execute(
        select(Announcement)
        .options(
            selectinload(Announcement.author),
            selectinload(Announcement.comments).selectinload(AnnouncementComment.user),
        )
        .order_by(Announcement.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().unique().all())


async def get_announcement(db: AsyncSession, announcement_id: uuid.UUID) -> Announcement | None:
    result = await db.execute(select(Announcement).where(Announcement.id == announcement_id))
    return result.scalar_one_or_none()


async def delete_announcement(db: AsyncSession, announcement_id: uuid.UUID) -> None:
    await db.execute(delete(Announcement).where(Announcement.id == announcement_id))
    await db.commit()


async def like_counts(db: AsyncSession, announcement_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
    if not announcement_ids:
        return {}
    result = await db.execute(
        select(AnnouncementLike.announcement_id, func.count())
        .where(AnnouncementLike.announcement_id.in_(announcement_ids))
        .group_by(AnnouncementLike.announcement_id)
    )
    return {row[0]: row[1] for row in result.all()}


async def liked_announcement_ids(db: AsyncSession, user_id: uuid.UUID, announcement_ids: list[uuid.UUID]) -> set[uuid.UUID]:
    if not announcement_ids:
        return set()
    result = await db.execute(
        select(AnnouncementLike.announcement_id).where(
            AnnouncementLike.user_id == user_id, AnnouncementLike.announcement_id.in_(announcement_ids)
        )
    )
    return {row[0] for row in result.all()}


async def toggle_like(db: AsyncSession, announcement_id: uuid.UUID, user_id: uuid.UUID) -> tuple[bool, int]:
    """Returns (liked, like_count) after toggling."""
    result = await db.execute(
        select(AnnouncementLike).where(
            AnnouncementLike.announcement_id == announcement_id, AnnouncementLike.user_id == user_id
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        await db.delete(existing)
        liked = False
    else:
        db.add(AnnouncementLike(announcement_id=announcement_id, user_id=user_id))
        liked = True
    await db.commit()

    count_result = await db.execute(
        select(func.count()).select_from(AnnouncementLike).where(AnnouncementLike.announcement_id == announcement_id)
    )
    return liked, count_result.scalar_one()


async def add_comment(
    db: AsyncSession, announcement_id: uuid.UUID, user_id: uuid.UUID, payload: CommentCreate
) -> AnnouncementComment:
    comment = AnnouncementComment(announcement_id=announcement_id, user_id=user_id, body=payload.body)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    user_result = await db.execute(select(User).where(User.id == user_id))
    comment.user = user_result.scalar_one()
    return comment
