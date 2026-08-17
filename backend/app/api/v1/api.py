from fastapi import APIRouter

from app.api.v1.endpoints import auth, face_enrollments, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    face_enrollments.router, prefix="/face-enrollments", tags=["face-enrollments"]
)
