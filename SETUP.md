# Attendance System — Setup & Operations Guide

Everything needed to run the three parts of this project: the **backend
API**, the **admin portal**, and the **student webapp** (the phone-facing
client — see §0 for why this replaced a native Android app).

> This is milestone 1–2 of the full project brief: auth, RBAC, the full DB
> schema, and the face-enrollment/approval/attendance-matching pipeline.
> Schedule/geo-fence config, leave management, announcements, chat, and
> assignments are not built yet.

## Quick start

```powershell
.\start-all.ps1
```

Starts Docker (Postgres+PostGIS, Redis), runs migrations, and launches the
backend + admin portal + student webapp each in their own window. See §12 if
something doesn't come up.

---

## 0. Why a webapp instead of an Android app

A native Flutter/Android app was built first, but installing it on a real
device turned into a dead end: MIUI (Xiaomi) blocks `adb install` with
`INSTALL_FAILED_USER_RESTRICTED` regardless of USB vs. wireless debugging,
and side-loading via browser download worked but was still one more
install/permissions step for every device. The Flutter project is still in
`mobile/` for reference but is no longer the delivery path.

**`student-webapp/`** does the same job (register, login, face enrollment,
attendance marking) as a mobile-responsive website. A phone on the same
Wi-Fi just opens a URL in Chrome — no install, no adb, no MIUI restriction,
no Android cleartext-traffic policy to fight.

---

## 1. Architecture at a glance

```
                    ┌──────────────────────┐
                    │   PostgreSQL+PostGIS   │  :5432
                    │   Redis (provisioned,  │  :6379
                    │   unused so far)       │
                    └──────────┬────────────┘
                               │
                    ┌──────────▼────────────┐
                    │   FastAPI backend      │  :8000
                    │   (Python 3.13, venv)  │
                    └──────┬───────────┬─────┘
                           │           │
              ┌────────────▼──┐   ┌────▼───────────────┐
              │  Admin portal  │   │  Student webapp     │
              │  React+Vite    │   │  React+Vite          │
              │  :5173         │   │  :5174 (LAN-bound)   │
              │  desktop only  │   │  open on phone's     │
              │                │   │  browser, same Wi-Fi │
              └────────────────┘   └─────────────────────┘
```

- **Backend**: `backend/` — FastAPI + SQLAlchemy (async) + Alembic +
  InsightFace (self-hosted ArcFace-style face embeddings, CPU).
- **Admin portal**: `admin-portal/` — React + TypeScript + Vite, admin/
  super_admin only.
- **Student webapp**: `student-webapp/` — React + TypeScript + Vite, any
  authenticated role, camera capture via `<input capture="user">`, designed
  mobile-first for phone browsers.
- **`mobile/`** — the earlier Flutter attempt. Kept for reference, not run.

---

## 2. Prerequisites

| Tool | Version used | Notes |
|---|---|---|
| Python | 3.13 | `python --version` |
| Docker Desktop | any recent | Postgres+PostGIS and Redis |
| Node.js | 18+ | admin portal + student webapp |

---

## 3. Backend setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate              # Windows
pip install -r requirements.txt
cp .env.example .env                # already done in this repo; edit if needed
```

### 3.1 Start Postgres + Redis

From the **repo root**:
```bash
docker compose up -d db redis
```

First time only — enable PostGIS:
```bash
docker exec attendance_system-db-1 psql -U attendance -d attendance -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

### 3.2 Run migrations
```bash
cd backend
python -m alembic upgrade head
```

### 3.3 Run the API server

**LAN-reachable** (needed so a phone can reach it — this is the default
`start-all.ps1` uses):
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Local-only**:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Health check: http://127.0.0.1:8000/health
Interactive API docs: http://127.0.0.1:8000/docs

### 3.4 Backend configuration (`backend/.env`)

```env
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://attendance:attendance@localhost:5432/attendance
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://localhost:5174","http://192.168.1.5:5174"]
```

- `SECRET_KEY` is a dev placeholder — **rotate before any real deployment**,
  it signs JWTs.
- `CORS_ORIGINS` must include every origin a browser-based client is served
  from — both the admin portal's and student webapp's ports/IPs are already
  listed above.
- Face enrollment images are stored on local disk at `backend/uploads/`
  (gitignored) — a stand-in for S3-style object storage.
- The InsightFace `buffalo_l` model (~280MB) downloads once to
  `~/.insightface/models/buffalo_l/` on first use and is cached after that.

---

## 4. Admin portal setup

```bash
cd admin-portal
npm install
npm run dev
```

Opens on **http://localhost:5173** (desktop only — not meant to be opened on
a phone). Only `admin`/`super_admin` accounts can log in.

Talks to the backend at `http://localhost:8000` (hardcoded as `API_ORIGIN` in
`admin-portal/src/api/client.ts`).

**What's built**: Login · Dashboard (pending/approved/rejected counts) ·
Face Enrollments queue (image previews, Approve / Reject-with-reason /
Request resubmission).

---

## 5. Student webapp setup

```bash
cd student-webapp
npm install
npm run dev
```

Vite is configured (`student-webapp/vite.config.ts`) to bind `0.0.0.0:5174`,
so it's reachable both at `http://localhost:5174` (this PC) and
`http://<LAN-IP>:5174` (any phone on the same Wi-Fi).

**What's built**: Register · Login (session persisted in `localStorage`,
auto-restored) · Home (profile + live enrollment status from
`/face-enrollments/me`) · Face enrollment (2-shot guided capture via the
phone's camera, submits to `POST /face-enrollments`) · Mark attendance
(single live capture, submits to `POST /face-enrollments/match`, shows
matched/needs-review/no-match with the similarity score).

### Configuration (`student-webapp/src/config.ts`)

```ts
export const API_ORIGIN = 'http://192.168.1.5:8000';
```

**Hardcoded to this machine's current LAN IP.** If it changes (different
network, DHCP renewal), update this constant — no rebuild needed, Vite
picks it up live in dev mode.

---

## 6. Connecting a phone to the student webapp (and the webapp to the backend)

1. **Find this machine's LAN IP**: `ipconfig` → the adapter actually bridged
   to your router. On this machine that's `vEthernet (Lab_Switch)` →
   `192.168.1.5` — *not* the Wi-Fi adapters, which are unused here (Hyper-V's
   external switch bridges the physical NIC instead).
2. **Backend must bind `0.0.0.0`**, not `127.0.0.1` (§3.3 / default in
   `start-all.ps1`).
3. **Open the Windows Firewall** for both ports (run as Administrator —
   Claude Code cannot do this itself, no elevated shell access):
   ```powershell
   New-NetFirewallRule -DisplayName "Attendance Backend" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
   New-NetFirewallRule -DisplayName "Attendance Student Webapp" -Direction Inbound -Protocol TCP -LocalPort 5174 -Action Allow
   ```
   `start-all.ps1` checks for these on every run and prints the exact
   command again if either is missing.
4. **Phone must be on the same Wi-Fi network** as this machine — same
   router; guest networks / AP client-isolation will break this even on the
   "same" Wi-Fi (see §12).
5. On the phone, open **`http://192.168.1.5:5174`** in Chrome. Bookmark it —
   there's nothing to install.
6. `student-webapp/src/config.ts`'s `API_ORIGIN` must match the backend's
   LAN IP (already set to `192.168.1.5`).

### Verify connectivity independent of the app

On the phone's browser, visit `http://192.168.1.5:8000/health` — you should
see `{"status":"ok"}`. If that fails, it's a network/firewall problem
upstream of the webapp; fix that before debugging the app itself.

---

## 7. `start-all.ps1` reference

```powershell
.\start-all.ps1                    # everything, backend bound to 0.0.0.0
.\start-all.ps1 -Lan:$false         # backend bound to 127.0.0.1 (no phone testing)
.\start-all.ps1 -NoPortal           # skip the admin portal
.\start-all.ps1 -NoStudentApp       # skip the student webapp
.\start-all.ps1 -NoBackend          # skip the backend (e.g. already running)
```

It's idempotent — re-running stops any previous uvicorn/vite instances it
started before launching fresh ones, so ports never collide. It also warns
if `student-webapp/src/config.ts`'s IP doesn't match the machine's current
LAN IP, and if either firewall rule from §6 is missing.

---

## 8. Credentials & accounts currently in the dev database

| Email | Password | Role | Notes |
|---|---|---|---|
| `portaladmin@example.com` | `password123` | admin | Log into the **admin portal** with this |
| `mobiletest@example.com` | `password123` | student | Test account, no face enrollment |

To create more admin accounts (no user-management UI yet):
```bash
# 1. Register normally via the student webapp or POST /auth/register — always creates a student.
# 2. Promote via SQL:
docker exec attendance_system-db-1 psql -U attendance -d attendance -c "UPDATE users SET role='ADMIN' WHERE email='someone@example.com';"
```

Every account uses the same JWT secret (`SECRET_KEY` in `.env`) — tokens
aren't portable across environments with different secrets.

---

## 9. Ports & URLs reference

| Service | URL | Notes |
|---|---|---|
| Backend API | `http://192.168.1.5:8000` / `http://localhost:8000` | bind `0.0.0.0` for phone access |
| API docs (Swagger) | `http://localhost:8000/docs` | |
| Admin portal | `http://localhost:5173` | desktop only |
| Student webapp | `http://192.168.1.5:5174` / `http://localhost:5174` | open on the phone |
| Postgres | `localhost:5432` | user/pass/db: `attendance`/`attendance`/`attendance` |
| Redis | `localhost:6379` | provisioned, not yet used by any feature |

---

## 10. Directory reference

```
attendance_system/
├── SETUP.md                  ← this file
├── start-all.ps1              ← starts everything (see §7)
├── docker-compose.yml         ← Postgres+PostGIS, Redis, backend service
├── .gitignore
├── backend/
│   ├── app/
│   │   ├── main.py             FastAPI app entrypoint
│   │   ├── core/                config.py, security.py (JWT), deps.py (RBAC)
│   │   ├── models/               SQLAlchemy models (one file per domain)
│   │   ├── schemas/              Pydantic request/response models
│   │   ├── crud/                  DB query helpers
│   │   ├── services/               face_service.py (InsightFace), storage.py
│   │   └── api/v1/endpoints/       auth.py, users.py, face_enrollments.py
│   ├── alembic/versions/           migrations
│   ├── uploads/                     face enrollment images (gitignored)
│   ├── requirements.txt
│   └── .env / .env.example
├── admin-portal/
│   └── src/
│       ├── api/                     client.ts, types.ts
│       ├── auth/                     AuthContext.tsx, ProtectedRoute.tsx
│       ├── components/               Layout.tsx, AuthImage.tsx
│       └── pages/                    LoginPage, DashboardPage, EnrollmentsPage
├── student-webapp/
│   └── src/
│       ├── config.ts                 ← API_ORIGIN (LAN IP)
│       ├── api/                       client.ts, types.ts
│       ├── auth/                       AuthContext.tsx, ProtectedRoute.tsx
│       ├── components/                 TopBar.tsx
│       └── pages/                      LoginPage, RegisterPage, HomePage,
│                                        EnrollPage, AttendancePage
└── mobile/                    ← earlier Flutter attempt, kept for reference, not run
```

---

## 11. End-to-end walkthrough

1. **Register** — student webapp's "Create an account", or
   `POST /api/v1/auth/register`. Always creates a `student` account.
2. **Submit face enrollment** — student webapp → Home → "Start enrollment" →
   take 2 photos → submit. Backend runs quality checks (single face, size,
   blur) before accepting.
3. **Approve/reject in the admin portal** — log in as
   `portaladmin@example.com` → Face Enrollments → review the images →
   Approve (computes the trusted embedding from the stored photos) or Reject
   (reason required).
4. **Mark attendance** — student webapp → Home → "Mark attendance" (only
   shown once approved) → live capture → compares against the approved
   embedding, creates an `AttendanceRecord` on a confident match, flags
   borderline matches for review instead of auto-accepting.

---

## 12. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Phone can't reach the student webapp at all | Backend/webapp bound to `127.0.0.1` | Use `start-all.ps1` defaults (`0.0.0.0`) or pass `-Lan` explicitly |
| Phone can't reach the student webapp | Windows Firewall blocking port 5174 or 8000 | Run the `New-NetFirewallRule` commands in §6 (needs an elevated PowerShell) |
| Phone can't reach the student webapp | Phone and PC on different networks/subnets, or router has AP/client isolation | Confirm both devices' IPs share the same `/24` (e.g. both `192.168.1.x`); some guest Wi-Fi networks block device-to-device traffic — use the main network |
| Webapp loads but API calls fail | PC's LAN IP changed since `config.ts` was set | Re-run `ipconfig`, update `student-webapp/src/config.ts`'s `API_ORIGIN` and `backend/.env`'s `CORS_ORIGINS` to match |
| Admin portal shows a CORS error in the browser console | Portal's origin not in backend's `CORS_ORIGINS` | Add it to `backend/.env`, restart uvicorn |
| Camera capture button does nothing on phone | Site opened over `http://` from a browser that requires a secure context for camera, or camera permission denied | Chrome allows camera on LAN-IP `http://` for local/private addresses; if blocked, check site permissions in Chrome settings |
| Alembic autogenerate wants to drop `tiger`/`topology`/PostGIS tables | Those come from the `postgis/postgis` Docker image's bundled extensions | Already handled — `alembic/env.py`'s `include_object` filter ignores tables not in our own models |
| `insightface`/`onnxruntime` import errors | Dependencies not installed in the venv | `pip install -r backend/requirements.txt` (pinned versions confirmed working on Python 3.13) |
| First face-enrollment request is slow (~1 min) | InsightFace downloading the `buffalo_l` model (~280MB) on first use | One-time; cached afterward at `~/.insightface/models/buffalo_l/` |
| `start-all.ps1` fails at "Backend virtualenv not found" | Backend never set up | Follow §3 first |

---

## 13. Known gaps / next steps

- No password-reset / forgot-password flow.
- No admin UI for creating other admin/teacher accounts (SQL workaround in §8).
- Schedule, geo-fence, leave management, announcements, chat, and
  assignments are not built (see the original project brief, milestones 3–6).
- `SECRET_KEY`, DB password, and other dev defaults must be changed before
  any real deployment.
- The student webapp's camera capture (`<input capture="user">`) opens the
  phone's native camera app rather than an in-page live preview — simpler
  and more reliable across browsers, but less polished than a custom
  `getUserMedia` preview would be.
