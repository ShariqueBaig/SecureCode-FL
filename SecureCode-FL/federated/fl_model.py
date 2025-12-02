"""
Federated Learning Model
========================

Neural network model compatible with Flower FL framework.
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import regularizers

from fl_config import (
    TFIDF_MAX_FEATURES, HIDDEN_LAYERS, DROPOUT_RATES,
    L2_REGULARIZATION, LEARNING_RATE
)


def create_model(input_dim=TFIDF_MAX_FEATURES):
    """
    Create the MLP model for vulnerability detection.
    
    Architecture (same as best performing MLP_v3):
    - Input: TF-IDF features
    - Hidden: 256 -> 128 -> 64 with BatchNorm, Dropout, L2
    - Output: Sigmoid for binary classification
    """
    model = keras.Sequential([
        keras.layers.Input(shape=(input_dim,)),
        
        # First hidden layer
        keras.layers.Dense(
            HIDDEN_LAYERS[0], 
            activation='relu',
            kernel_regularizer=regularizers.l2(L2_REGULARIZATION)
        ),
        keras.layers.BatchNormalization(),
        keras.layers.Dropout(DROPOUT_RATES[0]),
        
        # Second hidden layer
        keras.layers.Dense(
            HIDDEN_LAYERS[1], 
            activation='relu',
            kernel_regularizer=regularizers.l2(L2_REGULARIZATION)
        ),
        keras.layers.BatchNormalization(),
        keras.layers.Dropout(DROPOUT_RATES[1]),
        
        # Third hidden layer
        keras.layers.Dense(
            HIDDEN_LAYERS[2], 
            activation='relu',
            kernel_regularizer=regularizers.l2(L2_REGULARIZATION)
        ),
        keras.layers.Dropout(DROPOUT_RATES[2]),
        
        # Output layer
        keras.layers.Dense(1, activation='sigmoid')
    ])
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    
    return model


def get_model_weights(model):
    """Extract model weights as numpy arrays"""
    return model.get_weights()


def set_model_weights(model, weights):
    """Set model weights from numpy arrays"""
    model.set_weights(weights)
    return model


class FLModel:
    """
    Wrapper class for FL-compatible model operations.
    """
    
    def __init__(self, input_dim=TFIDF_MAX_FEATURES):
        self.input_dim = input_dim
        self.model = create_model(input_dim)
        
    def get_weights(self):
        """Get model weights for FL aggregation"""
        return self.model.get_weights()
    
    def set_weights(self, weights):
        """Set model weights from FL server"""
        self.model.set_weights(weights)
        
    def fit(self, X, y, epochs=1, batch_size=32, verbose=0):
        """Train model locally"""
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            verbose=verbose,
            validation_split=0.1
        )
        return history
    
    def evaluate(self, X, y, verbose=0):
        """Evaluate model"""
        loss, accuracy = self.model.evaluate(X, y, verbose=verbose)
        return loss, accuracy
    
    def predict(self, X):
        """Make predictions"""
        return self.model.predict(X, verbose=0)
    
    def save(self, path):
        """Save model"""
        self.model.save(path)
        
    def load(self, path):
        """Load model"""
        self.model = keras.models.load_model(path)


def fedavg_aggregate(weights_list, num_samples_list):
    """
    Federated Averaging (FedAvg) aggregation.
    
    w_global = Σ (n_k / n) * w_k
    
    where:
    - w_k = weights from client k
    - n_k = number of samples at client k
    - n = total samples across all clients
    
    Args:
        weights_list: List of weight arrays from each client
        num_samples_list: List of sample counts from each client
    
    Returns:
        Aggregated weights
    """
    total_samples = sum(num_samples_list)
    
    # Initialize aggregated weights with zeros
    aggregated_weights = [
        np.zeros_like(w) for w in weights_list[0]
    ]
    
    # Weighted average
    for client_weights, num_samples in zip(weights_list, num_samples_list):
        weight_factor = num_samples / total_samples
        for i, layer_weights in enumerate(client_weights):
            aggregated_weights[i] += weight_factor * layer_weights
    
    return aggregated_weights


if __name__ == "__main__":
    # Test model creation
    print("Creating FL Model...")
    model = create_model()
    model.summary()
    
    # Test weight operations
    print("\nTesting weight operations...")
    weights = model.get_weights()
    print(f"Number of weight arrays: {len(weights)}")
    for i, w in enumerate(weights):
        print(f"  Layer {i}: shape {w.shape}")
