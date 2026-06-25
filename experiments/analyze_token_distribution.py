"""
Token Distribution Analysis for Label Leakage Detection
Checks if certain tokens are over-represented in one class vs the other.
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from collections import Counter
import re

# Load dataset
df = pd.read_csv('data/expanded_dataset_v2.csv')

# Encode labels: Error = 1 (Vulnerable), Good = 0 (Secure)
df['label'] = df['Result'].map({'Error': 1, 'Good': 0})

print("="*70)
print(" TOKEN DISTRIBUTION ANALYSIS FOR LABEL LEAKAGE")
print("="*70)

print(f"\nDataset: {len(df)} samples")
print(f"Vulnerable (1): {(df['label'] == 1).sum()}")
print(f"Secure (0): {(df['label'] == 0).sum()}")

# Separate by class
vulnerable_code = df[df['label'] == 1]['Code'].tolist()
secure_code = df[df['label'] == 0]['Code'].tolist()

# Simple tokenizer
def tokenize(text):
    if pd.isna(text):
        return []
    return re.findall(r'\b\w+\b', str(text).lower())

# Count tokens per class
vuln_tokens = Counter()
secure_tokens = Counter()

for code in vulnerable_code:
    vuln_tokens.update(tokenize(code))

for code in secure_code:
    secure_tokens.update(tokenize(code))

# Get all tokens
all_tokens = set(vuln_tokens.keys()) | set(secure_tokens.keys())

# Calculate token ratios
print(f"\n{'='*70}")
print(" TOKENS HIGHLY ASSOCIATED WITH VULNERABLE CODE")
print(f"{'='*70}")

token_ratios = []
for token in all_tokens:
    v_count = vuln_tokens.get(token, 0)
    s_count = secure_tokens.get(token, 0)
    total = v_count + s_count
    if total >= 10:  # Only consider tokens that appear at least 10 times
        vuln_ratio = v_count / total if total > 0 else 0
        token_ratios.append({
            'token': token,
            'vuln_count': v_count,
            'secure_count': s_count,
            'total': total,
            'vuln_ratio': vuln_ratio
        })

# Sort by vulnerability ratio
token_ratios.sort(key=lambda x: x['vuln_ratio'], reverse=True)

print(f"\n{'Token':<25} {'Vuln':>8} {'Secure':>8} {'Total':>8} {'Vuln%':>8}")
print("-" * 60)
for t in token_ratios[:20]:
    print(f"{t['token']:<25} {t['vuln_count']:>8} {t['secure_count']:>8} {t['total']:>8} {t['vuln_ratio']*100:>7.1f}%")

print(f"\n{'='*70}")
print(" TOKENS HIGHLY ASSOCIATED WITH SECURE CODE")
print(f"{'='*70}")
print(f"\n{'Token':<25} {'Vuln':>8} {'Secure':>8} {'Total':>8} {'Secure%':>8}")
print("-" * 60)
token_ratios.sort(key=lambda x: x['vuln_ratio'])
for t in token_ratios[:20]:
    print(f"{t['token']:<25} {t['vuln_count']:>8} {t['secure_count']:>8} {t['total']:>8} {(1-t['vuln_ratio'])*100:>7.1f}%")

# Check for suspicious patterns
print(f"\n{'='*70}")
print(" CHECKING FOR LABEL-LEAKING TOKENS")
print(f"{'='*70}")

suspicious_tokens = ['vulnerable', 'insecure', 'unsafe', 'bad', 'wrong', 'secure', 'safe', 'good', 'correct', 'proper']

print(f"\n{'Token':<15} {'In Vuln Code':>12} {'In Secure Code':>15} {'Concern?':>10}")
print("-" * 55)
for token in suspicious_tokens:
    v = vuln_tokens.get(token, 0)
    s = secure_tokens.get(token, 0)
    total = v + s
    if total > 0:
        concern = "⚠️ YES" if (v/(v+s) > 0.8 or s/(v+s) > 0.8) else "✅ OK"
    else:
        concern = "N/A"
    print(f"{token:<15} {v:>12} {s:>15} {concern:>10}")

print("\n" + "="*70)
print(" ANALYSIS COMPLETE")
print("="*70)
