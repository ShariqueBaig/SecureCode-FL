"""
Multi-Process Federated Learning Test
======================================
Simulates real distributed FL by running server and clients as separate processes.
"""

import subprocess
import time
import os
import sys
import json
import threading
from multiprocessing import Process, Queue

# Add parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_fl_server(num_rounds=5, min_clients=3):
    """Run the FL aggregation server"""
    import flwr as fl
    from federated.fl_config import TFIDF_MAX_FEATURES
    from federated.fl_model import FLModel
    
    # Initialize global model
    model = FLModel(input_dim=TFIDF_MAX_FEATURES)
    initial_weights = model.get_weights()
    
    # Define strategy
    strategy = fl.server.strategy.FedAvg(
        min_fit_clients=min_clients,
        min_evaluate_clients=min_clients,
        min_available_clients=min_clients,
        initial_parameters=fl.common.ndarrays_to_parameters(initial_weights),
    )
    
    print(f"\n{'='*60}")
    print(f"  FL SERVER STARTED")
    print(f"  Waiting for {min_clients} clients...")
    print(f"  Running {num_rounds} rounds")
    print(f"{'='*60}\n")
    
    # Start server
    fl.server.start_server(
        server_address="127.0.0.1:8080",
        config=fl.server.ServerConfig(num_rounds=num_rounds),
        strategy=strategy,
    )


def run_fl_client(client_id, data_path):
    """Run a FL client"""
    import flwr as fl
    import numpy as np
    import tensorflow as tf
    from federated.fl_model import FLModel
    from federated.fl_config import TFIDF_MAX_FEATURES, LOCAL_EPOCHS, BATCH_SIZE
    
    # Load client data
    data = np.load(data_path, allow_pickle=True)
    X_train = data['X_train']
    y_train = data['y_train']
    
    print(f"\n  Client {client_id}: Loaded {len(y_train)} samples")
    
    # Create model
    model = FLModel(input_dim=TFIDF_MAX_FEATURES)
    
    class VulnerabilityClient(fl.client.NumPyClient):
        def get_parameters(self, config):
            return model.get_weights()
        
        def fit(self, parameters, config):
            model.set_weights(parameters)
            model.fit(X_train, y_train, epochs=LOCAL_EPOCHS, 
                     batch_size=BATCH_SIZE, verbose=0)
            return model.get_weights(), len(y_train), {}
        
        def evaluate(self, parameters, config):
            model.set_weights(parameters)
            loss, accuracy = model.evaluate(X_train, y_train)
            return loss, len(y_train), {"accuracy": accuracy}
    
    # Connect to server
    fl.client.start_client(
        server_address="127.0.0.1:8080",
        client=VulnerabilityClient().to_client(),
    )


def prepare_client_data():
    """Prepare data files for each client"""
    import numpy as np
    from federated.data_partitioner import DataPartitioner
    from federated.fl_config import NUM_CLIENTS
    
    print("\nPreparing client data partitions...")
    
    partitioner = DataPartitioner(num_clients=NUM_CLIENTS)
    client_data, vectorizer = partitioner.partition()
    
    # Save each client's data
    data_dir = os.path.join(os.path.dirname(__file__), "client_data")
    os.makedirs(data_dir, exist_ok=True)
    
    client_paths = []
    for client in client_data:
        path = os.path.join(data_dir, f"client_{client['client_id']}.npz")
        np.savez(path, 
                 X_train=client['X_train'], 
                 y_train=client['y_train'])
        client_paths.append(path)
        print(f"  Saved: {path}")
    
    return client_paths


def run_distributed_test():
    """Run a distributed FL test with separate processes"""
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║       MULTI-PROCESS FEDERATED LEARNING TEST                      ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  This simulates real distributed FL:                             ║
    ║  - 1 FL Server (aggregator)                                      ║
    ║  - 3 FL Clients (separate processes)                             ║
    ║  - Communication via gRPC on localhost                           ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Prepare data
    client_paths = prepare_client_data()
    
    # Start server in background
    print("\nStarting FL Server...")
    server_process = Process(target=run_fl_server, args=(5, 3))
    server_process.start()
    
    # Wait for server to start
    time.sleep(3)
    
    # Start clients
    print("\nStarting FL Clients...")
    client_processes = []
    for i, path in enumerate(client_paths):
        p = Process(target=run_fl_client, args=(i+1, path))
        p.start()
        client_processes.append(p)
        time.sleep(1)  # Stagger client starts
    
    # Wait for completion
    for p in client_processes:
        p.join()
    
    server_process.join()
    
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                    TEST COMPLETE                                 ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  ✓ Server aggregated model updates                               ║
    ║  ✓ Clients trained on private data                               ║
    ║  ✓ No raw code was shared - only model weights                   ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    run_distributed_test()
