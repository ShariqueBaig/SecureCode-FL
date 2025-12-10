"""
Rebuild Vectorizer and Retrain Models
======================================
After dataset cleanup, rebuild TF-IDF vectorizer and retrain all models.
"""

import pandas as pd
import numpy as np
import os
import sys
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
import joblib
import tensorflow as tf
from datetime import datetime

print("="*70)
print("STEP 1: REBUILD TFIDF VECTORIZER FROM CLEANED DATA")
print("="*70)

# Load cleaned dataset
df = pd.read_csv('data/expanded_dataset_v2.csv')
print(f"\n✓ Loaded cleaned dataset: {len(df)} samples")

# Create and fit vectorizer
print("\nBuilding TF-IDF vectorizer...")
vectorizer = TfidfVectorizer(max_features=2000, stop_words='english', min_df=2)
X = vectorizer.fit_transform(df['Code'].astype(str))

print(f"✓ Vectorizer created: {X.shape[1]} features")

# Check for label-leaking features
feature_names = vectorizer.get_feature_names_out()
leaking_keywords = ['vulnerable', 'secure_api', 'vulnerable_api', 'authorization', 'authentication']
leaking_count = 0

print("\nChecking for remaining label-leaking features...")
for keyword in leaking_keywords:
    matches = [f for f in feature_names if keyword in f.lower()]
    if matches:
        leaking_count += len(matches)
        print(f"  ⚠️  {keyword}: {len(matches)} features")
        for match in matches[:2]:
            print(f"      - {match}")

if leaking_count == 0:
    print("  ✓ NO label-leaking features found!")
else:
    print(f"\n⚠️  WARNING: {leaking_count} potentially problematic features remain")
    print("  These may be false positives if they appear in actual code patterns")

# Save vectorizer
vectorizer_path = 'models/tfidf_vectorizer.pkl'
joblib.dump(vectorizer, vectorizer_path)
print(f"\n✓ Vectorizer saved: {vectorizer_path}")

print("\n" + "="*70)
print("STEP 2: PREPARE DATA FOR TRAINING")
print("="*70)

# Convert labels (1=vulnerable, 0=secure)
y = (df['Primary Vulnerability'] != 'None').astype(int).values

# Convert to dense for model training
X_dense = X.toarray()

print(f"\nDataset composition:")
print(f"  Total samples: {len(df)}")
print(f"  Vulnerable: {np.sum(y)} ({np.sum(y)/len(y)*100:.1f}%)")
print(f"  Secure: {len(y)-np.sum(y)} ({(len(y)-np.sum(y))/len(y)*100:.1f}%)")

# Split data properly: 80/20 BEFORE client partitioning
X_train, X_test, y_train, y_test = train_test_split(
    X_dense, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\nTrain/Test split:")
print(f"  Training: {len(X_train)} samples ({np.sum(y_train)} vulnerable)")
print(f"  Test: {len(X_test)} samples ({np.sum(y_test)} vulnerable)")

print("\n" + "="*70)
print("STEP 3: RETRAIN CENTRALIZED MODEL")
print("="*70)

# Create model with optimized architecture (from best config)
model = tf.keras.Sequential([
    tf.keras.layers.Dense(128, activation='relu', input_shape=(X_train.shape[1],)),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.Dropout(0.3),
    
    tf.keras.layers.Dense(64, activation='relu'),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.Dropout(0.2),
    
    tf.keras.layers.Dense(32, activation='relu'),
    tf.keras.layers.BatchNormalization(),
    tf.keras.layers.Dropout(0.1),
    
    tf.keras.layers.Dense(1, activation='sigmoid')
])

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.005),
    loss='binary_crossentropy',
    metrics=['accuracy', tf.keras.metrics.Precision(), tf.keras.metrics.Recall()]
)

print("\nTraining centralized model...")
history = model.fit(
    X_train, y_train,
    validation_split=0.2,
    epochs=30,
    batch_size=16,
    verbose=1
)

# Evaluate on test set
print("\n" + "="*70)
print("STEP 4: EVALUATE ON TEST SET")
print("="*70)

y_pred_prob = model.predict(X_test, verbose=0).flatten()
y_pred = (y_pred_prob >= 0.5).astype(int)

from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

test_accuracy = accuracy_score(y_test, y_pred)
test_precision = precision_score(y_test, y_pred)
test_recall = recall_score(y_test, y_pred)
test_f1 = f1_score(y_test, y_pred)

tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

print(f"\nTest Set Results (Cleaned Dataset):")
print(f"  Accuracy:  {test_accuracy:.2%}")
print(f"  Precision: {test_precision:.2%}")
print(f"  Recall:    {test_recall:.2%}")
print(f"  F1-Score:  {test_f1:.2%}")
print(f"\nConfusion Matrix:")
print(f"  True Negatives:  {tn}")
print(f"  False Positives: {fp}")
print(f"  False Negatives: {fn}")
print(f"  True Positives:  {tp}")

# Cross-validation
print("\n" + "="*70)
print("STEP 5: CROSS-VALIDATION")
print("="*70)

from sklearn.model_selection import cross_val_score

cv_scores = []
for fold in range(3):
    fold_train_indices = np.random.choice(len(X_train), size=int(0.8*len(X_train)), replace=False)
    fold_val_indices = np.array([i for i in range(len(X_train)) if i not in fold_train_indices])
    
    fold_model = tf.keras.Sequential([
        tf.keras.layers.Dense(128, activation='relu', input_shape=(X_train.shape[1],)),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dropout(0.1),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    
    fold_model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.005),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    
    fold_model.fit(
        X_train[fold_train_indices], y_train[fold_train_indices],
        epochs=30, batch_size=16, verbose=0
    )
    
    fold_acc = fold_model.evaluate(X_train[fold_val_indices], y_train[fold_val_indices], verbose=0)[1]
    cv_scores.append(fold_acc)

print(f"\n3-Fold Cross-Validation:")
print(f"  Fold scores: {[f'{s:.2%}' for s in cv_scores]}")
print(f"  Mean: {np.mean(cv_scores):.2%} ± {np.std(cv_scores):.2%}")

# Save model
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
model_path = f'models/neural_networks/cleaned_model_{timestamp}.keras'
model.save(model_path)
print(f"\n✓ Model saved: {model_path}")

# Save results
results = {
    'timestamp': datetime.now().isoformat(),
    'dataset': 'expanded_dataset_v2_cleaned',
    'test_accuracy': float(test_accuracy),
    'test_precision': float(test_precision),
    'test_recall': float(test_recall),
    'test_f1': float(test_f1),
    'cv_mean': float(np.mean(cv_scores)),
    'cv_std': float(np.std(cv_scores)),
    'confusion_matrix': {'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp)},
    'vectorizer_features': int(X_train.shape[1]),
    'training_set_size': len(X_train),
    'test_set_size': len(X_test),
    'notes': 'Retrained on cleaned dataset with label-revealing patterns removed'
}

import json
results_path = f'results/cleaned_dataset_results_{timestamp}.json'
os.makedirs('results', exist_ok=True)
with open(results_path, 'w') as f:
    json.dump(results, f, indent=2)

print(f"✓ Results saved: {results_path}")

print("\n" + "="*70)
print("✓ RETRAINING COMPLETE")
print("="*70)
print(f"\nKey Metrics (Cleaned Dataset):")
print(f"  Test Accuracy: {test_accuracy:.2%}")
print(f"  CV Accuracy: {np.mean(cv_scores):.2%} ± {np.std(cv_scores):.2%}")
print(f"  Vectorizer Features: {X_train.shape[1]}")
print(f"\nCompare to original model:")
print(f"  Original Test Accuracy: 87.4%")
print(f"  Cleaned Dataset Test Accuracy: {test_accuracy:.2%}")

if test_accuracy < 0.87:
    print(f"\n⚠️  Performance dropped by {(0.87-test_accuracy)*100:.1f}%")
    print("    This suggests the model was relying on label-leaking features!")
else:
    print(f"\n✓ Performance maintained or improved!")
    print("    The model learns from legitimate patterns.")

print("\n" + "="*70)
