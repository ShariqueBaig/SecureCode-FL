@echo off
REM SecureCode-FL Setup Script for Python 3.12
REM This script checks Python version and sets up the virtual environment

echo.
echo ============================================================
echo  SecureCode-FL Environment Setup
echo ============================================================
echo.

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Current Python version: %PYTHON_VERSION%
echo.

REM Check if version is compatible (3.11 or 3.12)
if "%PYTHON_VERSION:~0,4%"=="3.14" (
    echo [ERROR] Python 3.14 is not compatible with TensorFlow 2.20
    echo.
    echo Please download and install Python 3.12 from:
    echo   https://www.python.org/downloads/release/python-3127/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

if "%PYTHON_VERSION:~0,4%"=="3.13" (
    echo [WARNING] Python 3.13 may have compatibility issues
    echo Recommended: Python 3.11 or 3.12
    echo.
)

if "%PYTHON_VERSION:~0,4%"=="3.11" (
    echo [OK] Python 3.11 is compatible
) else if "%PYTHON_VERSION:~0,4%"=="3.12" (
    echo [OK] Python 3.12 is compatible
) else (
    echo [WARNING] Python version %PYTHON_VERSION% may not be fully tested
)

echo.
echo Removing old virtual environment...

REM Always remove old venv to ensure clean setup
if exist venv (
    echo [INFO] Removing old virtual environment...
    rmdir /s /q venv
    if errorlevel 1 (
        echo [WARNING] Could not remove venv, attempting alternative method...
        for /d %%D in (venv) do (
            cd /d "%%~fD" && cd.. && powershell -Command "Remove-Item 'venv' -Recurse -Force -ErrorAction SilentlyContinue"
        )
    )
)

echo [INFO] Creating fresh virtual environment with Python 3.12...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment
    echo Make sure Python 3.12 is in PATH: python --version
    pause
    exit /b 1
)
echo [OK] Virtual environment created

echo.
echo Installing dependencies...
echo.

REM Upgrade pip
echo [1/4] Upgrading pip...
call venv\Scripts\python.exe -m pip install --upgrade pip --quiet
if errorlevel 1 goto error

REM Install main requirements
echo [2/4] Installing main dependencies...
call venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
if errorlevel 1 goto error

REM Install server requirements
echo [3/4] Installing inference server dependencies...
call venv\Scripts\python.exe -m pip install -r inference_server\requirements.txt --quiet
if errorlevel 1 goto error

REM Install FL requirements
echo [4/4] Installing federated learning dependencies...
call venv\Scripts\python.exe -m pip install flwr cryptography --quiet
if errorlevel 1 goto error

echo.
echo ============================================================
echo  SETUP COMPLETE
echo ============================================================
echo.
echo You can now:
echo   1. Start the server:   .\start_server.bat
echo   2. Run validation:     .\venv\Scripts\python.exe main.py
echo   3. Start extension:    cd vscode-extension ^& code .
echo.
echo To test that everything works, run:
echo   .\venv\Scripts\python.exe -c "import tensorflow; print('[OK] Ready!')"
echo.
pause
exit /b 0

:error
echo.
echo [ERROR] Installation failed!
echo.
echo Possible solutions:
echo   1. Check your internet connection
echo   2. Try reinstalling Python 3.12
echo   3. Run: python -m pip install --upgrade pip
echo   4. Run: python -m pip install -r requirements.txt --no-cache-dir
echo.
pause
exit /b 1
