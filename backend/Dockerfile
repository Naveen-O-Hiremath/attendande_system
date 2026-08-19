FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# libpq-dev/gcc: build a couple of C-extension deps.
# libgl1/libglib2.0-0/libsm6/libxext6/libxrender1: insightface pulls in
# full "opencv-python" (not just our pinned opencv-python-headless) as a
# transitive dependency, and whichever cv2 build wins import resolution
# needs these at import time even though we never use any GUI features.
# libgomp1: onnxruntime's CPU execution provider needs the OpenMP runtime,
# which python:3.12-slim doesn't ship by default.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Bake the InsightFace buffalo_l model (~280MB) into the image at build
# time instead of letting the first face-enrollment request download it.
# Means the running container needs zero network access for face
# recognition to work, and there's no slow/flaky first request on a fresh
# machine.
RUN python -c "from insightface.app import FaceAnalysis; FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider']).prepare(ctx_id=0, det_size=(640, 640))"

EXPOSE 8000

CMD ["python", "docker_entrypoint.py"]
