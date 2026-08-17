import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenType, decode_token
from app.crud.user import get_user_by_id
from app.db.session import get_db
from app.models.enums import UserRole, UserStatus
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise credentials_error from exc

    if payload.get("type") != TokenType.ACCESS.value:
        raise credentials_error

    try:
        user_id = uuid.UUID(payload.get("sub", ""))
    except ValueError as exc:
        raise credentials_error from exc

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise credentials_error
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is not active")

    return user


def require_roles(*roles: UserRole):
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return dependency


require_admin = require_roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)
require_student = require_roles(UserRole.STUDENT)
