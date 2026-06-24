param(
    [string]$BackendHost = "127.0.0.1",
    [int]$BackendPort = 8000,
    [string]$FrontendHost = "localhost",
    [int]$FrontendPort = 3000,
    [string]$ArgusMode = "auto"
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$LogsDir = Join-Path $Root "artifacts\logs"
$BackendUrl = "http://$BackendHost`:$BackendPort"
$FrontendUrl = "http://$FrontendHost`:$FrontendPort"
$SwaggerUrl = "$BackendUrl/docs"
$Python = Join-Path $Root ".venv\Scripts\python.exe"

New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null

if (-not (Test-Path $Python)) {
    Write-Host "ARGUS startup failed: Python virtual environment was not found at $Python" -ForegroundColor Red
    Write-Host "Create it first with: python -m venv .venv"
    exit 1
}

function Test-UrlReady {
    param([string]$Url)
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
    } catch {
        return $false
    }
}

function Wait-ForUrl {
    param(
        [string]$Url,
        [string]$Name,
        [int]$Seconds = 90
    )
    for ($index = 0; $index -lt $Seconds; $index++) {
        if (Test-UrlReady -Url $Url) {
            Write-Host "$Name ready: $Url" -ForegroundColor Green
            return $true
        }
        Start-Sleep -Seconds 1
    }
    Write-Host "$Name did not become ready: $Url" -ForegroundColor Red
    return $false
}

$env:ARGUS_MODE = $ArgusMode
$env:NEXT_PUBLIC_ARGUS_API_URL = $BackendUrl

$BackendLog = Join-Path $LogsDir "backend.log"
$FrontendLog = Join-Path $LogsDir "frontend.log"

Write-Host "Starting ARGUS..." -ForegroundColor Cyan
Write-Host "Mode: $ArgusMode"
Write-Host "Backend log: $BackendLog"
Write-Host "Frontend log: $FrontendLog"

$backendArgs = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-Command",
    "cd '$Root'; `$env:ARGUS_MODE='$ArgusMode'; & '$Python' -m uvicorn backend.main:app --reload --host $BackendHost --port $BackendPort *> '$BackendLog'"
)
$backendProcess = Start-Process powershell -ArgumentList $backendArgs -PassThru -WindowStyle Minimized

$frontendArgs = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-Command",
    "cd '$Root'; `$env:NEXT_PUBLIC_ARGUS_API_URL='$BackendUrl'; npm --prefix frontend run dev -- --hostname $FrontendHost --port $FrontendPort *> '$FrontendLog'"
)
$frontendProcess = Start-Process powershell -ArgumentList $frontendArgs -PassThru -WindowStyle Minimized

$backendReady = Wait-ForUrl -Url "$BackendUrl/api/health" -Name "Backend"
$frontendReady = Wait-ForUrl -Url $FrontendUrl -Name "Frontend"

Write-Host ""
Write-Host "ARGUS URLs" -ForegroundColor Cyan
Write-Host "Frontend: $FrontendUrl"
Write-Host "Backend:  $BackendUrl"
Write-Host "Swagger:  $SwaggerUrl"
Write-Host ""

if ($backendReady -and $frontendReady) {
    Write-Host "ARGUS is ready for judging." -ForegroundColor Green
    Start-Process $FrontendUrl
    exit 0
}

Write-Host "ARGUS did not start cleanly. Check the logs above." -ForegroundColor Red
Write-Host "Backend process id: $($backendProcess.Id)"
Write-Host "Frontend process id: $($frontendProcess.Id)"
exit 1
