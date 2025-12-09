"""
Federated Learning Client with User Feedback Integration
=========================================================

This module extends the FL client to train on user feedback data.
Users mark code as:
- False Positive (secure but flagged as vulnerable)
- Missed Vulnerability (vulnerable but not detected)

Only model weights are shared, never the actual code.
"""

import os
import sys
import numpy as np
import tensorflow as tf
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from federated.fl_model import create_model, get_model_weights, set_model_weights
from federated.fl_config import TFIDF_MAX_FEATURES, LOCAL_EPOCHS, BATCH_SIZE
import joblib

# Suppress TF warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
tf.get_logger().setLevel('ERROR')


class FeedbackTrainer:
    """
    Trainer that uses user feedback to improve the model.
    
    This is a local training component that:
    1. Loads user feedback from the database
    2. Vectorizes the code snippets
    3. Trains the model locally
    4. Can participate in Federated Learning
    
    PRIVACY: User code stays LOCAL, only model weights are shared.
    """
    
    def __init__(self, model_path: Optional[str] = None, vectorizer_path: Optional[str] = None):
        """
        Initialize the feedback trainer.
        
        Args:
            model_path: Path to the model file
            vectorizer_path: Path to the TF-IDF vectorizer
        """
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Load model
        if model_path is None:
            model_path = os.path.join(base_path, "models", "federated", "fl_global_model.keras")
        
        if os.path.exists(model_path):
            self.model = tf.keras.models.load_model(model_path)
            print(f"✓ Loaded model from: {model_path}")
        else:
            # Create new model if none exists
            self.model = create_model(input_dim=TFIDF_MAX_FEATURES)
            print("⚠ Created new model (no existing model found)")
        
        # Load vectorizer
        if vectorizer_path is None:
            vectorizer_paths = [
                os.path.join(base_path, "models", "tfidf_vectorizer.pkl"),
                os.path.join(base_path, "models", "tfidf_vectorizer.joblib"),
            ]
            for path in vectorizer_paths:
                if os.path.exists(path):
                    vectorizer_path = path
                    break
        
        if vectorizer_path and os.path.exists(vectorizer_path):
            self.vectorizer = joblib.load(vectorizer_path)
            print(f"✓ Loaded vectorizer from: {vectorizer_path}")
            
            # Check if model input matches vectorizer output
            vectorizer_features = len(self.vectorizer.get_feature_names_out())
            model_input_dim = self.model.input_shape[-1]
            
            if vectorizer_features != model_input_dim:
                print(f"ℹ Dimension note: model expects {model_input_dim}, vectorizer has {vectorizer_features}")
                print(f"  Will pad features during training (fine-tuning mode)")
                # Store dimensions for padding during vectorization
                self.model_input_dim = model_input_dim
                self.vectorizer_features = vectorizer_features
            else:
                self.model_input_dim = model_input_dim
                self.vectorizer_features = vectorizer_features
        else:
            self.vectorizer = None
            print("⚠ No vectorizer found - will need to create one")
        
        self.base_path = base_path
        self.model_path = model_path
    
    def load_feedback_data(self) -> Tuple[List[str], List[int]]:
        """
        Load untrained feedback from the database.
        
        Returns:
            Tuple of (code_snippets, labels)
            Labels: 0 = vulnerable, 1 = secure
        """
        # Import here to avoid circular dependency
        sys.path.append(os.path.join(self.base_path, "inference_server"))
        from feedback import get_feedback_db
        
        db = get_feedback_db()
        untrained = db.get_untrained_feedback()
        
        if not untrained:
            print("ℹ No untrained feedback available")
            return [], []
        
        code_snippets = []
        labels = []
        
        for fb in untrained:
            code_snippets.append(fb.code_snippet)
            # 1 = vulnerable (Error), 0 = secure (Good) - matching original training format
            labels.append(1 if fb.user_label == "vulnerable" else 0)
        
        print(f"✓ Loaded {len(untrained)} feedback entries")
        print(f"  - Vulnerable: {labels.count(0)}")
        print(f"  - Secure: {labels.count(1)}")
        
        return code_snippets, labels
    
    def vectorize_code(self, code_snippets: List[str]) -> np.ndarray:
        """
        Convert code snippets to TF-IDF feature vectors.
        Pads features to match model input dimension if needed.
        
        Args:
            code_snippets: List of code strings
        
        Returns:
            Feature matrix (n_samples, n_features)
        """
        if self.vectorizer is None:
            raise ValueError("No vectorizer loaded - cannot vectorize code")
        
        features = self.vectorizer.transform(code_snippets).toarray()
        features = features.astype(np.float32)
        
        # Pad features to match model input dimension if needed
        if hasattr(self, 'model_input_dim') and features.shape[1] < self.model_input_dim:
            padding_size = self.model_input_dim - features.shape[1]
            print(f"  Padding features: {features.shape[1]} → {self.model_input_dim} (adding {padding_size} zeros)")
            features = np.pad(features, ((0, 0), (0, padding_size)), mode='constant', constant_values=0)
        
        return features
    
    def train_on_feedback(
        self, 
        epochs: int = LOCAL_EPOCHS,
        batch_size: int = BATCH_SIZE,
        save_model: bool = True
    ) -> Dict:
        """
        Train the model on user feedback.
        
        Args:
            epochs: Number of training epochs
            batch_size: Training batch size
            save_model: Whether to save the updated model
        
        Returns:
            Training metrics
        """
        # Load feedback
        code_snippets, labels = self.load_feedback_data()
        
        if not code_snippets:
            return {
                "status": "no_data",
                "message": "No feedback data available for training"
            }
        
        # Vectorize
        try:
            X = self.vectorize_code(code_snippets)
            y = np.array(labels, dtype=np.float32)
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to vectorize feedback: {e}"
            }
        
        print(f"\n🎯 Fine-tuning on {len(y)} feedback samples...")
        print(f"   Epochs: {epochs}, Batch size: {batch_size}")
        
        # Use a very low learning rate for fine-tuning to prevent catastrophic forgetting
        # This preserves the knowledge from the 471 samples while adapting to user feedback
        fine_tune_lr = 0.0001  # 10x lower than default 0.001
        
        # Recompile model with lower learning rate for fine-tuning
        self.model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=fine_tune_lr),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        print(f"   Learning rate: {fine_tune_lr} (reduced for fine-tuning)")
        
        # Train with early stopping to prevent overfitting
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2 if len(y) > 10 else 0,
            verbose=1
        )
        
        # Get final metrics
        final_loss = history.history['loss'][-1]
        final_acc = history.history['accuracy'][-1]
        
        print(f"\n✓ Training complete!")
        print(f"  Final Loss: {final_loss:.4f}")
        print(f"  Final Accuracy: {final_acc:.4f}")
        
        # Save model
        if save_model:
            # Save with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            feedback_model_dir = os.path.join(self.base_path, "models", "feedback")
            os.makedirs(feedback_model_dir, exist_ok=True)
            
            # Save timestamped version
            timestamped_path = os.path.join(feedback_model_dir, f"model_feedback_{timestamp}.keras")
            self.model.save(timestamped_path)
            print(f"✓ Saved model to: {timestamped_path}")
            
            # Also update the main model
            self.model.save(self.model_path)
            print(f"✓ Updated main model: {self.model_path}")
        
        # Mark feedback as trained
        sys.path.append(os.path.join(self.base_path, "inference_server"))
        from feedback import get_feedback_db
        
        db = get_feedback_db()
        untrained = db.get_untrained_feedback()
        feedback_ids = [fb.id for fb in untrained]
        db.mark_as_trained(feedback_ids)
        
        return {
            "status": "success",
            "samples_trained": len(y),
            "final_loss": final_loss,
            "final_accuracy": final_acc,
            "epochs": epochs,
            "model_saved": save_model
        }
    
    def get_weights(self) -> List[np.ndarray]:
        """Get current model weights for FL."""
        return get_model_weights(self.model)
    
    def set_weights(self, weights: List[np.ndarray]):
        """Set model weights (received from FL server)."""
        set_model_weights(self.model, weights)


def create_feedback_fl_client(trainer: FeedbackTrainer):
    """
    Create a Flower FL client from the feedback trainer.
    
    This allows the feedback-trained model to participate in
    Federated Learning with other clients.
    """
    import flwr as fl
    
    class FeedbackFLClient(fl.client.NumPyClient):
        def __init__(self, trainer: FeedbackTrainer):
            self.trainer = trainer
        
        def get_parameters(self, config):
            return self.trainer.get_weights()
        
        def fit(self, parameters, config):
            # Set global weights
            self.trainer.set_weights(parameters)
            
            # Train on local feedback
            result = self.trainer.train_on_feedback(
                epochs=config.get("local_epochs", LOCAL_EPOCHS),
                save_model=False  # Don't save during FL
            )
            
            num_samples = result.get("samples_trained", 0)
            
            return (
                self.trainer.get_weights(),
                num_samples,
                {
                    "loss": result.get("final_loss", 0),
                    "accuracy": result.get("final_accuracy", 0)
                }
            )
        
        def evaluate(self, parameters, config):
            self.trainer.set_weights(parameters)
            
            # Load feedback for evaluation
            code_snippets, labels = self.trainer.load_feedback_data()
            
            if not code_snippets:
                return 0.0, 0, {"accuracy": 0.0}
            
            X = self.trainer.vectorize_code(code_snippets)
            y = np.array(labels, dtype=np.float32)
            
            loss, accuracy = self.trainer.model.evaluate(X, y, verbose=0)
            
            return loss, len(y), {"accuracy": accuracy}
    
    return FeedbackFLClient(trainer)


def run_local_training():
    """Run local training on user feedback (standalone mode)."""
    print("=" * 60)
    print("  SecureCode-FL: Training on User Feedback")
    print("=" * 60)
    
    trainer = FeedbackTrainer()
    result = trainer.train_on_feedback()
    
    print("\n" + "=" * 60)
    print("  Training Result:")
    print(f"  Status: {result['status']}")
    if result['status'] == 'success':
        print(f"  Samples: {result['samples_trained']}")
        print(f"  Accuracy: {result['final_accuracy']:.4f}")
    elif result['status'] == 'no_data':
        print(f"  Message: {result['message']}")
    print("=" * 60)
    
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Train on user feedback")
    parser.add_argument("--mode", choices=["local", "fl"], default="local",
                        help="Training mode: local or federated learning")
    parser.add_argument("--server", default="localhost:8080",
                        help="FL server address (for fl mode)")
    args = parser.parse_args()
    
    if args.mode == "local":
        run_local_training()
    else:
        # FL mode - connect to server
        import flwr as fl
        
        print("=" * 60)
        print("  SecureCode-FL: Connecting to FL Server")
        print(f"  Server: {args.server}")
        print("=" * 60)
        
        trainer = FeedbackTrainer()
        client = create_feedback_fl_client(trainer)
        
        fl.client.start_client(
            server_address=args.server,
            client=client.to_client()
        )
