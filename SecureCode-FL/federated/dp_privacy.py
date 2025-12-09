"""
Differential Privacy for Federated Learning
=============================================

Implements Differentially Private Stochastic Gradient Descent (DP-SGD).
Adds Gaussian noise to model weights before aggregation to protect privacy.
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass


@dataclass
class DPConfig:
    """Configuration for Differential Privacy."""
    epsilon: float = 1.0  # Privacy budget (smaller = more private, less accurate)
    delta: float = 1e-5   # Probability of privacy breach (typically 1/N)
    noise_type: str = 'gaussian'  # Type of noise: 'gaussian' or 'laplace'
    clip_norm: float = 1.0  # Gradient clipping norm


class DifferentialPrivacyMechanism:
    """
    Implements Gaussian Differential Privacy mechanism for FL updates.
    
    Theory:
    - For each client update, add Gaussian noise N(0, σ²)
    - σ = C * sqrt(2 * log(1.25/δ)) / ε
    - Where C = gradient clipping norm, ε = privacy budget
    - Smaller ε = more noise = more private but less accurate
    """
    
    def __init__(self, config: DPConfig):
        """
        Initialize DP mechanism.
        
        Args:
            config: DPConfig with privacy parameters
        """
        self.config = config
        self.sigma = self._calculate_sigma()
        
        print(f"\n[DP MECHANISM]")
        print(f"  Epsilon: {self.config.epsilon}")
        print(f"  Delta: {self.config.delta}")
        print(f"  Noise Std Dev: {self.sigma:.6f}")
    
    def _calculate_sigma(self) -> float:
        """
        Calculate noise standard deviation for Gaussian mechanism.
        
        Based on moments accountant analysis:
        σ = C * sqrt(2 * log(1.25/δ)) / ε
        """
        import math
        
        numerator = self.config.clip_norm * math.sqrt(2 * math.log(1.25 / self.config.delta))
        sigma = numerator / self.config.epsilon
        
        return sigma
    
    def add_noise(self, weights: List[np.ndarray]) -> List[np.ndarray]:
        """
        Add Gaussian noise to model weights.
        
        Args:
            weights: List of numpy arrays (model weights)
        
        Returns:
            Noisy weights
        """
        noisy_weights = []
        
        for weight_matrix in weights:
            # Add Gaussian noise with σ calculated above
            noise = np.random.normal(
                loc=0,
                scale=self.sigma,
                size=weight_matrix.shape
            )
            noisy_weight = weight_matrix + noise
            noisy_weights.append(noisy_weight)
        
        return noisy_weights
    
    def clip_gradient(self, gradient: np.ndarray) -> np.ndarray:
        """
        Clip gradient to bounded norm.
        
        Args:
            gradient: Gradient array
        
        Returns:
            Clipped gradient
        """
        norm = np.linalg.norm(gradient)
        if norm > self.config.clip_norm:
            gradient = gradient * (self.config.clip_norm / norm)
        
        return gradient
    
    def add_laplace_noise(self, weights: List[np.ndarray]) -> List[np.ndarray]:
        """
        Add Laplace noise (alternative to Gaussian).
        
        Args:
            weights: List of numpy arrays
        
        Returns:
            Laplace-noisy weights
        """
        laplace_sigma = self.config.clip_norm / self.config.epsilon
        laplace_weights = []
        
        for weight_matrix in weights:
            noise = np.random.laplace(
                loc=0,
                scale=laplace_sigma,
                size=weight_matrix.shape
            )
            noisy_weight = weight_matrix + noise
            laplace_weights.append(noisy_weight)
        
        return laplace_weights


class PrivacyAnalyzer:
    """
    Analyzes privacy guarantees and privacy-accuracy trade-offs.
    """
    
    @staticmethod
    def compose_epsilons(epsilons: List[float]) -> float:
        """
        Compose privacy budgets over multiple rounds.
        
        For sequential composition:
        ε_total = sum(ε_i) for independent mechanisms
        
        Args:
            epsilons: List of epsilon values per round
        
        Returns:
            Total epsilon
        """
        return sum(epsilons)
    
    @staticmethod
    def estimate_privacy_loss(
        epsilon: float,
        delta: float,
        num_rounds: int
    ) -> Dict[str, float]:
        """
        Estimate privacy loss after multiple FL rounds.
        
        Args:
            epsilon: Privacy budget per round
            delta: Failure probability per round
            num_rounds: Number of FL rounds
        
        Returns:
            Dictionary with privacy metrics
        """
        import math
        
        # Sequential composition
        total_epsilon = epsilon * math.sqrt(2 * num_rounds * math.log(1 / delta))
        
        return {
            'epsilon_per_round': epsilon,
            'delta_per_round': delta,
            'num_rounds': num_rounds,
            'total_epsilon': total_epsilon,
            'privacy_guarantee': f'({total_epsilon:.4f}, {delta})-DP'
        }
    
    @staticmethod
    def privacy_budget_breakdown(epsilon: float, num_clients: int) -> Dict:
        """
        Show how privacy budget distributes across clients.
        
        Args:
            epsilon: Total privacy budget
            num_clients: Number of clients
        
        Returns:
            Dictionary with per-client budgets
        """
        per_client = epsilon / num_clients
        
        return {
            'total_epsilon': epsilon,
            'num_clients': num_clients,
            'epsilon_per_client': per_client,
            'privacy_level': 'Strong' if epsilon < 1.0 else 'Moderate' if epsilon < 5.0 else 'Weak'
        }


class DPFLClient:
    """
    Federated Learning client with Differential Privacy.
    
    Workflow:
    1. Receive global model from server
    2. Train locally on private data
    3. Compute model updates (deltas)
    4. ADD NOISE to updates (DP)
    5. Send noisy updates to server (code never shared!)
    """
    
    def __init__(self, client_id: int, dp_config: DPConfig):
        """
        Initialize DP-FL client.
        
        Args:
            client_id: Unique client identifier
            dp_config: Differential Privacy configuration
        """
        self.client_id = client_id
        self.dp_config = dp_config
        self.dp_mechanism = DifferentialPrivacyMechanism(dp_config)
        
        print(f"[Client {client_id}] Initialized with DP (ε={dp_config.epsilon})")
    
    def compute_update_with_dp(
        self,
        global_weights: List[np.ndarray],
        local_weights: List[np.ndarray]
    ) -> List[np.ndarray]:
        """
        Compute model update with DP noise added.
        
        Args:
            global_weights: Weights from server
            local_weights: Weights after local training
        
        Returns:
            Noisy weight updates (safe to send)
        """
        # Calculate delta weights (updates)
        deltas = []
        for local, global_w in zip(local_weights, global_weights):
            delta = local - global_w
            deltas.append(delta)
        
        # Clip gradients for DP
        clipped_deltas = [
            self.dp_mechanism.clip_gradient(delta) for delta in deltas
        ]
        
        # Add DP noise
        noisy_deltas = self.dp_mechanism.add_noise(clipped_deltas)
        
        return noisy_deltas
    
    def get_privacy_guarantee(self) -> str:
        """Get privacy guarantee for this client."""
        return f"({self.dp_config.epsilon}, {self.dp_config.delta})-Differentially Private"


def create_epsilon_schedule(num_rounds: int, target_epsilon: float) -> List[float]:
    """
    Create epsilon schedule across FL rounds.
    
    Uniform budget: each round gets equal epsilon.
    
    Args:
        num_rounds: Total number of rounds
        target_epsilon: Total privacy budget
    
    Returns:
        List of epsilon values per round
    """
    return [target_epsilon / num_rounds] * num_rounds
