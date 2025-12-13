"""
Retrain Federated Learning on Cleaned Dataset
==============================================
Retrain the federated learning system using cleaned data and improved vectorizer.
"""

import sys
import os
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import joblib
from datetime import datetime
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'federated'))

from federated.data_partitioner import DataPartitioner
from federated.fl_simulation import FederatedLearningSimulation
from fl_config import (
    LEARNING_RATE, HIDDEN_LAYERS, DROPOUT_RATES, L2_REGULARIZATION,
    TFIDF_MAX_FEATURES, NUM_ROUNDS, NUM_CLIENTS, BATCH_SIZE, EPOCHS
)

print("="*70)
print("FEDERATED LEARNING RETRAINING - CLEANED DATASET")
print("="*70)

# Load cleaned dataset
df = pd.read_csv('data/expanded_dataset_v2.csv')
label_map = {'Error': 1, 'Good': 0}  # Error=1 (Vulnerable), Good=0 (Secure)
y = df['Result'].map(label_map).values

print(f"\n✓ Loaded cleaned dataset: {len(df)} samples")
print(f"  Vulnerable: {np.sum(y == 0)} ({np.sum(y == 0)/len(y)*100:.1f}%)")
print(f"  Secure: {np.sum(y == 1)} ({np.sum(y == 1)/len(y)*100:.1f}%)")

# Load vectorizer
vectorizer = joblib.load('models/tfidf_vectorizer.pkl')
X = vectorizer.transform(df['Code'].astype(str)).toarray()

print(f"✓ Loaded vectorizer: {X.shape[1]} features")

# Split data: 80/20 BEFORE client partitioning
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\nTrain/Test Split:")
print(f"  Training: {len(X_train)} samples")
print(f"  Test: {len(X_test)} samples")

# Create client data for federated learning
print(f"\n" + "="*70)
print(f"PREPARING FEDERATED DATA")
print("="*70)

# Prepare client data with stratification
np.random.seed(42)
n_clients = NUM_CLIENTS

client_data = {i: {'X': [], 'y': []} for i in range(n_clients)}

# Distribute training data to clients (stratified)
vulnerable_indices = np.where(y_train == 0)[0]
secure_indices = np.where(y_train == 1)[0]

np.random.shuffle(vulnerable_indices)
np.random.shuffle(secure_indices)

# Distribute equally across clients
vuln_per_client = len(vulnerable_indices) // n_clients
secure_per_client = len(secure_indices) // n_clients

for i in range(n_clients):
    start_v = i * vuln_per_client
    end_v = start_v + vuln_per_client if i < n_clients - 1 else len(vulnerable_indices)
    
    start_s = i * secure_per_client
    end_s = start_s + secure_per_client if i < n_clients - 1 else len(secure_indices)
    
    client_vuln_idx = vulnerable_indices[start_v:end_v]
    client_secure_idx = secure_indices[start_s:end_s]
    
    all_idx = np.concatenate([client_vuln_idx, client_secure_idx])
    
    client_data[i]['X'] = X_train[all_idx]
    client_data[i]['y'] = y_train[all_idx]
    
    print(f"\nClient {i}: {len(all_idx)} samples")
    print(f"  Vulnerable: {np.sum(client_data[i]['y'] == 0)}")
    print(f"  Secure: {np.sum(client_data[i]['y'] == 1)}")

# Initialize federated learning
print(f"\n" + "="*70)
print(f"FEDERATED LEARNING TRAINING")
print("="*70)
print(f"\nConfiguration:")
print(f"  Rounds: {NUM_ROUNDS}")
print(f"  Clients: {NUM_CLIENTS}")
print(f"  Learning Rate: {LEARNING_RATE}")
print(f"  Architecture: {HIDDEN_LAYERS}")
print(f"  Dropout: {DROPOUT_RATES}")

# Create FL simulation
fl_sim = FederatedLearningSimulation(
    num_clients=NUM_CLIENTS,
    input_dim=X_train.shape[1],
    learning_rate=LEARNING_RATE,
    hidden_layers=HIDDEN_LAYERS,
    dropout_rates=DROPOUT_RATES,
    l2_reg=L2_REGULARIZATION
)

# Train federated
print(f"\nTraining...")
history = fl_sim.train(
    client_data=client_data,
    num_rounds=NUM_ROUNDS,
    epochs_per_round=EPOCHS,
    batch_size=BATCH_SIZE,
    verbose=1
)

# Evaluate on test set
print(f"\n" + "="*70)
print(f"EVALUATION")
print("="*70)

global_model = fl_sim.get_global_model()
y_pred_prob = global_model.predict(X_test, verbose=0).flatten()
y_pred = (y_pred_prob >= 0.5).astype(int)

test_accuracy = accuracy_score(y_test, y_pred)
test_precision = precision_score(y_test, y_pred)
test_recall = recall_score(y_test, y_pred)
test_f1 = f1_score(y_test, y_pred)

tn, fp, fn, tp = confusion_matrix(y_test, y_pred, labels=[0, 1]).ravel()

print(f"\nTest Set Results (Cleaned Dataset, FL):")
print(f"  Accuracy:  {test_accuracy:.2%}")
print(f"  Precision: {test_precision:.2%}")
print(f"  Recall:    {test_recall:.2%}")
print(f"  F1-Score:  {test_f1:.2%}")
print(f"\nConfusion Matrix:")
print(f"  TN: {tn}, FP: {fp}, FN: {fn}, TP: {tp}")

print(f"\nComparison to original FL:")
print(f"  Original FL accuracy:  86.3%")
print(f"  Cleaned FL accuracy:   {test_accuracy:.2%}")
if test_accuracy >= 0.86:
    print(f"  ✓ Maintained performance on cleaned data")
else:
    print(f"  ⚠️  Slight variation from original")

# Save model
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
model_path = f'models/federated/fl_global_model_cleaned_{timestamp}.keras'
global_model.save(model_path)
print(f"\n✓ FL Model saved: {model_path}")

# Save results
results = {
    'timestamp': datetime.now().isoformat(),
    'dataset': 'expanded_dataset_v2_cleaned',
    'federated_config': {
        'num_rounds': NUM_ROUNDS,
        'num_clients': NUM_CLIENTS,
        'learning_rate': LEARNING_RATE,
        'architecture': HIDDEN_LAYERS,
        'dropout': DROPOUT_RATES
    },
    'test_metrics': {
        'accuracy': float(test_accuracy),
        'precision': float(test_precision),
        'recall': float(test_recall),
        'f1': float(test_f1)
    },
    'confusion_matrix': {'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp)},
    'training_set_size': len(X_train),
    'test_set_size': len(X_test),
    'comparison': {
        'original_fl_accuracy': 0.863,
        'cleaned_fl_accuracy': float(test_accuracy),
        'difference': float(test_accuracy - 0.863)
    },
    'convergence_history': history
}

results_path = f'results/federated/fl_cleaned_results_{timestamp}.json'
os.makedirs('results/federated', exist_ok=True)
with open(results_path, 'w') as f:
    json.dump(results, f, indent=2)

print(f"✓ Results saved: {results_path}")

print(f"\n" + "="*70)
print(f"✓ FL RETRAINING COMPLETE")
print(f"="*70)
