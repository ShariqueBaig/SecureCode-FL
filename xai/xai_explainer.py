"""
Real-Time XAI Explainer
=======================

Provides real-time SHAP explanations for vulnerability detections.
Shows which code tokens/features caused the vulnerability alert.

This bridges the thesis (SHAP analysis) with the IDE extension (real-time feedback).
"""

import numpy as np
import shap
from typing import Dict, List, Tuple, Optional
import joblib
import os
from pathlib import Path


class VulnerabilityExplainer:
    """
    Real-time SHAP explainer for vulnerability detections.
    
    Explains:
    - Which specific code features/tokens triggered the alert
    - Feature importance for each detection
    - Top contributing tokens (for developer feedback)
    """
    
    def __init__(self, vectorizer_path: str, model=None):
        """
        Initialize the explainer.
        
        Args:
            vectorizer_path: Path to TF-IDF vectorizer (pkl file)
            model: Pre-trained Keras model for predictions
        """
        self.vectorizer = joblib.load(vectorizer_path)
        self.model = model
        self.explainer = None
        self.background_data = None
        
        # Feature names from vectorizer
        self.feature_names = self.vectorizer.get_feature_names_out()
        
        print(f"[OK] Loaded vectorizer with {len(self.feature_names)} features")
    
    def prepare_background_data(self, X: np.ndarray, num_samples: int = 100):
        """
        Prepare background data for SHAP explainer.
        
        Args:
            X: Training feature matrix
            num_samples: Number of background samples to use (for speed)
        """
        if len(X) > num_samples:
            indices = np.random.choice(len(X), num_samples, replace=False)
            self.background_data = X[indices]
        else:
            self.background_data = X
        
        print(f"[OK] Background data prepared: {self.background_data.shape}")
    
    def create_explainer(self, model_predict_fn):
        """
        Create SHAP explainer using Kernel SHAP (model-agnostic).
        
        Args:
            model_predict_fn: Function that takes X and returns predictions
        """
        if self.background_data is None:
            raise ValueError("Call prepare_background_data first")
        
        # Use Kernel SHAP for model-agnostic explanations
        self.explainer = shap.KernelExplainer(
            model_predict_fn,
            self.background_data,
            link="logit"  # For probability outputs
        )
        
        print("[OK] SHAP explainer initialized (Kernel SHAP)")
    
    def explain_prediction(
        self, 
        X: np.ndarray, 
        code_text: Optional[str] = None,
        top_k: int = 5
    ) -> Dict:
        """
        Explain a single prediction.
        
        Args:
            X: Feature vector (shape: (1, num_features))
            code_text: Original code text (optional, for context)
            top_k: Number of top features to return
        
        Returns:
            Dictionary with explanation details
        """
        if self.explainer is None:
            raise ValueError("Call create_explainer first")
        
        # Get prediction
        prediction = self.model.predict(X, verbose=0)[0][0]
        
        # Get SHAP values
        shap_values = self.explainer.shap_values(X)[0]  # First sample
        
        # Find top contributing features
        abs_shap = np.abs(shap_values)
        top_indices = np.argsort(abs_shap)[-top_k:][::-1]
        
        # Get feature names (handle dimension mismatch)
        num_features = len(self.feature_names)
        top_features = []
        for idx in top_indices:
            if idx < num_features:  # Only include actual feature names
                top_features.append({
                    'feature': self.feature_names[idx],
                    'shap_value': float(shap_values[idx]),
                    'abs_shap': float(abs_shap[idx]),
                    'contribution': 'increases risk' if shap_values[idx] > 0 else 'decreases risk'
                })
            else:  # Padding features (zeros)
                top_features.append({
                    'feature': f'padding_{idx}',
                    'shap_value': float(shap_values[idx]),
                    'abs_shap': float(abs_shap[idx]),
                    'contribution': 'increases risk' if shap_values[idx] > 0 else 'decreases risk'
                })
        
        return {
            'prediction': float(prediction),
            'is_vulnerable': prediction < 0.5,  # < 0.5 = vulnerable (0), >= 0.5 = secure (1)
            'confidence': float(prediction) if prediction >= 0.5 else float(1 - prediction),
            'top_features': top_features,
            'all_shap_values': shap_values.tolist(),
            'feature_names': self.feature_names.tolist()
        }
    
    def explain_batch(self, X: np.ndarray, top_k: int = 5) -> List[Dict]:
        """
        Explain multiple predictions.
        
        Args:
            X: Feature matrix (shape: (num_samples, num_features))
            top_k: Number of top features per sample
        
        Returns:
            List of explanation dictionaries
        """
        if self.explainer is None:
            raise ValueError("Call create_explainer first")
        
        # Get predictions
        predictions = self.model.predict(X, verbose=0).flatten()
        
        # Get SHAP values for all samples
        shap_values = self.explainer.shap_values(X)
        
        explanations = []
        for i, (pred, shap_val) in enumerate(zip(predictions, shap_values)):
            # Top features for this sample
            abs_shap = np.abs(shap_val)
            top_indices = np.argsort(abs_shap)[-top_k:][::-1]
            
            top_features = [
                {
                    'feature': self.feature_names[idx],
                    'shap_value': float(shap_val[idx]),
                    'abs_shap': float(abs_shap[idx]),
                    'contribution': 'increases risk' if shap_val[idx] > 0 else 'decreases risk'
                }
                for idx in top_indices
            ]
            
            explanations.append({
                'sample_id': i,
                'prediction': float(pred),
                'is_vulnerable': pred < 0.5,
                'confidence': float(pred) if pred >= 0.5 else float(1 - pred),
                'top_features': top_features
            })
        
        return explanations
    
    def get_feature_importance_summary(self) -> Dict[str, float]:
        """
        Get average feature importance across background data.
        
        Returns:
            Dictionary mapping features to importance scores
        """
        if self.explainer is None:
            raise ValueError("Call create_explainer first")
        
        # Calculate mean absolute SHAP values
        shap_values = self.explainer.shap_values(self.background_data)
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        
        # Sort by importance
        indices = np.argsort(mean_abs_shap)[::-1][:20]  # Top 20
        
        return {
            self.feature_names[idx]: float(mean_abs_shap[idx])
            for idx in indices
        }


# For integration with inference server
def create_explainer_from_paths(
    vectorizer_path: str,
    model_path: str
) -> VulnerabilityExplainer:
    """
    Convenience function to create explainer from file paths.
    
    Args:
        vectorizer_path: Path to TF-IDF vectorizer
        model_path: Path to Keras model
    
    Returns:
        Initialized VulnerabilityExplainer
    """
    import tensorflow as tf
    
    explainer = VulnerabilityExplainer(vectorizer_path)
    model = tf.keras.models.load_model(model_path)
    explainer.model = model
    
    return explainer
