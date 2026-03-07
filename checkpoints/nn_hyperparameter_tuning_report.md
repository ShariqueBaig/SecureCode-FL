# Neural Network Hyperparameter Tuning Report

**Date:** 2025-12-10 16:07:57

## Executive Summary

- **Total Configurations Tested:** 500
- **Dataset Size:** 471 samples
- **Features:** 2000 (TF-IDF)
- **Cross-Validation:** 5-Fold Stratified

## Hyperparameter Grid

| Parameter | Values | Count |
|-----------|--------|-------|
| Architectures | 5 variants | 5 |
| Learning Rates | [0.0001, 0.0005, 0.001, 0.005, 0.01] | 5 |
| Dropout Configs | 4 variants | 4 |
| L2 Penalties | [0.0, 0.0005, 0.001, 0.005, 0.01] | 5 |
| **Total Combinations** | - | **500** |

## Top 20 Results

| Rank | Accuracy | Std | Architecture | Learning Rate | Dropout | L2 |
|------|----------|-----|--------------|---------------|---------|-----|
| 1 | 93.84% | ±1.83% | 