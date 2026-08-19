<#
.SYNOPSIS
  Stops every Attendance System container started by docker-up.ps1.

.PARAMETER Wipe
  Also delete the database volume (all data — students, enrollments,
  attendance records, announcements — gone for good). Omit to keep data
  between sessions (the default and normal case).

.EXAMPLE
  .\docker-down.ps1
  .\docker-down.ps1 -Wipe
#>

param(
    [switch]$Wipe
)

$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
if ($Wipe) {
    Write-Host 'Stopping containers and deleting all data (db volume)...' -ForegroundColor Yellow
    docker compose down -v
} else {
    docker compose down
}
Pop-Location
Write-Host 'Stopped.' -ForegroundColor Green
