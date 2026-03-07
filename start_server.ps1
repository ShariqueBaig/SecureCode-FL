# SecureCode-FL Inference Server Startup Script (PowerShell)
# More robust version with better error handling

param(
    [int]$port = 5000,
    [switch]$noPause = $false
)

# Get the directory where this script is located
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Change to the script directory
Set-Location $scriptDir

Write-Host @"
============================================================
  SecureCode-FL Inference Server
============================================================

"@

Write-Host "Starting server from: $scriptDir"
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run the following commands:" -ForegroundColor Yellow
    Write-Host "  python -m venv venv" -ForegroundColor Cyan
    Write-Host "  .\venv\Scripts\pip install -r requirements.txt" -ForegroundColor Cyan
    Write-Host "  .\venv\Scripts\pip install -r inference_server\requirements.txt" -ForegroundColor Cyan
    Write-Host ""
    if (-not $noPause) {
        Read-Host "Press Enter to exit"
    }
    exit 1
}

# Check if model exists (warning only, not critical)
if (-not (Test-Path "models\federated\fl_global_model.keras")) {
    Write-Host "WARNING: Model file not found at models\federated\fl_global_model.keras" -ForegroundColor Yellow
    Write-Host "The server will use pattern-based detection only." -ForegroundColor Yellow
    Write-Host ""
}

# Check if feedback database exists
if (-not (Test-Path "data\user_feedback.db")) {
    Write-Host "Creating new feedback database..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Path "data" -Force | Out-Null
}

# Start the server
Write-Host "Starting server on http://localhost:$port" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

& .\venv\Scripts\python.exe inference_server\server.py --port $port

if (-not $noPause) {
    Read-Host "Press Enter to exit"
}
