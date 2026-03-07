"""
Timing Measurement Script for SecureCode-FL Paper
==================================================
Measures:
1. Centralized training time
2. Federated training time (per round, total)
3. Communication overhead (model weight size)
4. Inference latency
"""

import os
import sys
import time
import json
import numpy as np

# Suppress TF warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import tensorflow as tf
tf.get_logger().setLevel('ERROR')

# Add project paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'federated'))

from config import RANDOM_STATE
from federated.fl_config import (
    NUM_CLIENTS, NUM_ROUNDS, LOCAL_EPOCHS, BATCH_SIZE,
    TFIDF_MAX_FEATURES, HIDDEN_LAYERS, DROPOUT_RATES,
    L2_REGULARIZATION, LEARNING_RATE
)
from federated.data_partitioner import DataPartitioner
from federated.fl_model import create_model, FLModel, fedavg_aggregate
from sklearn.model_selection import train_test_split

np.random.seed(RANDOM_STATE)
tf.random.set_seed(RANDOM_STATE)

print("=" * 70)
print(" SecureCode-FL TIMING MEASUREMENT")
print("=" * 70)

# =============================================================================
# 1. Load and prepare data
# =============================================================================
print("\n[1] Loading data...")
partitioner = DataPartitioner(num_clients=1)
partitioner.load_data()
X_all, y_all = partitioner.create_tfidf_features()

X_train_all, X_test, y_train_all, y_test = train_test_split(
    X_all, y_all, test_size=0.2, random_state=RANDOM_STATE, stratify=y_all
)

print(f"    Total samples: {len(y_all)}")
print(f"    Training samples: {len(y_train_all)}")
print(f"    Test samples: {len(y_test)}")
print(f"    Feature dim: {X_all.shape[1]}")

# =============================================================================
# 2. Measure CENTRALIZED training time
# =============================================================================
print("\n[2] Measuring CENTRALIZED training time...")

total_centralized_epochs = NUM_ROUNDS * LOCAL_EPOCHS  # 20 * 3 = 60 epochs

centralized_model = FLModel(input_dim=TFIDF_MAX_FEATURES)

start_time = time.perf_counter()
centralized_model.fit(
    X_train_all, y_train_all,
    epochs=total_centralized_epochs,
    batch_size=BATCH_SIZE,
    verbose=0
)
centralized_time = time.perf_counter() - start_time

# Single epoch time
single_epoch_time = centralized_time / total_centralized_epochs

_, centralized_acc = centralized_model.evaluate(X_test, y_test, verbose=0)

print(f"    Total epochs: {total_centralized_epochs}")
print(f"    Total time: {centralized_time:.2f}s")
print(f"    Time per epoch: {single_epoch_time:.4f}s")
print(f"    Accuracy: {centralized_acc*100:.2f}%")

# =============================================================================
# 3. Measure FEDERATED training time
# =============================================================================
print("\n[3] Measuring FEDERATED training time...")

# Partition training data to clients
train_indices = np.arange(len(y_train_all))
np.random.shuffle(train_indices)
split_indices = np.array_split(train_indices, NUM_CLIENTS)

client_data = []
for client_id, client_indices in enumerate(split_indices):
    client_data.append({
        'X_train': X_train_all[client_indices],
        'y_train': y_train_all[client_indices],
        'num_samples': len(client_indices)
    })
    print(f"    Client {client_id}: {len(client_indices)} samples")

# Initialize global model
global_model = FLModel(input_dim=TFIDF_MAX_FEATURES)
global_weights = global_model.get_weights()

round_times = []
client_train_times = []
aggregation_times = []

total_fl_start = time.perf_counter()

for round_num in range(NUM_ROUNDS):
    round_start = time.perf_counter()
    
    # Broadcast weights (simulate - just copy)
    client_weights = []
    client_num_samples = []
    round_client_times = []
    
    # Each client trains locally
    for client in client_data:
        client_model = FLModel(input_dim=TFIDF_MAX_FEATURES)
        client_model.set_weights(global_weights)
        
        client_start = time.perf_counter()
        client_model.fit(
            client['X_train'], client['y_train'],
            epochs=LOCAL_EPOCHS,
            batch_size=BATCH_SIZE,
            verbose=0
        )
        client_time = time.perf_counter() - client_start
        round_client_times.append(client_time)
        
        client_weights.append(client_model.get_weights())
        client_num_samples.append(client['num_samples'])
    
    # Aggregate
    agg_start = time.perf_counter()
    global_weights = fedavg_aggregate(client_weights, client_num_samples)
    agg_time = time.perf_counter() - agg_start
    
    global_model.set_weights(global_weights)
    
    round_time = time.perf_counter() - round_start
    round_times.append(round_time)
    client_train_times.append(round_client_times)
    aggregation_times.append(agg_time)

total_fl_time = time.perf_counter() - total_fl_start

_, federated_acc = global_model.evaluate(X_test, y_test, verbose=0)

avg_round_time = np.mean(round_times)
avg_client_time = np.mean([np.mean(r) for r in client_train_times])
avg_agg_time = np.mean(aggregation_times)

print(f"\n    Total FL time: {total_fl_time:.2f}s")
print(f"    Avg wall-clock per round: {avg_round_time:.4f}s")
print(f"    Avg client training time: {avg_client_time:.4f}s")
print(f"    Avg aggregation time: {avg_agg_time:.6f}s")
print(f"    FL Accuracy: {federated_acc*100:.2f}%")

# =============================================================================
# 4. Measure COMMUNICATION overhead
# =============================================================================
print("\n[4] Measuring communication overhead...")

# Model weights size
import pickle
weights = global_model.get_weights()
weights_bytes = len(pickle.dumps(weights))
weights_mb = weights_bytes / (1024 * 1024)

# Per round: each client sends weights + server broadcasts weights
comm_per_round_upload = weights_mb * NUM_CLIENTS  # clients -> server
comm_per_round_download = weights_mb * NUM_CLIENTS  # server -> clients
comm_per_round_total = comm_per_round_upload + comm_per_round_download
total_comm = comm_per_round_total * NUM_ROUNDS

print(f"    Model weights size: {weights_bytes} bytes ({weights_mb:.4f} MB)")
print(f"    Comm per round (upload): {comm_per_round_upload:.4f} MB")
print(f"    Comm per round (download): {comm_per_round_download:.4f} MB")
print(f"    Comm per round (total): {comm_per_round_total:.4f} MB")
print(f"    Total communication (20 rounds): {total_comm:.2f} MB")

# =============================================================================
# 5. Measure INFERENCE latency
# =============================================================================
print("\n[5] Measuring inference latency...")

# Warm up
_ = global_model.predict(X_test[:1])

# Measure single sample inference
num_inference_runs = 100
inference_times = []
for i in range(num_inference_runs):
    sample = X_test[i % len(X_test):i % len(X_test) + 1]
    start = time.perf_counter()
    _ = global_model.predict(sample, verbose=0)
    inference_times.append(time.perf_counter() - start)

avg_inference_ms = np.mean(inference_times) * 1000
p50_inference_ms = np.percentile(inference_times, 50) * 1000
p99_inference_ms = np.percentile(inference_times, 99) * 1000

# Batch inference
batch_start = time.perf_counter()
_ = global_model.predict(X_test, verbose=0)
batch_time = time.perf_counter() - batch_start
batch_per_sample_ms = (batch_time / len(X_test)) * 1000

print(f"    Single sample (avg): {avg_inference_ms:.2f} ms")
print(f"    Single sample (p50): {p50_inference_ms:.2f} ms")
print(f"    Single sample (p99): {p99_inference_ms:.2f} ms")
print(f"    Batch inference: {batch_per_sample_ms:.4f} ms/sample ({len(X_test)} samples)")

# =============================================================================
# 6. Measure model parameter count
# =============================================================================
print("\n[6] Model info...")
total_params = sum(np.prod(w.shape) for w in weights)
print(f"    Total parameters: {total_params:,}")

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "=" * 70)
print(" SUMMARY TABLE (for paper)")
print("=" * 70)

results = {
    "centralized_total_time_s": round(centralized_time, 2),
    "centralized_time_per_epoch_s": round(single_epoch_time, 4),
    "centralized_accuracy": round(centralized_acc * 100, 2),
    "fl_total_time_s": round(total_fl_time, 2),
    "fl_avg_round_time_s": round(avg_round_time, 4),
    "fl_avg_client_time_s": round(avg_client_time, 4),
    "fl_avg_agg_time_s": round(avg_agg_time, 6),
    "fl_accuracy": round(federated_acc * 100, 2),
    "model_weights_mb": round(weights_mb, 4),
    "comm_per_round_mb": round(comm_per_round_total, 4),
    "total_comm_mb": round(total_comm, 2),
    "inference_avg_ms": round(avg_inference_ms, 2),
    "inference_p50_ms": round(p50_inference_ms, 2),
    "inference_batch_ms_per_sample": round(batch_per_sample_ms, 4),
    "total_parameters": int(total_params),
    "num_rounds": NUM_ROUNDS,
    "num_clients": NUM_CLIENTS,
    "local_epochs": LOCAL_EPOCHS,
    "batch_size": BATCH_SIZE,
}

print(f"\nMetric                          | Centralized    | Federated")
print(f"-" * 70)
print(f"Total Training Time (s)         | {results['centralized_total_time_s']:>12}   | {results['fl_total_time_s']:>12}")
print(f"Time per Epoch (s)              | {results['centralized_time_per_epoch_s']:>12}   | {results['fl_avg_client_time_s']:>12} x{NUM_CLIENTS}")
print(f"Wall-Clock per FL Round (s)     | {'---':>12}   | {results['fl_avg_round_time_s']:>12}")
print(f"Communication per Round (MB)    | {'---':>12}   | {results['comm_per_round_mb']:>12}")
print(f"Total Communication (MB)        | {'---':>12}   | {results['total_comm_mb']:>12}")
print(f"Inference Latency (ms/sample)   | {results['inference_avg_ms']:>12}   | {results['inference_avg_ms']:>12}")
print(f"Accuracy                        | {results['centralized_accuracy']:>11}%  | {results['fl_accuracy']:>11}%")

# Save results
results_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "timing_results.json")
with open(results_path, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to: {results_path}")
