"""
Differential Privacy Federated Learning Simulation
===================================================

Simulates FL with differential privacy guarantees.
Compares accuracy across different privacy budgets (ε).
"""

import os
import sys
import numpy as np
import tensorflow as tf
from datetime import datetime
import json

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from federated.dp_model import create_dp_model, DPTrainer, get_model_weights, set_model_weights, compute_epsilon
from federated.data_partitioner import DataPartitioner
from federated.fl_config import (
    NUM_CLIENTS, NUM_ROUNDS, LOCAL_EPOCHS, BATCH_SIZE,
    DP_EPSILON, DP_DELTA, DP_CLIP_NORM, RANDOM_STATE,
    RESULTS_DIR, MODELS_DIR, TFIDF_MAX_FEATURES, LEARNING_RATE
)
from sklearn.model_selection import train_test_split

# Suppress TF warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
tf.get_logger().setLevel('ERROR')

np.random.seed(RANDOM_STATE)
tf.random.set_seed(RANDOM_STATE)


def fedavg_aggregate(client_weights: list, client_sizes: list) -> list:
    """
    Federated Averaging: weighted average of client weights.
    """
    total_size = sum(client_sizes)
    aggregated = []
    
    for layer_idx in range(len(client_weights[0])):
        layer_weights = np.zeros_like(client_weights[0][layer_idx])
        for client_idx, weights in enumerate(client_weights):
            weight = client_sizes[client_idx] / total_size
            layer_weights += weight * weights[layer_idx]
        aggregated.append(layer_weights)
    
    return aggregated


class DPFederatedSimulator:
    """
    Federated Learning Simulator with Differential Privacy.
    """
    
    def __init__(
        self,
        num_clients: int = NUM_CLIENTS,
        num_rounds: int = NUM_ROUNDS,
        noise_multiplier: float = 1.0,
        l2_norm_clip: float = DP_CLIP_NORM
    ):
        self.num_clients = num_clients
        self.num_rounds = num_rounds
        self.noise_multiplier = noise_multiplier
        self.l2_norm_clip = l2_norm_clip
        
        self.global_model = None
        self.client_data = []
        self.X_test = None
        self.y_test = None
        
        self.history = {
            'rounds': [],
            'global_accuracy': [],
            'client_accuracies': [],
            'epsilon_per_round': [],
            'total_epsilon': 0.0
        }
        
    def prepare_data(self):
        """Load and partition data across clients."""
        print(f"\n{'='*60}")
        print(" PREPARING DATA FOR DP-FL")
        print(f"{'='*60}")
        
        # Load data
        partitioner = DataPartitioner(num_clients=1)
        partitioner.load_data()
        X_all, y_all = partitioner.create_tfidf_features()
        
        # Split train/test
        X_train_all, self.X_test, y_train_all, self.y_test = train_test_split(
            X_all, y_all,
            test_size=0.2,
            random_state=RANDOM_STATE,
            stratify=y_all
        )
        
        print(f"Total samples: {len(y_all)}")
        print(f"Training samples: {len(y_train_all)}")
        print(f"Test samples: {len(self.y_test)}")
        
        # Partition to clients
        samples_per_client = len(y_train_all) // self.num_clients
        indices = np.arange(len(y_train_all))
        np.random.shuffle(indices)
        
        for i in range(self.num_clients):
            start = i * samples_per_client
            end = start + samples_per_client if i < self.num_clients - 1 else len(indices)
            client_indices = indices[start:end]
            
            self.client_data.append({
                'X_train': X_train_all[client_indices],
                'y_train': y_train_all[client_indices]
            })
            print(f"Client {i}: {len(client_indices)} samples")
            
    def initialize_global_model(self):
        """Initialize the global model."""
        print("\n[*] Initializing global model...")
        self.global_model = create_dp_model(input_dim=TFIDF_MAX_FEATURES)
        print(f"    Model parameters: {self.global_model.count_params()}")
        
    def train_round(self, round_num: int) -> float:
        """Execute one round of DP-FL training."""
        print(f"\n--- Round {round_num + 1}/{self.num_rounds} ---")
        
        global_weights = get_model_weights(self.global_model)
        client_weights = []
        client_sizes = []
        client_accs = []
        round_epsilon = 0.0
        
        for client_id, data in enumerate(self.client_data):
            # Create local model and set global weights
            local_model = create_dp_model(input_dim=data['X_train'].shape[1])
            set_model_weights(local_model, global_weights)
            
            # Create DP trainer
            trainer = DPTrainer(
                model=local_model,
                l2_norm_clip=self.l2_norm_clip,
                noise_multiplier=self.noise_multiplier,
                learning_rate=LEARNING_RATE
            )
            
            # Train locally with DP
            history = trainer.fit(
                data['X_train'],
                data['y_train'],
                epochs=LOCAL_EPOCHS,
                batch_size=BATCH_SIZE,
                verbose=0
            )
            
            # Get epsilon for this client
            client_epsilon = trainer.get_epsilon(
                dataset_size=len(data['y_train']),
                batch_size=BATCH_SIZE,
                delta=DP_DELTA
            )
            round_epsilon = max(round_epsilon, client_epsilon)
            
            # Collect weights
            client_weights.append(get_model_weights(local_model))
            client_sizes.append(len(data['y_train']))
            client_accs.append(history['accuracy'][-1])
            
            print(f"  Client {client_id}: acc={history['accuracy'][-1]:.4f}, ε={client_epsilon:.2f}")
            
        # Aggregate weights
        aggregated_weights = fedavg_aggregate(client_weights, client_sizes)
        set_model_weights(self.global_model, aggregated_weights)
        
        # Evaluate on test set
        _, global_acc = self.global_model.evaluate(self.X_test, self.y_test, verbose=0)
        
        # Update history
        self.history['rounds'].append(round_num + 1)
        self.history['global_accuracy'].append(float(global_acc))
        self.history['client_accuracies'].append(client_accs)
        self.history['epsilon_per_round'].append(round_epsilon)
        self.history['total_epsilon'] += round_epsilon
        
        print(f"  Global accuracy: {global_acc:.4f}")
        print(f"  Round ε: {round_epsilon:.2f}, Total ε: {self.history['total_epsilon']:.2f}")
        
        return global_acc
        
    def run_simulation(self):
        """Run the complete DP-FL simulation."""
        print(f"\n{'='*60}")
        print(f" DP-FL SIMULATION")
        print(f" Noise multiplier: {self.noise_multiplier}")
        print(f" L2 clip norm: {self.l2_norm_clip}")
        print(f"{'='*60}")
        
        self.prepare_data()
        self.initialize_global_model()
        
        for round_num in range(self.num_rounds):
            self.train_round(round_num)
            
        # Final evaluation
        final_acc = self.history['global_accuracy'][-1]
        total_eps = self.history['total_epsilon']
        
        print(f"\n{'='*60}")
        print(f" SIMULATION COMPLETE")
        print(f"{'='*60}")
        print(f"  Final accuracy: {final_acc:.4f} ({final_acc*100:.2f}%)")
        print(f"  Total ε spent: {total_eps:.2f}")
        print(f"  δ: {DP_DELTA}")
        print(f"{'='*60}")
        
        return final_acc, total_eps
        
    def save_results(self, filename: str = None):
        """Save simulation results."""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"dp_fl_results_{timestamp}.json"
            
        filepath = os.path.join(RESULTS_DIR, filename)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'config': {
                'num_clients': self.num_clients,
                'num_rounds': self.num_rounds,
                'noise_multiplier': self.noise_multiplier,
                'l2_norm_clip': self.l2_norm_clip,
                'local_epochs': LOCAL_EPOCHS,
                'batch_size': BATCH_SIZE,
                'delta': DP_DELTA
            },
            'history': self.history,
            'final_accuracy': self.history['global_accuracy'][-1] if self.history['global_accuracy'] else 0,
            'total_epsilon': self.history['total_epsilon']
        }
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)
            
        print(f"\nResults saved to: {filepath}")
        return filepath


def run_privacy_comparison():
    """Run simulations at different privacy levels."""
    print("\n" + "="*70)
    print(" PRIVACY-ACCURACY TRADEOFF ANALYSIS")
    print("="*70)
    
    # Different noise multipliers (higher = more private = lower accuracy)
    noise_levels = [
        (0.0, "No DP"),
        (0.5, "Low noise"),
        (1.0, "Medium noise"),
        (2.0, "High noise")
    ]
    
    results = []
    
    for noise_mult, label in noise_levels:
        print(f"\n{'='*60}")
        print(f" Testing: {label} (noise={noise_mult})")
        print(f"{'='*60}")
        
        simulator = DPFederatedSimulator(
            num_clients=NUM_CLIENTS,
            num_rounds=10,  # Fewer rounds for comparison
            noise_multiplier=noise_mult,
            l2_norm_clip=DP_CLIP_NORM
        )
        
        accuracy, epsilon = simulator.run_simulation()
        
        results.append({
            'label': label,
            'noise_multiplier': noise_mult,
            'accuracy': accuracy,
            'epsilon': epsilon
        })
        
    # Print summary
    print("\n" + "="*70)
    print(" PRIVACY-ACCURACY TRADEOFF SUMMARY")
    print("="*70)
    print(f"{'Setting':<20} {'Noise':<10} {'Accuracy':<12} {'ε (Privacy)':<10}")
    print("-"*52)
    for r in results:
        eps_str = f"{r['epsilon']:.2f}" if r['epsilon'] != float('inf') else "∞"
        print(f"{r['label']:<20} {r['noise_multiplier']:<10} {r['accuracy']*100:.2f}%{'':<6} {eps_str}")
        
    return results


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='DP-FL Simulation')
    parser.add_argument('--compare', action='store_true', help='Run privacy comparison')
    parser.add_argument('--noise', type=float, default=1.0, help='Noise multiplier')
    parser.add_argument('--rounds', type=int, default=NUM_ROUNDS, help='Number of rounds')
    args = parser.parse_args()
    
    if args.compare:
        run_privacy_comparison()
    else:
        simulator = DPFederatedSimulator(
            num_clients=NUM_CLIENTS,
            num_rounds=args.rounds,
            noise_multiplier=args.noise
        )
        simulator.run_simulation()
        simulator.save_results()
        return simulator


if __name__ == "__main__":
    main()
```
