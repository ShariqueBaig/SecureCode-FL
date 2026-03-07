"""
Configuration file for SecureCode-FL
Replicating the thesis: "Code Validation through Machine Learning - A Left Shift Focus Strategy"
"""

import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")
# Use expanded dataset (471 samples) instead of original (60 samples)
DATASET_PATH = os.path.join(DATA_DIR, "expanded_dataset_v2.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models")
RESULTS_DIR = os.path.join(BASE_DIR, "results")

# Create directories if they don't exist
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# Dataset Configuration
RANDOM_STATE = 42
TEST_SIZE = 0.2

# TF-IDF Configuration (as per thesis methodology)
TFIDF_CONFIG = {
    'max_features': 1000,
    'ngram_range': (1, 2),
    'min_df': 1,
    'max_df': 0.95,
    'stop_words': None,  # Keep code-related terms
}

# Models to evaluate (from thesis)
MODELS_CONFIG = {
    'Logistic Regression': {
        'random_state': RANDOM_STATE,
        'max_iter': 1000,
        'solver': 'lbfgs'
    },
    'Random Forest': {
        'n_estimators': 100,
        'random_state': RANDOM_STATE,
        'n_jobs': -1
    },
    'SVM': {
        'kernel': 'rbf',
        'random_state': RANDOM_STATE,
        'probability': True
    },
    'Gradient Boosting': {
        'n_estimators': 100,
        'random_state': RANDOM_STATE,
        'learning_rate': 0.1
    },
    'Extra Trees': {
        'n_estimators': 100,
        'random_state': RANDOM_STATE,
        'n_jobs': -1
    },
    'XGBoost': {
        'n_estimators': 100,
        'random_state': RANDOM_STATE,
        'learning_rate': 0.1,
        'use_label_encoder': False,
        'eval_metric': 'logloss'
    }
}

# Expected Results from Thesis (for validation)
EXPECTED_RESULTS = {
    'Extra Trees': 0.833,  # 83.3% - Best model in thesis
}
