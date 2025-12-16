# Python Installation Issue - Solution Guide

## Problem
- Python 3.14.2 is installed
- TensorFlow 2.20 doesn't support Python 3.14 (too new)
- DLL loading error when importing TensorFlow

## Solution

### Option 1: Use Python 3.11 or 3.12 (RECOMMENDED)

1. **Download Python 3.11 or 3.12** from https://www.python.org/downloads/
   - Python 3.11.8 (Latest 3.11)
   - Python 3.12.7 (Latest 3.12)
   
   During installation:
   ✓ Check "Add Python to PATH"
   ✓ Check "Install pip"
   ✓ Uncheck "Install py launcher"

2. **Verify Installation**
   ```powershell
   python --version
   python -m pip --version
   ```

3. **Delete old virtual environment**
   ```powershell
   cd "d:\Sharique\sem 5\CS\Research again\SecureCode-FL"
   Remove-Item venv -Recurse -Force
   ```

4. **Create new virtual environment**
   ```powershell
   python -m venv venv
   .\venv\Scripts\python.exe -m pip install --upgrade pip
   ```

5. **Install dependencies**
   ```powershell
   .\venv\Scripts\python.exe -m pip install -r requirements.txt
   .\venv\Scripts\python.exe -m pip install -r inference_server/requirements.txt
   .\venv\Scripts\python.exe -m pip install flwr cryptography
   ```

6. **Verify Installation**
   ```powershell
   .\venv\Scripts\python.exe -c "import tensorflow; import flask; print('[OK] Setup successful')"
   ```

### Option 2: Use CPU-only TensorFlow

If you want to keep Python 3.14, install CPU-only TensorFlow:

```powershell
.\venv\Scripts\python.exe -m pip install tensorflow-cpu
```

### Option 3: Use Conda (Alternative)

Download Miniconda from https://docs.conda.io/projects/miniconda/en/latest/

```powershell
conda create -n securecode python=3.11
conda activate securecode
pip install -r requirements.txt
pip install -r inference_server/requirements.txt
```

## Recommended: Option 1 with Python 3.12

Python 3.12 is the latest stable version with full TensorFlow 2.20 support.

### Quick Setup Commands for Python 3.12:

1. Install Python 3.12 from https://www.python.org/downloads/release/python-3127/
2. Run these commands in PowerShell:

```powershell
cd "d:\Sharique\sem 5\CS\Research again\SecureCode-FL"

# Remove old venv
Remove-Item venv -Recurse -Force -ErrorAction SilentlyContinue

# Create new venv with Python 3.12
python -m venv venv

# Upgrade pip
.\venv\Scripts\python.exe -m pip install --upgrade pip

# Install all dependencies
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m pip install -r inference_server/requirements.txt
.\venv\Scripts\python.exe -m pip install flwr cryptography

# Test
.\venv\Scripts\python.exe -c "import tensorflow; print('[OK] Ready!')"

# Start server
.\start_server.ps1
```

## After Fixed Setup:

```powershell
# Start the inference server
.\start_server.ps1

# OR in another terminal, run models
.\venv\Scripts\python.exe main.py
```

