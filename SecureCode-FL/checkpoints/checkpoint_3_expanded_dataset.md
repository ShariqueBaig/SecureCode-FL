# Checkpoint 3: Neural Networks on Expanded Dataset

Date: 2025-12-02 15:42:28

## Dataset Expansion Summary

| Metric | Value |
|--------|-------|
| Original samples | 60 |
| Expanded samples | 471 |
| Increase | 411 (685%) |
| TF-IDF Features | 2000 |

## Model Results (5-Fold CV)

| Model | Accuracy | Std Dev |
|-------|----------|----------|
| MLP_v3 | 93.4% | ±1.4% |
| MLP_v2 | 92.6% | ±1.8% |
| MLP_v1 | 92.6% | ±2.6% |

## Best Model: MLP_v3 - 93.4%

## Comparison with 60-Sample Results

| Metric | 60 samples | 471 samples |
|--------|------------|-------------|
| Best Accuracy | 63.3% (LSTM) | 93.4% (MLP_v3) |
| Improvement | - | +30.1% |

## Key Findings

1. Dataset expansion from 60 to 471 samples significantly improved accuracy
2. Best model: MLP_v3 with 93.4% accuracy
3. MLP with TF-IDF features shows strong performance for code classification
4. Model is now suitable for Federated Learning implementation

## Next Steps

1. Implement Federated Learning using Flower framework
2. Simulate multiple clients for distributed training
3. Evaluate FL performance vs centralized training
