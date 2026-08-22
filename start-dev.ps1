$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$FrontendPath = Join-Path $ProjectRoot "frontend"
$PythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonPath)) {
    Write-Host "ERROR: Python virtual environment was not found."
    Write-Host "Expected: $PythonPath"
    exit 1
}

if (-not (Test-Path $FrontendPath)) {
    Write-Host "ERROR: Frontend folder was not found."
    Write-Host "Expected: $FrontendPath"
    exit 1
}

Write-Host ""
Write-Host "Starting ZELVION development environment..."
Write-Host ""

Start-Process powershell.exe -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$ProjectRoot'; & '$PythonPath' -m uvicorn backend.app.main:app --reload"
)

Start-Sleep -Seconds 2

Start-Process powershell.exe -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$FrontendPath'; npm run dev"
)

Write-Host "Backend starting at:"
Write-Host "http://127.0.0.1:8000"
Write-Host ""
Write-Host "API docs:"
Write-Host "http://127.0.0.1:8000/docs"
Write-Host ""
Write-Host "Frontend starting at:"
Write-Host "http://localhost:5173"
Write-Host ""
Write-Host "ZELVION development servers launched."