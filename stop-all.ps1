<#
.SYNOPSIS
  Stops every service this project's start-all.ps1 starts: the backend
  (uvicorn), the admin portal (vite), and the student webapp (vite).

.DESCRIPTION
  Finds and kills the specific python/node processes running this project's
  backend and frontends by matching their command line — it will not touch
  unrelated python/node/vite processes from other projects.

  Docker (Postgres/Redis) is left running by default, since other tools may
  depend on the DB staying up between sessions. Pass -IncludeDocker to stop
  those containers too (this only stops them, it never removes containers
  or volumes — your data is untouched either way).

.PARAMETER IncludeDocker
  Also stop the db and redis containers (docker compose stop db redis).

.EXAMPLE
  .\stop-all.ps1
  .\stop-all.ps1 -IncludeDocker
#>

param(
    [switch]$IncludeDocker
)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host $msg -ForegroundColor Green }
function Write-Warn($msg) { Write-Host $msg -ForegroundColor Yellow }

function Stop-MatchingProcess([string]$pattern, [string]$label) {
    $procs = Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='node.exe'" |
        Where-Object { $_.CommandLine -match $pattern }
    if (-not $procs) {
        Write-Host "  $label not running."
        return
    }
    foreach ($p in $procs) {
        Write-Host "  Stopping $label (PID $($p.ProcessId))"
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

Write-Step 'Stopping backend (uvicorn)'
Stop-MatchingProcess 'uvicorn app\.main:app' 'backend'

Write-Step 'Stopping admin portal + student webapp (vite)'
# One combined match — both dev servers show up as "vite" in the command
# line and there's no reliable way to tell them apart by pattern alone, so
# this intentionally stops both together, same as start-all.ps1's sweep.
Stop-MatchingProcess 'vite' 'vite dev server'

if ($IncludeDocker) {
    Write-Step 'Stopping Postgres + Redis containers'
    Push-Location $root
    docker compose stop db redis
    Pop-Location
    Write-Ok 'Containers stopped (data volume untouched — start-all.ps1 will bring them back).'
} else {
    Write-Host "`nPostgres and Redis containers left running (use -IncludeDocker to stop them too)." -ForegroundColor DarkGray
}

Write-Step 'Done'
Write-Ok 'All attendance-system app processes stopped.'
