import pandas as pd
import re

# Load cleaned dataset
df = pd.read_csv('data/expanded_dataset_v2.csv')

print("="*70)
print("CHECKING FOR REMAINING LABEL-REVEALING NAMES")
print("="*70)

# Keywords that might reveal labels
suspicious_keywords = [
    'vulnerable', 'vulnerable_api', 'secure_api', 'secure',
    'unsafe', 'safe', 'exploit', 'attack', 'bypass',
    'vulnerability', 'error_handler',
    'def vulnerable', 'def secure', 'def error', 'def good'
]

print("\nScanning all code samples for suspicious patterns...\n")

found_issues = []

for idx, row in df.iterrows():
    code = str(row['Code']).lower()
    vuln_type = row['Primary Vulnerability']
    
    for keyword in suspicious_keywords:
        if keyword.lower() in code:
            found_issues.append({
                'row': idx,
                'keyword': keyword,
                'vulnerability_type': vuln_type
            })

if found_issues:
    print(f"⚠️  FOUND {len(found_issues)} POTENTIAL ISSUES:\n")
    seen = set()
    for issue in found_issues:
        key = (issue['row'], issue['keyword'])
        if key not in seen:
            print(f"  Row {issue['row']}: '{issue['keyword']}' in {issue['vulnerability_type']}")
            seen.add(key)
else:
    print("✓ NO label-revealing keywords found in dataset!")

# More detailed search
print("\n" + "="*70)
print("DETAILED FUNCTION/ROUTE NAME ANALYSIS")
print("="*70)

function_pattern = r'def\s+(\w+)\s*\('
route_pattern = r"@app\.route\(['\"]([^'\"]+)"

issues_detail = []

for idx, row in df.iterrows():
    code = str(row['Code'])
    
    # Find function names
    func_matches = re.findall(function_pattern, code, re.IGNORECASE)
    for func in func_matches:
        if any(bad in func.lower() for bad in ['vulnerable', 'secure', 'error', 'good']):
            issues_detail.append(('function', idx, func, row['Primary Vulnerability']))
    
    # Find route names
    route_matches = re.findall(route_pattern, code, re.IGNORECASE)
    for route in route_matches:
        if any(bad in route.lower() for bad in ['vulnerable', 'secure', 'error', 'good']):
            issues_detail.append(('route', idx, route, row['Primary Vulnerability']))

if issues_detail:
    print(f"\n⚠️  Found {len(issues_detail)} revealing function/route names:\n")
    for item_type, row_num, name, vuln_type in issues_detail[:15]:
        print(f"  Row {row_num} [{item_type}]: '{name}'")
        print(f"    Vulnerability: {vuln_type}\n")
else:
    print("\n✓ NO revealing function or route names found!")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
if not found_issues and not issues_detail:
    print("\n✅ CLEANED DATASET IS SAFE - No label-revealing names detected")
else:
    total = len(set((i['row'], i['keyword']) for i in found_issues)) + len(issues_detail)
    print(f"\n⚠️  POTENTIAL REMAINING ISSUES: {total} cases")
    print("   May need further cleanup")
