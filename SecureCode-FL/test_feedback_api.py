"""
Test script for the User Feedback System API
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_health():
    """Test health endpoint"""
    print("\n1. Testing /health endpoint...")
    try:
        r = requests.get(f"{BASE_URL}/health")
        print(f"   Status: {r.status_code}")
        print(f"   Response: {json.dumps(r.json(), indent=2)}")
        return r.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_feedback_stats():
    """Test feedback stats endpoint"""
    print("\n2. Testing /feedback/stats endpoint...")
    try:
        r = requests.get(f"{BASE_URL}/feedback/stats")
        print(f"   Status: {r.status_code}")
        print(f"   Response: {json.dumps(r.json(), indent=2)}")
        return r.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_submit_feedback():
    """Test submitting feedback"""
    print("\n3. Testing /feedback POST endpoint...")
    try:
        feedback_data = {
            "code_snippet": "password = 'super_secret_123'",
            "user_label": "vulnerable",
            "start_line": 1,
            "end_line": 1,
            "start_column": 0,
            "end_column": 35,
            "severity": "high",
            "vulnerability_type": "Broken Authentication",
            "notes": "This is a hardcoded password - definitely vulnerable",
            "file_path": "/test/example.py",
            "language": "python"
        }
        r = requests.post(f"{BASE_URL}/feedback", json=feedback_data)
        print(f"   Status: {r.status_code}")
        print(f"   Response: {json.dumps(r.json(), indent=2)}")
        return r.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_submit_false_positive():
    """Test submitting a false positive"""
    print("\n4. Testing false positive feedback...")
    try:
        feedback_data = {
            "code_snippet": "password = os.environ.get('DB_PASSWORD')",
            "user_label": "secure",
            "start_line": 5,
            "end_line": 5,
            "start_column": 0,
            "end_column": 42,
            "original_detection": "Broken Authentication",
            "notes": "This uses environment variable, not hardcoded",
            "file_path": "/test/config.py",
            "language": "python"
        }
        r = requests.post(f"{BASE_URL}/feedback", json=feedback_data)
        print(f"   Status: {r.status_code}")
        print(f"   Response: {json.dumps(r.json(), indent=2)}")
        return r.status_code == 200 or r.status_code == 409
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_list_feedback():
    """Test listing feedback"""
    print("\n5. Testing /feedback/list endpoint...")
    try:
        r = requests.get(f"{BASE_URL}/feedback/list")
        print(f"   Status: {r.status_code}")
        data = r.json()
        print(f"   Total feedback entries: {data.get('count', 0)}")
        if data.get('feedback'):
            print("   Sample entries:")
            for fb in data['feedback'][:3]:
                print(f"      - ID: {fb['id']}, Type: {fb['feedback_type']}, Label: {fb['user_label']}")
        return r.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_untrained_feedback():
    """Test getting untrained feedback"""
    print("\n6. Testing /feedback/untrained endpoint...")
    try:
        r = requests.get(f"{BASE_URL}/feedback/untrained")
        print(f"   Status: {r.status_code}")
        data = r.json()
        print(f"   Untrained entries: {data.get('count', 0)}")
        return r.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False

def test_scan_with_feedback():
    """Test scanning code"""
    print("\n7. Testing /scan endpoint...")
    try:
        code = '''
def login(username, password):
    # Hardcoded password - BAD!
    admin_password = "admin123"
    
    if password == admin_password:
        return True
    return False
'''
        r = requests.post(f"{BASE_URL}/scan", json={
            "code": code,
            "language": "python",
            "filename": "test.py"
        })
        print(f"   Status: {r.status_code}")
        data = r.json()
        print(f"   Vulnerabilities found: {len(data.get('vulnerabilities', []))}")
        for v in data.get('vulnerabilities', [])[:3]:
            print(f"      - Line {v['line']}: {v['message']}")
        return r.status_code == 200
    except Exception as e:
        print(f"   Error: {e}")
        return False

def main():
    print("=" * 60)
    print("  SecureCode-FL User Feedback System - API Tests")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health),
        ("Feedback Stats", test_feedback_stats),
        ("Submit Vulnerability", test_submit_feedback),
        ("Submit False Positive", test_submit_false_positive),
        ("List Feedback", test_list_feedback),
        ("Untrained Feedback", test_untrained_feedback),
        ("Scan Code", test_scan_with_feedback),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"   Test failed with exception: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("  Test Results")
    print("=" * 60)
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {status} - {name}")
    
    passed_count = sum(1 for _, p in results if p)
    print(f"\n   Total: {passed_count}/{len(results)} tests passed")
    print("=" * 60)

if __name__ == "__main__":
    main()
