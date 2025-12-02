# Phase 2 Checkpoint: Neural Network Conversion

## Date: December 2, 2025

---

## Goal

Convert from Tree-based models to Neural Networks for Federated Learning compatibility.

### Why This Conversion is Necessary

> **Critical Insight**: Federated Learning cannot work with Tree-based models (Random Forest, Extra Trees, XGBoost) because you cannot mathematically average decision trees. FL requires gradient-based models where weights can be aggregated using the FedAvg algorithm.

---

## Neural Network Architectures Tested

### Architecture A: Multi-Layer Perceptron (MLP)

**Input**: TF-IDF features (1000 dimensions)

```
Input(1000) → Dense(256) → BatchNorm → Dropout(0.3)
           → Dense(128) → BatchNorm → Dropout(0.3)
           → Dense(64) → Dropout(0.2)
           → Dense(32) → Dense(1, sigmoid)
```

### Architecture B: LSTM

**Input**: Token sequences (150 length, 562 vocab)

```
Embedding(562, 128) → LSTM(64, return_sequences=True) → Dropout(0.3)
                    → LSTM(32) → Dropout(0.3)
                    → Dense(32) → Dense(1, sigmoid)
```

### Architecture C: Bidirectional LSTM

```
Embedding(562, 128) → BiLSTM(64, return_sequences=True) → Dropout(0.3)
                    → BiLSTM(32) → Dropout(0.3)
                    → Dense(32) → Dense(1, sigmoid)
```

### Architecture D: 1D CNN

```
Embedding(562, 128) → Conv1D(64, 3) → MaxPool(2)
                    → Conv1D(32, 3) → MaxPool(2)
                    → Conv1D(16, 3) → GlobalMaxPool
                    → Dense(64) → Dropout(0.3)
                    → Dense(32) → Dense(1, sigmoid)
```

---

## Results (5-Fold Cross-Validation)

| Model      | Mean Accuracy | Std Dev | Fold Scores               |
| ---------- | ------------- | ------- | ------------------------- |
| **LSTM**   | **63.3%** ⭐  | ±10.0%  | [50%, 75%, 58%, 75%, 58%] |
| **BiLSTM** | **63.3%**     | ±10.0%  | [50%, 75%, 58%, 75%, 58%] |
| MLP_Small  | 55.0%         | ±19.4%  | [50%, 50%, 33%, 50%, 92%] |
| CNN        | 55.0%         | ±11.3%  | [42%, 50%, 58%, 75%, 50%] |
| MLP        | 53.3%         | ±16.3%  | [50%, 50%, 33%, 50%, 83%] |

### Best Neural Network

- **Model**: LSTM / BiLSTM
- **Accuracy**: 63.3% (±10.0%)

---

## Comparison with Baselines

| Model Type     | Best Model        | Accuracy  | FL Compatible |
| -------------- | ----------------- | --------- | ------------- |
| Tree-based     | Gradient Boosting | **76.7%** | ❌ NO         |
| Neural Network | LSTM              | 63.3%     | ✅ YES        |
| Thesis Target  | Extra Trees       | 83.3%     | ❌ NO         |

### Performance Gap

- **Tree-based → Neural Network**: -13.4% (76.7% → 63.3%)
- **This gap is expected** with only 60 samples
- Neural networks require more data to learn effectively

---

## Analysis

### Why Neural Networks Underperform on This Dataset

1. **Dataset Size**: Only 60 samples is extremely small for neural networks

   - Tree-based models handle small datasets better
   - NNs need thousands of samples to learn effectively

2. **High Variance**: ±10-20% standard deviation shows instability

   - Each fold has only 12 samples
   - 1 misclassification = 8.3% accuracy change

3. **Overfitting Risk**: Models quickly overfit on training data
   - Early stopping triggered within 16-20 epochs
   - Validation loss never improved significantly

### Key Observations

1. **Sequence models (LSTM) outperform MLP** on code data

   - Code has sequential structure that LSTM captures
   - TF-IDF loses sequential information

2. **MLP shows highest variance** (±19.4%)

   - Some folds achieve 92%, others 33%
   - Very unstable with small data

3. **CNN underperforms** on this task
   - May need more data to learn local patterns

---

## Model Artifacts Saved

| File                               | Description                   | Size    |
| ---------------------------------- | ----------------------------- | ------- |
| `mlp_vulnerability_detector.keras` | Final MLP model               | ~1.5 MB |
| `tokenizer.pkl`                    | Tokenizer for sequence models | ~50 KB  |

---

## Recommendations for Phase 3 (Federated Learning)

### Option A: Proceed with Current Model

- Use LSTM (63.3% accuracy) for FL implementation
- Accept lower accuracy as trade-off for privacy
- FL aggregation may improve accuracy over time

### Option B: Expand Dataset First (Recommended)

- Current 60 samples is insufficient
- Target: 500-1000 samples minimum
- Options:
  1. Generate synthetic vulnerable code
  2. Use public vulnerability datasets (CVE, NVD)
  3. Augment existing samples with variations

### Option C: Use Transfer Learning

- Use pre-trained code models (CodeBERT, CodeT5)
- Fine-tune on vulnerability task
- Requires: PyTorch, Transformers library

---

## Files Created in Phase 2

```
SecureCode-FL/
├── neural_network_models.py    # NN architectures and training
├── models/
│   └── neural_networks/
│       ├── mlp_vulnerability_detector.keras
│       └── tokenizer.pkl
└── results/
    └── neural_network_results.csv
```

---

## Conclusion

**Phase 2 Status**: ✅ COMPLETED with caveats

### What We Achieved

- [x] Converted tree-based models to FL-compatible neural networks
- [x] Tested 5 different architectures (MLP, MLP_Small, LSTM, BiLSTM, CNN)
- [x] Best NN: LSTM at 63.3% accuracy
- [x] Saved models in portable format

### What We Learned

- Neural networks need more data than 60 samples
- LSTM captures code structure better than MLP
- Trade-off: FL compatibility vs accuracy

### Decision Point

Before Phase 3 (Federated Learning), we should:

1. **Expand dataset** to improve base accuracy
2. **Or** proceed with 63.3% accuracy and improve via FL

---

## Next Steps

**Phase 3: Federated Learning Implementation**

- Framework: Flower (flwr)
- Algorithm: FedAvg
- Simulate: Multiple organizations with local data
