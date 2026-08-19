# Attendance System — Master README

Face-recognition-based attendance system. Three services: a **FastAPI
backend**, a **React admin portal** (desktop), and a **React student webapp**
(mobile-first, opened in a phone's browser). This file is the single
step-by-step guide to get from a clean checkout to all three running —
**on this machine or any other**.

For credentials, troubleshooting, and design rationale beyond the setup
steps, see [SETUP.md](SETUP.md).

---

## 1. What's in this repo

```
attendance_system/
├── README.md              ← you are here — setup & run guide
├── SETUP.md                ← credentials, troubleshooting, architecture notes
├── docker-compose.yml        ← the whole stack: db, redis, backend, admin-portal, student-webapp
├── docker-up.ps1               ← builds + starts everything in Docker (§4, recommended)
├── docker-down.ps1              ← stops it
├── db-init/                       ← Postgres init scripts (auto-enables PostGIS on first boot)
├── start-all.ps1                    ← runs everything from local Python/Node instead (§5, alternative)
├── stop-all.ps1                      ← stops that
├── run-mobile-web.ps1                  ← connects a phone over USB via `adb reverse` (§7)
├── backend/                              FastAPI + SQLAlchemy (async) + Alembic + InsightFace
│   ├── Dockerfile                          builds the backend image; bakes in the face model
│   ├── docker_entrypoint.py                 waits for db → migrates → seeds admin → serves
│   ├── app/
│   │   ├── main.py                            app entrypoint, CORS, router mounting
│   │   ├── seed.py                              creates the default admin account (idempotent)
│   │   ├── core/                                 config.py (Settings), security.py (JWT), deps.py (RBAC)
│   │   ├── models/                                SQLAlchemy models
│   │   ├── schemas/                                Pydantic request/response models
│   │   ├── crud/                                    DB query helpers
│   │   ├── services/                                 face_service.py (InsightFace), storage.py
│   │   └── api/v1/endpoints/                          auth, users, classes, face_enrollments, announcements, attendance
│   ├── alembic/versions/                                DB migrations
│   ├── tests/                                             pytest suite
│   ├── uploads/                                             face enrollment images (gitignored)
│   ├── requirements.txt
│   └── .env / .env.example                                   only used by the non-Docker path (§5)
├── admin-portal/            React + TypeScript + Vite — admin/super_admin only
│   ├── Dockerfile             multi-stage: Node build → nginx serving the static bundle
│   └── src/{api,auth,components,pages}/
├── student-webapp/          React + TypeScript + Vite — the phone-facing client
│   ├── Dockerfile             same multi-stage pattern
│   └── src/{api,auth,components,pages}/, config.ts
└── mobile/                  earlier Flutter attempt — reference only, not run (see SETUP.md §0)
```

---

## 2. Prerequisites

**Docker path (recommended — this is the only thing you need):**

| Tool | Check |
|---|---|
| Docker Desktop | `docker --version` |

Nothing else. Python and Node.js run **only inside the containers** —
neither needs to be installed on the host at all.

**Manual path (§5, for active local development with hot reload):**

| Tool | Version | Check |
|---|---|---|
| Python | 3.13 | `python --version` |
| Docker Desktop | any recent | for Postgres+PostGIS and Redis only |
| Node.js | 18+ | `node --version` |

All commands below are PowerShell, run from the **repo root**.

---

## 3. Why Docker is the recommended path

Every dependency the project needs — the exact Python version, InsightFace's
native libraries, Node's build toolchain, Postgres+PostGIS, Redis — is
declared in a Dockerfile and built inside a Linux container, identically on
every machine. That specifically avoids the failure modes that hit when
moving this project to a different laptop:

- No "Python 3.13 not found" / wrong-Python-on-PATH issues — the backend
  image pins its own Python 3.12.
- No Windows-vs-Linux native binary mismatches in `node_modules` (Vite's
  `esbuild`/`rollup` ship OS-specific binaries) — `npm ci` runs *inside* the
  Linux build stage, never touching whatever's on the host.
- No missing `libgomp`/`libGL` errors from onnxruntime/opencv — installed
  in the image via `apt-get`.
- No slow/flaky first face-enrollment request — the ~280MB InsightFace
  model is downloaded once at **image build time**, not on first use.
- No manual `.env` file to create, no manual `CREATE EXTENSION postgis`,
  no manual Alembic migration step, no manual admin-account SQL — all of
  it happens automatically every time the backend container starts
  (`backend/docker_entrypoint.py`), idempotently.
- No `CORS`/IP hardcoding — the backend's CORS accepts `localhost` or any
  LAN IP on the known ports (`app/core/config.py`), and the student
  webapp derives its own backend URL from `window.location.hostname` at
  runtime. Nothing to edit when moving to a different network.

---

## 4. Docker path — first run and every run after

```powershell
.\docker-up.ps1
```

That's it. On a brand new machine this one command:
1. Starts Docker Desktop if it isn't running.
2. Builds all three images (backend, admin-portal, student-webapp) —
   the first build takes several minutes (Python deps + the face model
   download + two Node builds); every build after that is fast thanks to
   Docker's layer cache.
3. Starts Postgres+PostGIS (auto-creates the `postgis` extension on first
   boot via `db-init/`) and Redis.
4. Starts the backend, which waits for the database, runs migrations, and
   seeds a default admin account — automatically, every time, and safely
   repeatable.
5. Starts the admin portal and student webapp, each served by nginx.
6. Self-heals the two Windows Firewall rules needed for a phone to reach
   the webapp over Wi-Fi (one-time UAC prompt).
7. Prints every URL.

```powershell
.\docker-up.ps1 -Rebuild     # force a full rebuild (after changing requirements.txt/package.json)
.\docker-down.ps1            # stop everything
.\docker-down.ps1 -Wipe      # stop everything AND delete all data (fresh start)
docker compose logs -f       # tail logs from every container
docker compose logs -f backend   # just the backend
```

Re-running `.\docker-up.ps1` is always safe — data in Postgres persists
across restarts (it's a named volume), and the seed step is idempotent so
it won't touch an admin account that already exists.

### Verify it's up

```powershell
curl http://localhost:8000/health     # {"status":"ok"}
curl http://localhost:5173/           # admin portal HTML
curl http://localhost:5174/           # student webapp HTML
```

---

## 5. Manual path — for active local development

Prefer this only if you're actively editing backend/frontend code and want
instant hot reload without a Docker rebuild each time. Postgres and Redis
still run in Docker either way.

### 5.1 Python virtualenv + backend dependencies

The virtualenv lives at the **repo root** (`.venv/`), not inside `backend/`.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

### 5.2 Backend environment file

```powershell
cd backend
copy .env.example .env
cd ..
```

### 5.3 Start Postgres + Redis

```powershell
docker compose up -d db redis
```

PostGIS is enabled automatically on first boot via `db-init/01-postgis.sql`
— no manual step needed.

### 5.4 Run database migrations

```powershell
cd backend
..\.venv\Scripts\python.exe -m alembic upgrade head
cd ..
```

### 5.5 Seed the default admin account (optional, one time)

```powershell
cd backend
..\.venv\Scripts\python.exe -m app.seed
cd ..
```

### 5.6 Install frontend dependencies

```powershell
cd admin-portal
npm install
cd ..\student-webapp
npm install
cd ..
```

### 5.7 Run everything

```powershell
.\start-all.ps1
```

Or manually in three terminals — see
[SETUP.md §7](SETUP.md#7-start-allps1-reference) for the exact commands
and flags (`-Lan:$false`, `-NoPortal`, `-NoStudentApp`, `-NoBackend`).

---

## 6. Executing individual files / commands

| Task | Command |
|---|---|
| Run the backend API directly (manual path) | `cd backend; ..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| Run backend tests | `cd backend; ..\.venv\Scripts\python.exe -m pytest` |
| Create a new migration after changing a model | `cd backend; ..\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "describe change"` |
| Apply migrations | `cd backend; ..\.venv\Scripts\python.exe -m alembic upgrade head` |
| Run the admin portal directly (manual path) | `cd admin-portal; npm run dev` |
| Run the student webapp directly (manual path) | `cd student-webapp; npm run dev` |
| Rebuild one Docker image | `docker compose build backend` (or `admin-portal` / `student-webapp`) |
| Restart one container | `docker compose restart backend` |
| Open a psql shell in the DB container | `docker exec -it attendance_system-db-1 psql -U attendance -d attendance` |
| Open a shell inside the backend container | `docker compose exec backend bash` |

---

## 7. Using it on a phone

The student webapp is what a phone opens. Two connection methods —
**USB is recommended**, it has no Wi-Fi/firewall/subnet failure modes:

```powershell
.\run-mobile-web.ps1
```

Plug the phone in via USB with USB debugging enabled, run the script, then
open **`http://localhost:5174`** in the phone's Chrome. It works because
`adb reverse` tunnels the phone's own `localhost` ports to this PC over the
cable — no IP address, firewall rule, or shared Wi-Fi network involved.
This works identically whether the backend/webapp are running in Docker or
manually, since it just tunnels TCP ports.

If USB isn't available, use the same Wi-Fi network instead: find this
machine's LAN IP (`ipconfig`) and open `http://<this-machine's-LAN-IP>:5174`
on the phone — `docker-up.ps1`/`start-all.ps1` already create the firewall
rules this needs. Full details in
[SETUP.md §6](SETUP.md#6-connecting-a-phone-to-the-student-webapp).

---

## 8. Default credentials

| Email | Password | Role | Use for |
|---|---|---|---|
| `portaladmin@example.com` | `password123` | admin | Admin portal login — **created automatically** by the backend on first startup (`app/seed.py`), Docker or manual path alike |

To create more accounts, register via the student webapp (always creates a
`student`) and promote via SQL — see
[SETUP.md §8](SETUP.md#8-credentials--accounts-currently-in-the-dev-database).

---

## 9. Ports & URLs

| Service | URL | Notes |
|---|---|---|
| Backend API | `http://localhost:8000` (or `http://<LAN-IP>:8000`) | |
| API docs (Swagger) | `http://localhost:8000/docs` | |
| Admin portal | `http://localhost:5173` | desktop browser only |
| Student webapp | `http://localhost:5174` (or `http://<LAN-IP>:5174`) | open this on the phone |
| Postgres | `localhost:5432` | db/user/pass: `attendance`/`attendance`/`attendance` |
| Redis | `localhost:6379` | provisioned, not yet used by any feature |

---

## 10. What's built so far

Register → login → face enrollment (2-shot capture) → admin
approve/reject/request-resubmission (computes the trusted face embedding
only on approval) → live attendance matching against the approved
embedding, with borderline matches flagged for review instead of
auto-accepted.

A matched face only records attendance once the student is assigned to a
class — admin portal → **Classes** lets you create classes and assign each
student to one.

Admin portal also has **Announcements** (post updates, see likes/comments
from students) and **Attendance** (every marked record, filterable by
class, with CSV export). The student webapp's home screen shows the live
announcement feed with like/comment.

Not yet built: schedules, geo-fencing, leave management, chat,
assignments — see [SETUP.md §13](SETUP.md#13-known-gaps--next-steps).

---

## 11. Troubleshooting

Full table in [SETUP.md §12](SETUP.md#12-troubleshooting). Quick pointers:

- **Anything won't start** → `docker compose logs -f` (or `logs -f backend`
  for just that service) — the entrypoint prints exactly what step it's on
  (waiting for db / migrating / seeding / serving).
- **Phone can't reach anything** → use `.\run-mobile-web.ps1` (§7); it
  sidesteps Wi-Fi/firewall issues entirely.
- **Rebuilt but still seeing old behavior** → `.\docker-up.ps1 -Rebuild`
  forces a clean rebuild with no layer cache.
- **Want a totally fresh database** → `.\docker-down.ps1 -Wipe` then
  `.\docker-up.ps1`.
- **CORS error in a browser console** → check `app/core/config.py`'s
  `CORS_ORIGINS` / `CORS_ORIGIN_REGEX` covers the origin shown in the
  error (it should already cover `localhost`/any LAN IP on ports
  3000/5173/5174 out of the box).
