# Attendance System — Master README

Face-recognition-based attendance system. Three services: a **FastAPI
backend**, a **React admin portal** (desktop), and a **React student webapp**
(mobile-first, opened in a phone's browser). This file is the single
step-by-step guide to get from a clean checkout to all three running.

For credentials, troubleshooting, and design rationale beyond the setup
steps, see [SETUP.md](SETUP.md).

---

## 1. What's in this repo

```
attendance_system/
├── README.md              ← you are here — setup & run guide
├── SETUP.md                ← credentials, troubleshooting, architecture notes
├── start-all.ps1            ← starts every service in one go (§5)
├── run-mobile-web.ps1         ← connects a phone over USB via `adb reverse` (§6)
├── docker-compose.yml         ← Postgres+PostGIS, Redis, backend container def
├── .venv/                       ← Python virtualenv for the backend (repo root, not backend/)
├── backend/                      FastAPI + SQLAlchemy (async) + Alembic + InsightFace
│   ├── app/
│   │   ├── main.py                  app entrypoint, CORS, router mounting
│   │   ├── core/                     config.py (Settings), security.py (JWT), deps.py (RBAC)
│   │   ├── models/                    SQLAlchemy models
│   │   ├── schemas/                    Pydantic request/response models
│   │   ├── crud/                        DB query helpers
│   │   ├── services/                     face_service.py (InsightFace), storage.py
│   │   └── api/v1/endpoints/              auth.py, users.py, face_enrollments.py
│   ├── alembic/versions/                  DB migrations
│   ├── tests/                               pytest suite
│   ├── uploads/                              face enrollment images (gitignored)
│   ├── requirements.txt
│   └── .env / .env.example
├── admin-portal/            React + TypeScript + Vite — admin/super_admin only
│   └── src/{api,auth,components,pages}/
├── student-webapp/          React + TypeScript + Vite — the phone-facing client
│   └── src/{api,auth,components,pages}/, config.ts
└── mobile/                  earlier Flutter attempt — reference only, not run (see SETUP.md §0)
```

---

## 2. Prerequisites

| Tool | Version | Check |
|---|---|---|
| Python | 3.13 | `python --version` |
| Docker Desktop | any recent | must be installed; `start-all.ps1` will launch it if it isn't running |
| Node.js | 18+ | `node --version` |
| (Optional) Android platform-tools (`adb`) | any | only needed for USB phone testing, §6 |

All commands below are PowerShell, run from the **repo root**
(`c:\projects\attendance_system`) unless a `cd` is shown.

---

## 3. First-time setup (one time only)

### 3.1 Python virtualenv + backend dependencies

The virtualenv lives at the **repo root** (`.venv/`), not inside `backend/`
— `start-all.ps1` expects it there.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

This also pulls in `insightface` / `onnxruntime` / `opencv-python-headless`
for face recognition — the install can take a few minutes.

### 3.2 Backend environment file

```powershell
cd backend
copy .env.example .env
cd ..
```

The defaults in `.env.example` work as-is for local development (dev DB
password, dev JWT secret). See [SETUP.md §3.4](SETUP.md#34-backend-configuration-backendenv)
for what each value means.

### 3.3 Start Postgres + Redis and enable PostGIS

```powershell
docker compose up -d db redis
```

Wait for it to report healthy (`docker ps` should show `db` as
`healthy`), then, **first time only**:

```powershell
docker exec attendance_system-db-1 psql -U attendance -d attendance -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

### 3.4 Run database migrations

```powershell
cd backend
..\.venv\Scripts\python.exe -m alembic upgrade head
cd ..
```

### 3.5 Install frontend dependencies

```powershell
cd admin-portal
npm install
cd ..\student-webapp
npm install
cd ..
```

Setup is now complete. Everything from here on is day-to-day running.

---

## 4. Executing individual files / commands

If you want to run or inspect pieces individually rather than via the
all-in-one script:

| Task | Command |
|---|---|
| Run the backend API directly | `cd backend; ..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| Run backend tests | `cd backend; ..\.venv\Scripts\python.exe -m pytest` |
| Create a new migration after changing a model | `cd backend; ..\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "describe change"` |
| Apply migrations | `cd backend; ..\.venv\Scripts\python.exe -m alembic upgrade head` |
| Run the admin portal directly | `cd admin-portal; npm run dev` |
| Run the student webapp directly | `cd student-webapp; npm run dev` |
| Build admin portal for production | `cd admin-portal; npm run build` |
| Build student webapp for production | `cd student-webapp; npm run build` |
| Lint a frontend package | `cd admin-portal; npm run lint` (or `student-webapp`) |
| Bring up only Postgres+Redis | `docker compose up -d db redis` |
| Stop the Docker containers | `docker compose down` |
| Open a psql shell in the DB container | `docker exec -it attendance_system-db-1 psql -U attendance -d attendance` |

---

## 5. Running everything (day-to-day)

### Option A — one command (recommended)

```powershell
.\start-all.ps1
```

What it does, in order:
1. Makes sure Docker Desktop is running (starts it if not).
2. `docker compose up -d db redis`, waits for Postgres to be healthy.
3. Enables the PostGIS extension (idempotent, safe to repeat).
4. Runs `alembic upgrade head`.
5. Starts the backend (`uvicorn`, bound `0.0.0.0:8000` by default so a
   phone on the same Wi-Fi can reach it), the admin portal
   (`localhost:5173`), and the student webapp (`0.0.0.0:5174`) — each in
   its own PowerShell window.
6. Self-heals the two Windows Firewall rules the phone needs for Wi-Fi
   access (one-time UAC prompt, only if a rule is missing).
7. Prints a summary of every URL in use.

It's safe to re-run any time — it stops any instances it previously
started before launching fresh ones, so ports never collide.

Useful flags:
```powershell
.\start-all.ps1 -Lan:$false      # backend bound to 127.0.0.1 only — no phone testing
.\start-all.ps1 -NoPortal        # skip the admin portal
.\start-all.ps1 -NoStudentApp    # skip the student webapp
.\start-all.ps1 -NoBackend       # skip the backend (e.g. it's already running)
```

### Option B — manual, step by step (separate terminals)

Terminal 1 — backend:
```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Terminal 2 — admin portal:
```powershell
cd admin-portal
npm run dev
```

Terminal 3 — student webapp:
```powershell
cd student-webapp
npm run dev
```

Start Docker (`docker compose up -d db redis`) and run migrations
(§3.4) before either terminal, if you haven't already.

### Verify it's up

```powershell
curl http://localhost:8000/health     # {"status":"ok"}
curl http://localhost:5173/           # admin portal HTML
curl http://localhost:5174/           # student webapp HTML
```

---

## 6. Using it on a phone

The student webapp is what a phone opens. Two connection methods —
**USB is recommended**, it has no Wi-Fi/firewall/subnet failure modes:

```powershell
.\run-mobile-web.ps1
```

Plug the phone in via USB with USB debugging enabled, run the script, then
open **`http://localhost:5174`** in the phone's Chrome. It works because
`adb reverse` tunnels the phone's own `localhost` ports to this PC over the
cable — no IP address, firewall rule, or shared Wi-Fi network involved.

If USB isn't available, use the same Wi-Fi network instead: find this
machine's LAN IP (`ipconfig`), make sure `start-all.ps1` was run with its
`-Lan` default (backend/webapp bound to `0.0.0.0`), and open
`http://<this-machine's-LAN-IP>:5174` on the phone. Full details,
including firewall rules and troubleshooting, are in
[SETUP.md §6](SETUP.md#6-connecting-a-phone-to-the-student-webapp).

Neither the backend's CORS config nor the student webapp's API config has
any IP hardcoded — both derive the right origin at runtime, so this works
unchanged on any machine or network.

---

## 7. Default credentials

| Email | Password | Role | Use for |
|---|---|---|---|
| `portaladmin@example.com` | `password123` | admin | Admin portal login |
| `mobiletest@example.com` | `password123` | student | Student webapp login |

To create more accounts, register via the student webapp (always creates a
`student`) and promote via SQL — see
[SETUP.md §8](SETUP.md#8-credentials--accounts-currently-in-the-dev-database).

---

## 8. Ports & URLs

| Service | URL | Notes |
|---|---|---|
| Backend API | `http://localhost:8000` (or `http://<LAN-IP>:8000`) | |
| API docs (Swagger) | `http://localhost:8000/docs` | |
| Admin portal | `http://localhost:5173` | desktop browser only |
| Student webapp | `http://localhost:5174` (or `http://<LAN-IP>:5174`) | open this on the phone |
| Postgres | `localhost:5432` | db/user/pass: `attendance`/`attendance`/`attendance` |
| Redis | `localhost:6379` | provisioned, not yet used by any feature |

---

## 9. What's built so far

Register → login → face enrollment (2-shot capture) → admin
approve/reject/request-resubmission (computes the trusted face embedding
only on approval) → live attendance matching against the approved
embedding, with borderline matches flagged for review instead of
auto-accepted.

Not yet built: schedules, geo-fencing, leave management, announcements,
chat, assignments — see [SETUP.md §13](SETUP.md#13-known-gaps--next-steps).

---

## 10. Troubleshooting

Full table in [SETUP.md §12](SETUP.md#12-troubleshooting). Quick pointers:

- **Phone can't reach anything** → use `.\run-mobile-web.ps1` (§6); it
  sidesteps Wi-Fi/firewall issues entirely.
- **`start-all.ps1` fails at "Backend virtualenv not found"** → run §3.1
  first (venv goes at the repo root, not inside `backend/`).
- **CORS error in a browser console** → check `backend/.env`'s
  `CORS_ORIGINS` / `CORS_ORIGIN_REGEX` (`app/core/config.py`) covers the
  origin shown in the error.
- **First face-enrollment request is slow (~1 min)** → InsightFace is
  downloading the `buffalo_l` model (~280MB) once; cached after that at
  `~/.insightface/models/buffalo_l/`.
