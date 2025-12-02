"""
Federated Learning Configuration
================================

Configuration settings for the FL system.
"""

import os

# =============================================================================
# FL Server Configuration
# =============================================================================
SERVER_ADDRESS = "127.0.0.1:8080"
NUM_ROUNDS = 20  # Number of federated training rounds
MIN_FIT_CLIENTS = 3  # Minimum clients for training round
MIN_EVALUATE_CLIENTS = 3  # Minimum clients for evaluation
MIN_AVAILABLE_CLIENTS = 3  # Minimum clients to start

# =============================================================================
# FL Client Configuration
# =============================================================================
NUM_CLIENTS = 3  # Number of simulated clients/organizations
LOCAL_EPOCHS = 3  # Epochs per client per round
BATCH_SIZE = 16
LEARNING_RATE = 0.001

# =============================================================================
# Model Configuration
# =============================================================================
TFIDF_MAX_FEATURES = 2000
HIDDEN_LAYERS = [256, 128, 64]
DROPOUT_RATES = [0.4, 0.3, 0.2]
L2_REGULARIZATION = 0.001

# =============================================================================
# Data Partitioning
# =============================================================================
# How to split data across clients
# 'iid' = Independent and Identically Distributed (random)
# 'non_iid' = Non-IID (each client has different vulnerability types)
DATA_DISTRIBUTION = 'non_iid'

# For non-IID: number of vulnerability types per client
CLASSES_PER_CLIENT = 5

# =============================================================================
# Paths
# =============================================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models", "federated")
RESULTS_DIR = os.path.join(BASE_DIR, "results", "federated")
CHECKPOINTS_DIR = os.path.join(BASE_DIR, "checkpoints")

# Create directories
for dir_path in [MODELS_DIR, RESULTS_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# =============================================================================
# Random Seeds
# =============================================================================
RANDOM_STATE = 42

# =============================================================================
# Privacy Settings (for future Differential Privacy)
# =============================================================================
ENABLE_DP = False  # Enable Differential Privacy
DP_EPSILON = 1.0  # Privacy budget
DP_DELTA = 1e-5  # Privacy parameter
DP_CLIP_NORM = 1.0  # Gradient clipping norm
