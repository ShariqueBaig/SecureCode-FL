import pandas as pd
import numpy as np

# Load expanded dataset
df = pd.read_csv('data/expanded_dataset_v2.csv')

print("="*70)
print("CHECKING FOR DATA LEAKAGE IN DATASET")
print("="*70)

# Check first few rows
print("\nFirst 5 rows:")
print(df.head())

print("\n" + "="*70)
print("Column names:")
print(df.columns.tolist())

print("\n" + "="*70)
print("Sample code snippets (first 3 rows):")
for i in range(3):
    print(f"\n--- Row {i} ---")
    code = str(df.iloc[i, 0])[:300]  # First 300 chars of code
    label = df.iloc[i, 1] if len(df.columns) > 1 else "?"
    print(f"Label: {label}")
    print(f"Code snippet: {code}...")
    
    # Check if label is mentioned in code
    if isinstance(code, str):
        if 'vulnerable' in code.lower() or 'vulnerability' in code.lower():
            print("⚠️  WARNING: 'vulnerable' found in code!")
        if 'secure' in code.lower() or 'safe' in code.lower():
            print("⚠️  WARNING: 'secure/safe' found in code!")

print("\n" + "="*70)
print("CHECKING KEYWORDS IN CODE SAMPLES")
print("="*70)

# Sample 20 random rows
sample_indices = np.random.choice(len(df), min(20, len(df)), replace=False)
vuln_keyword_count = 0
secure_keyword_count = 0
vulnerable_label_count = 0

for idx in sample_indices:
    code = str(df.iloc[idx, 0]).lower()
    label = df.iloc[idx, 1] if len(df.columns) > 1 else "?"
    
    # Check for label words in code
    has_vuln_keyword = 'vulnerable' in code or 'vulnerability' in code or 'exploit' in code
    has_secure_keyword = 'secure' in code or 'safe' in code or 'sanitize' in code
    is_vulnerable_label = (label == 1 or label == 'vulnerable')
    
    if has_vuln_keyword:
        vuln_keyword_count += 1
        print(f"\n[Row {idx}] Label={label}, Has vulnerability-related keyword in code")
    if has_secure_keyword:
        secure_keyword_count += 1
        print(f"\n[Row {idx}] Label={label}, Has secure-related keyword in code")
    
    if is_vulnerable_label:
        vulnerable_label_count += 1

print("\n" + "="*70)
print("LEAKAGE ANALYSIS RESULTS")
print("="*70)
print(f"Sample size: 20 random rows")
print(f"Rows with 'vulnerable' in code: {vuln_keyword_count}/20 ({vuln_keyword_count/20*100:.1f}%)")
print(f"Rows with 'secure/safe' in code: {secure_keyword_count}/20 ({secure_keyword_count/20*100:.1f}%)")
print(f"Rows labeled as vulnerable: {vulnerable_label_count}/20 ({vulnerable_label_count/20*100:.1f}%)")

if vuln_keyword_count > 0:
    print("\n⚠️  LEAKAGE DETECTED: Label words appear in code comments!")
    print("This could be inflating SHAP feature importance!")
else:
    print("\n✓ NO LEAKAGE: Label words not found in code snippets")
