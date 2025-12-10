"""
Clean Baseline Validation Test
===============================

This script tests the model WITHOUT federated learning first.
Purpose: Verify basic model functionality and data integrity before Phase 5.

Steps:
1. Load data with CONSISTENT label encoding
2. Split into train/test (verify NO overlap)
3. Train a fresh model
4. Evaluate on test set only
5. Check data leakage

Author: Validation Team
Date: 2025-12-09
"""

import sys
import os
import numpy as np
import pandas as pd
import tensorflow as tf
from datetime import datetime
import hashlib

# Add to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_preprocessing import DataPreprocessor
from config import RANDOM_STATE, TEST_SIZE

# Set seeds for reproducibility
np.random.seed(RANDOM_STATE)
tf.random.set_seed(RANDOM_STATE)


def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def hash_data(data):
    """Create hash of data for comparison (detect contamination)"""
    return hashlib.md5(np.asarray(data).tobytes()).hexdigest()


def build_simple_model(input_dim):
    """Build a simple MLP for baseline testing"""
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(input_dim,)),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    
    return model


def test_baseline():
    """Run clean baseline test"""
    
    print_section("STEP 0: DATA LOADING WITH CONSISTENT ENCODING")
    
    # Load data
    preprocessor = DataPreprocessor()
    preprocessor.load_data()
    
    print(f"\nDataset shape: {preprocessor.df.shape}")
    print(f"Result column values: {preprocessor.df['Result'].unique()}")
    
    # CRITICAL: Use consistent encoding
    # Error = 1 (VULNERABLE), Good = 0 (SECURE)
    preprocessor.df['label'] = preprocessor.df['Result'].apply(
        lambda x: 1 if str(x).strip().lower() == 'error' else 0
    )
    
    y = preprocessor.df['label'].values
    print(f"\nLabel encoding (CONSISTENT):")
    print(f"  Error (vulnerable) → 1: {sum(y == 1)} samples")
    print(f"  Good (secure) → 0: {sum(y == 0)} samples")
    
    # CRITICAL: Extract features
    print_section("STEP 1: FEATURE EXTRACTION")
    
    X = preprocessor.extract_features()
    print(f"\nFeature matrix shape: {X.shape}")
    print(f"Feature sparsity: {(X == 0).sum() / (X.shape[0] * X.shape[1]) * 100:.2f}%")
    
    # CRITICAL: Data split with verification
    print_section("STEP 2: TRAIN/TEST SPLIT WITH LEAKAGE DETECTION")
    
    X_train, X_test, y_train, y_test = preprocessor.split_data(X, y)
    
    print(f"\nTraining set:")
    print(f"  Samples: {X_train.shape[0]}")
    print(f"  Vulnerable: {sum(y_train == 1)} ({sum(y_train == 1)/len(y_train)*100:.1f}%)")
    print(f"  Secure: {sum(y_train == 0)} ({sum(y_train == 0)/len(y_train)*100:.1f}%)")
    
    print(f"\nTest set:")
    print(f"  Samples: {X_test.shape[0]}")
    print(f"  Vulnerable: {sum(y_test == 1)} ({sum(y_test == 1)/len(y_test)*100:.1f}%)")
    print(f"  Secure: {sum(y_test == 0)} ({sum(y_test == 0)/len(y_test)*100:.1f}%)")
    
    # CRITICAL: Check for data leakage
    print(f"\nData Leakage Detection:")
    train_hash = hash_data(X_train)
    test_hash = hash_data(X_test)
    
    if train_hash == test_hash:
        print("  ❌ ERROR: Train and test sets are IDENTICAL!")
        return False
    else:
        print("  [OK] Train and test sets are different")
    
    # Check for duplicate rows between train/test
    train_str = [tuple(row) for row in X_train.toarray()]
    test_str = [tuple(row) for row in X_test.toarray()]
    overlap = len(set(train_str) & set(test_str))
    
    if overlap > 0:
        print(f"  ⚠️  WARNING: {overlap} duplicate rows between train and test!")
    else:
        print(f"  [OK] No duplicate rows between train and test")
    
    # CRITICAL: Train model on training data only
    print_section("STEP 3: TRAIN BASELINE MODEL")
    
    input_dim = X_train.shape[1]
    print(f"\nBuilding model with input_dim={input_dim}")
    
    model = build_simple_model(input_dim)
    
    print(f"\nModel architecture:")
    model.summary()
    
    print(f"\nTraining on {X_train.shape[0]} samples...")
    
    history = model.fit(
        X_train, y_train,
        epochs=50,
        batch_size=32,
        validation_split=0.2,  # Use ONLY training data for validation
        verbose=0,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            )
        ]
    )
    
    print(f"[OK] Training complete")
    print(f"  Final training loss: {history.history['loss'][-1]:.4f}")
    print(f"  Final training accuracy: {history.history['accuracy'][-1]:.4f}")
    print(f"  Final validation accuracy: {history.history['val_accuracy'][-1]:.4f}")
    
    # CRITICAL: Evaluate ONLY on test data
    print_section("STEP 4: EVALUATE ON TEST SET ONLY")
    
    test_loss, test_accuracy = model.evaluate(X_test, y_test, verbose=0)
    
    print(f"\nTest Set Evaluation:")
    print(f"  Loss: {test_loss:.4f}")
    print(f"  Accuracy: {test_accuracy:.4f} ({test_accuracy*100:.2f}%)")
    
    # Per-class metrics
    y_pred_proba = model.predict(X_test, verbose=0).flatten()
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
    
    print(f"\nDetailed Metrics:")
    print(classification_report(y_test, y_pred, 
                               target_names=['Secure (0)', 'Vulnerable (1)']))
    
    cm = confusion_matrix(y_test, y_pred)
    print(f"\nConfusion Matrix:")
    print(f"  [[TN={cm[0,0]}, FP={cm[0,1]}],")
    print(f"   [FN={cm[1,0]}, TP={cm[1,1]}]]")
    
    try:
        auc = roc_auc_score(y_test, y_pred_proba)
        print(f"\nROC-AUC Score: {auc:.4f}")
    except:
        print(f"\nROC-AUC Score: N/A (single class predictions)")
    
    # CRITICAL: Sanity check - model should perform reasonably
    print_section("STEP 5: SANITY CHECKS")
    
    checks = []
    
    # Check 1: Test accuracy > 50% (better than random)
    if test_accuracy > 0.50:
        checks.append(("[OK] Test accuracy > 50%", True))
    else:
        checks.append(("❌ Test accuracy <= 50% (worse than random!)", False))
    
    # Check 2: Training accuracy > test accuracy (no extreme overfitting)
    train_acc = history.history['accuracy'][-1]
    if train_acc - test_accuracy < 0.2:
        checks.append(("[OK] Train-test gap < 20% (no extreme overfitting)", True))
    else:
        checks.append((f"⚠️  Train-test gap = {(train_acc - test_accuracy)*100:.1f}% (possible overfitting)", False))
    
    # Check 3: Data split is stratified
    train_ratio = sum(y_train == 1) / len(y_train)
    test_ratio = sum(y_test == 1) / len(y_test)
    ratio_diff = abs(train_ratio - test_ratio)
    if ratio_diff < 0.05:
        checks.append(("[OK] Train/test class distribution similar (stratified)", True))
    else:
        checks.append((f"⚠️  Class distribution difference = {ratio_diff*100:.1f}%", False))
    
    # Check 4: Predictions are diverse (not always predicting same class)
    pred_ratio = sum(y_pred == 1) / len(y_pred)
    if 0.1 < pred_ratio < 0.9:
        checks.append(("[OK] Predictions are diverse", True))
    else:
        checks.append((f"⚠️  Predictions are skewed ({pred_ratio*100:.1f}% positive)", False))
    
    print(f"\nSanity Checks:")
    for msg, passed in checks:
        print(f"  {msg}")
    
    all_passed = all(p for _, p in checks)
    
    # Save results
    print_section("STEP 6: SAVE RESULTS")
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'test_type': 'Baseline Model (Non-Federated)',
        'dataset_samples': len(preprocessor.df),
        'train_samples': X_train.shape[0],
        'test_samples': X_test.shape[0],
        'num_features': input_dim,
        'test_accuracy': float(test_accuracy),
        'test_loss': float(test_loss),
        'roc_auc': float(auc) if 'auc' in locals() else None,
        'train_accuracy': float(train_acc),
        'train_test_gap': float(train_acc - test_accuracy),
        'confusion_matrix': cm.tolist(),
        'data_leakage_check': 'PASS' if overlap == 0 else 'FAIL',
        'sanity_checks_passed': all_passed,
        'label_encoding': {
            'error': 'vulnerable (1)',
            'good': 'secure (0)'
        },
        'class_distribution_train': {
            'vulnerable': int(sum(y_train == 1)),
            'secure': int(sum(y_train == 0))
        },
        'class_distribution_test': {
            'vulnerable': int(sum(y_test == 1)),
            'secure': int(sum(y_test == 0))
        }
    }
    
    os.makedirs('results/baseline', exist_ok=True)
    results_path = f"results/baseline/clean_baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    import json
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {results_path}")
    
    # Save model
    model_path = f"models/baseline_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.keras"
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    model.save(model_path)
    print(f"Model saved to: {model_path}")
    
    # Final verdict
    print_section("FINAL VERDICT")
    
    if all_passed and test_accuracy > 0.70:
        print(f"\n✅ BASELINE TEST PASSED")
        print(f"   - Model accuracy: {test_accuracy*100:.2f}%")
        print(f"   - Data integrity: OK")
        print(f"   - Ready for Phase 5 (XAI & Privacy)")
        return True
    else:
        print(f"\n⚠️  BASELINE TEST NEEDS ATTENTION")
        if not all_passed:
            print(f"   - Sanity checks failed")
        if test_accuracy <= 0.70:
            print(f"   - Accuracy too low: {test_accuracy*100:.2f}%")
        print(f"   - Review results and rerun")
        return False


if __name__ == "__main__":
    success = test_baseline()
    sys.exit(0 if success else 1)
