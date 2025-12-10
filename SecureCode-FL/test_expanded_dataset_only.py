"""
Test with Expanded Dataset
===========================

This script tests the model using the EXPANDED dataset (471 samples)
instead of the original 60 samples.

This should show if the problem is the dataset size.
"""

import sys
import os
import numpy as np
import pandas as pd
import tensorflow as tf
from datetime import datetime

# Add to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import RANDOM_STATE

# Set seeds
np.random.seed(RANDOM_STATE)
tf.random.set_seed(RANDOM_STATE)


def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def build_model(input_dim):
    """Build baseline MLP"""
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


def test_expanded_dataset():
    """Test on expanded dataset"""
    
    print_section("STEP 1: LOAD EXPANDED DATASET")
    
    # Load expanded dataset
    expanded_path = "data/expanded_dataset_v2.csv"
    
    if not os.path.exists(expanded_path):
        print(f"❌ Expanded dataset not found: {expanded_path}")
        return False
    
    df = pd.read_csv(expanded_path)
    print(f"\nDataset loaded: {expanded_path}")
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"\nFirst few rows:")
    print(df.head())
    
    # Check what columns contain code and labels
    print(f"\nColumn info:")
    for col in df.columns:
        print(f"  {col}: {df[col].dtype}, {len(df[col].unique())} unique values")
    
    # Identify label column
    print(f"\nResult/Label column values:")
    if 'Result' in df.columns:
        print(df['Result'].value_counts())
    elif 'label' in df.columns:
        print(df['label'].value_counts())
    else:
        print("No 'Result' or 'label' column found!")
        return False
    
    # Identify code column
    code_col = None
    for col in ['Code', 'code', 'snippet', 'Code Snippet']:
        if col in df.columns:
            code_col = col
            break
    
    if not code_col:
        print(f"❌ No code column found")
        return False
    
    print(f"Code column: {code_col}")
    
    # Extract features
    print_section("STEP 2: EXTRACT TF-IDF FEATURES")
    
    from sklearn.feature_extraction.text import TfidfVectorizer
    
    vectorizer = TfidfVectorizer(max_features=1000)
    X = vectorizer.fit_transform(df[code_col]).toarray()
    
    # Encode labels
    label_col = 'Result' if 'Result' in df.columns else 'label'
    if label_col == 'Result':
        y = (df[label_col].str.lower() == 'error').astype(int).values
    else:
        y = df[label_col].values
    
    print(f"\nFeature matrix shape: {X.shape}")
    print(f"Vulnerable (1): {sum(y == 1)}")
    print(f"Secure (0): {sum(y == 0)}")
    
    # Split data
    print_section("STEP 3: SPLIT TRAIN/TEST")
    
    from sklearn.model_selection import train_test_split
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    
    print(f"\nTraining set:")
    print(f"  Samples: {X_train.shape[0]}")
    print(f"  Vulnerable: {sum(y_train == 1)}")
    print(f"  Secure: {sum(y_train == 0)}")
    
    print(f"\nTest set:")
    print(f"  Samples: {X_test.shape[0]}")
    print(f"  Vulnerable: {sum(y_test == 1)}")
    print(f"  Secure: {sum(y_test == 0)}")
    
    # Train model
    print_section("STEP 4: TRAIN MODEL")
    
    input_dim = X_train.shape[1]
    model = build_model(input_dim)
    
    print(f"Training on {X_train.shape[0]} samples with {input_dim} features...")
    
    history = model.fit(
        X_train, y_train,
        epochs=50,
        batch_size=32,
        validation_split=0.2,
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
    print(f"  Final training accuracy: {history.history['accuracy'][-1]:.4f}")
    print(f"  Final validation accuracy: {history.history['val_accuracy'][-1]:.4f}")
    
    # Evaluate
    print_section("STEP 5: EVALUATE ON TEST SET")
    
    test_loss, test_accuracy = model.evaluate(X_test, y_test, verbose=0)
    
    print(f"\nTest Set Results:")
    print(f"  Loss: {test_loss:.4f}")
    print(f"  Accuracy: {test_accuracy:.4f} ({test_accuracy*100:.2f}%)")
    
    # Detailed metrics
    y_pred_proba = model.predict(X_test, verbose=0).flatten()
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    from sklearn.metrics import classification_report, confusion_matrix
    
    print(f"\nDetailed Metrics:")
    print(classification_report(y_test, y_pred, 
                               target_names=['Secure (0)', 'Vulnerable (1)']))
    
    cm = confusion_matrix(y_test, y_pred)
    print(f"\nConfusion Matrix:")
    print(f"  Secure (0): TP={cm[0,0]}, FP={cm[0,1]}")
    print(f"  Vulnerable (1): FN={cm[1,0]}, TP={cm[1,1]}")
    
    # Analysis
    print_section("ANALYSIS")
    
    train_acc = history.history['accuracy'][-1]
    train_test_gap = train_acc - test_accuracy
    
    print(f"\nDataset Size Comparison:")
    print(f"  Original dataset: 60 samples, 1000 features → 33.33% test accuracy")
    print(f"  Expanded dataset: 471 samples, 1000 features → {test_accuracy*100:.2f}% test accuracy")
    print(f"\nOverfitting Analysis:")
    print(f"  Train-test gap: {train_test_gap*100:.1f}%")
    
    if test_accuracy > 0.70:
        print(f"\n✅ Good! Larger dataset significantly improves generalization")
        return True
    elif test_accuracy > 0.50:
        print(f"\n⚠️  Moderate results. Still some overfitting")
        return True
    else:
        print(f"\n❌ Still overfitting even with larger dataset")
        return False


if __name__ == "__main__":
    success = test_expanded_dataset()
    sys.exit(0 if success else 1)
