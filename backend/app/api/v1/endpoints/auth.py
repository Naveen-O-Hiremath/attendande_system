import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.security import TokenType, create_access_token, create_refresh_token, decode_token
from app.crud.user import authenticate, create_user, get_user_by_email, get_user_by_id
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import AccessTokenResponse, LoginRequest, RefreshRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    """Public self-registration. Always creates a STUDENT account pending face enrollment approval."""
    if await get_user_by_email(db, payload.email) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    payload.role = UserRole.STUDENT
    try:
        return await create_user(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    user = await authenticate(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)) -> AccessTokenResponse:
    invalid = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    try:
        claims = decode_token(payload.refresh_token)
    except ValueError as exc:
        raise invalid from exc

    if claims.get("type") != TokenType.REFRESH.value:
        raise invalid

    user = await get_user_by_id(db, uuid.UUID(claims["sub"]))
    if user is None:
        raise invalid

    return AccessTokenResponse(access_token=create_access_token(user.id, user.role.value))


@router.get("/me", response_model=UserRead)
async def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
