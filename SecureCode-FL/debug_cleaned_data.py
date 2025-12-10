"""
Debug: Check cleaned dataset characteristics
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer

# Load cleaned dataset
df = pd.read_csv('data/expanded_dataset_v2.csv')

print("="*70)
print("CLEANED DATASET ANALYSIS")
print("="*70)

# Check labels
y = (df['Primary Vulnerability'] != 'None').astype(int).values

print(f"\nTotal samples: {len(df)}")
print(f"Vulnerable (1): {np.sum(y)}")
print(f"Secure (0): {len(y) - np.sum(y)}")

# Check for 'None' label
print(f"\nUnique vulnerability types:")
print(df['Primary Vulnerability'].value_counts())

# Recreate TF-IDF
vectorizer = TfidfVectorizer(max_features=2000, stop_words='english', min_df=2)
X = vectorizer.fit_transform(df['Code'].astype(str))

X_dense = X.toarray()

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X_dense, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\n" + "="*70)
print("TRAIN/TEST SPLIT")
print("="*70)
print(f"Training set: {len(X_train)} samples")
print(f"  Vulnerable: {np.sum(y_train)} ({np.sum(y_train)/len(y_train)*100:.1f}%)")
print(f"  Secure: {len(y_train)-np.sum(y_train)} ({(len(y_train)-np.sum(y_train))/len(y_train)*100:.1f}%)")

print(f"\nTest set: {len(X_test)} samples")
print(f"  Vulnerable: {np.sum(y_test)} ({np.sum(y_test)/len(y_test)*100:.1f}%)")
print(f"  Secure: {len(y_test)-np.sum(y_test)} ({(len(y_test)-np.sum(y_test))/len(y_test)*100:.1f}%)")

# The issue: all 'None' are being labeled as 1 (vulnerable), but actually 'None' should be secure (0)
print(f"\n" + "="*70)
print("LABEL ENCODING CHECK")
print("="*70)

# Check what 'None' really means
none_mask = df['Primary Vulnerability'] == 'None'
print(f"\nRows with 'None' label: {np.sum(none_mask)}")

# Let's see what actual vulnerability types exist
print(f"\nAll unique vulnerability types:")
unique_vulns = df['Primary Vulnerability'].unique()
for i, vuln in enumerate(unique_vulns):
    count = np.sum(df['Primary Vulnerability'] == vuln)
    print(f"  {i+1}. '{vuln}': {count} samples")

print(f"\n⚠️  Issue: 'None' is being treated as vulnerable, but it's probably secure code!")
print(f"    Need to fix label encoding: 'None' should = 0 (secure), others = 1 (vulnerable)")
