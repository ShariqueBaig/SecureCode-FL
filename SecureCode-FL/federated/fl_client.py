"""
Flower FL Client
================

Client implementation for Federated Learning using Flower framework.
Each client represents an organization training on their private code.
"""

import flwr as fl
import numpy as np
import tensorflow as tf
from typing import Dict, List, Tuple

from fl_model import create_model, get_model_weights, set_model_weights
from fl_config import LOCAL_EPOCHS, BATCH_SIZE, TFIDF_MAX_FEATURES

# Suppress TF warnings
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
tf.get_logger().setLevel('ERROR')


class VulnerabilityDetectionClient(fl.client.NumPyClient):
    """
    Flower client for vulnerability detection.
    
    Each client:
    1. Receives global model weights from server
    2. Trains locally on private code data
    3. Sends updated weights back (NOT the code!)
    """
    
    def __init__(self, client_id: int, X_train: np.ndarray, y_train: np.ndarray):
        """
        Initialize client with local data.
        
        Args:
            client_id: Unique identifier for this client
            X_train: TF-IDF features of local code samples
            y_train: Labels (0=vulnerable, 1=secure)
        """
        self.client_id = client_id
        self.X_train = X_train
        self.y_train = y_train
        self.model = create_model(input_dim=X_train.shape[1])
        
        print(f"[Client {client_id}] Initialized with {len(y_train)} samples")
        print(f"  - Vulnerable: {(y_train == 0).sum()}")
        print(f"  - Secure: {(y_train == 1).sum()}")
    
    def get_parameters(self, config: Dict) -> List[np.ndarray]:
        """Return current model weights."""
        return get_model_weights(self.model)
    
    def set_parameters(self, parameters: List[np.ndarray]) -> None:
        """Set model weights from server."""
        set_model_weights(self.model, parameters)
    
    def fit(
        self, 
        parameters: List[np.ndarray], 
        config: Dict
    ) -> Tuple[List[np.ndarray], int, Dict]:
        """
        Train model on local data.
        
        This is where the magic happens:
        - Code stays LOCAL (never leaves the client)
        - Only model WEIGHTS are shared
        
        Args:
            parameters: Global model weights from server
            config: Training configuration
        
        Returns:
            Updated weights, number of samples, metrics
        """
        # Set the global model weights
        self.set_parameters(parameters)
        
        # Get training config
        epochs = config.get("local_epochs", LOCAL_EPOCHS)
        batch_size = config.get("batch_size", BATCH_SIZE)
        
        # Train locally
        history = self.model.fit(
            self.X_train, 
            self.y_train,
            epochs=epochs,
            batch_size=batch_size,
            verbose=0,
            validation_split=0.1
        )
        
        # Get final training metrics
        train_loss = history.history['loss'][-1]
        train_acc = history.history['accuracy'][-1]
        
        print(f"[Client {self.client_id}] Training complete - "
              f"Loss: {train_loss:.4f}, Acc: {train_acc:.4f}")
        
        # Return updated weights (NOT the code!)
        return (
            self.get_parameters(config={}),
            len(self.X_train),
            {"loss": train_loss, "accuracy": train_acc}
        )
    
    def evaluate(
        self, 
        parameters: List[np.ndarray], 
        config: Dict
    ) -> Tuple[float, int, Dict]:
        """
        Evaluate model on local data.
        
        Args:
            parameters: Model weights to evaluate
            config: Evaluation configuration
        
        Returns:
            Loss, number of samples, metrics
        """
        self.set_parameters(parameters)
        
        loss, accuracy = self.model.evaluate(
            self.X_train, 
            self.y_train, 
            verbose=0
        )
        
        print(f"[Client {self.client_id}] Evaluation - "
              f"Loss: {loss:.4f}, Acc: {accuracy:.4f}")
        
        return loss, len(self.X_train), {"accuracy": accuracy}


def create_client(client_id: int, client_data: Dict) -> VulnerabilityDetectionClient:
    """
    Factory function to create a FL client.
    
    Args:
        client_id: Client identifier
        client_data: Dictionary with X_train, y_train
    
    Returns:
        Configured VulnerabilityDetectionClient
    """
    return VulnerabilityDetectionClient(
        client_id=client_id,
        X_train=client_data['X_train'],
        y_train=client_data['y_train']
    )


def client_fn(cid: str, client_data_map: Dict) -> fl.client.Client:
    """
    Client function for Flower simulation.
    
    Args:
        cid: Client ID as string
        client_data_map: Mapping of client_id -> client_data
    
    Returns:
        Flower client
    """
    client_id = int(cid)
    client_data = client_data_map[client_id]
    
    return VulnerabilityDetectionClient(
        client_id=client_id,
        X_train=client_data['X_train'],
        y_train=client_data['y_train']
    ).to_client()


if __name__ == "__main__":
    # Test client creation
    print("Testing FL Client...")
    
    # Create dummy data
    X_dummy = np.random.rand(100, TFIDF_MAX_FEATURES).astype(np.float32)
    y_dummy = np.random.randint(0, 2, 100).astype(np.float32)
    
    client = VulnerabilityDetectionClient(
        client_id=0,
        X_train=X_dummy,
        y_train=y_dummy
    )
    
    # Test methods
    weights = client.get_parameters(config={})
    print(f"\nWeight shapes: {[w.shape for w in weights[:3]]}...")
    
    print("\nClient test complete!")
