from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_admin
from app.crud import school_class as class_crud
from app.db.session import get_db
from app.models.user import User
from app.schemas.school_class import SchoolClassCreate, SchoolClassRead

router = APIRouter()


@router.post("", response_model=SchoolClassRead, status_code=status.HTTP_201_CREATED)
async def create_class(
    payload: SchoolClassCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> SchoolClassRead:
    obj = await class_crud.create_class(db, payload)
    return SchoolClassRead(id=obj.id, name=obj.name, section=obj.section, year=obj.year, student_count=0)


@router.get("", response_model=list[SchoolClassRead])
async def list_classes(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[SchoolClassRead]:
    classes = await class_crud.list_classes(db)
    return [
        SchoolClassRead(id=c.id, name=c.name, section=c.section, year=c.year, student_count=len(c.students))
        for c in classes
    ]
