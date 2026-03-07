"""
Flower FL Server
================

Server implementation for Federated Learning using Flower framework.
Aggregates model updates from clients using FedAvg algorithm.
"""

import flwr as fl
from flwr.common import Metrics
from flwr.server.strategy import FedAvg
import numpy as np
from typing import Dict, List, Optional, Tuple
import json
import os
from datetime import datetime

from fl_model import create_model, get_model_weights
from fl_config import (
    NUM_ROUNDS, MIN_FIT_CLIENTS, MIN_EVALUATE_CLIENTS,
    MIN_AVAILABLE_CLIENTS, TFIDF_MAX_FEATURES, RESULTS_DIR, MODELS_DIR
)


def weighted_average(metrics: List[Tuple[int, Metrics]]) -> Metrics:
    """
    Aggregate metrics from multiple clients using weighted average.
    
    Args:
        metrics: List of (num_samples, metrics_dict) tuples
    
    Returns:
        Aggregated metrics
    """
    # Calculate weighted average for accuracy
    accuracies = [num_samples * m["accuracy"] for num_samples, m in metrics]
    total_samples = sum([num_samples for num_samples, _ in metrics])
    
    return {"accuracy": sum(accuracies) / total_samples}


class VulnerabilityDetectionStrategy(FedAvg):
    """
    Custom FL strategy for vulnerability detection.
    
    Extends FedAvg with:
    - Custom metric aggregation
    - Round-by-round logging
    - Model checkpointing
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.round_metrics = []
        
    def aggregate_fit(
        self,
        server_round: int,
        results,
        failures,
    ):
        """Aggregate training results and log metrics."""
        # Call parent aggregate_fit
        aggregated = super().aggregate_fit(server_round, results, failures)
        
        if aggregated is not None:
            # Log round metrics
            accuracies = [r.metrics["accuracy"] for _, r in results]
            avg_accuracy = np.mean(accuracies)
            
            self.round_metrics.append({
                "round": server_round,
                "avg_train_accuracy": avg_accuracy,
                "num_clients": len(results),
                "failures": len(failures)
            })
            
            print(f"\n[Server] Round {server_round} complete:")
            print(f"  - Clients participated: {len(results)}")
            print(f"  - Average training accuracy: {avg_accuracy:.4f}")
            
        return aggregated
    
    def aggregate_evaluate(
        self,
        server_round: int,
        results,
        failures,
    ):
        """Aggregate evaluation results."""
        if not results:
            return None, {}
        
        # Calculate weighted average accuracy
        total_samples = sum([num_samples for _, num_samples, _ in results])
        weighted_acc = sum([
            num_samples * metrics["accuracy"] 
            for _, num_samples, metrics in results
        ]) / total_samples
        
        print(f"[Server] Round {server_round} evaluation:")
        print(f"  - Weighted accuracy: {weighted_acc:.4f}")
        
        return super().aggregate_evaluate(server_round, results, failures)
    
    def save_metrics(self, filepath: str):
        """Save round metrics to file."""
        with open(filepath, 'w') as f:
            json.dump(self.round_metrics, f, indent=2)


def create_strategy(
    initial_parameters=None,
    fraction_fit: float = 1.0,
    fraction_evaluate: float = 1.0,
) -> VulnerabilityDetectionStrategy:
    """
    Create FL strategy with custom configuration.
    
    Args:
        initial_parameters: Initial model weights
        fraction_fit: Fraction of clients for training
        fraction_evaluate: Fraction of clients for evaluation
    
    Returns:
        Configured strategy
    """
    # Get initial model parameters if not provided
    if initial_parameters is None:
        model = create_model(TFIDF_MAX_FEATURES)
        initial_parameters = fl.common.ndarrays_to_parameters(
            get_model_weights(model)
        )
    
    strategy = VulnerabilityDetectionStrategy(
        fraction_fit=fraction_fit,
        fraction_evaluate=fraction_evaluate,
        min_fit_clients=MIN_FIT_CLIENTS,
        min_evaluate_clients=MIN_EVALUATE_CLIENTS,
        min_available_clients=MIN_AVAILABLE_CLIENTS,
        initial_parameters=initial_parameters,
        evaluate_metrics_aggregation_fn=weighted_average,
    )
    
    return strategy


def run_server(strategy: VulnerabilityDetectionStrategy, num_rounds: int = NUM_ROUNDS):
    """
    Start the FL server.
    
    Args:
        strategy: FL aggregation strategy
        num_rounds: Number of federated rounds
    """
    print(f"\n{'='*60}")
    print(f" FEDERATED LEARNING SERVER")
    print(f"{'='*60}")
    print(f"Rounds: {num_rounds}")
    print(f"Min clients for fit: {MIN_FIT_CLIENTS}")
    print(f"Min clients for evaluate: {MIN_EVALUATE_CLIENTS}")
    print(f"{'='*60}\n")
    
    # Start server
    fl.server.start_server(
        server_address="0.0.0.0:8080",
        config=fl.server.ServerConfig(num_rounds=num_rounds),
        strategy=strategy,
    )
    
    # Save metrics after training
    metrics_path = os.path.join(RESULTS_DIR, "fl_training_metrics.json")
    strategy.save_metrics(metrics_path)
    print(f"\nMetrics saved to: {metrics_path}")


if __name__ == "__main__":
    print("Creating FL Strategy...")
    strategy = create_strategy()
    print("Strategy created successfully!")
    print("\nTo start the server, run: fl.server.start_server(...)")
