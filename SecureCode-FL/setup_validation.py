#!/usr/bin/env python3
"""
SecureCode-FL Project Setup & Validation Script
================================================

This script validates the complete project setup.
"""

import os
import sys
import json
import subprocess
from typing import Dict, List, Tuple

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{'='*70}")
    print(f" {text}")
    print(f"{'='*70}\n")

def check_exists(path: str, is_dir: bool = False) -> Tuple[bool, str]:
    """Check if file/dir exists"""
    if is_dir:
        exists = os.path.isdir(path)
        status = "[OK]" if exists else "[NO]"
        return exists, f"  {status} {path}/"
    else:
        exists = os.path.exists(path)
        status = "[OK]" if exists else "[NO]"
        return exists, f"  {status} {path}"

def main():
    """Main validation routine"""
    print("\n" + "="*70)
    print(" SecureCode-FL Setup & Validation")
    print(" Version 1.0 | December 2025")
    print("="*70)
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    results = {}
    
    # 1. Project Structure
    print_header("1. PROJECT STRUCTURE VALIDATION")
    
    dirs_ok = True
    for dir_name in ["inference_server", "federated", "vscode-extension", "models", "data", "results", "venv"]:
        exists, msg = check_exists(os.path.join(base_path, dir_name), is_dir=True)
        print(msg)
        dirs_ok = dirs_ok and exists
    
    results["Project Structure"] = dirs_ok
    
    # 2. Dependencies
    print_header("2. PYTHON DEPENDENCIES VALIDATION")
    
    packages = [
        ("tensorflow", "TensorFlow"),
        ("keras", "Keras"),
        ("flask", "Flask"),
        ("flask_cors", "Flask-CORS"),
        ("pandas", "Pandas"),
        ("numpy", "NumPy"),
        ("sklearn", "Scikit-Learn"),
        ("xgboost", "XGBoost"),
        ("shap", "SHAP"),
        ("flwr", "Flower"),
        ("joblib", "Joblib"),
    ]
    
    deps_ok = True
    for import_name, display_name in packages:
        try:
            __import__(import_name)
            print(f"  [OK] {display_name}")
        except ImportError:
            print(f"  [NO] {display_name} - NOT INSTALLED")
            deps_ok = False
    
    results["Dependencies"] = deps_ok
    
    # 3. Models
    print_header("3. MODEL FILES VALIDATION")
    
    model_path = os.path.join(base_path, "models", "federated", "fl_global_model.keras")
    if os.path.exists(model_path):
        size_mb = os.path.getsize(model_path) / (1024 * 1024)
        print(f"  [OK] FL Global Model ({size_mb:.1f} MB)")
        models_ok = True
    else:
        print(f"  [NO] FL Global Model not found")
        print("  Server will use pattern-based detection only")
        models_ok = False
    
    results["Models"] = models_ok
    
    # 4. Data
    print_header("4. DATA FILES VALIDATION")
    
    data_files = [
        ("../Previous/Unsecured Codes.xlsx", "Original Dataset"),
        ("data/expanded_dataset_v2.csv", "Expanded Dataset"),
    ]
    
    data_ok = False
    for rel_path, name in data_files:
        full_path = os.path.normpath(os.path.join(base_path, rel_path))
        if os.path.exists(full_path):
            size_mb = os.path.getsize(full_path) / (1024 * 1024)
            print(f"  [OK] {name} ({size_mb:.2f} MB)")
            data_ok = True
        else:
            print(f"  [--] {name} (not found)")
    
    results["Data"] = data_ok
    
    # 5. Configuration
    print_header("5. CONFIGURATION VALIDATION")
    
    try:
        sys.path.insert(0, base_path)
        from config import DATASET_PATH, MODELS_DIR, RESULTS_DIR
        print(f"  [OK] Configuration loaded")
        print(f"    Models: {MODELS_DIR}")
        print(f"    Results: {RESULTS_DIR}")
        config_ok = True
    except Exception as e:
        print(f"  [NO] Config error: {e}")
        config_ok = False
    
    results["Configuration"] = config_ok
    
    # 6. Extension
    print_header("6. VS CODE EXTENSION VALIDATION")
    
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, timeout=5)
        if result.returncode == 0:
            print(f"  [OK] Node.js {result.stdout.decode().strip()}")
            ext_ok = True
        else:
            print(f"  [NO] Node.js not available")
            ext_ok = False
    except:
        print(f"  [NO] Node.js check failed")
        ext_ok = False
    
    results["Extension"] = ext_ok
    
    # Summary
    print_header("VALIDATION SUMMARY")
    
    all_ok = True
    for check, passed in results.items():
        status = "[OK]" if passed else "[NO]"
        print(f"  {status} {check}")
        all_ok = all_ok and passed
    
    # Next Steps
    print_header("NEXT STEPS")
    
    print("\n1. Start Inference Server:")
    print("   .\\start_server.ps1  (PowerShell)")
    print("   .\\start_server.bat  (CMD)")
    print("   python inference_server/server.py")
    
    print("\n2. Train Models (if needed):")
    print("   python main.py")
    
    print("\n3. Launch VS Code Extension:")
    print("   cd vscode-extension")
    print("   code .")
    print("   Press F5 to debug")
    
    print("\n4. Test API:")
    print("   curl http://localhost:5000/health")
    
    # Final status
    print_header("FINAL STATUS")
    if all_ok:
        print("[OK] All checks passed! Project is ready.")
        return 0
    else:
        print("[NO] Some checks failed. Review output above.")
        print("\nFix issues:")
        print("  pip install -r requirements.txt")
        print("  pip install -r inference_server/requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
