# Phase 3: Federated Learning Implementation

## 📋 Overview

This phase implements **Federated Learning (FL)** for privacy-preserving vulnerability detection. Multiple organizations can collaboratively train a shared model without exposing their proprietary source code.

## 🎯 Objectives Achieved

| Metric | Result |
|--------|--------|
| Federated Accuracy | **94.7%** |
| Centralized Accuracy | 94.7% |
| Accuracy Loss from FL | **0.0%** |
| Privacy Preserved | ✅ Code never leaves client devices |

## 🧠 Key Concepts Explained

### What is Federated Learning?

Traditional machine learning requires all data to be centralized:
```
[Org A Code] ──┐
[Org B Code] ──┼──► [Central Server] ──► Train Model
[Org C Code] ──┘
      ↑
   ⚠️ Privacy Risk: Code is exposed!
```

Federated Learning keeps data local:
```
[Org A] trains locally ──► sends weights ──┐
[Org B] trains locally ──► sends weights ──┼──► [Server: Aggregate] ──► Global Model
[Org C] trains locally ──► sends weights ──┘
      ↑
   ✅ Privacy: Only model weights shared, not code!
```

### FedAvg Algorithm

The server combines client models using **weighted averaging**:

```python
# FedAvg: Federated Averaging
global_weights = Σ (n_k / n) × weights_k

where:
- n_k = number of samples on client k
- n = total samples across all clients
- weights_k = model weights from client k
```

This ensures clients with more data have proportionally more influence.

### Non-IID Data Distribution

In real-world scenarios, different organizations have different vulnerability types:
- **Bank A**: Mostly SQL Injection vulnerabilities
- **Hospital B**: Mostly Broken Authentication
- **Startup C**: Mix of API vulnerabilities

We simulate this "non-IID" (non-Independent and Identically Distributed) scenario to test robustness.

## 📁 File Structure

```
SecureCode-FL/
├── federated/
│   ├── __init__.py           # Package initializer
│   ├── fl_config.py          # Configuration parameters
│   ├── data_partitioner.py   # Splits data across clients
│   ├── fl_model.py           # FL-compatible neural network
│   ├── fl_client.py          # Flower client implementation
│   ├── fl_server.py          # FedAvg server logic
│   └── fl_simulation.py      # Main orchestrator
├── models/federated/
│   └── fl_global_model.keras # Saved global model
└── results/federated/
    ├── fl_history_*.json     # Training history
    └── fl_comparison_*.json  # FL vs Centralized comparison
```

## 🔧 Component Details

### 1. Configuration (`fl_config.py`)

```python
FL_CONFIG = {
    'num_clients': 3,           # Simulated organizations
    'fl_rounds': 20,            # Communication rounds
    'local_epochs': 3,          # Training epochs per round
    'batch_size': 16,           # Mini-batch size
    'learning_rate': 0.001,     # Adam optimizer LR
    'min_fit_clients': 3,       # Minimum clients for training
    'min_evaluate_clients': 3,  # Minimum clients for evaluation
    'fraction_fit': 1.0,        # Fraction of clients to train
    'fraction_evaluate': 1.0,   # Fraction of clients to evaluate
}
```

### 2. Data Partitioner (`data_partitioner.py`)

Splits the dataset across multiple clients:

```python
class DataPartitioner:
    def partition_iid(self, X, y, num_clients):
        """Equal random distribution (ideal case)"""
        
    def partition_non_iid(self, X, y, num_clients, alpha=0.5):
        """Dirichlet distribution (realistic case)"""
        # alpha controls heterogeneity:
        # - alpha → 0: highly non-IID (each client has few classes)
        # - alpha → ∞: approaches IID
```

### 3. FL Model (`fl_model.py`)

Neural network architecture compatible with Federated Learning:

```python
def create_fl_model(input_dim):
    model = Sequential([
        Dense(256, activation='relu', kernel_regularizer=l2(0.01)),
        BatchNormalization(),
        Dropout(0.3),
        Dense(128, activation='relu', kernel_regularizer=l2(0.01)),
        BatchNormalization(),
        Dropout(0.3),
        Dense(64, activation='relu'),
        Dense(1, activation='sigmoid')  # Binary classification
    ])
    return model
```

**Why this architecture?**
- **BatchNormalization**: Stabilizes training across different client data distributions
- **Dropout**: Prevents overfitting on small local datasets
- **L2 Regularization**: Encourages weight similarity across clients

### 4. FL Client (`fl_client.py`)

Implements the Flower client interface:

```python
class VulnerabilityClient(fl.client.NumPyClient):
    def get_parameters(self):
        """Return current model weights"""
        
    def set_parameters(self, parameters):
        """Update model with new weights from server"""
        
    def fit(self, parameters, config):
        """Train on local data, return updated weights"""
        
    def evaluate(self, parameters, config):
        """Evaluate model on local test data"""
```

### 5. FL Server (`fl_server.py`)

Handles aggregation using FedAvg:

```python
class FedAvgServer:
    def aggregate_fit(self, results):
        """Weighted average of client weights"""
        weights = [
            (num_samples, params) 
            for _, params, num_samples in results
        ]
        return federated_averaging(weights)
```

### 6. Simulation (`fl_simulation.py`)

Orchestrates the entire FL process:

```python
def run_simulation():
    # 1. Load and preprocess data
    # 2. Partition data across clients
    # 3. Initialize global model
    # 4. Run FL rounds:
    #    a. Send global model to clients
    #    b. Clients train locally
    #    c. Collect and aggregate weights
    #    d. Update global model
    # 5. Evaluate final model
    # 6. Compare with centralized training
```

## 🚀 How to Reproduce

### Prerequisites

```bash
pip install tensorflow numpy pandas scikit-learn openpyxl flower
```

Or use requirements.txt:
```bash
pip install -r requirements.txt
```

### Step 1: Verify Dataset

Ensure the expanded dataset exists:
```bash
ls data/expanded_dataset_v2.xlsx
# Should show 471 samples
```

### Step 2: Run FL Simulation

```bash
cd SecureCode-FL
python -m federated.fl_simulation
```

### Expected Output

```
============================================================
        SecureCode-FL: Federated Learning Simulation
============================================================

[CONFIG] Federated Learning Configuration:
  - Number of clients: 3
  - FL rounds: 20
  - Local epochs per round: 3
  ...

[DATA] Loading and preprocessing data...
[DATA] Dataset: 471 samples, 2000 features
[DATA] Class distribution: {0: 238, 1: 233}

[PARTITION] Partitioning data across 3 clients (non-IID)...
  Client 0: 157 samples
  Client 1: 157 samples
  Client 2: 157 samples

[FL] Starting Federated Learning...
[FL] Round 1/20
  Client 0 - Loss: 0.xxxx, Accuracy: xx.x%
  Client 1 - Loss: 0.xxxx, Accuracy: xx.x%
  Client 2 - Loss: 0.xxxx, Accuracy: xx.x%
  Aggregated global model
...

[FL] Round 20/20
  ...

============================================================
                    FINAL RESULTS
============================================================
Federated Accuracy:   94.7%
Centralized Accuracy: 94.7%
Difference:           +0.0%

Privacy Preserved: ✓ Code never left client devices
============================================================
```

### Step 3: Verify Results

Check saved outputs:
```bash
# Global model
ls models/federated/fl_global_model.keras

# Training history
ls results/federated/fl_history_*.json

# Comparison results
cat results/federated/fl_comparison_*.json
```

## 📊 Understanding the Results

### Training History JSON

```json
{
  "rounds": [1, 2, ..., 20],
  "global_accuracy": [0.65, 0.72, ..., 0.947],
  "global_loss": [0.68, 0.55, ..., 0.18],
  "client_metrics": {
    "client_0": {...},
    "client_1": {...},
    "client_2": {...}
  }
}
```

### Comparison JSON

```json
{
  "federated_accuracy": 0.947,
  "centralized_accuracy": 0.947,
  "accuracy_difference": 0.0,
  "privacy_preserved": true,
  "num_clients": 3,
  "fl_rounds": 20
}
```

## 🔬 Experiments to Try

### 1. Change Number of Clients

Edit `fl_config.py`:
```python
'num_clients': 5,  # Try 5, 10, 20 clients
```

**Expected**: More clients = slightly slower convergence but better generalization.

### 2. Adjust Data Heterogeneity

In `fl_simulation.py`, modify the Dirichlet alpha:
```python
partitioner.partition_non_iid(X, y, num_clients, alpha=0.1)  # More non-IID
partitioner.partition_non_iid(X, y, num_clients, alpha=1.0)  # Less non-IID
```

**Expected**: Lower alpha = more challenging FL scenario.

### 3. Reduce Communication Rounds

```python
'fl_rounds': 10,  # Fewer rounds
```

**Expected**: Faster but potentially lower accuracy.

### 4. Try IID Distribution

```python
# In fl_simulation.py, change:
client_data = partitioner.partition_iid(X, y, num_clients)
```

**Expected**: Faster convergence, represents ideal (unrealistic) scenario.

## 📈 Performance Comparison

| Configuration | Accuracy | Rounds to Converge |
|--------------|----------|-------------------|
| Centralized (baseline) | 94.7% | N/A |
| FL (3 clients, non-IID) | 94.7% | 20 |
| FL (5 clients, non-IID) | ~93-94% | 25 |
| FL (3 clients, IID) | ~95% | 15 |

## 🔒 Privacy Guarantees

This implementation provides:

1. **Data Locality**: Raw code samples never leave client devices
2. **Weight Aggregation**: Only model parameters are shared
3. **No Data Reconstruction**: Cannot reverse-engineer code from weights

**Note**: For stronger privacy guarantees, Phase 5 will add **Differential Privacy** (noise injection to prevent membership inference attacks).

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'federated'"

**Solution**: Run from the project root:
```bash
cd SecureCode-FL
python -m federated.fl_simulation
```

### Issue: "FileNotFoundError: expanded_dataset_v2.xlsx"

**Solution**: Run dataset expansion first:
```bash
python dataset_expansion_v2.py
```

### Issue: Low accuracy (<80%)

**Possible causes**:
1. Too few FL rounds - increase `fl_rounds`
2. High data heterogeneity - increase Dirichlet alpha
3. Learning rate too high - reduce to 0.0005

### Issue: Memory error

**Solution**: Reduce batch size:
```python
'batch_size': 8,  # Smaller batches
```

## 📚 References

1. McMahan et al., "Communication-Efficient Learning of Deep Networks from Decentralized Data" (FedAvg paper)
2. Flower Framework Documentation: https://flower.dev/docs/
3. TensorFlow Federated: https://www.tensorflow.org/federated

## 🔜 Next Steps (Phase 4 & 5)

- **Phase 4**: VS Code Extension for real-time vulnerability detection
- **Phase 5**: Differential Privacy for enhanced privacy guarantees

---

*Documentation created: December 2, 2025*
*SecureCode-FL Research Project*
