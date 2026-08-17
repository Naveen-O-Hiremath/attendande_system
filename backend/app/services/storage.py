import uuid
from pathlib import Path

from app.core.config import settings

UPLOAD_ROOT = Path(__file__).resolve().parent.parent.parent / "uploads"
FACE_ENROLLMENT_SUBDIR = "face_enrollments"

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def save_face_enrollment_image(student_id: uuid.UUID, content: bytes, content_type: str) -> str:
    """Saves an enrollment image to local disk and returns its relative URL.

    Local filesystem storage is a stand-in for the S3-compatible object
    storage described in the project brief; swapping the implementation here
    keeps the API surface (image_urls of relative/absolute URLs) unchanged.
    """
    extension = ALLOWED_CONTENT_TYPES.get(content_type)
    if extension is None:
        raise ValueError(f"Unsupported image content type: {content_type}")

    student_dir = UPLOAD_ROOT / FACE_ENROLLMENT_SUBDIR / str(student_id)
    student_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4()}.{extension}"
    file_path = student_dir / filename
    file_path.write_bytes(content)

    # Served through an authenticated route, not a public static mount —
    # see the /face-enrollments/images/... endpoint.
    return f"{settings.API_V1_PREFIX}/face-enrollments/images/{student_id}/{filename}"


def resolve_face_enrollment_image_path(student_id: str, filename: str) -> Path:
    """Resolves a stored (student_id, filename) pair to an on-disk path,
    guarding against path traversal via the filename component."""
    safe_filename = Path(filename).name
    return UPLOAD_ROOT / FACE_ENROLLMENT_SUBDIR / student_id / safe_filename
