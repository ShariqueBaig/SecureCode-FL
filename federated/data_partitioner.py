"""
Data Partitioner for Federated Learning
=======================================

Splits the dataset across multiple clients simulating different organizations.
Supports both IID and Non-IID distributions.
"""

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
import os

from fl_config import (
    DATA_DIR, NUM_CLIENTS, DATA_DISTRIBUTION, 
    CLASSES_PER_CLIENT, TFIDF_MAX_FEATURES, RANDOM_STATE
)

np.random.seed(RANDOM_STATE)


class DataPartitioner:
    """
    Partitions dataset across federated clients.
    
    Simulates organizations with different code repositories.
    """
    
    def __init__(self, num_clients=NUM_CLIENTS, distribution=DATA_DISTRIBUTION):
        self.num_clients = num_clients
        self.distribution = distribution
        self.vectorizer = None
        self.df = None
        
    def load_data(self):
        """Load the expanded dataset"""
        csv_path = os.path.join(DATA_DIR, "expanded_dataset_v2.csv")
        self.df = pd.read_csv(csv_path)
        
        # FIXED: Match main training encoding: Error = 1 (Vulnerable), Good = 0 (Secure)
        self.df['label'] = self.df['Result'].map({'Error': 1, 'Good': 0})
        
        print(f"Loaded dataset: {len(self.df)} samples")
        print(f"Vulnerability types: {self.df['Primary Vulnerability'].nunique()}")
        print(f"Label distribution: Vulnerable={sum(self.df['label']==1)}, Secure={sum(self.df['label']==0)}")
        
        return self.df
    
    def create_tfidf_features(self):
        """Create TF-IDF features for all data"""
        self.vectorizer = TfidfVectorizer(
            max_features=TFIDF_MAX_FEATURES,
            ngram_range=(1, 2),
            stop_words=None
        )
        
        X = self.vectorizer.fit_transform(self.df['Code'].values).toarray()
        y = self.df['label'].values
        
        return X, y
    
    def partition_iid(self, X, y):
        """
        IID Partitioning: Random split across clients.
        Each client gets a random subset of the data.
        """
        indices = np.random.permutation(len(X))
        split_indices = np.array_split(indices, self.num_clients)
        
        client_data = []
        for i, client_indices in enumerate(split_indices):
            client_X = X[client_indices]
            client_y = y[client_indices]
            client_data.append({
                'client_id': i,
                'X_train': client_X,
                'y_train': client_y,
                'num_samples': len(client_y),
                'class_distribution': {
                    'vulnerable': int((client_y == 1).sum()),
                    'secure': int((client_y == 0).sum())
                }
            })
            
        return client_data
    
    def partition_non_iid(self, X, y):
        """
        Non-IID Partitioning: Each client specializes in certain vulnerability types.
        
        This simulates real-world scenarios where:
        - Company A works mostly on authentication code
        - Company B works mostly on data validation code
        - Company C works mostly on API security code
        """
        # Get vulnerability types
        vuln_types = self.df['Primary Vulnerability'].unique()
        
        # Shuffle vulnerability types
        np.random.shuffle(vuln_types)
        
        # Assign vulnerability types to clients
        # Each client gets CLASSES_PER_CLIENT types (with overlap allowed)
        client_vuln_mapping = []
        for i in range(self.num_clients):
            # Circular assignment with overlap
            start_idx = (i * CLASSES_PER_CLIENT) % len(vuln_types)
            client_vulns = []
            for j in range(CLASSES_PER_CLIENT):
                idx = (start_idx + j) % len(vuln_types)
                client_vulns.append(vuln_types[idx])
            client_vuln_mapping.append(client_vulns)
        
        # Create client datasets
        client_data = []
        for i in range(self.num_clients):
            # Get indices for this client's vulnerability types
            mask = self.df['Primary Vulnerability'].isin(client_vuln_mapping[i])
            client_indices = self.df[mask].index.values
            
            # Add some random samples from other types for diversity (10%)
            other_indices = self.df[~mask].index.values
            num_other = max(1, len(client_indices) // 10)
            if len(other_indices) > 0:
                random_other = np.random.choice(other_indices, 
                                                min(num_other, len(other_indices)), 
                                                replace=False)
                client_indices = np.concatenate([client_indices, random_other])
            
            np.random.shuffle(client_indices)
            
            client_X = X[client_indices]
            client_y = y[client_indices]
            
            client_data.append({
                'client_id': i,
                'X_train': client_X,
                'y_train': client_y,
                'num_samples': len(client_y),
                'vulnerability_types': client_vuln_mapping[i],
                'class_distribution': {
                    'vulnerable': int((client_y == 1).sum()),
                    'secure': int((client_y == 0).sum())
                }
            })
        
        return client_data
    
    def partition(self):
        """Main partitioning method"""
        print(f"\n{'='*60}")
        print(f" DATA PARTITIONING: {self.distribution.upper()} Distribution")
        print(f"{'='*60}")
        
        # Load and prepare data
        self.load_data()
        X, y = self.create_tfidf_features()
        
        print(f"\nFeature shape: {X.shape}")
        print(f"Total samples: {len(y)}")
        print(f"Vulnerable: {(y == 1).sum()}, Secure: {(y == 0).sum()}")
        
        # Partition based on distribution type
        if self.distribution == 'iid':
            client_data = self.partition_iid(X, y)
        else:
            client_data = self.partition_non_iid(X, y)
        
        # Print partition summary
        print(f"\n{'-'*60}")
        print(f" CLIENT DATA DISTRIBUTION")
        print(f"{'-'*60}")
        
        for client in client_data:
            print(f"\nClient {client['client_id']}:")
            print(f"  Samples: {client['num_samples']}")
            print(f"  Vulnerable: {client['class_distribution']['vulnerable']}")
            print(f"  Secure: {client['class_distribution']['secure']}")
            if 'vulnerability_types' in client:
                print(f"  Specialization: {client['vulnerability_types'][:3]}...")
        
        return client_data, self.vectorizer
    
    def create_test_set(self, X, y, test_size=0.2):
        """Create a held-out test set for global evaluation"""
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=RANDOM_STATE, stratify=y
        )
        return X_test, y_test


def main():
    """Test the data partitioner"""
    partitioner = DataPartitioner(num_clients=3, distribution='non_iid')
    client_data, vectorizer = partitioner.partition()
    
    print(f"\n{'='*60}")
    print(f" PARTITIONING COMPLETE")
    print(f"{'='*60}")
    print(f"Number of clients: {len(client_data)}")
    print(f"TF-IDF vocabulary size: {len(vectorizer.vocabulary_)}")
    
    return client_data, vectorizer


if __name__ == "__main__":
    client_data, vectorizer = main()
