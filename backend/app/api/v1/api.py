from fastapi import APIRouter

from app.api.v1.endpoints import announcements, attendance, auth, classes, face_enrollments, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(classes.router, prefix="/classes", tags=["classes"])
api_router.include_router(
    face_enrollments.router, prefix="/face-enrollments", tags=["face-enrollments"]
)
api_router.include_router(announcements.router, prefix="/announcements", tags=["announcements"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
