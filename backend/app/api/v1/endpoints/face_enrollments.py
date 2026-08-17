import asyncio
import uuid
from datetime import datetime, timezone

import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_admin, require_student
from app.crud import audit as audit_crud
from app.crud import face_enrollment as face_crud
from app.db.session import get_db
from app.models.attendance import AttendanceRecord
from app.models.enums import AttendanceMethod, AttendanceStatus, EnrollmentStatus
from app.models.face_enrollment import FaceEnrollment
from app.models.user import StudentProfile, User
from app.schemas.face_enrollment import (
    FaceEnrollmentRead,
    FaceMatchResponse,
    RejectRequest,
    ResubmissionRequest,
)
from app.services.face_service import (
    MATCH_THRESHOLD,
    REVIEW_THRESHOLD,
    FaceQualityError,
    FaceService,
)
from app.services.storage import resolve_face_enrollment_image_path, save_face_enrollment_image

router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MIN_ENROLLMENT_IMAGES = 2
MAX_ENROLLMENT_IMAGES = 5


async def _get_student_profile(db: AsyncSession, user: User) -> StudentProfile:
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
    return profile


@router.post("", response_model=FaceEnrollmentRead, status_code=status.HTTP_201_CREATED)
async def submit_enrollment(
    files: list[UploadFile] = File(...),
    device_id: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_student),
) -> FaceEnrollment:
    """Student submits multiple face captures (different angles/lighting) for admin approval.

    Embeddings are NOT computed here — only image quality/liveness-adjacent
    checks (single face, size, blur). The trusted embedding is generated only
    once an admin approves the submission (see /approve).
    """
    if len(files) < MIN_ENROLLMENT_IMAGES or len(files) > MAX_ENROLLMENT_IMAGES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Submit between {MIN_ENROLLMENT_IMAGES} and {MAX_ENROLLMENT_IMAGES} images.",
        )

    if await face_crud.get_pending_for_student(db, current_user.id) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a submission pending admin review.",
        )

    face_service = FaceService.get()
    image_urls: list[str] = []
    per_image_quality: list[dict] = []

    for index, upload in enumerate(files):
        if upload.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Image {index + 1}: unsupported file type '{upload.content_type}'.",
            )
        content = await upload.read()
        try:
            analysis = await asyncio.to_thread(face_service.analyze, content)
        except FaceQualityError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Image {index + 1}: {exc.reason}",
            ) from exc

        url = save_face_enrollment_image(current_user.id, content, upload.content_type)
        image_urls.append(url)
        per_image_quality.append(
            {
                "det_score": analysis["det_score"],
                "blur_score": analysis["blur_score"],
                "bbox": analysis["bbox"],
            }
        )

    enrollment = FaceEnrollment(
        student_id=current_user.id,
        image_urls=image_urls,
        status=EnrollmentStatus.PENDING,
        capture_metadata={"per_image": per_image_quality, "device_id": device_id},
    )
    db.add(enrollment)

    profile = await _get_student_profile(db, current_user)
    profile.enrollment_status = EnrollmentStatus.PENDING

    await db.commit()
    await db.refresh(enrollment)
    return enrollment


@router.get("/images/{student_id}/{filename}")
async def get_enrollment_image(
    student_id: uuid.UUID,
    filename: str,
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """Serves a stored enrollment image. Only the enrolled student or an admin may view it."""
    is_owner = current_user.id == student_id
    is_admin = current_user.role.value in ("admin", "super_admin")
    if not (is_owner or is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this image")

    path = resolve_face_enrollment_image_path(str(student_id), filename)
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return FileResponse(path)


@router.get("", response_model=list[FaceEnrollmentRead])
async def list_enrollments(
    status_filter: EnrollmentStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[FaceEnrollment]:
    return await face_crud.list_enrollments(db, status_filter, limit, offset)


@router.get("/me", response_model=FaceEnrollmentRead | None)
async def get_my_latest_enrollment(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_student),
) -> FaceEnrollment | None:
    """The student's own latest submission (any status), or null if they've never submitted."""
    return await face_crud.get_latest_for_student(db, current_user.id)


@router.get("/{enrollment_id}", response_model=FaceEnrollmentRead)
async def get_enrollment(
    enrollment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FaceEnrollment:
    enrollment = await face_crud.get(db, enrollment_id)
    if enrollment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
    is_owner = current_user.id == enrollment.student_id
    is_admin = current_user.role.value in ("admin", "super_admin")
    if not (is_owner or is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this enrollment")
    return enrollment


@router.post("/{enrollment_id}/approve", response_model=FaceEnrollmentRead)
async def approve_enrollment(
    enrollment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> FaceEnrollment:
    enrollment = await face_crud.get(db, enrollment_id)
    if enrollment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
    if enrollment.status != EnrollmentStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only pending submissions can be approved")

    face_service = FaceService.get()
    embeddings: list[list[float]] = []
    for url in enrollment.image_urls:
        # url looks like {API_V1_PREFIX}/face-enrollments/images/{student_id}/{filename}
        student_id, filename = url.split("/")[-2:]
        path = resolve_face_enrollment_image_path(student_id, filename)
        if not path.is_file():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="A submitted image is missing from storage. Ask the student to resubmit.",
            )
        try:
            analysis = await asyncio.to_thread(face_service.analyze, path.read_bytes())
        except FaceQualityError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Re-analysis failed on a submitted image: {exc.reason}. Ask the student to resubmit.",
            ) from exc
        embeddings.append(analysis["embedding"])

    averaged = np.mean(np.array(embeddings), axis=0)
    norm = np.linalg.norm(averaged)
    final_embedding = (averaged / norm if norm > 0 else averaged).tolist()

    enrollment.status = EnrollmentStatus.APPROVED
    enrollment.embedding = final_embedding
    enrollment.approved_by = admin.id
    enrollment.approved_at = datetime.now(timezone.utc)
    enrollment.rejection_reason = None

    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == enrollment.student_id))
    profile = result.scalar_one()
    profile.enrollment_status = EnrollmentStatus.APPROVED

    await audit_crud.record(
        db,
        actor_id=admin.id,
        action="face_enrollment.approve",
        entity_type="face_enrollment",
        entity_id=str(enrollment.id),
        metadata={"student_id": str(enrollment.student_id)},
    )

    await db.commit()
    await db.refresh(enrollment)
    return enrollment


@router.post("/{enrollment_id}/reject", response_model=FaceEnrollmentRead)
async def reject_enrollment(
    enrollment_id: uuid.UUID,
    payload: RejectRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> FaceEnrollment:
    enrollment = await face_crud.get(db, enrollment_id)
    if enrollment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
    if enrollment.status != EnrollmentStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only pending submissions can be rejected")

    enrollment.status = EnrollmentStatus.REJECTED
    enrollment.rejection_reason = payload.reason

    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == enrollment.student_id))
    profile = result.scalar_one()
    profile.enrollment_status = EnrollmentStatus.REJECTED

    await audit_crud.record(
        db,
        actor_id=admin.id,
        action="face_enrollment.reject",
        entity_type="face_enrollment",
        entity_id=str(enrollment.id),
        metadata={"student_id": str(enrollment.student_id), "reason": payload.reason},
    )

    await db.commit()
    await db.refresh(enrollment)
    return enrollment


@router.post("/{enrollment_id}/request-resubmission", response_model=FaceEnrollmentRead)
async def request_resubmission(
    enrollment_id: uuid.UUID,
    payload: ResubmissionRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> FaceEnrollment:
    enrollment = await face_crud.get(db, enrollment_id)
    if enrollment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
    if enrollment.status != EnrollmentStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only pending submissions can be actioned")

    enrollment.status = EnrollmentStatus.RESUBMISSION_REQUESTED
    enrollment.rejection_reason = payload.reason

    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == enrollment.student_id))
    profile = result.scalar_one()
    profile.enrollment_status = EnrollmentStatus.RESUBMISSION_REQUESTED

    await audit_crud.record(
        db,
        actor_id=admin.id,
        action="face_enrollment.request_resubmission",
        entity_type="face_enrollment",
        entity_id=str(enrollment.id),
        metadata={"student_id": str(enrollment.student_id), "reason": payload.reason},
    )

    await db.commit()
    await db.refresh(enrollment)
    return enrollment


@router.post("/match", response_model=FaceMatchResponse)
async def match_face(
    file: UploadFile = File(...),
    device_id: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_student),
) -> FaceMatchResponse:
    """Live capture vs. the student's own approved embedding.

    This demonstrates the recognition pipeline end-to-end. It intentionally
    does NOT gate on geo-fence or class schedule yet (those aren't built) —
    matched attempts are recorded with geo_verified=False as a placeholder.
    """
    approved = await face_crud.get_latest_approved_for_student(db, current_user.id)
    if approved is None or approved.embedding is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No approved face enrollment on file. Complete enrollment first.",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type '{file.content_type}'.",
        )

    content = await file.read()
    face_service = FaceService.get()
    try:
        analysis = await asyncio.to_thread(face_service.analyze, content)
    except FaceQualityError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.reason) from exc

    similarity = face_service.cosine_similarity(analysis["embedding"], approved.embedding)

    matched = similarity >= MATCH_THRESHOLD
    needs_review = REVIEW_THRESHOLD <= similarity < MATCH_THRESHOLD

    attendance_record_id: uuid.UUID | None = None
    if matched:
        profile = await _get_student_profile(db, current_user)
        if profile.school_class_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Face matched, but you're not assigned to a class yet. Contact your admin.",
            )
        record = AttendanceRecord(
            student_id=current_user.id,
            school_class_id=profile.school_class_id,
            marked_at=datetime.now(timezone.utc),
            status=AttendanceStatus.PRESENT,
            method=AttendanceMethod.FACE_ONLINE,
            geo_verified=False,
            match_confidence=similarity,
            device_id=device_id,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        attendance_record_id = record.id
        message = "Attendance marked."
    elif needs_review:
        message = "Borderline match — flagged for admin review. Attendance not marked automatically."
    else:
        message = "Face not recognized. Try again with better lighting or contact your admin."

    return FaceMatchResponse(
        matched=matched,
        needs_review=needs_review,
        similarity=similarity,
        attendance_record_id=attendance_record_id,
        message=message,
    )
