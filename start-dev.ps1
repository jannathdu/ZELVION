$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$FrontendPath = Join-Path $ProjectRoot "frontend"
$PythonPath = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

$BackendPort = 8000
$FrontendPort = 5173


function Get-ListeningProcessId {
    param(
        [int]$Port
    )

    $connection = Get-NetTCPConnection `
        -LocalPort $Port `
        -State Listen `
        -ErrorAction SilentlyContinue |
        Select-Object -First 1

    if ($null -eq $connection) {
        return $null
    }

    return [int]$connection.OwningProcess
}


function Get-CommandLine {
    param(
        [int]$ProcessId
    )

    $process = Get-CimInstance `
        Win32_Process `
        -Filter "ProcessId = $ProcessId" `
        -ErrorAction SilentlyContinue

    if ($null -eq $process) {
        return ""
    }

    return [string]$process.CommandLine
}


if (-not (Test-Path $PythonPath)) {
    Write-Host ""
    Write-Host "ERROR: Python virtual environment was not found."
    Write-Host "Expected:"
    Write-Host $PythonPath
    exit 1
}


if (-not (Test-Path $FrontendPath)) {
    Write-Host ""
    Write-Host "ERROR: Frontend folder was not found."
    Write-Host "Expected:"
    Write-Host $FrontendPath
    exit 1
}


Write-Host ""
Write-Host "ZELVION development startup"
Write-Host "---------------------------"
Write-Host ""


# --------------------------------------------------
# Preflight backend port
# --------------------------------------------------

$BackendProcessId = Get-ListeningProcessId `
    -Port $BackendPort

$BackendAlreadyRunning = $false

if ($null -ne $BackendProcessId) {
    $BackendCommandLine = Get-CommandLine `
        -ProcessId $BackendProcessId

    $IsZelvionBackend =
        $BackendCommandLine -match "uvicorn" -and
        $BackendCommandLine -match "backend\.app\.main" -and
        $BackendCommandLine -match "ZELVION"

    if ($IsZelvionBackend) {
        $BackendAlreadyRunning = $true

        Write-Host (
            "Backend already running on port " +
            "$BackendPort (PID $BackendProcessId)."
        )
    }
    else {
        Write-Host (
            "ERROR: Port $BackendPort is already in use " +
            "by another process."
        )

        Write-Host (
            "PID: $BackendProcessId"
        )

        Write-Host (
            "Command: $BackendCommandLine"
        )

        exit 1
    }
}


# --------------------------------------------------
# Preflight frontend port
# --------------------------------------------------

$FrontendProcessId = Get-ListeningProcessId `
    -Port $FrontendPort

$FrontendAlreadyRunning = $false

if ($null -ne $FrontendProcessId) {
    $FrontendCommandLine = Get-CommandLine `
        -ProcessId $FrontendProcessId

    $IsZelvionFrontend =
        $FrontendCommandLine -match "node" -and
        $FrontendCommandLine -match "vite" -and
        $FrontendCommandLine -match "ZELVION"

    if ($IsZelvionFrontend) {
        $FrontendAlreadyRunning = $true

        Write-Host (
            "Frontend already running on port " +
            "$FrontendPort (PID $FrontendProcessId)."
        )
    }
    else {
        Write-Host (
            "ERROR: Port $FrontendPort is already in use " +
            "by another process."
        )

        Write-Host (
            "PID: $FrontendProcessId"
        )

        Write-Host (
            "Command: $FrontendCommandLine"
        )

        exit 1
    }
}


# --------------------------------------------------
# Start backend
# --------------------------------------------------

if (-not $BackendAlreadyRunning) {
    Write-Host "Starting backend..."

    Start-Process powershell.exe -ArgumentList @(
        "-NoExit",
        "-Command",
        (
            "Set-Location '$ProjectRoot'; " +
            "& '$PythonPath' -m uvicorn " +
            "backend.app.main:app --reload"
        )
    )
}


# --------------------------------------------------
# Start frontend
# --------------------------------------------------

if (-not $FrontendAlreadyRunning) {
    Write-Host "Starting frontend..."

    Start-Process powershell.exe -ArgumentList @(
        "-NoExit",
        "-Command",
        (
            "Set-Location '$FrontendPath'; " +
            "npm run dev -- --port $FrontendPort --strictPort"
        )
    )
}


Write-Host ""
Write-Host "Backend:"
Write-Host "http://127.0.0.1:$BackendPort"

Write-Host ""
Write-Host "API docs:"
Write-Host "http://127.0.0.1:$BackendPort/docs"

Write-Host ""
Write-Host "Frontend:"
Write-Host "http://localhost:$FrontendPort"

Write-Host ""
Write-Host "ZELVION development environment ready."
Write-Host ""