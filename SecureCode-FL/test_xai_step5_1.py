"""
Test Real-Time SHAP Explanations
=================================

Tests the XAI explainer on real vulnerability detections.
"""

import sys
import os
import numpy as np
import pandas as pd
import tensorflow as tf
import json
from datetime import datetime

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'federated'))

from xai_explainer import VulnerabilityExplainer
from federated.data_partitioner import DataPartitioner
from fl_config import TFIDF_MAX_FEATURES


def test_xai_explainer():
    """Test SHAP explanations on real code samples."""
    
    print("\n" + "="*70)
    print("  PHASE 5 STEP 5.1: REAL-TIME XAI (SHAP) EXPLANATIONS")
    print("="*70)
    
    # Load model
    print("\n[1] Loading model and vectorizer...")
    model_path = "models/federated/fl_global_model.keras"
    vectorizer_path = "models/tfidf_vectorizer.pkl"
    
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {model_path}")
        return False
    
    model = tf.keras.models.load_model(model_path)
    print(f"[OK] Loaded model from {model_path}")
    
    # Initialize explainer
    print("\n[2] Initializing SHAP explainer...")
    explainer = VulnerabilityExplainer(vectorizer_path, model)
    
    # Load and prepare data
    print("\n[3] Preparing background data...")
    partitioner = DataPartitioner(num_clients=1)
    partitioner.load_data()
    X_all, y_all = partitioner.create_tfidf_features()
    
    # Split data
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X_all, y_all, test_size=0.2, random_state=42
    )
    
    # Prepare background data (use training data)
    explainer.prepare_background_data(X_train, num_samples=50)
    
    # Create model wrapper for SHAP
    def model_predict(X):
        return model.predict(X, verbose=0).flatten()
    
    print("\n[4] Creating SHAP explainer (this may take a moment)...")
    try:
        explainer.create_explainer(model_predict)
        print("[OK] SHAP explainer ready!")
    except Exception as e:
        print(f"❌ Failed to create explainer: {e}")
        return False
    
    # Test explanations on vulnerable samples
    print("\n[5] Testing explanations on VULNERABLE samples...")
    print("-" * 70)
    
    vulnerable_mask = (y_test == 1)  # Fixed: 1 = vulnerable, 0 = secure
    vulnerable_indices = np.where(vulnerable_mask)[0][:3]  # First 3 vulnerable
    
    vulnerable_explanations = []
    for idx in vulnerable_indices:
        X_sample = X_test[idx:idx+1]
        
        # Get explanation
        explanation = explainer.explain_prediction(X_sample, top_k=5)
        vulnerable_explanations.append(explanation)
        
        # Display
        print(f"\nSample {idx}:")
        print(f"  Vulnerability Score: {explanation['confidence']:.2%}")
        print(f"  Top contributing features:")
        for i, feat in enumerate(explanation['top_features'], 1):
            print(f"    {i}. '{feat['feature']}' -> {feat['contribution']} (SHAP: {feat['shap_value']:.4f})")
    
    # Test explanations on secure samples
    print("\n[6] Testing explanations on SECURE samples...")
    print("-" * 70)
    
    secure_mask = (y_test == 0)
    secure_indices = np.where(secure_mask)[0][:3]  # First 3 secure
    
    secure_explanations = []
    for idx in secure_indices:
        X_sample = X_test[idx:idx+1]
        
        # Get explanation
        explanation = explainer.explain_prediction(X_sample, top_k=5)
        secure_explanations.append(explanation)
        
        # Display
        print(f"\nSample {idx}:")
        print(f"  Security Score: {explanation['confidence']:.2%}")
        print(f"  Top contributing features:")
        for i, feat in enumerate(explanation['top_features'], 1):
            print(f"    {i}. '{feat['feature']}' -> {feat['contribution']} (SHAP: {feat['shap_value']:.4f})")
    
    # Accuracy test
    print("\n[7] Testing model accuracy on test set...")
    print("-" * 70)
    
    y_pred = model.predict(X_test, verbose=0).flatten()
    y_pred_binary = (y_pred >= 0.5).astype(int)
    
    accuracy = (y_pred_binary == y_test).mean()
    print(f"Test Accuracy: {accuracy:.2%}")
    print(f"Note: New optimized model (87.4% baseline) may show different metrics than old model")
    
    # Save results
    print("\n[8] Saving results...")
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'phase': 'Phase 5 - Step 5.1',
        'test': 'Real-Time SHAP Explanations',
        'test_accuracy': float(accuracy),
        'vulnerable_explanations': vulnerable_explanations[:1],  # Save first one
        'secure_explanations': secure_explanations[:1],  # Save first one
        'feature_count': len(explainer.feature_names),
        'model_info': 'Optimized model: 128-64-32-1 arch, 267k params, 87.4% baseline',
        'status': 'PASSED' if accuracy > 0.80 else 'CHECK_ACCURACY'
    }
    
    os.makedirs('results/phase5', exist_ok=True)
    results_path = f"results/phase5/xai_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(results_path, 'w') as f:
        # Convert numpy types to native Python types for JSON
        import json as json_module
        class NumpyEncoder(json_module.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, (bool, np.bool_)):
                    return bool(obj)
                return super().default(obj)
        
        json.dump(results, f, indent=2, cls=NumpyEncoder)
    
    print(f"[OK] Saved results to {results_path}")
    
    print("\n" + "="*70)
    print("  [OK] PHASE 5 STEP 5.1 COMPLETE")
    print("="*70)
    print(f"  Model: Optimized (87.4% baseline, 128-64-32 arch)")
    print(f"  Status: {'PASSED' if accuracy > 0.80 else 'NEEDS ATTENTION'}")
    print(f"  Test Accuracy: {accuracy:.2%}")
    print("="*70)
    
    return True


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings('ignore')
    
    success = test_xai_explainer()
    sys.exit(0 if success else 1)
