# Attendance System — Admin Portal

React + TypeScript + Vite admin portal for the face-enrollment approval workflow.

## Scope

- Login (admin/super_admin only — student/teacher accounts are rejected client- and server-side)
- Dashboard: pending/approved/rejected enrollment counts
- Face Enrollments: filterable queue with image previews, Approve / Reject (with reason) /
  Request resubmission

Everything else in the project brief (schedule/geo-fence config, leave management,
announcements, chat, assignments, reporting) is not built yet.

## Local setup

```bash
npm install
npm run dev
```

Runs on http://localhost:5173. Expects the backend at http://localhost:8000
(see `../backend/README.md`) — its CORS_ORIGINS must include
`http://localhost:5173` (already set in `backend/.env.example`).

## Auth

JWT access token stored in `localStorage`. On load, the token is validated
against `/auth/me`; a non-admin role clears the session. There's no refresh
flow here yet — the admin simply logs back in when the access token expires
(30 min by default).

## Images

Face enrollment images are biometric data and are served through an
authenticated backend route (`/api/v1/face-enrollments/images/...`), not a
public static mount. `src/components/AuthImage.tsx` fetches each image with
the bearer token and renders it via an object URL.
