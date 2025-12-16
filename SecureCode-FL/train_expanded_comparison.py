"""
Train Model with Expanded OWASP Dataset
========================================

Trains and evaluates model on the expanded 1000-sample OWASP dataset,
then compares with original dataset accuracy.
"""

import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tensorflow as tf
from tensorflow import keras
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib

from config import RANDOM_STATE

# Suppress TF warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
tf.get_logger().setLevel('ERROR')

np.random.seed(RANDOM_STATE)
tf.random.set_seed(RANDOM_STATE)


def load_expanded_dataset():
    """Load the expanded OWASP dataset."""
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'owasp_expanded_dataset.csv')
    df = pd.read_csv(data_path)
    
    # Label encoding: Error=1 (Vulnerable), Good=0 (Secure)
    df['Label'] = df['Result'].map({'Error': 1, 'Good': 0})
    
    print(f"Loaded expanded dataset:")
    print(f"  Total samples: {len(df)}")
    print(f"  Vulnerable (Error=1): {(df['Label'] == 1).sum()}")
    print(f"  Secure (Good=0): {(df['Label'] == 0).sum()}")
    print(f"  Vulnerability types: {df['vulnerability_type'].nunique()}")
    
    return df


def load_original_dataset():
    """Load the original cleaned dataset."""
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'expanded_dataset_v2.csv')
    df = pd.read_csv(data_path)
    
    # Label encoding: Error=1 (Vulnerable), Good=0 (Secure)
    df['Label'] = df['Result'].map({'Error': 1, 'Good': 0})
    
    print(f"Loaded original dataset:")
    print(f"  Total samples: {len(df)}")
    print(f"  Vulnerable (Error=1): {(df['Label'] == 1).sum()}")
    print(f"  Secure (Good=0): {(df['Label'] == 0).sum()}")
    
    return df


def create_model(input_dim, hidden_layers=[128, 64, 32], dropout_rates=[0.3, 0.2, 0.1]):
    """Create neural network model."""
    model = keras.Sequential()
    model.add(keras.layers.Input(shape=(input_dim,)))
    
    for units, dropout in zip(hidden_layers, dropout_rates):
        model.add(keras.layers.Dense(units, activation='relu', 
                                     kernel_regularizer=keras.regularizers.l2(0.01)))
        model.add(keras.layers.Dropout(dropout))
    
    model.add(keras.layers.Dense(1, activation='sigmoid'))
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.005),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    
    return model


def train_and_evaluate(df, dataset_name, epochs=50, batch_size=16):
    """Train model and return accuracy."""
    print(f"\n{'='*60}")
    print(f" Training on: {dataset_name}")
    print(f"{'='*60}")
    
    X = df['Code'].values
    y = df['Label'].values
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    
    # Create TF-IDF features
    vectorizer = TfidfVectorizer(max_features=2000, ngram_range=(1, 2))
    X_train_tfidf = vectorizer.fit_transform(X_train).toarray().astype(np.float32)
    X_test_tfidf = vectorizer.transform(X_test).toarray().astype(np.float32)
    
    print(f"  Train: {len(X_train)} samples")
    print(f"  Test: {len(X_test)} samples")
    print(f"  Features: {X_train_tfidf.shape[1]}")
    
    # Create and train model
    model = create_model(input_dim=X_train_tfidf.shape[1])
    
    early_stop = keras.callbacks.EarlyStopping(
        monitor='val_loss', patience=10, restore_best_weights=True
    )
    
    history = model.fit(
        X_train_tfidf, y_train,
        epochs=epochs,
        batch_size=batch_size,
        validation_split=0.2,
        callbacks=[early_stop],
        verbose=0
    )
    
    # Evaluate
    _, test_accuracy = model.evaluate(X_test_tfidf, y_test, verbose=0)
    train_accuracy = max(history.history['accuracy'])
    val_accuracy = max(history.history['val_accuracy'])
    
    print(f"\n  Results:")
    print(f"    Train accuracy: {train_accuracy:.4f} ({train_accuracy*100:.2f}%)")
    print(f"    Val accuracy: {val_accuracy:.4f} ({val_accuracy*100:.2f}%)")
    print(f"    Test accuracy: {test_accuracy:.4f} ({test_accuracy*100:.2f}%)")
    
    return {
        'dataset': dataset_name,
        'samples': len(df),
        'train_accuracy': train_accuracy,
        'val_accuracy': val_accuracy,
        'test_accuracy': test_accuracy,
        'model': model,
        'vectorizer': vectorizer
    }


def main():
    """Compare original vs expanded dataset accuracy."""
    print("="*60)
    print(" DATASET EXPANSION ACCURACY COMPARISON")
    print("="*60)
    
    # Train on original dataset
    original_df = load_original_dataset()
    original_results = train_and_evaluate(original_df, "Original (471 samples)")
    
    # Train on expanded dataset
    expanded_df = load_expanded_dataset()
    expanded_results = train_and_evaluate(expanded_df, "Expanded (1000 samples)")
    
    # Train on combined dataset
    combined_df = pd.concat([original_df[['Code', 'Result', 'Label']], 
                             expanded_df[['Code', 'Result', 'Label']]], 
                            ignore_index=True)
    combined_results = train_and_evaluate(combined_df, "Combined (1471 samples)")
    
    # Summary
    print("\n" + "="*60)
    print(" COMPARISON SUMMARY")
    print("="*60)
    print(f"{'Dataset':<25} {'Samples':<10} {'Test Acc':<12} {'Improvement':<12}")
    print("-"*60)
    
    baseline = original_results['test_accuracy']
    for result in [original_results, expanded_results, combined_results]:
        improvement = result['test_accuracy'] - baseline
        imp_str = f"+{improvement*100:.2f}%" if improvement > 0 else f"{improvement*100:.2f}%"
        print(f"{result['dataset']:<25} {result['samples']:<10} {result['test_accuracy']*100:.2f}%{'':<6} {imp_str if result['dataset'] != 'Original (471 samples)' else '-'}")
    
    # Save best model (combined)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    model_path = f"models/neural_networks/combined_model_{timestamp}.keras"
    vectorizer_path = f"models/vectorizers/combined_vectorizer_{timestamp}.pkl"
    
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    combined_results['model'].save(model_path)
    joblib.dump(combined_results['vectorizer'], vectorizer_path)
    
    print(f"\n  Best model saved to: {model_path}")
    print(f"  Vectorizer saved to: {vectorizer_path}")
    
    return {
        'original': original_results,
        'expanded': expanded_results,
        'combined': combined_results
    }


if __name__ == "__main__":
    results = main()
