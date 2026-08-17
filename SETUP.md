# Attendance System — Setup & Operations Guide

This covers everything needed to run the three parts of this project locally
or on a fresh machine: the **backend API**, the **admin portal**, and the
**Android mobile app**. It also documents current dev credentials, IPs, ports,
and known gotchas so nothing has to be rediscovered.

> This is milestone 1–2 of the full brief: auth, RBAC, the full DB schema, and
> the face-enrollment/approval/attendance-matching pipeline. Schedule/geo-fence
> config, leave management, announcements, chat, and assignments are not built
> yet.

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
              │  Admin portal  │   │  Android app        │
              │  React+Vite    │   │  Flutter (Kotlin/   │
              │  :5173         │   │  Java on Android)   │
              └────────────────┘   └─────────────────────┘
```

- **Backend**: `backend/` — FastAPI + SQLAlchemy (async) + Alembic + InsightFace
  (self-hosted ArcFace-style face embeddings, CPU).
- **Admin portal**: `admin-portal/` — React 19 + TypeScript + Vite, no UI
  framework (hand-rolled CSS matching the app's brand colors).
- **Mobile app**: `mobile/` — Flutter, Android target only so far (`android/`
  folder configured; iOS was not scaffolded).

---

## 2. Prerequisites

| Tool | Version used | Notes |
|---|---|---|
| Python | 3.13 | `python --version` |
| Docker Desktop | any recent | for Postgres+PostGIS and Redis |
| Node.js | 18+ | for the admin portal |
| Flutter SDK | 3.44+ | only needed if you want to rebuild the mobile app from source |
| Android SDK / platform-tools (`adb`) | via Android Studio or Flutter's SDK manager | only needed for USB/wireless install or rebuilding |

On this machine, Flutter + Android SDK were already installed at:
- Flutter: `C:\Users\Expert\flutter`
- Android SDK: `C:\Users\Expert\AppData\Local\Android\sdk`
- `adb.exe`: `C:\Users\Expert\AppData\Local\Android\sdk\platform-tools\adb.exe`

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

From the **repo root** (docker-compose.yml lives there, not in backend/):

```bash
docker compose up -d db redis
```

First time only — enable PostGIS on the database:

```bash
docker exec <db-container-name> psql -U attendance -d attendance -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

Container name in this setup: `attendance_system-db-1`.

### 3.2 Run migrations

```bash
cd backend
python -m alembic upgrade head
```

### 3.3 Run the API server

**Local-only** (only reachable from this machine):
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**LAN-reachable** (needed for the mobile app on a phone over Wi-Fi):
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Health check: http://127.0.0.1:8000/health
Interactive API docs: http://127.0.0.1:8000/docs
OpenAPI schema: http://127.0.0.1:8000/api/v1/openapi.json

### 3.4 Backend configuration (`backend/.env`)

```env
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://attendance:attendance@localhost:5432/attendance
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

- `SECRET_KEY` is a dev placeholder — **rotate before any real deployment**,
  it signs JWTs.
- `CORS_ORIGINS` must include whatever origin the admin portal is served from
  (default Vite dev server is `http://localhost:5173`).
- Face enrollment images are stored on local disk at `backend/uploads/`
  (gitignored — this is a stand-in for S3-style object storage described in
  the project brief).
- The InsightFace `buffalo_l` model (~280MB) downloads once to
  `C:\Users\<you>\.insightface\models\buffalo_l\` on first use and is cached
  after that.

---

## 4. Admin portal setup

```bash
cd admin-portal
npm install
npm run dev
```

Opens on **http://localhost:5173**.

- Only `admin` / `super_admin` role accounts can log in (student/teacher
  accounts are rejected client- and server-side).
- The portal talks to the backend at `http://localhost:8000` (hardcoded in
  `admin-portal/src/api/client.ts` as `API_ORIGIN`) — change that constant if
  the backend moves elsewhere.
- Production build: `npm run build` → output in `admin-portal/dist/`.

### What's in the portal today

- **Login** (`/login`)
- **Dashboard** (`/`) — pending/approved/rejected enrollment counts
- **Face Enrollments** (`/enrollments`) — filterable queue, image previews,
  Approve / Reject (reason required) / Request resubmission

---

## 5. Mobile app setup

### Option A — Rebuild from source (requires Flutter SDK)

```bash
cd mobile
flutter pub get
flutter build apk --debug
```

Output: `mobile/build/app/outputs/flutter-apk/app-debug.apk`

### Option B — Install the prebuilt APK without rebuilding

A copy is kept at `apk_release/attendance-app.apk` and can be served over the
LAN for direct phone download (see §6.3).

### Mobile app configuration

`mobile/lib/config.dart`:
```dart
const String apiBaseUrl = 'http://192.168.1.5:8000/api/v1';
```

This is **hardcoded to this machine's current LAN IP**. If the backend
machine's IP changes (different network, DHCP renewal, etc.), update this
constant and rebuild (`flutter build apk --debug`), or see §6.4 for a
USB-based alternative that doesn't need a rebuild.

App icon / splash: generated from `mobile/assets/icon/app_icon.png` via
`flutter_launcher_icons` and `flutter_native_splash` (see
`mobile/pubspec.yaml` for their config blocks). Re-run after changing the
icon:
```bash
dart run flutter_launcher_icons
dart run flutter_native_splash:create
```

---

## 6. Connecting the mobile app to the backend

The phone and the backend machine must be able to reach each other. Two
approaches:

### 6.1 Same Wi-Fi network (no cable, what the APK is currently built for)

1. Confirm this machine's LAN IP (Windows): `ipconfig` → look for the
   adapter actually bridged to your router (on this machine that's
   **`vEthernet (Lab_Switch)` → `192.168.1.5`**, *not* the Wi-Fi adapters,
   which are unused/disconnected here — Hyper-V's external switch bridges the
   physical NIC).
2. Start the backend bound to `0.0.0.0` (§3.3), not `127.0.0.1`.
3. **Open the Windows Firewall** for the ports in use (run as Administrator —
   Claude Code cannot do this itself, no elevated shell access):
   ```powershell
   New-NetFirewallRule -DisplayName "Attendance Backend" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
   New-NetFirewallRule -DisplayName "Attendance APK Server" -Direction Inbound -Protocol TCP -LocalPort 8090 -Action Allow
   ```
   (Already run on this machine — both rules exist and are enabled.)
4. Make sure the phone is on the **same Wi-Fi network** as this machine
   (same router; guest networks / AP client-isolation will break this even on
   the "same" Wi-Fi — see troubleshooting).
5. `mobile/lib/config.dart` must point at that IP (already set to
   `192.168.1.5`, see §5).
6. `mobile/android/app/src/main/res/xml/network_security_config.xml` must
   list that IP under cleartext-permitted domains (Android blocks plain HTTP
   by default) — already includes `192.168.1.5`, `localhost`, `127.0.0.1`,
   `10.0.2.2` (emulator alias).

### 6.2 Verify connectivity independent of the app

On the phone's browser, visit `http://192.168.1.5:8000/health` — you should
see `{"status":"ok"}`. If that fails, it's a network/firewall problem, not an
app bug — fix that first before touching the app.

### 6.3 Installing the APK (MIUI/Xiaomi note)

`adb install` was blocked on this phone (`INSTALL_FAILED_USER_RESTRICTED`)
even with wireless debugging authorized — this is MIUI's "Install via USB"
restriction, independent of the USB-vs-wireless ADB transport. Two ways
around it:

**A. Direct browser download (used here, no adb needed):**
```bash
cd apk_release
python -m http.server 8090 --bind 0.0.0.0
```
Then on the phone (same Wi-Fi), open `http://192.168.1.5:8090/attendance-app.apk`
in Chrome, download it, tap the downloaded file, allow "install from this
source" if prompted, install.

**B. Fix the MIUI restriction and use adb normally:**
Settings → Additional settings → Developer options → enable **"Install via
USB"** (may require a SIM card + Mi account verification on some MIUI
versions). Then:
```bash
adb install -r mobile/build/app/outputs/flutter-apk/app-debug.apk
```

### 6.4 Alternative: USB + adb reverse (no LAN/firewall needed at all)

If Wi-Fi connectivity is inconvenient, plug the phone in via USB (enable
"USB debugging" in Developer options, accept the RSA key prompt on the
phone), then:
```bash
adb reverse tcp:8000 tcp:8000
```
This tunnels the phone's `localhost:8000` to the backend running on the dev
machine — no firewall rules, no LAN IP needed. It requires `apiBaseUrl` in
`config.dart` to be `http://localhost:8000/api/v1` instead of the LAN IP
(that was the original config before switching to LAN mode; swap back and
rebuild if you want to use this path instead).

---

## 7. Credentials & accounts currently in the dev database

| Email | Password | Role | Notes |
|---|---|---|---|
| `portaladmin@example.com` | `password123` | admin | Use this to log into the **admin portal** |
| `mobiletest@example.com` | `password123` | student | Test account, no face enrollment |
| `naveen@codearrive.com` | *(set on device)* | student | Created via the mobile app during testing |

To create more admin accounts, either:
- Use the admin portal itself once logged in as an existing admin — no UI
  for user management yet, so for now:
- Register normally (always creates a `student` via `POST /auth/register`),
  then promote via SQL:
  ```bash
  docker exec attendance_system-db-1 psql -U attendance -d attendance -c "UPDATE users SET role='ADMIN' WHERE email='someone@example.com';"
  ```

**Every account uses the same JWT secret** (`SECRET_KEY` in `.env`) — tokens
aren't portable across environments with different secrets.

---

## 8. Ports & URLs reference

| Service | URL | Notes |
|---|---|---|
| Backend API | `http://192.168.1.5:8000` / `http://localhost:8000` | bind `0.0.0.0` for LAN access |
| API docs (Swagger) | `http://localhost:8000/docs` | |
| Admin portal | `http://localhost:5173` | `npm run dev` in `admin-portal/` |
| Postgres | `localhost:5432` | user/pass/db: `attendance`/`attendance`/`attendance` |
| Redis | `localhost:6379` | provisioned, not yet used by any feature |
| APK download server (temporary) | `http://192.168.1.5:8090/attendance-app.apk` | only while `python -m http.server 8090` is running in `apk_release/` |

---

## 9. Directory reference

```
attendance_system/
├── SETUP.md                  ← this file
├── docker-compose.yml        ← Postgres+PostGIS, Redis, backend service
├── .gitignore
├── backend/
│   ├── app/
│   │   ├── main.py           ← FastAPI app entrypoint
│   │   ├── core/              config.py, security.py (JWT), deps.py (RBAC)
│   │   ├── models/            SQLAlchemy models (one file per domain)
│   │   ├── schemas/           Pydantic request/response models
│   │   ├── crud/               DB query helpers
│   │   ├── services/           face_service.py (InsightFace), storage.py
│   │   └── api/v1/endpoints/   auth.py, users.py, face_enrollments.py
│   ├── alembic/versions/       migrations
│   ├── uploads/                 face enrollment images (gitignored)
│   ├── requirements.txt
│   ├── .env / .env.example
│   └── README.md
├── admin-portal/
│   ├── src/
│   │   ├── api/                 client.ts, types.ts
│   │   ├── auth/                 AuthContext.tsx, ProtectedRoute.tsx
│   │   ├── components/           Layout.tsx, AuthImage.tsx
│   │   └── pages/                LoginPage, DashboardPage, EnrollmentsPage
│   └── README.md
├── mobile/
│   ├── lib/
│   │   ├── config.dart           ← apiBaseUrl (LAN IP)
│   │   ├── api/                   api_client.dart, auth_api.dart
│   │   ├── providers/             auth_provider.dart
│   │   ├── screens/               loading/login/register/home
│   │   └── theme.dart
│   ├── android/app/src/main/
│   │   ├── AndroidManifest.xml    ← INTERNET permission, network security config ref
│   │   └── res/xml/network_security_config.xml  ← cleartext-allowed hosts
│   └── assets/icon/app_icon.png
└── apk_release/
    └── attendance-app.apk    ← prebuilt debug APK for direct install
```

---

## 10. End-to-end walkthrough (what works today)

1. **Register a student** — via the mobile app ("New student? Create an
   account") or `POST /api/v1/auth/register`. Always creates a `student`
   account.
2. **Submit face enrollment** — not yet wired into the mobile UI (see §11);
   can be exercised directly against the API (`POST /api/v1/face-enrollments`,
   multipart, 2–5 images) or via a REST client.
3. **Approve/reject in the admin portal** — log in as
   `portaladmin@example.com`, go to **Face Enrollments**, review the
   submitted images, Approve (computes the trusted embedding) or Reject
   (with a reason).
4. **Mark attendance by face** — `POST /api/v1/face-enrollments/match` with a
   live capture; compares against the approved embedding, creates an
   `AttendanceRecord` on a confident match. Not yet wired into the mobile UI.
5. **Everything else in the mobile app today**: register, login/logout
   (JWT access+refresh, auto-restored on relaunch), home screen showing
   name/email/role/status.

---

## 11. Known gaps / next steps

- Mobile app has no camera capture UI yet for enrollment or attendance
  marking — those flows only exist as backend endpoints right now. The home
  screen shows a "coming soon" placeholder card for face enrollment.
- No password-reset / forgot-password flow.
- No admin UI for creating other admin/teacher accounts (SQL workaround in
  §7).
- Schedule, geo-fence, leave management, announcements, chat, and
  assignments are not built (see the original project brief, milestones 3–6).
- `SECRET_KEY`, DB password, and other dev defaults must be changed before
  any real deployment.

---

## 12. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Mobile app can't reach backend | Backend bound to `127.0.0.1` instead of `0.0.0.0` | Restart uvicorn with `--host 0.0.0.0` |
| Mobile app can't reach backend | Windows Firewall blocking port 8000 | Run the `New-NetFirewallRule` commands in §6.1 (needs an elevated PowerShell) |
| Mobile app can't reach backend | Phone and PC on different networks/subnets, or router has AP/client isolation | Confirm both devices' IPs share the same `/24` (e.g. both `192.168.1.x`); some guest Wi-Fi networks block device-to-device traffic — use the main network |
| Mobile app can't reach backend | PC's LAN IP changed | Re-run `ipconfig`, update `mobile/lib/config.dart`, rebuild |
| `CLEARTEXT communication not permitted` error in app | Backend's IP not listed in `network_security_config.xml` | Add the IP/domain there, rebuild |
| Admin portal shows CORS error in browser console | Portal's origin not in backend's `CORS_ORIGINS` | Add it to `backend/.env`, restart uvicorn |
| `adb install` fails with `INSTALL_FAILED_USER_RESTRICTED` | MIUI "Install via USB" restriction | See §6.3 — use browser download instead, or enable that Developer option |
| `adb devices` shows nothing | USB debugging not authorized yet, or cable in charge-only mode | Check for the "Allow USB debugging?" popup on the phone; switch USB mode to File Transfer/MTP |
| Alembic autogenerate wants to drop `tiger`/`topology`/PostGIS tables | Those come from the `postgis/postgis` Docker image's bundled extensions | Already handled — `alembic/env.py`'s `include_object` filter ignores tables not in our own models |
| `insightface`/`onnxruntime` import errors | Dependencies not installed in the venv | `pip install -r backend/requirements.txt` (all pinned versions confirmed working on Python 3.13) |
| First face-enrollment request is slow (~1 min) | InsightFace downloading the `buffalo_l` model (~280MB) on first use | One-time; cached afterward at `~/.insightface/models/buffalo_l/` |
