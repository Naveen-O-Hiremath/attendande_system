<#
.SYNOPSIS
  Builds and starts the entire Attendance System — database, backend, admin
  portal, and student webapp — as Docker containers. This is the
  recommended way to run the project on a machine that has never seen it
  before: no Python, no Node.js, and no manual setup steps are required on
  the host at all. Only Docker Desktop.

.DESCRIPTION
  Runs `docker compose up --build`, which:
    - Builds the backend image (installs all Python deps, including
      InsightFace/onnxruntime/opencv, and bakes in the face-recognition
      model at build time so the container needs no network access to use
      it later).
    - Builds the admin portal and student webapp images (Node.js only
      exists inside the build stage — the final images are just nginx
      serving the built static files, so the host never needs Node
      installed).
    - Starts Postgres+PostGIS and Redis.
    - The backend container waits for the database, runs migrations, and
      seeds a default admin account, before starting the API server —
      all automatically, every time.

  Safe to re-run. Add -Rebuild after pulling code changes to rebuild
  images; without it, Docker reuses layers that haven't changed.

.PARAMETER Rebuild
  Force a full rebuild (no layer cache) — use after dependency changes.

.EXAMPLE
  .\docker-up.ps1
  .\docker-up.ps1 -Rebuild
#>

param(
    [switch]$Rebuild
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host $msg -ForegroundColor Green }
function Write-Warn($msg) { Write-Host $msg -ForegroundColor Yellow }

function Get-LanIp {
    $cfg = Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -and $_.IPv4Address }
    if ($cfg) { return ($cfg | Select-Object -First 1).IPv4Address.IPAddress }
    return $null
}

Write-Step 'Checking Docker Desktop'
docker info *> $null
if (-not $?) {
    Write-Host 'Docker engine not responding — starting Docker Desktop...'
    $dockerExe = 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
    if (Test-Path $dockerExe) { Start-Process $dockerExe } else { throw 'Docker Desktop.exe not found — install Docker Desktop first: https://www.docker.com/products/docker-desktop/' }

    $deadline = (Get-Date).AddMinutes(3)
    while ($true) {
        docker info *> $null
        if ($?) { break }
        if ((Get-Date) -gt $deadline) { throw 'Docker did not start within 3 minutes.' }
        Start-Sleep -Seconds 3
    }
}
Write-Ok 'Docker is up.'

Write-Step 'Building and starting all containers (this can take several minutes the first time)'
Push-Location $root
if ($Rebuild) {
    docker compose build --no-cache
}
docker compose up --build -d
Pop-Location

Write-Step 'Waiting for the backend to become healthy (migrations + seeding run automatically)'
$deadline = (Get-Date).AddMinutes(5)
while ($true) {
    $status = docker inspect --format='{{.State.Health.Status}}' attendance_system-backend-1 2>$null
    if ($status -eq 'healthy') { break }
    if ($status -eq 'unhealthy') {
        Write-Warn 'Backend reported unhealthy — check its logs:'
        Write-Host '  docker compose logs backend'
        break
    }
    if ((Get-Date) -gt $deadline) {
        Write-Warn 'Backend did not become healthy within 5 minutes. Check its logs:'
        Write-Host '  docker compose logs backend'
        break
    }
    Start-Sleep -Seconds 3
}

# Firewall rules for phone/LAN access — same one-time self-heal as the
# manual-mode start-all.ps1.
$requiredRules = @{
    'Attendance Backend'        = 8000
    'Attendance Student Webapp' = 5174
}
$missingRules = @($requiredRules.Keys | Where-Object { -not (Get-NetFirewallRule -DisplayName $_ -ErrorAction SilentlyContinue) })
if ($missingRules.Count -gt 0) {
    Write-Step "Creating $($missingRules.Count) missing firewall rule(s) — approve the admin prompt"
    $cmds = foreach ($name in $missingRules) {
        "New-NetFirewallRule -DisplayName `"$name`" -Direction Inbound -Protocol TCP -LocalPort $($requiredRules[$name]) -Action Allow | Out-Null"
    }
    try {
        Start-Process powershell -Verb RunAs -WindowStyle Hidden -ArgumentList '-NoProfile', '-Command', ($cmds -join '; ') -Wait -ErrorAction Stop
        Write-Ok 'Firewall rules created — this will not ask again on this machine.'
    } catch {
        Write-Warn 'Elevation was cancelled — the phone will not reach the webapp over Wi-Fi until these rules exist. Run as Administrator:'
        foreach ($name in $missingRules) {
            Write-Host "  New-NetFirewallRule -DisplayName `"$name`" -Direction Inbound -Protocol TCP -LocalPort $($requiredRules[$name]) -Action Allow"
        }
    }
} else {
    Write-Ok 'Firewall rules already in place.'
}

$lanIp = Get-LanIp
if (-not $lanIp) { $lanIp = '127.0.0.1' }

Write-Step 'All set'
Write-Host "Backend API:      http://localhost:8000  (docs: http://localhost:8000/docs)"
Write-Host "Admin portal:     http://localhost:5173   (login: portaladmin@example.com / password123)"
Write-Host "Student webapp:   http://localhost:5174   (on this PC) / http://$($lanIp):5174 (on a phone, same Wi-Fi)"
Write-Host "`nLogs:    docker compose logs -f              View all container logs"
Write-Host "Stop:    .\docker-down.ps1                    Stop every container"
Write-Host 'See SETUP.md for the USB-based phone connection option and troubleshooting.'
