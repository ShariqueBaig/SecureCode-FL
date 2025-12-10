# SecureCode-FL: Complete Project Phases Reference Guide

**Last Updated:** December 10, 2025  
**Purpose:** Comprehensive reference for all research phases - use this when switching contexts or models  
**Status:** Phases 1-4 Complete ✅ | Phases 5-6 In Progress 🔄

---

## Table of Contents

1. [Quick Phase Overview](#quick-phase-overview)
2. [Phase 1: Baseline Reproduction](#phase-1-baseline-reproduction)
3. [Phase 2: Neural Network Conversion](#phase-2-neural-network-conversion)
4. [Phase 2.5: Dataset Expansion](#phase-25-dataset-expansion)
5. [Phase 3: Federated Learning](#phase-3-federated-learning)
6. [Phase 4: VS Code Extension & Feedback](#phase-4-vs-code-extension--feedback)
7. [Phase 5: XAI & Privacy](#phase-5-xai--privacy)
8. [Phase 6: Evaluation & Documentation](#phase-6-evaluation--documentation)
9. [Critical Data Fixes Applied](#critical-data-fixes-applied)
10. [Current Status & Next Steps](#current-status--next-steps)

---

## Quick Phase Overview

| Phase | Name | Status | Key Metric | Files Created | Time |
|-------|------|--------|-----------|----------------|------|
| **1** | Baseline Reproduction | ✅ DONE | 76.7% accuracy (Gradient Boosting) | 8 files | Dec 2 |
| **2** | Neural Network Conversion | ✅ DONE | 63.3% accuracy (LSTM) | 5 files | Dec 2 |
| **2.5** | Dataset Expansion | ✅ DONE | 471 samples, 93.4% accuracy (MLP) | 3 files | Dec 2 |
| **3** | Federated Learning | ✅ DONE | 84.2% accuracy (proper train/test) | 8 files | Dec 9 |
| **4** | VS Code Extension | ✅ DONE | Real-time diagnostics, <50ms latency | 5 files | Dec 2-3 |
| **5a** | Explainability (XAI) | 🔄 IN PROGRESS | SHAP analysis pending | - | TBD |
| **5b** | Privacy (Differential Privacy) | ⏳ PENDING | DP-SGD implementation | - | TBD |
| **6** | Evaluation & Documentation | ⏳ PENDING | Research paper finalization | - | TBD |

---

# PHASE 1: BASELINE REPRODUCTION

## Overview
Replicate the thesis results using the original 60-sample dataset as a "control group" to establish benchmark performance.

## ✅ WHAT WAS DONE

### 1.1: Data Preprocessing
- **Input:** `Previous/Unsecured Codes.xlsx` (60 samples: 30 secure, 30 vulnerable)
- **Process:** 
  - Whitespace normalization
  - TF-IDF vectorization with 1000 features
  - Unigrams + Bigrams
- **Output:** Feature matrix (60 × 1000)

### 1.2: Model Training
Six ML models trained with 5-Fold Cross-Validation:

| Model | Accuracy | Status |
|-------|----------|--------|
| **Gradient Boosting** | **76.7%** | ⭐ Best |
| XGBoost | 75.0% | - |
| Random Forest | 71.7% | - |
| Extra Trees | 70.0% | - |
| Logistic Regression | 35.0% | - |
| SVM | 26.7% | - |

### 1.3: XAI Analysis
Top features identified using SHAP:
- `is` (5.523) - Conditional checks
- `__main__ app` (1.113) - Flask pattern
- `json get` (1.037) - Data handling
- `request` (0.794) - API input
- `authorization` - Security keywords
- `token` - Authentication

## 📊 Key Finding
Small dataset (60 samples) causes high variance (±10-17%). Tree-based models outperform neural networks on small datasets.

## ⚠️ LIMITATION
❌ **Tree-based models NOT compatible with Federated Learning** - Cannot average decision trees mathematically. FedAvg requires gradient-based models.

---

# PHASE 2: NEURAL NETWORK CONVERSION

## Overview
Convert from tree-based models to neural networks to enable Federated Learning, despite performance loss on small dataset.

## ✅ WHAT WAS DONE

### 2.1: NN Architecture Testing
Five architectures tested on 60 samples:

| Architecture | Accuracy | Type | FL Compatible |
|--------------|----------|------|----------------|
| **LSTM** | **63.3%** | Sequential | ✅ YES |
| BiLSTM | 63.3% | Sequential | ✅ YES |
| MLP_Small | 55.0% | Dense | ✅ YES |
| CNN | 55.0% | Convolutional | ✅ YES |
| MLP | 53.3% | Dense | ✅ YES |

### 2.2: Model Serialization
- **Best Model:** LSTM (63.3% accuracy ±10%)
- **Format:** `.keras` (Keras native format)
- **Size:** ~1.5 MB (portable for edge)
- **Tokenizer:** Saved as `.pkl` (50 KB)

## 📊 Key Tradeoff
- **Performance Loss:** 76.7% (GB) → 63.3% (LSTM) = **-13.4%**
- **Gain:** FL compatibility ✅
- **Reason:** Small dataset insufficient for deep learning

## ⚠️ PROBLEM IDENTIFIED
Neural networks underperformed on 60 samples. Recommended **Phase 2.5: Dataset Expansion** before full FL implementation.

---

# PHASE 2.5: DATASET EXPANSION

## Overview
Generate synthetic dataset from OWASP templates to improve neural network performance.

## ✅ WHAT WAS DONE

### 2.5.1: Synthetic Data Generation
Generated code samples covering OWASP API Security Top 10:

| Vulnerability Category | Samples |
|------------------------|---------|
| Unsafe API Consumption (SQL/Command Injection) | 117 |
| Security Misconfiguration | 108 |
| Broken Object Level Authorization | 55 |
| Broken Authentication | 49 |
| Server Side Request Forgery | 23 |
| Unrestricted Access to Business Flows | 23 |
| Broken Object Property Level Authorization | 23 |
| Broken Function Level Authorization | 23 |
| Improper Inventory Management | 22 |
| Unrestricted Resource Consumption | 22 |
| **TOTAL** | **471** |

### 2.5.2: Dataset Summary
| Metric | Value |
|--------|-------|
| Total Samples | **471** |
| Vulnerable (Class 1) | 233 (49.5%) |
| Secure (Class 0) | 238 (50.5%) |
| Balance Ratio | 0.98 (well-balanced) |
| Languages | Python |
| Frameworks | Flask, Django, FastAPI |

### 2.5.3: Neural Network Retraining
5-Fold Cross-Validation on expanded dataset:

| Model | Accuracy | Std Dev | Improvement |
|-------|----------|---------|------------|
| **MLP_v3 (L2)** | **93.4%** | ±1.4% | +40.1% |
| MLP_v2 (Deeper) | 92.6% | ±1.8% | - |
| MLP_v1 | 92.6% | ±2.6% | - |

### 2.5.4: Best Model Architecture
```
Input (2000 TF-IDF features)
    ↓
Dense(256, ReLU) + L2(0.001) + BatchNorm + Dropout(0.4)
    ↓
Dense(128, ReLU) + L2(0.001) + BatchNorm + Dropout(0.3)
    ↓
Dense(64, ReLU) + Dropout(0.2)
    ↓
Dense(1, Sigmoid) → Binary Classification
```

**Training:** Adam(lr=0.001), Binary Cross-Entropy loss

## 📊 Key Success Metrics
- **Accuracy:** +30.1% improvement (63.3% → 93.4%)
- **Variance:** Reduced from ±10% to ±1.4%
- **Result:** Dataset size **massively impacts** NN performance

## 📁 Files Created
- `dataset_expansion.py` - OWASP vulnerability generators
- `dataset_expansion_v2.py` - Additional patterns
- `data/expanded_dataset_v2.csv` - Final 471-sample dataset
- Training notebooks for v1, v2, v3 models

---

# PHASE 3: FEDERATED LEARNING IMPLEMENTATION

## Overview
Implement FedAvg algorithm for distributed training across 3 simulated clients without sharing source code.

## ✅ WHAT WAS DONE

### 3.1: Federated Framework Setup
- **Framework:** Flower (flwr) 1.24.0
- **Algorithm:** Federated Averaging (FedAvg)
- **Clients:** 3 simulated clients (non-IID distribution)
- **Rounds:** 20 training rounds
- **Local Epochs:** 3 epochs per round
- **Batch Size:** 32

### 3.2: Data Partitioning
**CRITICAL FIX APPLIED (Dec 9, 2025):**

#### The Problem
- Initial FL results showed **94.7% accuracy** (vs 89.4% centralized)
- Mathematical impossibility detected: **646 client samples from 471 total dataset**
- Root cause: Test data contaminated with training data

#### The Solution
1. **Split first** (80/20): 471 → 376 training + 95 test
2. **Partition second**: Only 376 training samples to clients
3. **Evaluate separately**: 95 test set completely isolated

#### Client Distribution (Training Set Only)
| Client | Samples | Vulnerable (1) | Secure (0) |
|--------|---------|---|---|
| Client 0 | 126 | 64 (50.8%) | 62 (49.2%) |
| Client 1 | 125 | 58 (46.4%) | 67 (53.6%) |
| Client 2 | 125 | 64 (51.2%) | 61 (48.8%) |
| **Total** | **376** | **186 (49.5%)** | **190 (50.5%)** |
| **Test (Held-Out)** | **95** | **47** | **48** |

### 3.3: Training Results
**20-Round Convergence:**

| Round | Accuracy | Notes |
|-------|----------|-------|
| 1 | 51.6% | Random initialization |
| 5 | 52.6% | Early training |
| 10 | 55.8% | Mid-training |
| 15 | 71.6% | Convergence begins |
| 20 | **84.2%** | Final accuracy |

### 3.4: Comparison Results
| Model | Accuracy | Dataset |
|-------|----------|---------|
| **Federated (3 clients, non-IID)** | **84.2%** | 376 training samples |
| **Centralized (pooled)** | **88.4%** | 376 training samples |
| **Difference** | **-4.2%** | Realistic tradeoff |

### 3.5: Error Analysis
**Confusion Matrix (95 test samples):**

|  | Predicted Vulnerable | Predicted Secure |
|---|---|---|
| **Actually Vulnerable** | 40 (TP) | 7 (FN) |
| **Actually Secure** | 8 (FP) | 40 (TN) |

- **Accuracy:** 80/95 = 84.2%
- **Vulnerable Recall:** 40/47 = 85.1%
- **Secure Precision:** 40/48 = 83.3%

## 📊 Key Findings
1. **Privacy Cost:** -4.2% accuracy gap is realistic for non-IID federated learning
2. **Data Leakage Prevention:** Critical to implement train/test split BEFORE partitioning
3. **Convergence:** Non-IID data causes variance but eventual convergence by round 20
4. **Non-IID Impact:** Different clients seeing different vulnerability types prevents overfitting

## 📁 Files Created
- `federated/fl_client.py` - Client implementation
- `federated/fl_server.py` - Server coordination
- `federated/fl_model.py` - Model definitions
- `federated/fl_simulation.py` - Local simulation (CORRECTED Dec 9)
- `federated/data_partitioner.py` - Non-IID partitioning
- `federated/test_distributed.py` - Integration tests
- `models/federated/fl_global_model.keras` - Trained FL model
- `results/federated/fl_comparison_*.json` - Results logs

## ⚠️ Critical Lesson Learned
**Data Leakage is Easy to Miss:** 94.7% accuracy "looked reasonable" but was 37% inflated due to hidden test contamination. Always verify sample counts mathematically!

---

# PHASE 4: VS CODE EXTENSION & USER FEEDBACK

## Overview
Create IDE integration for real-time vulnerability detection and implement human-in-the-loop feedback system for model improvement.

## ✅ WHAT WAS DONE

### 4.1: VS Code Extension
- **Framework:** VS Code Extension API (TypeScript)
- **Model:** Uses federated model from Phase 3 (84.2% accuracy)
- **Inference:** Flask-based API server

**Features Implemented:**
1. ✅ Real-time diagnostics (inline vulnerability warnings)
2. ✅ Code actions (quick fixes, feedback options)
3. ✅ Tree view (sidebar panel of all issues)
4. ✅ Context menu (right-click feedback)
5. ✅ Performance optimized (<50ms latency)

### 4.2: Inference Server
- **Framework:** Flask 2.0
- **Port:** 5000
- **Latency:** <50ms average (cache hit)
- **Memory:** ~150MB

**API Endpoints:**
```
POST /predict
  Input: Python code snippet
  Output: {
    "is_vulnerable": boolean,
    "confidence": float (0-1),
    "cwe_id": string,
    "start_line": int,
    "end_line": int
  }

POST /feedback
  Input: {
    "sample_id": string,
    "feedback_type": "false_positive" | "confirmed" | "manual",
    "code": string
  }
  Output: Success/error
```

### 4.3: User Feedback System
**Type 1: False Positive Feedback**
- User marks detection as incorrect
- Stores in SQLite database
- Used for fine-tuning (negative sample)

**Type 2: Confirmed Vulnerability**
- User confirms detection was correct
- Validates model prediction
- Improves confidence metrics

**Type 3: Manual Vulnerability**
- User identifies vulnerability not detected
- Adds to training corpus
- Creates positive sample for fine-tuning

**Storage:** SQLite database (`feedback.db`)
```sql
CREATE TABLE feedback (
  id INTEGER PRIMARY KEY,
  sample_id TEXT,
  code TEXT,
  feedback_type TEXT,
  timestamp DATETIME,
  user_id TEXT
);
```

### 4.4: Fine-Tuning Pipeline
**Challenge:** Feedback vectorizer outputs 1000 features, model expects 2000

**Solution:** Feature padding with zeros
```python
X_padded = np.concatenate([X_feedback, np.zeros((n, 1000))], axis=1)
```

**Result:** Preserves original weights while enabling incremental learning

### 4.5: Performance Metrics
| Metric | Value |
|--------|-------|
| Extension Load Time | <2 seconds |
| Average Latency (cold) | 45ms |
| Average Latency (cache) | <5ms |
| Cache Hit Rate | 78% |
| Server Memory | ~150MB |
| Model Size | 2.1 MB |

## 📁 Files Created
```
vscode-extension/
├── src/
│   ├── extension.ts      # Main extension entry
│   ├── scanner.ts        # Code analysis
│   ├── diagnostics.ts    # VS Code integration
│   ├── feedback.ts       # Feedback handling
│   ├── serverClient.ts   # API communication
│   └── feedbackManager.ts # Feedback storage
├── package.json
├── tsconfig.json
└── README.md

inference_server/
├── server.py            # Flask app
├── feedback.py          # Feedback endpoint
└── requirements.txt
```

---

# PHASE 5: EXPLAINABILITY & PRIVACY

## Overview
Add SHAP-based explainability for interpretable predictions and implement Differential Privacy for formal privacy guarantees.

## 5A: EXPLAINABILITY (XAI)

### Goal
Explain which code patterns led to vulnerability predictions using SHAP.

### Status
🔄 **IN PROGRESS** - test_xai_step5_1.py needs debugging (exit code 1)

### Planned Implementation
1. Train SHAP explainer on federated model
2. Generate feature importance rankings
3. Create visualization of top vulnerability patterns
4. Integrate explanations into VS Code extension

### Expected Outputs
- Feature importance for each prediction
- Local explanations (why this code is vulnerable)
- Global feature importance across all samples

## 5B: PRIVACY (DIFFERENTIAL PRIVACY)

### Goal
Add formal privacy guarantees using Differential Privacy.

### Status
⏳ **PENDING** - Planned after XAI completion

### Planned Implementation
1. **DP-SGD:** Add noise during local training
   - Clip gradients: norm ≤ C
   - Add Gaussian noise: N(0, σ²)
   - Configure privacy budget: ε, δ

2. **Privacy Accounting:** Track cumulative privacy loss
   - Moments accountant
   - Renyi differential privacy

3. **Privacy Hyperparameters:**
   ```python
   noise_multiplier = 1.5  # σ = C * noise_multiplier
   l2_norm_clip = 1.0      # Gradient clipping
   num_microbatches = 32   # For privacy amplification
   
   # After K rounds with N samples:
   epsilon, delta = compute_privacy_loss(K, N, noise_multiplier)
   ```

### Privacy-Utility Tradeoff
| Privacy (ε) | Expected Accuracy | Utility Loss |
|-------------|------------------|-------------|
| ∞ (No DP) | 84.2% | - |
| 10 | 83.8% | -0.4% |
| 5 | 82.5% | -1.7% |
| 1 | 78.2% | -6.0% |
| 0.1 | 70.5% | -13.7% |

---

# PHASE 6: EVALUATION & DOCUMENTATION

## Overview
Comprehensive evaluation and finalization of research paper.

### Status
⏳ **PENDING** - After Phase 5 completion

### Evaluation Framework
1. **Performance Metrics**
   - Detection accuracy
   - False positive rate
   - False negative rate
   - Precision, Recall, F1

2. **Privacy Analysis**
   - ε (epsilon) privacy budget
   - δ (delta) failure probability
   - Privacy-accuracy curves

3. **System Performance**
   - Inference latency
   - Model size
   - Memory usage
   - Extension performance

4. **Comparison Baselines**
   - Centralized learning
   - Distributed learning without privacy
   - Existing tools (SonarQube, CodeBERT)

### Research Paper Sections
1. ✅ **Phase 1-4:** COMPLETE (Updated Dec 10, 2025)
2. 🔄 **Phase 5 Results:** IN PROGRESS
3. ⏳ **Phase 6 Conclusion:** PENDING

---

# CRITICAL DATA FIXES APPLIED

## Dec 9, 2025: Federated Learning Train/Test Split Correction

### Issue Discovered
- Initial FL accuracy: 94.7% (seemed too high)
- Centralized baseline: 89.4%
- Implied improvement: +5.3%
- Mathematical check: 646 total client samples vs 471 total dataset = **IMPOSSIBLE**

### Root Cause Analysis
```
Original Code (WRONG):
├── Load 471 samples
├── Partition ALL 471 to 3 clients (TF-IDF vectorized)
└── Result: 646 client samples (646-471 = 175 extra = 37% duplicated)

Problem: Test set mixed with training data during partitioning
Result: Model training on its own test data = artificially high accuracy
```

### Fix Applied
```
Corrected Code (RIGHT):
├── Load 471 samples
├── Split 80/20 first: 376 train + 95 test
├── Partition ONLY 376 training samples to 3 clients
├── Keep 95 test completely separate
└── Result: 376 client samples (correct)

Verification: 376 + 95 = 471 ✅
```

### Results Updated
| Metric | Before (Wrong) | After (Correct) |
|--------|---|---|
| FL Accuracy | 94.7% ❌ | 84.2% ✅ |
| Centralized | 89.4% ⚠️ | 88.4% ✅ |
| Difference | +5.3% ❌ | -4.2% ✅ |
| Test Isolation | ❌ | ✅ |
| Paper Status | Invalid | Now Publishable |

### Research Paper Updated
All sections corrected:
- Abstract (84.2% vs 94.7%)
- Results section (new data leakage subsection)
- Discussion (privacy-accuracy tradeoff analysis)
- Conclusion (realistic findings)

### Lessons Learned for Other Projects
1. ✅ Always verify sample counts mathematically
2. ✅ Split train/test BEFORE partitioning to clients
3. ✅ Accuracy metrics alone can hide contamination
4. ✅ Non-IID federated learning overhead is REAL (not a bug)

---

# CURRENT STATUS & NEXT STEPS

## Completed ✅
- [x] Phase 1: Baseline Reproduction (76.7% accuracy)
- [x] Phase 2: Neural Network Conversion (63.3% accuracy, LSTM)
- [x] Phase 2.5: Dataset Expansion (471 samples, 93.4% accuracy)
- [x] Phase 3: Federated Learning (84.2% accuracy, proper train/test split)
- [x] Phase 4: VS Code Extension & Feedback System
- [x] Research Paper Phases 1-4 (Updated with corrections)

## In Progress 🔄
- [ ] Phase 5a: Explainability (SHAP) - test_xai_step5_1.py needs debugging
- [ ] Phase 5b: Privacy (Differential Privacy) - Planned

## Pending ⏳
- [ ] Phase 6: Evaluation & Final Documentation
- [ ] Final research paper submission

## Immediate Next Steps
1. **Debug test_xai_step5_1.py** (exit code 1)
   - Check model path (using corrected FL model)
   - Verify SHAP installation
   - Check data format compatibility

2. **Implement Phase 5b (DP-SGD)**
   - Use `tensorflow-privacy` library
   - Configure noise multiplier and clipping
   - Run privacy-accuracy tradeoff experiments

3. **Complete Phase 6**
   - Finalize all results tables
   - Write evaluation section
   - Submit research paper

---

## Quick Reference Commands

```bash
# Phase 3: Run Federated Learning Simulation
cd SecureCode-FL
python federated/fl_simulation.py

# Phase 4: Start Inference Server (for VS Code extension)
python inference_server/server.py

# Phase 5a: Run XAI Analysis
python test_xai_step5_1.py

# Phase 5b: Run with Differential Privacy (when ready)
python federated/fl_dp_simulation.py

# View latest FL results
cat results/federated/fl_comparison_*.json | tail -100
```

---

## Key Files by Phase

| Phase | Critical Files |
|-------|---|
| 1 | `main.py`, `config.py`, `data_preprocessing.py`, `cross_validation.py` |
| 2 | `neural_network_models.py`, `model_training.py` |
| 2.5 | `dataset_expansion_v2.py`, `data/expanded_dataset_v2.csv` |
| 3 | `federated/fl_simulation.py`, `federated/data_partitioner.py`, `federated/fl_client.py` |
| 4 | `vscode-extension/src/`, `inference_server/server.py` |
| 5a | `test_xai_step5_1.py`, `xai_analysis.py` |
| 5b | `federated/fl_dp_simulation.py` (to be created) |

---

## Document Version History

| Date | Update | Version |
|------|--------|---------|
| Dec 2, 2025 | Created initial phases 1-4 | 1.0 |
| Dec 9, 2025 | Added corrected FL results | 1.1 |
| Dec 10, 2025 | Created this comprehensive reference | 1.2 |

---

**Use this document when you need to recall context about any phase or switch to a different working environment/model.**
