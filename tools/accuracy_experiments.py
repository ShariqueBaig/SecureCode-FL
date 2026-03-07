"""
Accuracy Improvement Experiments for SecureCode-FL
Tests multiple techniques to improve binary classification accuracy:
  1. TF-IDF max_features scaling
  2. Class weight balancing (addresses 58/42 imbalance)
  3. Code-aware tokenization (preserves code tokens better)
  4. Feature engineering: add vulnerability-type hint as a feature
  5. MLP neural network (the model used in the FL paper)
"""
import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier, ExtraTreesClassifier, RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import LabelEncoder
from scipy.sparse import hstack
import warnings
warnings.filterwarnings('ignore')

df = pd.read_csv('data/merged_dataset.csv')
df['Primary Vulnerability'] = df['Primary Vulnerability'].replace(
    'Broken Object Level Authorizatio', 'Broken Object Level Authorization'
)

CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

def evaluate(X, y, model, label):
    scores = cross_val_score(model, X, y, cv=CV, scoring='accuracy')
    f1 = cross_val_score(model, X, y, cv=CV, scoring='f1')
    print(f"  {label}")
    print(f"    Accuracy: {scores.mean()*100:.2f}% ± {scores.std()*100:.2f}%   |   F1: {f1.mean():.3f}")

# Labels
y = (df['Result'] == 'Error').astype(int).values

# ── Preprocessing ─────────────────────────────────────────

def preprocess_basic(code):
    """Same as current pipeline."""
    if pd.isna(code): return ''
    return re.sub(r'\s+', ' ', str(code)).strip()

def preprocess_code_aware(code):
    """
    Better tokenization for code:
    - Keeps camelCase, snake_case splits
    - Preserves function names, keywords
    - Strips numeric literals (they add noise)
    """
    if pd.isna(code): return ''
    code = str(code)
    # Split camelCase: sqlInjection → sql Injection
    code = re.sub(r'([a-z])([A-Z])', r'\1 \2', code)
    # Split snake_case: sql_injection → sql injection
    code = re.sub(r'_', ' ', code)
    # Remove numeric literals
    code = re.sub(r'\b\d+\b', 'NUM', code)
    # Normalize whitespace
    code = re.sub(r'\s+', ' ', code)
    return code.strip().lower()


df['basic'] = df['Code'].apply(preprocess_basic)
df['smart'] = df['Code'].apply(preprocess_code_aware)

print("=" * 60)
print("ACCURACY IMPROVEMENT EXPERIMENTS")
print("Binary classification | 5-fold CV")
print("=" * 60)

# ── Experiment 1: TF-IDF Feature Count ─────────────────────
print("\n1. TF-IDF max_features scaling (LogisticRegression)")
for n in [500, 1000, 2000, 5000, 10000]:
    vec = TfidfVectorizer(max_features=n, ngram_range=(1, 2), min_df=1)
    X = vec.fit_transform(df['basic'])
    evaluate(X, y, LogisticRegression(max_iter=1000), f"max_features={n}")

# ── Experiment 2: Class Weights (handles imbalance) ────────
print("\n2. Class weight balancing (best max_features from above)")
vec = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), min_df=1)
X = vec.fit_transform(df['basic'])
evaluate(X, y, LogisticRegression(max_iter=1000, class_weight='balanced'), "LR + class_weight=balanced")
evaluate(X, y, RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42), "RandomForest + class_weight=balanced")
evaluate(X, y, ExtraTreesClassifier(n_estimators=100, class_weight='balanced', random_state=42), "ExtraTrees + class_weight=balanced")

# ── Experiment 3: Smart code tokenization ─────────────────
print("\n3. Code-aware tokenization vs basic (max_features=5000, LR)")
vec_basic = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), min_df=1)
X_basic = vec_basic.fit_transform(df['basic'])
evaluate(X_basic, y, LogisticRegression(max_iter=1000), "Basic tokenization")

vec_smart = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), min_df=1)
X_smart = vec_smart.fit_transform(df['smart'])
evaluate(X_smart, y, LogisticRegression(max_iter=1000), "Code-aware tokenization (camelCase splits, NUM replace)")

# ── Experiment 4: Add vulnerability type as feature ────────
print("\n4. Adding vulnerability type as auxiliary feature")
le = LabelEncoder()
vuln_type_feat = le.fit_transform(df['Primary Vulnerability']).reshape(-1, 1)
from scipy.sparse import csr_matrix
X_with_type = hstack([X_smart, csr_matrix(vuln_type_feat)])
evaluate(X_with_type, y, LogisticRegression(max_iter=1000), "Smart TF-IDF + vulnerability type hint")

# ── Experiment 5: MLP (what the FL paper uses) ─────────────
print("\n5. MLP neural network (the model used in FL paper)")
evaluate(X_smart, y, MLPClassifier(hidden_layer_sizes=(256, 128), max_iter=500, random_state=42), "MLP (256,128) basic tokens")
evaluate(X_smart, y, MLPClassifier(hidden_layer_sizes=(256, 128), max_iter=500, random_state=42, early_stopping=True), "MLP (256,128) + early stopping")

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
