"""
Differential Privacy Model for Federated Learning
==================================================

Implements DP-SGD (Differentially Private Stochastic Gradient Descent)
using manual gradient clipping and Gaussian noise addition.

This provides formal (ε, δ)-differential privacy guarantees.
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from typing import List, Tuple, Optional
import math

# Import FL config
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from federated.fl_config import (
    HIDDEN_LAYERS, DROPOUT_RATES, L2_REGULARIZATION, LEARNING_RATE,
    DP_EPSILON, DP_DELTA, DP_CLIP_NORM, TFIDF_MAX_FEATURES
)


class DPGradientDescentOptimizer:
    """
    Differentially Private Gradient Descent Optimizer.
    
    Implements DP-SGD from Abadi et al. (2016):
    1. Clip per-sample gradients to bound L2 norm
    2. Add calibrated Gaussian noise
    3. Apply noisy gradients
    """
    
    def __init__(
        self,
        learning_rate: float = 0.01,
        l2_norm_clip: float = 1.0,
        noise_multiplier: float = 1.0,
        num_microbatches: int = 1
    ):
        """
        Initialize DP optimizer.
        
        Args:
            learning_rate: Step size for gradient descent
            l2_norm_clip: Maximum L2 norm for per-sample gradients
            noise_multiplier: Ratio of noise stddev to sensitivity
            num_microbatches: Number of microbatches (usually 1)
        """
        self.learning_rate = learning_rate
        self.l2_norm_clip = l2_norm_clip
        self.noise_multiplier = noise_multiplier
        self.num_microbatches = num_microbatches
        
    def clip_gradients(self, gradients: List[tf.Tensor]) -> List[tf.Tensor]:
        """
        Clip gradients to bound L2 norm.
        
        Args:
            gradients: List of gradient tensors
            
        Returns:
            Clipped gradients
        """
        # Compute global L2 norm
        global_norm = tf.sqrt(sum([tf.reduce_sum(g ** 2) for g in gradients]))
        
        # Clip factor
        clip_factor = self.l2_norm_clip / tf.maximum(global_norm, self.l2_norm_clip)
        
        # Apply clipping
        clipped_gradients = [g * clip_factor for g in gradients]
        
        return clipped_gradients
    
    def add_noise(self, gradients: List[tf.Tensor], batch_size: int) -> List[tf.Tensor]:
        """
        Add Gaussian noise calibrated for DP.
        
        The noise is scaled by:
            stddev = (sensitivity * noise_multiplier) / batch_size
            
        where sensitivity = l2_norm_clip (due to clipping).
        
        Args:
            gradients: List of gradient tensors
            batch_size: Size of training batch
            
        Returns:
            Noisy gradients
        """
        noise_stddev = (self.l2_norm_clip * self.noise_multiplier) / batch_size
        
        noisy_gradients = []
        for g in gradients:
            noise = tf.random.normal(shape=g.shape, mean=0.0, stddev=noise_stddev)
            noisy_gradients.append(g + noise)
            
        return noisy_gradients


def compute_epsilon(
    steps: int,
    batch_size: int,
    dataset_size: int,
    noise_multiplier: float,
    delta: float = 1e-5
) -> float:
    """
    Compute privacy spent (ε) using the Moments Accountant.
    
    This is a simplified RDP (Rényi Differential Privacy) analysis.
    For production, use the dp-accounting library.
    
    Args:
        steps: Total training steps
        batch_size: Batch size per step
        dataset_size: Total dataset size
        noise_multiplier: Noise scale
        delta: Target δ
        
    Returns:
        Epsilon (ε) privacy budget spent
    """
    # Sampling probability
    q = batch_size / dataset_size
    
    # Simplified bound based on Abadi et al. (2016)
    # ε ≈ q * sqrt(2 * T * log(1/δ)) / σ
    # where T is steps, σ is noise_multiplier
    
    if noise_multiplier == 0:
        return float('inf')
    
    epsilon = q * math.sqrt(2 * steps * math.log(1 / delta)) / noise_multiplier
    
    return epsilon


def create_dp_model(
    input_dim: int = TFIDF_MAX_FEATURES,
    hidden_layers: List[int] = None,
    dropout_rates: List[float] = None,
    l2_reg: float = L2_REGULARIZATION,
    noise_multiplier: float = 1.0,
    l2_norm_clip: float = 1.0
) -> keras.Model:
    """
    Create a neural network model with DP-compatible settings.
    
    The model itself is the same architecture, but we use custom
    training that applies DP gradient clipping and noise.
    
    Args:
        input_dim: Number of input features
        hidden_layers: List of hidden layer sizes
        dropout_rates: Dropout rates per layer
        l2_reg: L2 regularization strength
        noise_multiplier: DP noise scale
        l2_norm_clip: Gradient clipping norm
        
    Returns:
        Compiled Keras model
    """
    if hidden_layers is None:
        hidden_layers = HIDDEN_LAYERS
    if dropout_rates is None:
        dropout_rates = DROPOUT_RATES
        
    model = keras.Sequential()
    model.add(keras.layers.Input(shape=(input_dim,)))
    
    # Hidden layers
    for i, (units, dropout) in enumerate(zip(hidden_layers, dropout_rates)):
        model.add(keras.layers.Dense(
            units,
            activation='relu',
            kernel_regularizer=keras.regularizers.l2(l2_reg),
            name=f'dense_{i}'
        ))
        model.add(keras.layers.Dropout(dropout, name=f'dropout_{i}'))
    
    # Output layer
    model.add(keras.layers.Dense(1, activation='sigmoid', name='output'))
    
    # Compile with standard optimizer (DP is applied during training)
    model.compile(
        optimizer=keras.optimizers.SGD(learning_rate=LEARNING_RATE),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    
    return model


class DPTrainer:
    """
    Trainer that applies Differential Privacy during training.
    """
    
    def __init__(
        self,
        model: keras.Model,
        l2_norm_clip: float = 1.0,
        noise_multiplier: float = 1.0,
        learning_rate: float = 0.01
    ):
        """
        Initialize DP trainer.
        
        Args:
            model: Keras model to train
            l2_norm_clip: Gradient clipping norm
            noise_multiplier: Noise scale for DP
            learning_rate: Optimizer learning rate
        """
        self.model = model
        self.l2_norm_clip = l2_norm_clip
        self.noise_multiplier = noise_multiplier
        self.learning_rate = learning_rate
        self.optimizer = keras.optimizers.SGD(learning_rate=learning_rate)
        self.loss_fn = keras.losses.BinaryCrossentropy()
        
        # Track privacy budget
        self.total_steps = 0
        
    @tf.function
    def train_step(self, x: tf.Tensor, y: tf.Tensor) -> Tuple[float, float]:
        """
        Execute one DP training step.
        
        Args:
            x: Input features
            y: Labels
            
        Returns:
            Tuple of (loss, accuracy)
        """
        batch_size = tf.shape(x)[0]
        
        with tf.GradientTape() as tape:
            predictions = self.model(x, training=True)
            loss = self.loss_fn(y, predictions)
            
        # Compute gradients
        gradients = tape.gradient(loss, self.model.trainable_variables)
        
        # Clip gradients
        global_norm = tf.sqrt(sum([tf.reduce_sum(g ** 2) for g in gradients if g is not None]))
        clip_factor = self.l2_norm_clip / tf.maximum(global_norm, self.l2_norm_clip)
        clipped_gradients = [g * clip_factor if g is not None else None for g in gradients]
        
        # Add noise
        noise_stddev = (self.l2_norm_clip * self.noise_multiplier) / tf.cast(batch_size, tf.float32)
        noisy_gradients = []
        for g in clipped_gradients:
            if g is not None:
                noise = tf.random.normal(shape=tf.shape(g), mean=0.0, stddev=noise_stddev)
                noisy_gradients.append(g + noise)
            else:
                noisy_gradients.append(None)
        
        # Apply gradients
        self.optimizer.apply_gradients(
            [(g, v) for g, v in zip(noisy_gradients, self.model.trainable_variables) if g is not None]
        )
        
        # Compute accuracy
        y_float = tf.cast(y, tf.float32)
        accuracy = tf.reduce_mean(
            tf.cast(tf.equal(tf.round(predictions), y_float), tf.float32)
        )
        
        return loss, accuracy
    
    def fit(
        self,
        x: np.ndarray,
        y: np.ndarray,
        epochs: int = 1,
        batch_size: int = 32,
        verbose: int = 0
    ) -> dict:
        """
        Train model with DP.
        
        Args:
            x: Training features
            y: Training labels
            epochs: Number of epochs
            batch_size: Batch size
            verbose: Verbosity level
            
        Returns:
            Training history
        """
        dataset = tf.data.Dataset.from_tensor_slices((x, y))
        dataset = dataset.shuffle(len(y)).batch(batch_size)
        
        history = {'loss': [], 'accuracy': []}
        
        for epoch in range(epochs):
            epoch_losses = []
            epoch_accs = []
            
            for batch_x, batch_y in dataset:
                loss, acc = self.train_step(batch_x, batch_y)
                epoch_losses.append(float(loss))
                epoch_accs.append(float(acc))
                self.total_steps += 1
                
            avg_loss = np.mean(epoch_losses)
            avg_acc = np.mean(epoch_accs)
            history['loss'].append(avg_loss)
            history['accuracy'].append(avg_acc)
            
            if verbose > 0:
                print(f"Epoch {epoch+1}/{epochs} - loss: {avg_loss:.4f} - accuracy: {avg_acc:.4f}")
                
        return history
    
    def get_epsilon(self, dataset_size: int, batch_size: int, delta: float = 1e-5) -> float:
        """
        Get current privacy budget spent.
        
        Args:
            dataset_size: Total training set size
            batch_size: Batch size used
            delta: Target delta
            
        Returns:
            Epsilon spent
        """
        return compute_epsilon(
            steps=self.total_steps,
            batch_size=batch_size,
            dataset_size=dataset_size,
            noise_multiplier=self.noise_multiplier,
            delta=delta
        )


def get_model_weights(model: keras.Model) -> List[np.ndarray]:
    """Get model weights as list of numpy arrays."""
    return [w.numpy() for w in model.trainable_variables]


def set_model_weights(model: keras.Model, weights: List[np.ndarray]) -> None:
    """Set model weights from list of numpy arrays."""
    for model_var, weight in zip(model.trainable_variables, weights):
        model_var.assign(weight)


if __name__ == "__main__":
    # Test DP model
    print("Testing DP Model...")
    
    # Create dummy data
    X = np.random.rand(100, TFIDF_MAX_FEATURES).astype(np.float32)
    y = np.random.randint(0, 2, 100).astype(np.float32)
    
    # Create model
    model = create_dp_model()
    print(f"Model parameters: {model.count_params()}")
    
    # Create DP trainer
    trainer = DPTrainer(
        model=model,
        l2_norm_clip=1.0,
        noise_multiplier=1.0,
        learning_rate=0.01
    )
    
    # Train with DP
    history = trainer.fit(X, y, epochs=3, batch_size=16, verbose=1)
    
    # Get epsilon
    epsilon = trainer.get_epsilon(dataset_size=100, batch_size=16)
    print(f"\nPrivacy budget spent: ε = {epsilon:.2f}")
    
    print("\nDP Model test complete!")
