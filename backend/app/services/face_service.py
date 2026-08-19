from __future__ import annotations

import logging
import threading

import cv2
import numpy as np
from insightface.app import FaceAnalysis

logger = logging.getLogger(__name__)

# Cosine similarity thresholds for ArcFace-style normalized embeddings.
# Below REVIEW_THRESHOLD: reject outright. Between REVIEW_THRESHOLD and
# MATCH_THRESHOLD: borderline, flag for manual admin review rather than a
# hard accept/reject (per the project brief's guidance on borderline matches).
MATCH_THRESHOLD = 0.42
REVIEW_THRESHOLD = 0.32

MIN_FACE_RATIO = 0.15  # face bbox must occupy at least this fraction of the shorter frame dimension

# Variance of Laplacian on the face crop only (not the full frame — a smooth
# background inflates whole-frame variance independent of face sharpness).
# Calibrated against real webcam captures: artificially-blurred frames
# scored 3-6, legitimately sharp frames scored 35-320. Set well clear of
# the blurry range so phone cameras (which apply noise reduction / "beauty"
# smoothing that a laptop webcam doesn't) aren't false-rejected — see the
# blur_score logged on every submission for real-world numbers.
MIN_BLUR_SCORE = 10.0


class FaceQualityError(Exception):
    """Raised when a submitted image fails detection/quality checks."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


class FaceService:
    _instance: "FaceService | None" = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self.app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        self.app.prepare(ctx_id=0, det_size=(640, 640))

    @classmethod
    def get(cls) -> "FaceService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @staticmethod
    def _decode(image_bytes: bytes) -> np.ndarray:
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise FaceQualityError("Could not read the uploaded image.")
        return img

    @staticmethod
    def _blur_score(img: np.ndarray) -> float:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())

    def analyze(self, image_bytes: bytes) -> dict:
        """Detects a single face, runs quality checks, and returns its embedding.

        Raises FaceQualityError with a user-facing reason if the image doesn't
        pass (no face / multiple faces / too small / too blurry).
        """
        img = self._decode(image_bytes)
        height, width = img.shape[:2]

        faces = self.app.get(img)
        if len(faces) == 0:
            raise FaceQualityError("No face detected. Make sure your face is clearly visible and well-lit.")
        if len(faces) > 1:
            raise FaceQualityError("Multiple faces detected. Please retake with only your face in frame.")

        face = faces[0]
        x1, y1, x2, y2 = face.bbox
        face_w, face_h = x2 - x1, y2 - y1
        if min(face_w / width, face_h / height) < MIN_FACE_RATIO:
            raise FaceQualityError("Your face is too small in the frame. Move closer to the camera.")

        # Blur is measured on the face crop only, not the full frame — a
        # smooth/plain background (very common in phone selfies) drags a
        # whole-frame Laplacian variance down even when the face itself is
        # perfectly sharp, causing false "too blurry" rejections.
        cx1 = max(0, int(x1))
        cy1 = max(0, int(y1))
        cx2 = min(width, int(x2))
        cy2 = min(height, int(y2))
        face_crop = img[cy1:cy2, cx1:cx2]
        blur_score = self._blur_score(face_crop) if face_crop.size else 0.0
        logger.info(
            "face quality: image=%dx%d det_score=%.3f blur_score=%.1f (min=%.1f)",
            width, height, face.det_score, blur_score, MIN_BLUR_SCORE,
        )
        if blur_score < MIN_BLUR_SCORE:
            raise FaceQualityError(
                f"Image is too blurry (score {blur_score:.1f}, need at least {MIN_BLUR_SCORE:.0f}). "
                "Hold the camera steady and retake."
            )

        return {
            "embedding": face.normed_embedding.astype(float).tolist(),
            "det_score": float(face.det_score),
            "blur_score": blur_score,
            "bbox": [float(v) for v in face.bbox],
            "image_size": [width, height],
        }

    @staticmethod
    def cosine_similarity(a: list[float], b: list[float]) -> float:
        va, vb = np.array(a, dtype=float), np.array(b, dtype=float)
        denom = np.linalg.norm(va) * np.linalg.norm(vb)
        if denom == 0:
            return 0.0
        return float(np.dot(va, vb) / denom)
