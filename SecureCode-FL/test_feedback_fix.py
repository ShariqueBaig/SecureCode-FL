"""Test script to verify the feedback training fix"""
import tensorflow as tf
import joblib
import numpy as np

# Load model and vectorizer
model = tf.keras.models.load_model('models/federated/fl_global_model.keras')
vectorizer = joblib.load('models/tfidf_vectorizer.pkl')

# Test cases
test_cases = [
    ("password = 'super_secret_123'", "Hardcoded password", "should be VULNERABLE"),
    ("password = os.environ.get('DB_PASSWORD')", "Env var password", "should be SECURE"),
    ("os.system('rm -rf ' + user_input)", "Shell injection", "should be VULNERABLE"),
    ("subprocess.run(['rm', '-rf', sanitized_path], check=True)", "Safe subprocess", "should be SECURE"),
    ("def query(name): sql = f\"SELECT * FROM users WHERE name = '{name}'\"", "SQL injection", "should be VULNERABLE"),
    ("cursor.execute('SELECT * FROM users WHERE name = ?', (name,))", "Parameterized query", "should be SECURE"),
]

print("=" * 70)
print("Testing Feedback-Trained Model Predictions")
print("=" * 70)
print(f"Model input shape: {model.input_shape}")
print(f"Vectorizer features: {len(vectorizer.get_feature_names_out())}")
print("=" * 70)

for code, desc, expected in test_cases:
    # Vectorize and pad
    features = vectorizer.transform([code]).toarray()
    if features.shape[1] < 2000:
        features = np.pad(features, ((0, 0), (0, 2000 - features.shape[1])))
    
    # Predict
    pred = model.predict(features, verbose=0)[0][0]
    result = "VULNERABLE" if pred > 0.5 else "SECURE"
    
    # Check if correct
    is_correct = ("VULNERABLE" in expected and result == "VULNERABLE") or \
                 ("SECURE" in expected and result == "SECURE")
    status = "✓" if is_correct else "✗"
    
    print(f"\n{status} {desc}")
    print(f"   Code: {code[:50]}...")
    print(f"   Prediction: {pred:.4f} -> {result}")
    print(f"   Expected: {expected}")

print("\n" + "=" * 70)
