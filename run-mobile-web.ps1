<#
.SYNOPSIS
  Connects a USB-attached phone to the backend + student webapp via `adb
  reverse` — no firewall rules, no matching Wi-Fi network, no LAN IP at all.

.DESCRIPTION
  This is the recommended way to test the student webapp on a real phone.
  It sidesteps every failure mode the LAN/firewall approach has (missing
  firewall rule, phone on a different/guest Wi-Fi, AP client isolation,
  the machine's IP changing) because `adb reverse` tunnels the phone's own
  "localhost" ports straight to this machine over the USB cable — the phone
  never touches the network at all.

  1. Finds adb (PATH, or the usual Android SDK install locations).
  2. Confirms a device is connected and authorized.
  3. Reverses the backend port (8000) and the student webapp's dev server
     port (5174) from the phone to this machine.
  4. Confirms the backend is actually healthy before declaring success.

  Requires: USB cable, "USB debugging" enabled on the phone, and the RSA key
  prompt accepted on-device (one-time). Does NOT require "Install via USB"
  (that MIUI restriction only blocks `adb install`, not `adb reverse`).

.PARAMETER ApiPort
  Backend port to reverse. Default 8000.

.PARAMETER WebPort
  Student webapp dev server port to reverse. Default 5174.

.EXAMPLE
  .\run-mobile-web.ps1
#>

param(
    [int]$ApiPort = 8000,
    [int]$WebPort = 5174
)

$ErrorActionPreference = 'Stop'

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host "    OK  $msg" -ForegroundColor Green }
function Write-WarnLine($msg) { Write-Host "    !!  $msg" -ForegroundColor Yellow }
function Write-Fail($msg) { Write-Host "    XX  $msg" -ForegroundColor Red }

function Resolve-AdbPath {
    if (Get-Command adb -ErrorAction SilentlyContinue) { return (Get-Command adb).Source }
    $candidates = @(
        "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe",
        "$env:LOCALAPPDATA\Android\sdk\platform-tools\adb.exe",
        "$env:USERPROFILE\AppData\Local\Android\Sdk\platform-tools\adb.exe",
        "$env:ANDROID_HOME\platform-tools\adb.exe",
        "$env:ANDROID_SDK_ROOT\platform-tools\adb.exe"
    )
    foreach ($c in $candidates) {
        if ($c -and (Test-Path -LiteralPath $c)) { return $c }
    }
    return $null
}

function Wait-HttpOk([string]$Url, [int]$TimeoutSec = 10) {
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    while ((Get-Date) -lt $deadline) {
        try {
            $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
            if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { return $true }
        } catch {
            Start-Sleep -Milliseconds 500
        }
    }
    return $false
}

Write-Step 'Checking backend'
if (-not (Wait-HttpOk "http://127.0.0.1:$ApiPort/health" 5)) {
    Write-Fail "Backend not responding at http://127.0.0.1:$ApiPort/health"
    Write-WarnLine 'Start it first: .\start-all.ps1'
    exit 1
}
Write-Ok "Backend healthy at http://127.0.0.1:$ApiPort"

Write-Step 'Checking student webapp dev server'
if (-not (Wait-HttpOk "http://127.0.0.1:$WebPort/" 5)) {
    Write-Fail "Student webapp not responding at http://127.0.0.1:$WebPort/"
    Write-WarnLine 'Start it first: .\start-all.ps1  (or  cd student-webapp; npm run dev)'
    exit 1
}
Write-Ok "Webapp healthy at http://127.0.0.1:$WebPort"

Write-Step 'Finding adb'
$adb = Resolve-AdbPath
if (-not $adb) {
    Write-Fail 'adb not found. Install Android SDK platform-tools, or add it to PATH.'
    exit 1
}
Write-Ok "Using adb: $adb"

Write-Step 'Checking for a connected device'
$devices = & $adb devices 2>$null | Select-Object -Skip 1 | Where-Object { $_ -match '\tdevice$' }
if (-not $devices) {
    Write-Fail 'No authorized Android device found.'
    Write-WarnLine 'Plug the phone in via USB, enable "USB debugging" in Developer options,'
    Write-WarnLine 'and accept the "Allow USB debugging?" prompt on the phone. Then re-run this script.'
    exit 1
}
Write-Ok "Device connected: $($devices -join ', ')"

Write-Step 'Tunneling ports over USB (adb reverse)'
& $adb reverse "tcp:$ApiPort" "tcp:$ApiPort" | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Fail "adb reverse tcp:$ApiPort failed"; exit 1 }
Write-Ok "tcp:$ApiPort  (phone's localhost:$ApiPort -> this PC's backend)"

& $adb reverse "tcp:$WebPort" "tcp:$WebPort" | Out-Null
if ($LASTEXITCODE -ne 0) { Write-Fail "adb reverse tcp:$WebPort failed"; exit 1 }
Write-Ok "tcp:$WebPort  (phone's localhost:$WebPort -> this PC's webapp)"

Write-Step 'Ready'
Write-Host "On the phone, open Chrome and go to:  http://localhost:$WebPort" -ForegroundColor Green
Write-Host 'No Wi-Fi network match, firewall rule, or IP address needed — this works purely over USB.'
