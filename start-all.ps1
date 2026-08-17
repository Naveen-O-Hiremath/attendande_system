<#
.SYNOPSIS
  Starts every service the Attendance System needs, in the right order,
  each pointed at the environment it's actually running in.

.DESCRIPTION
  1. Ensures Docker Desktop is running, then brings up Postgres+PostGIS and Redis.
  2. Waits for Postgres to report healthy, enables the PostGIS extension (idempotent).
  3. Runs Alembic migrations against the backend's venv.
  4. Detects this machine's LAN IP (for the student webapp / phone-over-Wi-Fi
     case) and warns if student-webapp/src/config.ts is pointing somewhere else.
  5. Starts the backend (uvicorn), the admin portal (vite dev server), and the
     student webapp (vite dev server, LAN-bound so a phone can open it),
     each in its own visible PowerShell window.
  6. Prints a summary of every URL/port in use, and flags missing firewall
     rules (it cannot create them itself — no elevated shell).

  Safe to re-run: it stops any previous uvicorn/vite instances it started
  before launching fresh ones, so ports don't collide.

.PARAMETER Lan
  Bind the backend to 0.0.0.0 so phones on the same Wi-Fi can reach it.
  Default: on. Use -Lan:$false for a laptop-only / no-phone-testing session
  (binds 127.0.0.1 instead).

.PARAMETER NoPortal
  Skip starting the admin portal dev server.

.PARAMETER NoStudentApp
  Skip starting the student webapp dev server.

.PARAMETER NoBackend
  Skip starting the backend API (e.g. if it's already running elsewhere).

.EXAMPLE
  .\start-all.ps1
  .\start-all.ps1 -Lan:$false -NoStudentApp
#>

param(
    [switch]$Lan = $true,
    [switch]$NoPortal,
    [switch]$NoStudentApp,
    [switch]$NoBackend
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$backendPath = Join-Path $root 'backend'
$portalPath = Join-Path $root 'admin-portal'
$studentAppPath = Join-Path $root 'student-webapp'
$venvPython = Join-Path $root '.venv\Scripts\python.exe'
$dbContainer = 'attendance_system-db-1'

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host $msg -ForegroundColor Green }
function Write-Warn($msg) { Write-Host $msg -ForegroundColor Yellow }

function Stop-MatchingProcess([string]$pattern, [string]$label) {
    $procs = Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='node.exe'" |
        Where-Object { $_.CommandLine -match $pattern }
    foreach ($p in $procs) {
        Write-Host "  Stopping existing $label (PID $($p.ProcessId))"
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

function Get-LanIp {
    $cfg = Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -and $_.IPv4Address }
    if ($cfg) { return ($cfg | Select-Object -First 1).IPv4Address.IPAddress }
    return $null
}

# ---------------------------------------------------------------------------
# 1. Docker Desktop + containers
# ---------------------------------------------------------------------------
Write-Step 'Checking Docker Desktop'
docker info *> $null
if (-not $?) {
    Write-Host 'Docker engine not responding — starting Docker Desktop...'
    $dockerExe = 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
    if (Test-Path $dockerExe) { Start-Process $dockerExe } else { throw 'Docker Desktop.exe not found — install Docker Desktop first.' }

    $deadline = (Get-Date).AddMinutes(3)
    while ($true) {
        docker info *> $null
        if ($?) { break }
        if ((Get-Date) -gt $deadline) { throw 'Docker did not start within 3 minutes.' }
        Start-Sleep -Seconds 3
    }
}
Write-Ok 'Docker is up.'

Write-Step 'Starting Postgres (PostGIS) + Redis'
Push-Location $root
docker compose up -d db redis
Pop-Location

Write-Step 'Waiting for Postgres to become healthy'
$deadline = (Get-Date).AddMinutes(2)
while ($true) {
    $status = docker inspect --format='{{.State.Health.Status}}' $dbContainer 2>$null
    if ($status -eq 'healthy') { break }
    if ((Get-Date) -gt $deadline) { throw "Postgres container '$dbContainer' did not become healthy in time." }
    Start-Sleep -Seconds 2
}
Write-Ok 'Postgres healthy.'

docker exec $dbContainer psql -U attendance -d attendance -c 'CREATE EXTENSION IF NOT EXISTS postgis;' | Out-Null

# ---------------------------------------------------------------------------
# 2. Backend environment + migrations
# ---------------------------------------------------------------------------
if (-not (Test-Path $venvPython)) {
    throw "Backend virtualenv not found at $venvPython. Follow SETUP.md section 3 first (python -m venv .venv; pip install -r backend/requirements.txt)."
}

Write-Step 'Running database migrations'
Push-Location $backendPath
& $venvPython -m alembic upgrade head
Pop-Location
Write-Ok 'Migrations up to date.'

# ---------------------------------------------------------------------------
# 3. Detect environment (LAN IP) and sanity-check the student webapp's config
# ---------------------------------------------------------------------------
$lanIp = Get-LanIp
if (-not $lanIp) {
    Write-Warn 'Could not detect a LAN IP with a default gateway — falling back to 127.0.0.1. Phones on Wi-Fi will not be able to reach the backend.'
    $lanIp = '127.0.0.1'
}

$studentConfigPath = Join-Path $studentAppPath 'src\config.ts'
if (Test-Path $studentConfigPath) {
    $configContent = Get-Content $studentConfigPath -Raw
    if ($configContent -notmatch [regex]::Escape($lanIp)) {
        Write-Warn "student-webapp/src/config.ts does not reference this machine's current LAN IP ($lanIp)."
        Write-Warn '  Update API_ORIGIN there if a phone cannot reach the backend (no rebuild needed — Vite picks it up on save).'
    }
}

# ---------------------------------------------------------------------------
# 4. Start services (each in its own window; stop any previous instances first)
# ---------------------------------------------------------------------------
if (-not $NoBackend) {
    Stop-MatchingProcess 'uvicorn app\.main:app' 'backend (uvicorn)'
}
if (-not $NoPortal -or -not $NoStudentApp) {
    # One combined sweep: killing per-app risks a later kill catching the
    # app just started earlier in this same run (both are "vite").
    Stop-MatchingProcess 'vite' 'vite dev server'
}

if (-not $NoBackend) {
    Write-Step 'Starting backend API'
    $bindHost = if ($Lan) { '0.0.0.0' } else { '127.0.0.1' }
    Start-Process powershell -ArgumentList '-NoExit', '-Command', "cd '$backendPath'; & '$venvPython' -m uvicorn app.main:app --host $bindHost --port 8000"
    Write-Ok "Backend starting — bind $bindHost, reachable at http://$($lanIp):8000"
}

if (-not $NoPortal) {
    Write-Step 'Starting admin portal'
    if (Test-Path (Join-Path $portalPath 'node_modules')) {
        Start-Process powershell -ArgumentList '-NoExit', '-Command', "cd '$portalPath'; npm run dev"
        Write-Ok 'Admin portal starting at http://localhost:5173'
    } else {
        Write-Warn 'admin-portal/node_modules not found — run "npm install" in admin-portal/ first. Skipping.'
    }
}

if (-not $NoStudentApp) {
    Write-Step 'Starting student webapp'
    if (Test-Path (Join-Path $studentAppPath 'node_modules')) {
        Start-Process powershell -ArgumentList '-NoExit', '-Command', "cd '$studentAppPath'; npm run dev"
        Write-Ok "Student webapp starting — reachable on this PC at http://localhost:5174 and on the phone at http://$($lanIp):5174"
    } else {
        Write-Warn 'student-webapp/node_modules not found — run "npm install" in student-webapp/ first. Skipping.'
    }
}

# ---------------------------------------------------------------------------
# 5. Firewall reminder (cannot self-elevate to fix this)
# ---------------------------------------------------------------------------
$requiredRules = @{
    'Attendance Backend'       = 8000
    'Attendance Student Webapp' = 5174
}
$missingRules = @()
foreach ($name in $requiredRules.Keys) {
    if (-not (Get-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue)) { $missingRules += $name }
}
if ($missingRules.Count -gt 0) {
    Write-Warn "`nMissing firewall rules: $($missingRules -join ', '). Your phone won't reach these services until you run (as Administrator):"
    foreach ($name in $missingRules) {
        Write-Host "  New-NetFirewallRule -DisplayName `"$name`" -Direction Inbound -Protocol TCP -LocalPort $($requiredRules[$name]) -Action Allow"
    }
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
Write-Step 'All set'
Write-Host "Backend API:      http://$($lanIp):8000  (docs: http://localhost:8000/docs)"
Write-Host 'Admin portal:     http://localhost:5173  (desktop browser only)'
Write-Host "Student webapp:   http://$($lanIp):5174  (open this on the phone's browser, same Wi-Fi)"
Write-Host 'Postgres:         localhost:5432  (db/user/pass: attendance/attendance/attendance)'
Write-Host 'Redis:            localhost:6379'
Write-Host "`nSee SETUP.md for credentials, troubleshooting, and full details."
