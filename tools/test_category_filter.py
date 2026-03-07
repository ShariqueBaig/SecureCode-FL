"""
Quick experiment: Test how dropping low-representation categories affects binary classification accuracy.
Usage: python tools/test_category_filter.py
"""
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
import re

df = pd.read_csv('data/merged_dataset.csv')

# Fix the typo category
df['Primary Vulnerability'] = df['Primary Vulnerability'].replace(
    'Broken Object Level Authorizatio', 'Broken Object Level Authorization'
)

def preprocess(code):
    if pd.isna(code): return ''
    return re.sub(r'\s+', ' ', str(code)).strip()

df['processed'] = df['Code'].apply(preprocess)

def evaluate(data, label):
    vec = TfidfVectorizer(max_features=1000, ngram_range=(1, 2), min_df=1)
    X = vec.fit_transform(data['processed'])
    y = (data['Result'] == 'Error').astype(int).values
    clf = LogisticRegression(max_iter=1000, random_state=42)
    scores = cross_val_score(clf, X, y, cv=5, scoring='accuracy')
    print(f"{label}")
    print(f"   N: {len(data)} samples | CV Accuracy: {scores.mean()*100:.2f}% ± {scores.std()*100:.2f}%")

print("=" * 60)
print("CATEGORY FILTER EXPERIMENT")
print("Binary classification (Vulnerable vs Secure)")
print("5-fold cross-validation | LogisticRegression")
print("=" * 60)

# Baseline: all categories
evaluate(df, "Baseline (all 11 categories, N=1490)")

# Drop categories under 30 samples (drops: Improper Inventory Mgmt, UASBF, BOPLA, typo)
counts = df['Primary Vulnerability'].value_counts()
for threshold in [15, 30, 50]:
    drop = counts[counts < threshold].index.tolist()
    filtered = df[~df['Primary Vulnerability'].isin(drop)].copy()
    evaluate(filtered, f"Drop categories < {threshold} samples (drops {len(drop)} cats, N={len(filtered)})")

print("\n--- Category-by-category contribution ---")
for cat in df['Primary Vulnerability'].value_counts().index:
    subset = df[df['Primary Vulnerability'] == cat]
    error_pct = (subset['Result'] == 'Error').mean() * 100
    print(f"  {cat}: {len(subset)} samples, {error_pct:.0f}% vulnerable")
