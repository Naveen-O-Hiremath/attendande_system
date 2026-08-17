from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.services.storage import UPLOAD_ROOT

UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)

app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_PREFIX}/openapi.json")

# Note: face enrollment images are biometric data and are intentionally NOT
# served via a public StaticFiles mount. They're only reachable through the
# authenticated /api/v1/face-enrollments/images/... route (see that router),
# which checks the requester is the enrolled student or an admin.

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
