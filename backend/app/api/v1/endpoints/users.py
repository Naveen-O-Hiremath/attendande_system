from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin
from app.crud.user import create_user, get_user_by_email
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead

router = APIRouter()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_staff_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> User:
    """Admin-only: create accounts with any role (admin, teacher, or student)."""
    if await get_user_by_email(db, payload.email) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    try:
        return await create_user(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("", response_model=list[UserRead])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[User]:
    result = await db.execute(select(User).offset(offset).limit(limit).order_by(User.created_at.desc()))
    return list(result.scalars().all())
