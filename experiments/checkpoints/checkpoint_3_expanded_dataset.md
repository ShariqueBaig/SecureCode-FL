# Checkpoint 3: Neural Networks on Expanded Dataset

Date: 2026-06-25 18:04:45

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
| MLP_v3 | 93.2% | ±1.8% |
| MLP_v1 | 92.8% | ±2.7% |
| MLP_v2 | 92.2% | ±3.0% |

## Best Model: MLP_v3 - 93.2%

## Comparison with 60-Sample Results

| Metric | 60 samples | 471 samples |
|--------|------------|-------------|
| Best Accuracy | 63.3% (LSTM) | 93.2% (MLP_v3) |
| Improvement | - | +29.9% |

## Key Findings

1. Dataset expansion from 60 to 471 samples significantly improved accuracy
2. Best model: MLP_v3 with 93.2% accuracy
3. MLP with TF-IDF features shows strong performance for code classification
4. Model is now suitable for Federated Learning implementation

## Next Steps

1. Implement Federated Learning using Flower framework
2. Simulate multiple clients for distributed training
3. Evaluate FL performance vs centralized training
