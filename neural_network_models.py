"""
Phase 2: Neural Network Models for Federated Learning
=====================================================

This module implements neural network architectures that are compatible with
Federated Learning (unlike tree-based models which cannot be averaged).

Why Neural Networks for FL?
- Tree-based models (Random Forest, XGBoost) cannot be mathematically averaged
- FL requires gradient-based models where weights can be aggregated
- FedAvg algorithm: w_global = Σ (n_k / n) * w_k

Architectures Implemented:
1. MLP (Multi-Layer Perceptron) - Simple, fast, works with TF-IDF
2. LSTM - Sequential model for code tokens
3. CNN - 1D Convolution for pattern detection
"""

import numpy as np
import pandas as pd
import os
import warnings
warnings.filterwarnings('ignore')

# TensorFlow/Keras imports
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import (
    Dense, Dropout, LSTM, Embedding, Conv1D, 
    MaxPooling1D, Flatten, Input, GlobalMaxPooling1D,
    Bidirectional, BatchNormalization
)
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

from config import MODELS_DIR, RESULTS_DIR, RANDOM_STATE

# Set random seeds for reproducibility
np.random.seed(RANDOM_STATE)
tf.random.set_seed(RANDOM_STATE)


class NeuralNetworkModels:
    """
    Neural Network models for vulnerability detection.
    These models are FL-compatible (gradient-based).
    """
    
    def __init__(self):
        self.models = {}
        self.histories = {}
        self.results = {}
        self.tokenizer = None
        
    # =========================================================
    # ARCHITECTURE A: Multi-Layer Perceptron (MLP)
    # =========================================================
    def build_mlp(self, input_dim, name="MLP"):
        """
        Simple MLP that works with TF-IDF features.
        Fast training, good baseline for FL.
        """
        model = Sequential([
            Input(shape=(input_dim,)),
            Dense(256, activation='relu'),
            BatchNormalization(),
            Dropout(0.3),
            Dense(128, activation='relu'),
            BatchNormalization(),
            Dropout(0.3),
            Dense(64, activation='relu'),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dense(1, activation='sigmoid')
        ], name=name)
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def build_mlp_small(self, input_dim, name="MLP_Small"):
        """
        Smaller MLP for edge deployment.
        Target: < 5MB model size.
        """
        model = Sequential([
            Input(shape=(input_dim,)),
            Dense(128, activation='relu'),
            Dropout(0.3),
            Dense(64, activation='relu'),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dense(1, activation='sigmoid')
        ], name=name)
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    # =========================================================
    # ARCHITECTURE B: LSTM (Long Short-Term Memory)
    # =========================================================
    def build_lstm(self, vocab_size, max_length, embedding_dim=128, name="LSTM"):
        """
        LSTM for sequential code analysis.
        Works with tokenized code sequences.
        """
        model = Sequential([
            Embedding(vocab_size, embedding_dim, input_length=max_length),
            LSTM(64, return_sequences=True),
            Dropout(0.3),
            LSTM(32),
            Dropout(0.3),
            Dense(32, activation='relu'),
            Dense(1, activation='sigmoid')
        ], name=name)
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def build_bilstm(self, vocab_size, max_length, embedding_dim=128, name="BiLSTM"):
        """
        Bidirectional LSTM for better context understanding.
        """
        model = Sequential([
            Embedding(vocab_size, embedding_dim, input_length=max_length),
            Bidirectional(LSTM(64, return_sequences=True)),
            Dropout(0.3),
            Bidirectional(LSTM(32)),
            Dropout(0.3),
            Dense(32, activation='relu'),
            Dense(1, activation='sigmoid')
        ], name=name)
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    # =========================================================
    # ARCHITECTURE C: 1D CNN
    # =========================================================
    def build_cnn(self, vocab_size, max_length, embedding_dim=128, name="CNN"):
        """
        1D CNN for pattern detection in code.
        Fast inference, good for edge deployment.
        """
        model = Sequential([
            Embedding(vocab_size, embedding_dim, input_length=max_length),
            Conv1D(64, 3, activation='relu', padding='same'),
            MaxPooling1D(2),
            Conv1D(32, 3, activation='relu', padding='same'),
            MaxPooling1D(2),
            Conv1D(16, 3, activation='relu', padding='same'),
            GlobalMaxPooling1D(),
            Dense(64, activation='relu'),
            Dropout(0.3),
            Dense(32, activation='relu'),
            Dense(1, activation='sigmoid')
        ], name=name)
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    # =========================================================
    # TRAINING METHODS
    # =========================================================
    def train_model(self, model, X_train, y_train, X_val, y_val, 
                    epochs=100, batch_size=8, verbose=1):
        """
        Train a neural network model with early stopping.
        """
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=15,
                restore_best_weights=True,
                verbose=1
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-6,
                verbose=1
            )
        ]
        
        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=verbose
        )
        
        return history
    
    def cross_validate_model(self, build_fn, X, y, n_splits=5, 
                             epochs=100, batch_size=8, **build_kwargs):
        """
        Perform cross-validation for neural network.
        """
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
        
        fold_results = []
        
        for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
            print(f"\n--- Fold {fold + 1}/{n_splits} ---")
            
            # Split data
            if hasattr(X, 'toarray'):
                X_train, X_val = X[train_idx].toarray(), X[val_idx].toarray()
            else:
                X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            
            # Build fresh model for each fold
            model = build_fn(**build_kwargs)
            
            # Train
            history = self.train_model(
                model, X_train, y_train, X_val, y_val,
                epochs=epochs, batch_size=batch_size, verbose=0
            )
            
            # Evaluate
            y_pred_prob = model.predict(X_val, verbose=0)
            y_pred = (y_pred_prob > 0.5).astype(int).flatten()
            
            accuracy = accuracy_score(y_val, y_pred)
            fold_results.append({
                'fold': fold + 1,
                'accuracy': accuracy,
                'history': history.history
            })
            
            print(f"Fold {fold + 1} Accuracy: {accuracy*100:.1f}%")
        
        # Summary
        accuracies = [r['accuracy'] for r in fold_results]
        mean_acc = np.mean(accuracies)
        std_acc = np.std(accuracies)
        
        print(f"\nCross-Validation Results:")
        print(f"Mean Accuracy: {mean_acc*100:.1f}% (±{std_acc*100:.1f}%)")
        
        return {
            'fold_results': fold_results,
            'mean_accuracy': mean_acc,
            'std_accuracy': std_acc,
            'all_accuracies': accuracies
        }
    
    # =========================================================
    # TOKENIZATION FOR SEQUENCE MODELS
    # =========================================================
    def prepare_sequences(self, texts, max_words=5000, max_length=200):
        """
        Prepare token sequences for LSTM/CNN models.
        """
        self.tokenizer = Tokenizer(num_words=max_words, oov_token='<OOV>')
        self.tokenizer.fit_on_texts(texts)
        
        sequences = self.tokenizer.texts_to_sequences(texts)
        padded = pad_sequences(sequences, maxlen=max_length, padding='post', truncating='post')
        
        vocab_size = min(len(self.tokenizer.word_index) + 1, max_words)
        
        return padded, vocab_size, max_length
    
    # =========================================================
    # MODEL SAVING
    # =========================================================
    def save_model(self, model, name, save_dir=None):
        """
        Save model in multiple formats for deployment.
        """
        if save_dir is None:
            save_dir = os.path.join(MODELS_DIR, 'neural_networks')
        os.makedirs(save_dir, exist_ok=True)
        
        # Save Keras format
        keras_path = os.path.join(save_dir, f'{name}.keras')
        model.save(keras_path)
        print(f"Saved: {keras_path}")
        
        # Save weights only (Keras 3 requires .weights.h5 extension)
        weights_path = os.path.join(save_dir, f'{name}.weights.h5')
        model.save_weights(weights_path)
        print(f"Saved: {weights_path}")
        
        # Get model size
        size_mb = os.path.getsize(keras_path) / (1024 * 1024)
        print(f"Model size: {size_mb:.2f} MB")
        
        return keras_path, size_mb
    
    def get_model_summary(self, model):
        """
        Get model summary with parameter count.
        """
        trainable = np.sum([np.prod(v.shape) for v in model.trainable_weights])
        non_trainable = np.sum([np.prod(v.shape) for v in model.non_trainable_weights])
        
        return {
            'total_params': trainable + non_trainable,
            'trainable_params': trainable,
            'non_trainable_params': non_trainable
        }


def main():
    """
    Main function to train and evaluate all neural network architectures.
    """
    from data_preprocessing import DataPreprocessor
    from scipy.sparse import vstack
    
    print("=" * 70)
    print(" PHASE 2: NEURAL NETWORK CONVERSION FOR FEDERATED LEARNING")
    print("=" * 70)
    
    # =========================================================
    # LOAD DATA
    # =========================================================
    print("\n[1] Loading and preprocessing data...")
    preprocessor = DataPreprocessor()
    X_train, X_test, y_train, y_test, vectorizer, feature_names = preprocessor.prepare_data()
    
    # Combine for full cross-validation
    X_full = vstack([X_train, X_test])
    y_full = np.concatenate([y_train, y_test])
    
    # Convert to dense for neural networks
    X_dense = X_full.toarray()
    
    print(f"\nDataset: {X_dense.shape[0]} samples, {X_dense.shape[1]} features")
    
    # =========================================================
    # INITIALIZE NEURAL NETWORK TRAINER
    # =========================================================
    nn_trainer = NeuralNetworkModels()
    results = {}
    
    # =========================================================
    # ARCHITECTURE A: MLP (with TF-IDF features)
    # =========================================================
    print("\n" + "=" * 70)
    print(" ARCHITECTURE A: Multi-Layer Perceptron (MLP)")
    print("=" * 70)
    
    # MLP with TF-IDF input
    print("\n[A1] Training MLP (Full)...")
    mlp_results = nn_trainer.cross_validate_model(
        build_fn=nn_trainer.build_mlp,
        X=X_dense, y=y_full,
        n_splits=5, epochs=100, batch_size=8,
        input_dim=X_dense.shape[1], name="MLP_Full"
    )
    results['MLP'] = mlp_results
    
    # MLP Small (for edge deployment)
    print("\n[A2] Training MLP Small (Edge-optimized)...")
    mlp_small_results = nn_trainer.cross_validate_model(
        build_fn=nn_trainer.build_mlp_small,
        X=X_dense, y=y_full,
        n_splits=5, epochs=100, batch_size=8,
        input_dim=X_dense.shape[1], name="MLP_Small"
    )
    results['MLP_Small'] = mlp_small_results
    
    # =========================================================
    # ARCHITECTURE B & C: LSTM and CNN (with token sequences)
    # =========================================================
    print("\n" + "=" * 70)
    print(" PREPARING SEQUENCES FOR LSTM/CNN")
    print("=" * 70)
    
    # Get original code text
    codes = preprocessor.df['processed_code'].values
    
    # Prepare sequences
    X_seq, vocab_size, max_length = nn_trainer.prepare_sequences(
        codes, max_words=3000, max_length=150
    )
    
    print(f"Vocabulary size: {vocab_size}")
    print(f"Sequence length: {max_length}")
    
    # =========================================================
    # ARCHITECTURE B: LSTM
    # =========================================================
    print("\n" + "=" * 70)
    print(" ARCHITECTURE B: LSTM")
    print("=" * 70)
    
    print("\n[B1] Training LSTM...")
    lstm_results = nn_trainer.cross_validate_model(
        build_fn=nn_trainer.build_lstm,
        X=X_seq, y=y_full,
        n_splits=5, epochs=100, batch_size=8,
        vocab_size=vocab_size, max_length=max_length, name="LSTM"
    )
    results['LSTM'] = lstm_results
    
    print("\n[B2] Training Bidirectional LSTM...")
    bilstm_results = nn_trainer.cross_validate_model(
        build_fn=nn_trainer.build_bilstm,
        X=X_seq, y=y_full,
        n_splits=5, epochs=100, batch_size=8,
        vocab_size=vocab_size, max_length=max_length, name="BiLSTM"
    )
    results['BiLSTM'] = bilstm_results
    
    # =========================================================
    # ARCHITECTURE C: CNN
    # =========================================================
    print("\n" + "=" * 70)
    print(" ARCHITECTURE C: 1D CNN")
    print("=" * 70)
    
    print("\n[C1] Training CNN...")
    cnn_results = nn_trainer.cross_validate_model(
        build_fn=nn_trainer.build_cnn,
        X=X_seq, y=y_full,
        n_splits=5, epochs=100, batch_size=8,
        vocab_size=vocab_size, max_length=max_length, name="CNN"
    )
    results['CNN'] = cnn_results
    
    # =========================================================
    # SUMMARY
    # =========================================================
    print("\n" + "=" * 70)
    print(" NEURAL NETWORK RESULTS SUMMARY")
    print("=" * 70)
    
    summary_data = []
    for name, res in results.items():
        summary_data.append({
            'Model': name,
            'Mean Accuracy': f"{res['mean_accuracy']*100:.1f}%",
            'Std': f"±{res['std_accuracy']*100:.1f}%",
            'Fold Scores': [f"{a*100:.0f}%" for a in res['all_accuracies']]
        })
    
    summary_df = pd.DataFrame(summary_data)
    print("\n" + summary_df.to_string(index=False))
    
    # Find best model
    best_name = max(results.keys(), key=lambda k: results[k]['mean_accuracy'])
    best_acc = results[best_name]['mean_accuracy']
    
    print(f"\n★ Best Neural Network: {best_name} with {best_acc*100:.1f}% accuracy")
    
    # Compare with tree-based baseline
    print("\n" + "-" * 40)
    print("COMPARISON WITH BASELINE:")
    print("-" * 40)
    print(f"Tree-based Baseline (Gradient Boosting): 76.7%")
    print(f"Best Neural Network ({best_name}): {best_acc*100:.1f}%")
    print(f"Thesis Target (Extra Trees): 83.3%")
    
    # =========================================================
    # TRAIN FINAL MODEL ON FULL DATA
    # =========================================================
    print("\n" + "=" * 70)
    print(" TRAINING FINAL MODEL ON FULL DATASET")
    print("=" * 70)
    
    # Train best MLP on full data
    final_model = nn_trainer.build_mlp(input_dim=X_dense.shape[1], name="MLP_Final")
    
    # Use 10% for validation
    from sklearn.model_selection import train_test_split
    X_tr, X_vl, y_tr, y_vl = train_test_split(
        X_dense, y_full, test_size=0.1, random_state=RANDOM_STATE, stratify=y_full
    )
    
    history = nn_trainer.train_model(
        final_model, X_tr, y_tr, X_vl, y_vl,
        epochs=100, batch_size=8, verbose=1
    )
    
    # Save the final model
    print("\n[Saving Final Model]")
    model_path, model_size = nn_trainer.save_model(final_model, "mlp_vulnerability_detector")
    
    # Save tokenizer for sequence models
    tokenizer_path = os.path.join(MODELS_DIR, 'neural_networks', 'tokenizer.pkl')
    joblib.dump(nn_trainer.tokenizer, tokenizer_path)
    print(f"Saved: {tokenizer_path}")
    
    # Save results
    os.makedirs(RESULTS_DIR, exist_ok=True)
    results_path = os.path.join(RESULTS_DIR, 'neural_network_results.csv')
    summary_df.to_csv(results_path, index=False)
    print(f"Saved: {results_path}")
    
    print("\n" + "=" * 70)
    print(" PHASE 2 COMPLETE")
    print("=" * 70)
    print(f"""
Summary:
- Trained 5 neural network architectures
- Best Model: {best_name} ({best_acc*100:.1f}%)
- Model Size: {model_size:.2f} MB
- FL Compatible: YES (gradient-based)

Next: Phase 3 - Federated Learning Implementation
""")
    
    return results, final_model, nn_trainer


if __name__ == "__main__":
    results, final_model, trainer = main()
