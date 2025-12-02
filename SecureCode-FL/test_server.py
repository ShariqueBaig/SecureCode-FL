"""
Test script for the SecureCode-FL inference server
"""

import requests
import json

# Test code with vulnerabilities
vulnerable_code = '''
# Hardcoded credentials
password = "admin123"
api_key = "sk-secret-key-12345"

# SQL injection
query = "SELECT * FROM users WHERE id = " + user_id

# Dangerous eval
result = eval(user_input)

# SSL disabled
requests.get(url, verify=False)

# Debug mode
DEBUG = True
'''

def test_health():
    """Test health endpoint"""
    print("=" * 50)
    print("Testing /health endpoint...")
    r = requests.get('http://127.0.0.1:5000/health')
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
    return r.status_code == 200

def test_scan():
    """Test scan endpoint"""
    print("\n" + "=" * 50)
    print("Testing /scan endpoint with vulnerable code...")
    r = requests.post('http://127.0.0.1:5000/scan', json={
        'code': vulnerable_code,
        'language': 'python',
        'filename': 'test.py'
    })
    print(f"Status: {r.status_code}")
    result = r.json()
    print(f"\nFound {len(result['vulnerabilities'])} vulnerabilities:")
    print(f"Scan time: {result['scan_time_ms']:.2f}ms")
    print()
    
    for i, vuln in enumerate(result['vulnerabilities'], 1):
        print(f"{i}. [{vuln['severity'].upper()}] Line {vuln['line']}: {vuln['vulnerability_type']}")
        print(f"   Message: {vuln['message']}")
        print(f"   CWE: {vuln.get('cwe_id', 'N/A')}")
        print(f"   Suggestion: {vuln['suggestion']}")
        print()
    
    return r.status_code == 200

def test_model_info():
    """Test model info endpoint"""
    print("=" * 50)
    print("Testing /model/info endpoint...")
    r = requests.get('http://127.0.0.1:5000/model/info')
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
    return r.status_code == 200

def test_vulnerability_types():
    """Test vulnerability types endpoint"""
    print("\n" + "=" * 50)
    print("Testing /vulnerability-types endpoint...")
    r = requests.get('http://127.0.0.1:5000/vulnerability-types')
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
    return r.status_code == 200

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  SecureCode-FL Server Tests")
    print("=" * 60 + "\n")
    
    try:
        results = []
        results.append(("Health Check", test_health()))
        results.append(("Model Info", test_model_info()))
        results.append(("Vulnerability Types", test_vulnerability_types()))
        results.append(("Vulnerability Scan", test_scan()))
        
        print("\n" + "=" * 60)
        print("  Test Results Summary")
        print("=" * 60)
        
        all_passed = True
        for name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status} - {name}")
            if not passed:
                all_passed = False
        
        print("\n" + ("✅ All tests passed!" if all_passed else "❌ Some tests failed"))
        
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to server at http://127.0.0.1:5000")
        print("   Make sure the server is running: python inference_server/server.py")
