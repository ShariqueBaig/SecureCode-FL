"""Test the server with the full test_vulnerable_code.py file"""
import requests

# Read the test file
with open("test_vulnerable_code.py", "r", encoding="utf-8") as f:
    test_code = f.read()

# Send to server
response = requests.post(
    "http://localhost:5000/scan",
    json={"code": test_code, "language": "python", "filename": "test_vulnerable_code.py"}
)

result = response.json()

print("=" * 70)
print(f"  FULL TEST FILE SCAN RESULTS")
print("=" * 70)
print(f"\nTotal vulnerabilities found: {len(result['vulnerabilities'])}")
print(f"Scan time: {result['scan_time_ms']}ms\n")

# Group by severity
by_severity = {"high": [], "medium": [], "low": []}
for v in result['vulnerabilities']:
    by_severity[v['severity']].append(v)

print(f"🔴 HIGH severity: {len(by_severity['high'])}")
print(f"🟡 MEDIUM severity: {len(by_severity['medium'])}")
print(f"🟢 LOW severity: {len(by_severity['low'])}")

print("\n" + "-" * 70)
print("DETAILED FINDINGS:")
print("-" * 70)

for i, v in enumerate(result['vulnerabilities'], 1):
    severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[v['severity']]
    print(f"\n{i}. {severity_icon} [{v['severity'].upper()}] Line {v['line']}")
    print(f"   Type: {v['vulnerability_type']}")
    print(f"   Message: {v['message']}")
    print(f"   CWE: {v['cwe_id']}")
