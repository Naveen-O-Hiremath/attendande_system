# Attendance System — Backend

FastAPI backend foundation: auth (JWT access + refresh), RBAC, and the full
core data model (users, academic structure, geo-fences, face enrollment,
attendance, leave, announcements, chat, assignments, audit log) as SQLAlchemy
models + an initial Alembic migration.

Face-matching, schedule/geo-fence endpoints, and the other business modules
described in the project brief are not implemented yet — this is milestone 1
only ("auth, roles, DB schema, base API" per the brief's delivery plan).

## Stack

- FastAPI + SQLAlchemy 2.0 (async, `asyncpg`) + Alembic
- PostgreSQL with PostGIS (`geo_fences.polygon` uses `geoalchemy2`)
- JWT auth (`python-jose`) + `passlib`/bcrypt password hashing
- Redis service is provisioned in Docker Compose for future caching/queues (unused so far)

## Local setup

```bash
python -m venv .venv
.venv/Scripts/activate        # or source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt

cp .env.example .env          # adjust if needed

# from the repo root:
docker compose up -d db redis

# enable PostGIS on first run (the image ships it, just needs enabling):
docker exec <db-container> psql -U attendance -d attendance -c "CREATE EXTENSION IF NOT EXISTS postgis;"

alembic upgrade head
uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs
Health check: http://127.0.0.1:8000/health

## Auth model

- `POST /api/v1/auth/register` — public, always creates a `student` account
  (pending face enrollment approval per the brief's workflow).
- `POST /api/v1/auth/login` — returns access + refresh JWTs.
- `POST /api/v1/auth/refresh` — exchange a refresh token for a new access token.
- `GET /api/v1/auth/me` — current user.
- `POST /api/v1/users` — admin-only, creates accounts with any role (admin/teacher/student).
- `GET /api/v1/users` — admin-only, paginated user list.

Roles: `super_admin`, `admin`, `teacher`, `student`. `app/core/deps.py` exposes
`require_roles(...)` for RBAC-gating new endpoints.

## Migrations

```bash
alembic revision --autogenerate -m "message"
alembic upgrade head
```

`alembic/env.py` filters out tables not in our own models (`include_object`)
so PostGIS/TIGER-geocoder tables bundled in the `postgis/postgis` image don't
show up as spurious "removed table" diffs.

## Tests

```bash
pytest
```
