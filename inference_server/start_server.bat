@echo off
REM SecureCode-FL Inference Server Startup Script
REM Automatically detects current directory

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Change to the script directory
cd /d "%SCRIPT_DIR%"

echo ============================================================
echo  SecureCode-FL Inference Server
echo ============================================================
echo.
echo Starting server from: %SCRIPT_DIR%
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then run: venv\Scripts\pip install -r requirements.txt
    echo           venv\Scripts\pip install -r inference_server\requirements.txt
    pause
    exit /b 1
)

REM Check if model exists
if not exist "models\federated\fl_global_model.keras" (
    echo WARNING: Model file not found at models\federated\fl_global_model.keras
    echo The server will use pattern-based detection only.
    echo.
)

REM Start the server
echo Starting server on http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
venv\Scripts\python.exe inference_server\server.py

pause
