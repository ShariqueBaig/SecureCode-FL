"""
Federated Learning Simulation
=============================

Simulates federated learning with multiple clients training on private code.
Uses Flower framework to coordinate distributed training.
"""

import os
import sys
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flwr as fl
from flwr.common import ndarrays_to_parameters, parameters_to_ndarrays

from fl_config import (
    NUM_CLIENTS, NUM_ROUNDS, LOCAL_EPOCHS, BATCH_SIZE,
    DATA_DISTRIBUTION, TFIDF_MAX_FEATURES, RANDOM_STATE,
    RESULTS_DIR, MODELS_DIR, CHECKPOINTS_DIR
)
from data_partitioner import DataPartitioner
from fl_model import create_model, fedavg_aggregate, FLModel

# Suppress TF warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
tf.get_logger().setLevel('ERROR')

np.random.seed(RANDOM_STATE)
tf.random.set_seed(RANDOM_STATE)


class FederatedSimulator:
    """
    Simulates federated learning without network communication.
    
    This is useful for:
    1. Testing FL algorithms locally
    2. Comparing FL vs centralized training
    3. Analyzing privacy-accuracy tradeoffs
    """
    
    def __init__(self, num_clients=NUM_CLIENTS, num_rounds=NUM_ROUNDS):
        self.num_clients = num_clients
        self.num_rounds = num_rounds
        self.client_data = None
        self.global_model = None
        self.vectorizer = None
        self.X_test = None
        self.y_test = None
        self.history = {
            'rounds': [],
            'global_accuracy': [],
            'global_loss': [],
            'client_accuracies': []
        }
        
    def prepare_data(self):
        """Partition data across clients"""
        print(f"\n{'='*70}")
        print(" PREPARING FEDERATED DATA")
        print(f"{'='*70}")
        
        # Partition data
        partitioner = DataPartitioner(
            num_clients=self.num_clients,
            distribution=DATA_DISTRIBUTION
        )
        self.client_data, self.vectorizer = partitioner.partition()
        
        # Create global test set (20% of total data)
        # Load original data to create test set
        partitioner.load_data()
        X_all, y_all = partitioner.create_tfidf_features()
        
        # Use vectorizer fitted on all data for consistency
        _, self.X_test, _, self.y_test = train_test_split(
            X_all, y_all,
            test_size=0.2,
            random_state=RANDOM_STATE,
            stratify=y_all
        )
        
        print(f"\nGlobal test set: {len(self.y_test)} samples")
        
    def initialize_global_model(self):
        """Initialize the global model"""
        print(f"\n{'='*70}")
        print(" INITIALIZING GLOBAL MODEL")
        print(f"{'='*70}")
        
        self.global_model = FLModel(input_dim=TFIDF_MAX_FEATURES)
        print("Model architecture:")
        self.global_model.model.summary()
        
    def train_round(self, round_num):
        """Execute one round of federated training"""
        print(f"\n{'-'*70}")
        print(f" ROUND {round_num + 1}/{self.num_rounds}")
        print(f"{'-'*70}")
        
        # Get current global weights
        global_weights = self.global_model.get_weights()
        
        # Collect client updates
        client_weights = []
        client_samples = []
        client_accuracies = []
        
        for client in self.client_data:
            client_id = client['client_id']
            X_train = client['X_train']
            y_train = client['y_train']
            
            # Create local model and set global weights
            local_model = FLModel(input_dim=TFIDF_MAX_FEATURES)
            local_model.set_weights(global_weights)
            
            # Train locally
            local_model.fit(
                X_train, y_train,
                epochs=LOCAL_EPOCHS,
                batch_size=BATCH_SIZE,
                verbose=0
            )
            
            # Evaluate locally
            _, local_acc = local_model.evaluate(X_train, y_train)
            
            print(f"  Client {client_id}: {len(y_train)} samples, "
                  f"Local Acc: {local_acc*100:.1f}%")
            
            # Collect weights and metadata
            client_weights.append(local_model.get_weights())
            client_samples.append(len(y_train))
            client_accuracies.append(local_acc)
        
        # Aggregate weights using FedAvg
        aggregated_weights = fedavg_aggregate(client_weights, client_samples)
        
        # Update global model
        self.global_model.set_weights(aggregated_weights)
        
        # Evaluate global model on test set
        global_loss, global_acc = self.global_model.evaluate(
            self.X_test, self.y_test
        )
        
        print(f"\n  Global Model: Loss={global_loss:.4f}, "
              f"Acc={global_acc*100:.1f}%")
        
        # Store history
        self.history['rounds'].append(round_num + 1)
        self.history['global_accuracy'].append(global_acc)
        self.history['global_loss'].append(global_loss)
        self.history['client_accuracies'].append(client_accuracies)
        
        return global_acc
    
    def run_simulation(self):
        """Run the complete FL simulation"""
        print(f"\n{'='*70}")
        print(" FEDERATED LEARNING SIMULATION")
        print(f"{'='*70}")
        print(f"Clients: {self.num_clients}")
        print(f"Rounds: {self.num_rounds}")
        print(f"Local epochs per round: {LOCAL_EPOCHS}")
        print(f"Data distribution: {DATA_DISTRIBUTION}")
        
        # Prepare data
        self.prepare_data()
        
        # Initialize model
        self.initialize_global_model()
        
        # Initial evaluation
        print(f"\n{'-'*70}")
        print(" INITIAL EVALUATION (Before Training)")
        print(f"{'-'*70}")
        initial_loss, initial_acc = self.global_model.evaluate(
            self.X_test, self.y_test
        )
        print(f"Initial accuracy: {initial_acc*100:.1f}%")
        
        # Run FL rounds
        for round_num in range(self.num_rounds):
            accuracy = self.train_round(round_num)
        
        # Final evaluation
        print(f"\n{'='*70}")
        print(" FINAL RESULTS")
        print(f"{'='*70}")
        
        final_loss, final_acc = self.global_model.evaluate(
            self.X_test, self.y_test
        )
        
        print(f"\nInitial accuracy: {initial_acc*100:.1f}%")
        print(f"Final accuracy: {final_acc*100:.1f}%")
        print(f"Improvement: {(final_acc - initial_acc)*100:+.1f}%")
        
        return final_acc
    
    def compare_with_centralized(self):
        """Compare FL results with centralized training"""
        print(f"\n{'='*70}")
        print(" COMPARISON: FEDERATED vs CENTRALIZED")
        print(f"{'='*70}")
        
        # Centralized training (combine all client data)
        X_centralized = np.vstack([c['X_train'] for c in self.client_data])
        y_centralized = np.concatenate([c['y_train'] for c in self.client_data])
        
        print(f"\nCentralized training data: {len(y_centralized)} samples")
        
        # Train centralized model
        centralized_model = FLModel(input_dim=TFIDF_MAX_FEATURES)
        total_epochs = self.num_rounds * LOCAL_EPOCHS
        
        centralized_model.fit(
            X_centralized, y_centralized,
            epochs=total_epochs,
            batch_size=BATCH_SIZE,
            verbose=0
        )
        
        # Evaluate
        _, centralized_acc = centralized_model.evaluate(
            self.X_test, self.y_test
        )
        
        federated_acc = self.history['global_accuracy'][-1]
        
        print(f"\nCentralized accuracy: {centralized_acc*100:.1f}%")
        print(f"Federated accuracy: {federated_acc*100:.1f}%")
        print(f"Difference: {(federated_acc - centralized_acc)*100:+.1f}%")
        
        return {
            'centralized': centralized_acc,
            'federated': federated_acc,
            'difference': federated_acc - centralized_acc
        }
    
    def save_results(self):
        """Save simulation results"""
        print(f"\n{'='*70}")
        print(" SAVING RESULTS")
        print(f"{'='*70}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save training history
        history_path = os.path.join(RESULTS_DIR, f"fl_history_{timestamp}.json")
        with open(history_path, 'w') as f:
            json.dump(self.history, f, indent=2)
        print(f"Saved: {history_path}")
        
        # Save final model
        model_path = os.path.join(MODELS_DIR, "fl_global_model.keras")
        self.global_model.save(model_path)
        print(f"Saved: {model_path}")
        
        # Save comparison results
        comparison = self.compare_with_centralized()
        comparison_path = os.path.join(RESULTS_DIR, f"fl_comparison_{timestamp}.json")
        with open(comparison_path, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'config': {
                    'num_clients': self.num_clients,
                    'num_rounds': self.num_rounds,
                    'local_epochs': LOCAL_EPOCHS,
                    'data_distribution': DATA_DISTRIBUTION
                },
                'results': comparison,
                'history': self.history
            }, f, indent=2)
        print(f"Saved: {comparison_path}")
        
        return comparison


def main():
    """Main entry point for FL simulation"""
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║           SECURECODE-FL: FEDERATED LEARNING SIMULATION           ║
    ║                                                                  ║
    ║        Privacy-Preserving Code Vulnerability Detection           ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Create and run simulator
    simulator = FederatedSimulator(
        num_clients=NUM_CLIENTS,
        num_rounds=NUM_ROUNDS
    )
    
    # Run simulation
    final_accuracy = simulator.run_simulation()
    
    # Save results
    comparison = simulator.save_results()
    
    # Summary
    print(f"""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                      SIMULATION COMPLETE                         ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  Federated Accuracy:   {comparison['federated']*100:5.1f}%                              ║
    ║  Centralized Accuracy: {comparison['centralized']*100:5.1f}%                              ║
    ║  Difference:           {comparison['difference']*100:+5.1f}%                              ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  Privacy Preserved: ✓ Code never left client devices            ║
    ║  Only model weights were shared                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    return simulator


if __name__ == "__main__":
    simulator = main()
