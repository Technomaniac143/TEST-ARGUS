param(
    [string]$RenderBackendUrl = "",
    [string]$VercelProductionUrl = "",
    [switch]$SkipValidation,
    [switch]$DeployPreview,
    [switch]$DeployProduction
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Frontend = Join-Path $Root "frontend"
$VercelData = Join-Path $Root ".vercel-cli"
$VercelLocal = Join-Path $Root ".vercel-cli-local"

New-Item -ItemType Directory -Force -Path $VercelData | Out-Null
New-Item -ItemType Directory -Force -Path $VercelLocal | Out-Null

$env:XDG_DATA_HOME = $VercelData
$env:LOCALAPPDATA = $VercelLocal

function Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Require-Command {
    param([string]$Command, [string]$InstallHint)
    if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
        Write-Host "$Command is not installed or not on PATH." -ForegroundColor Yellow
        Write-Host $InstallHint
        return $false
    }
    return $true
}

Set-Location $Root

Step "Precheck"
git status -sb
git log -1 --oneline
node --version
npm.cmd --version
if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Python virtual environment missing. Run: python -m venv .venv"
}
.\.venv\Scripts\python.exe --version

if (-not $SkipValidation) {
    Step "Local validation"
    npm.cmd --prefix frontend run build
    .\.venv\Scripts\python.exe -m pytest
}

Step "Vercel CLI"
if (-not (Require-Command "vercel.cmd" "Install it with: npm install -g vercel")) {
    exit 1
}
vercel.cmd --version

Write-Host "If you have not logged in yet, run: vercel.cmd login"

Step "Vercel project setup"
Write-Host "Frontend root: $Frontend"
Write-Host "If this is the first deploy, run:"
Write-Host "  cd frontend"
Write-Host "  vercel.cmd login"
Write-Host "  vercel.cmd link"

if ($RenderBackendUrl) {
    Step "Vercel environment wiring"
    Write-Host "Set NEXT_PUBLIC_ARGUS_API_URL to: $RenderBackendUrl"
    Write-Host "Run:"
    Write-Host "  cd frontend"
    Write-Host "  vercel.cmd env add NEXT_PUBLIC_ARGUS_API_URL production"
    Write-Host "  vercel.cmd env add NEXT_PUBLIC_ARGUS_API_URL preview"
} else {
    Write-Host "Render backend URL not supplied yet." -ForegroundColor Yellow
    Write-Host "After Render deploy, set:"
    Write-Host "  cd frontend"
    Write-Host "  vercel.cmd env add NEXT_PUBLIC_ARGUS_API_URL production"
    Write-Host "  vercel.cmd env add NEXT_PUBLIC_ARGUS_API_URL preview"
    Write-Host "Value:"
    Write-Host "  https://YOUR_RENDER_BACKEND.onrender.com"
}

if ($DeployPreview) {
    Step "Vercel preview deploy"
    Set-Location $Frontend
    vercel.cmd
    Set-Location $Root
}

if ($DeployProduction) {
    Step "Vercel production deploy"
    Set-Location $Frontend
    vercel.cmd --prod
    Set-Location $Root
}

Step "Render Blueprint deployment"
Write-Host "No reliable official Render CLI was detected locally. Use the Render Blueprint flow:"
Write-Host "1. Go to https://dashboard.render.com/"
Write-Host "2. New + > Blueprint"
Write-Host "3. Connect GitHub repo: mohammedsuhailrafek28/Argus"
Write-Host "4. Select render.yaml"
Write-Host "5. Create argus-backend and argus-postgres"
Write-Host "6. Set/update backend environment variables:"
Write-Host "   ARGUS_MODE=offline"
Write-Host "   ARGUS_OFFLINE_MODE=true"
Write-Host "   ARGUS_DEMO_MODE=false"
Write-Host "   ARGUS_CACHE_TTL_SECONDS=86400"
Write-Host "   ARGUS_CRAWL_CACHE_TTL_SECONDS=86400"
Write-Host "   ARGUS_SEARCH_TIMEOUT_SECONDS=10"
Write-Host "   ARGUS_MAX_RESULTS_PER_QUERY=10"
Write-Host "   ARGUS_MAX_SOURCE_QUERIES=12"
Write-Host "   ARGUS_MAX_PAGES_PER_SITE=4"
if ($VercelProductionUrl) {
    Write-Host "   CORS_ALLOWED_ORIGINS=$VercelProductionUrl,http://localhost:3000,http://127.0.0.1:3000"
} else {
    Write-Host "   CORS_ALLOWED_ORIGINS=https://YOUR_VERCEL_APP.vercel.app,http://localhost:3000,http://127.0.0.1:3000"
}
Write-Host "   DATABASE_URL should be provided by Render PostgreSQL."

Step "Final deployment wiring"
Write-Host "After Render gives you the backend URL:"
Write-Host "  cd frontend"
Write-Host "  vercel.cmd env add NEXT_PUBLIC_ARGUS_API_URL production"
Write-Host "  vercel.cmd --prod"
Write-Host ""
Write-Host "After Vercel gives you the production URL:"
Write-Host "  Update CORS_ALLOWED_ORIGINS on Render and redeploy backend."

Step "Production smoke checklist"
Write-Host "Backend health: https://YOUR_RENDER_BACKEND.onrender.com/api/health"
Write-Host "Swagger:        https://YOUR_RENDER_BACKEND.onrender.com/docs"
Write-Host "Frontend:       https://YOUR_VERCEL_APP.vercel.app"
Write-Host "Query:          Cardiologists in Chennai"
Write-Host "Mode:           Offline or Auto"
Write-Host "Verify: load, research start, progress, report complete, repeat query cache banner."

Write-Host ""
Write-Host "Deployment helper complete." -ForegroundColor Green
