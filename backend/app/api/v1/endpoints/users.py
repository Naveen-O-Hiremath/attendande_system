import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin
from app.crud import school_class as class_crud
from app.crud.user import create_user, get_user_by_email
from app.db.session import get_db
from app.models.user import StudentProfile, User
from app.schemas.school_class import ClassAssignmentUpdate, StudentSummary
from app.schemas.user import UserCreate, UserRead

router = APIRouter()


def _class_name(section_name: str, section: str | None) -> str:
    return f"{section_name} - {section}" if section else section_name


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


@router.get("/students", response_model=list[StudentSummary])
async def list_students(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[StudentSummary]:
    """Every student account with their roll number and current class assignment (or none)."""
    rows = await class_crud.list_students_with_class(db)
    return [
        StudentSummary(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            roll_no=profile.roll_no,
            enrollment_status=profile.enrollment_status.value,
            school_class_id=profile.school_class_id,
            school_class_name=_class_name(school_class.name, school_class.section) if school_class else None,
        )
        for user, profile, school_class in rows
    ]


@router.patch("/{user_id}/class", response_model=StudentSummary)
async def assign_class(
    user_id: uuid.UUID,
    payload: ClassAssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> StudentSummary:
    """Assign a student to a class, or unassign by passing school_class_id: null."""
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    school_class = None
    if payload.school_class_id is not None:
        school_class = await class_crud.get_class(db, payload.school_class_id)
        if school_class is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    profile.school_class_id = payload.school_class_id
    await db.commit()
    await db.refresh(profile)

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()
    return StudentSummary(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        roll_no=profile.roll_no,
        enrollment_status=profile.enrollment_status.value,
        school_class_id=profile.school_class_id,
        school_class_name=_class_name(school_class.name, school_class.section) if school_class else None,
    )
