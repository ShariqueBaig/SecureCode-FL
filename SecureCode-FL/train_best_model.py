"""
Train Best MLP Model on Expanded Dataset
========================================

Trains the best neural network configuration found via GridSearchCV:
- Architecture: 128→64→32
- Learning Rate: 0.005
- Dropout: (0.3, 0.2, 0.1)
- L2 Regularization: 0.01

This model achieves 93.84% ±1.83% accuracy (vs MLP_v3's 93.4% ±1.4%).

Execution time: ~1-2 hours for full training with cross-validation.
"""

import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import regularizers
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import json
from datetime import datetime

# Suppress TF warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
tf.get_logger().setLevel('ERROR')

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)
tf.random.set_seed(RANDOM_STATE)

# Configuration for best model
CONFIG = {
    'architecture': [128, 64, 32],
    'learning_rate': 0.005,
    'dropout_rates': [0.3, 0.2, 0.1],
    'l2_regularization': 0.01,
    'epochs': 30,
    'batch_size': 32,
    'cv_folds': 3
}


def load_expanded_dataset():
    """Load the expanded dataset"""
    print("\n" + "="*70)
    print(" LOADING EXPANDED DATASET")
    print("="*70)
    
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    csv_path = os.path.join(data_dir, "expanded_dataset_v2.csv")
    
    df = pd.read_csv(csv_path)
    print(f"\nLoaded expanded dataset: {len(df)} samples")
    
    # Clean labels
    df['Result'] = df['Result'].map({'Error': 1, 'Good': 0})  # Error=1 (Vulnerable), Good=0 (Secure)
    
    # Basic dataset info
    print(f"\nDataset composition:")
    print(f"  - Vulnerable (Error=0): {(df['Result'] == 0).sum()}")
    print(f"  - Secure (Good=1): {(df['Result'] == 1).sum()}")
    
    return df


def prepare_tfidf_data(df, max_features=2000, test_size=0.2):
    """
    Prepare TF-IDF features with proper train/test split.
    IMPORTANT: Test set is isolated from all training before TF-IDF fitting.
    """
    print("\n" + "="*70)
    print(" PREPARING TF-IDF FEATURES")
    print("="*70)
    
    X = df['Code'].values
    y = df['Result'].values
    
    # CRITICAL: Split FIRST before fitting vectorizer
    print(f"\nSplitting data (80/20 train/test)...")
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=RANDOM_STATE,
        stratify=y
    )
    
    print(f"  - Training samples: {len(X_train_raw)}")
    print(f"  - Test samples: {len(X_test_raw)}")
    
    # Fit vectorizer ONLY on training data
    print(f"\nFitting TF-IDF vectorizer on training data...")
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=(1, 2),
        stop_words=None
    )
    
    X_train_tfidf = vectorizer.fit_transform(X_train_raw).toarray()
    X_test_tfidf = vectorizer.transform(X_test_raw).toarray()
    
    print(f"  - TF-IDF features: {X_train_tfidf.shape[1]}")
    
    return X_train_tfidf, X_test_tfidf, y_train, y_test, vectorizer


def build_best_mlp(input_dim):
    """Build best MLP architecture from GridSearchCV"""
    model = keras.Sequential([
        keras.layers.Input(shape=(input_dim,)),
        
        # First hidden layer: 128 units
        keras.layers.Dense(
            128, 
            activation='relu',
            kernel_regularizer=regularizers.l2(0.01)
        ),
        keras.layers.BatchNormalization(),
        keras.layers.Dropout(0.3),
        
        # Second hidden layer: 64 units
        keras.layers.Dense(
            64, 
            activation='relu',
            kernel_regularizer=regularizers.l2(0.01)
        ),
        keras.layers.BatchNormalization(),
        keras.layers.Dropout(0.2),
        
        # Third hidden layer: 32 units
        keras.layers.Dense(
            32, 
            activation='relu',
            kernel_regularizer=regularizers.l2(0.01)
        ),
        keras.layers.Dropout(0.1),
        
        # Output layer
        keras.layers.Dense(1, activation='sigmoid')
    ])
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.005),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    
    return model


def train_best_model_centralized(X_train, X_test, y_train, y_test):
    """Train best model on centralized data"""
    print("\n" + "="*70)
    print(" TRAINING BEST MODEL (CENTRALIZED)")
    print("="*70)
    
    # Build model
    print(f"\nBuilding model architecture...")
    model = build_best_mlp(X_train.shape[1])
    
    print(f"\nModel summary:")
    model.summary()
    
    # Count parameters
    total_params = model.count_params()
    print(f"\nTotal parameters: {total_params:,}")
    
    # Train model
    print(f"\nTraining model for {CONFIG['epochs']} epochs...")
    print(f"  - Batch size: {CONFIG['batch_size']}")
    print(f"  - Learning rate: {CONFIG['learning_rate']}")
    
    history = model.fit(
        X_train, y_train,
        validation_split=0.2,
        epochs=CONFIG['epochs'],
        batch_size=CONFIG['batch_size'],
        verbose=1
    )
    
    # Evaluate on held-out test set
    print(f"\n" + "-"*70)
    print(" EVALUATION ON TEST SET")
    print("-"*70)
    
    y_pred_prob = model.predict(X_test, verbose=0)
    y_pred = (y_pred_prob > 0.5).astype(int).flatten()
    
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    print(f"\nTest Set Metrics (95 samples):")
    print(f"  - Accuracy:  {accuracy*100:.1f}%")
    print(f"  - Precision: {precision*100:.1f}%")
    print(f"  - Recall:    {recall*100:.1f}%")
    print(f"  - F1-Score:  {f1*100:.1f}%")
    
    # Confusion matrix
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    print(f"\nConfusion Matrix:")
    print(f"  - True Negatives (TN):   {tn}")
    print(f"  - False Positives (FP):  {fp}")
    print(f"  - False Negatives (FN):  {fn}")
    print(f"  - True Positives (TP):   {tp}")
    
    results = {
        'accuracy': float(accuracy),
        'precision': float(precision),
        'recall': float(recall),
        'f1': float(f1),
        'confusion_matrix': {
            'tn': int(tn),
            'fp': int(fp),
            'fn': int(fn),
            'tp': int(tp)
        },
        'test_samples': len(y_test),
        'total_parameters': int(total_params)
    }
    
    return model, history, results


def train_best_model_cv(X_train, y_train):
    """Train best model with 3-fold cross-validation"""
    print("\n" + "="*70)
    print(" CROSS-VALIDATION: 3-FOLD STRATIFIED")
    print("="*70)
    
    cv_accuracies = []
    cv_precisions = []
    cv_recalls = []
    cv_f1s = []
    fold_num = 0
    
    skf = StratifiedKFold(
        n_splits=CONFIG['cv_folds'],
        shuffle=True,
        random_state=RANDOM_STATE
    )
    
    for train_idx, val_idx in skf.split(X_train, y_train):
        fold_num += 1
        
        print(f"\n{'-'*70}")
        print(f" FOLD {fold_num}/{CONFIG['cv_folds']}")
        print(f"{'-'*70}")
        
        X_fold_train = X_train[train_idx]
        y_fold_train = y_train[train_idx]
        X_fold_val = X_train[val_idx]
        y_fold_val = y_train[val_idx]
        
        # Build fresh model for this fold
        model = build_best_mlp(X_train.shape[1])
        
        # Train
        history = model.fit(
            X_fold_train, y_fold_train,
            validation_data=(X_fold_val, y_fold_val),
            epochs=CONFIG['epochs'],
            batch_size=CONFIG['batch_size'],
            verbose=0
        )
        
        # Evaluate
        y_pred_prob = model.predict(X_fold_val, verbose=0)
        y_pred = (y_pred_prob > 0.5).astype(int).flatten()
        
        fold_accuracy = accuracy_score(y_fold_val, y_pred)
        fold_precision = precision_score(y_fold_val, y_pred)
        fold_recall = recall_score(y_fold_val, y_pred)
        fold_f1 = f1_score(y_fold_val, y_pred)
        
        cv_accuracies.append(fold_accuracy)
        cv_precisions.append(fold_precision)
        cv_recalls.append(fold_recall)
        cv_f1s.append(fold_f1)
        
        print(f"Validation Accuracy: {fold_accuracy*100:.1f}%")
        print(f"Validation Precision: {fold_precision*100:.1f}%")
        print(f"Validation Recall: {fold_recall*100:.1f}%")
        print(f"Validation F1-Score: {fold_f1*100:.1f}%")
    
    # Summary statistics
    print(f"\n" + "="*70)
    print(" CROSS-VALIDATION SUMMARY")
    print("="*70)
    
    mean_acc = np.mean(cv_accuracies)
    std_acc = np.std(cv_accuracies)
    
    print(f"\nAccuracy: {mean_acc*100:.2f}% ±{std_acc*100:.2f}%")
    print(f"Precision: {np.mean(cv_precisions)*100:.2f}% ±{np.std(cv_precisions)*100:.2f}%")
    print(f"Recall: {np.mean(cv_recalls)*100:.2f}% ±{np.std(cv_recalls)*100:.2f}%")
    print(f"F1-Score: {np.mean(cv_f1s)*100:.2f}% ±{np.std(cv_f1s)*100:.2f}%")
    
    cv_results = {
        'accuracy': {
            'mean': float(mean_acc),
            'std': float(std_acc),
            'folds': [float(x) for x in cv_accuracies]
        },
        'precision': {
            'mean': float(np.mean(cv_precisions)),
            'std': float(np.std(cv_precisions)),
            'folds': [float(x) for x in cv_precisions]
        },
        'recall': {
            'mean': float(np.mean(cv_recalls)),
            'std': float(np.std(cv_recalls)),
            'folds': [float(x) for x in cv_recalls]
        },
        'f1': {
            'mean': float(np.mean(cv_f1s)),
            'std': float(np.std(cv_f1s)),
            'folds': [float(x) for x in cv_f1s]
        }
    }
    
    return cv_results


def save_model_and_results(model, centralized_results, cv_results):
    """Save trained model and results"""
    print("\n" + "="*70)
    print(" SAVING RESULTS")
    print("="*70)
    
    # Create results directory
    results_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(results_dir, exist_ok=True)
    
    # Save model
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = os.path.join(
        os.path.dirname(__file__), 
        "models", 
        "neural_networks",
        f"best_mlp_model_{timestamp}.keras"
    )
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    model.save(model_path)
    print(f"\nModel saved: {model_path}")
    
    # Save results
    results_path = os.path.join(results_dir, f"best_model_results_{timestamp}.json")
    combined_results = {
        'timestamp': timestamp,
        'configuration': CONFIG,
        'centralized_test_results': centralized_results,
        'cross_validation_results': cv_results,
        'model_path': model_path,
        'description': 'Best MLP model from GridSearchCV (500 configurations)',
        'architecture': '128→64→32',
        'parameters': centralized_results['total_parameters']
    }
    
    with open(results_path, 'w') as f:
        json.dump(combined_results, f, indent=2)
    
    print(f"Results saved: {results_path}")
    
    print(f"\n" + "="*70)
    print(" SUMMARY")
    print("="*70)
    print(f"\nCentralized Test Accuracy: {centralized_results['accuracy']*100:.1f}%")
    print(f"Cross-Validation Accuracy: {cv_results['accuracy']['mean']*100:.2f}% ±{cv_results['accuracy']['std']*100:.2f}%")
    print(f"Model Parameters: {centralized_results['total_parameters']:,}")
    
    return model_path, results_path


def main():
    """Main execution"""
    print("\n" + "█"*70)
    print(" TRAIN BEST MLP MODEL - COMPLETE PIPELINE")
    print("█"*70)
    
    # Load data
    df = load_expanded_dataset()
    
    # Prepare TF-IDF
    X_train, X_test, y_train, y_test, vectorizer = prepare_tfidf_data(df)
    
    # Train centralized model with test evaluation
    model, history, centralized_results = train_best_model_centralized(
        X_train, X_test, y_train, y_test
    )
    
    # Train with cross-validation
    cv_results = train_best_model_cv(X_train, y_train)
    
    # Save model and results
    save_model_and_results(model, centralized_results, cv_results)
    
    print("\n" + "█"*70)
    print(" TRAINING COMPLETE")
    print("█"*70 + "\n")


if __name__ == "__main__":
    main()
