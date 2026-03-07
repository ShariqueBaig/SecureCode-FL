# SecureCode-FL: Quick Context Reference

**Use this when you need to quickly remember what phase you're in and what needs to happen next**

---

## 🎯 Project Overview

**Research Goal:** Privacy-preserving code vulnerability detection using Federated Learning  
**Dataset:** 471 Python code samples (233 vulnerable, 238 secure)  
**Model:** Deep MLP (256→128→64→1) trained on TF-IDF features  
**FL Setup:** 3 clients, 20 rounds, non-IID distribution  
**Final Metric:** 84.2% accuracy (federated) vs 88.4% (centralized)

---

## 📊 Current Status Dashboard

```
┌─────────────────────────────────────────────┐
│  PHASE COMPLETION STATUS                    │
├─────────────────────────────────────────────┤
│  Phase 1: Baseline (60 samples)      ✅ 100% │
│  Phase 2: Neural Networks           ✅ 100% │
│  Phase 2.5: Dataset (471 samples)   ✅ 100% │
│  Phase 3: Federated Learning        ✅ 100% │
│  Phase 4: VS Code + Feedback        ✅ 100% │
│  Phase 5a: XAI (SHAP)               🔴  0%* │
│  Phase 5b: Differential Privacy     🔴  0%  │
│  Phase 6: Evaluation & Paper        🔄 50%  │
├─────────────────────────────────────────────┤
│  *test_xai_step5_1.py failing (exit code 1)│
│   Need to debug SHAP integration           │
└─────────────────────────────────────────────┘

Paper Status:
├── Phases 1-4 Results: ✅ UPDATED (Dec 10)
├── Phase 5 Results: 🔄 PENDING
└── Final Submission: ⏳ READY AFTER PHASE 5
```

---

## 🔑 Key Numbers to Remember

| Component | Value | Context |
|-----------|-------|---------|
| **Total Dataset** | 471 samples | Expanded from original 60 |
| **Train/Test Split** | 376 / 95 | 80% train, 20% test |
| **Federated Accuracy** | **84.2%** | Corrected (was 94.7% with data leak) |
| **Centralized Accuracy** | 88.4% | Baseline for comparison |
| **Privacy Cost** | -4.2% | Expected non-IID federated gap |
| **FL Rounds** | 20 | With 3 clients, 3 local epochs each |
| **Inference Latency** | <50ms | Suitable for real-time IDE |
| **TF-IDF Features** | 2000 | Max features, actual 871 extracted |
| **Model Parameters** | 555,009 | MLP: 256→128→64→1 |

---

## 📝 Data Accuracy Check

### ✅ VERIFIED (Dec 10, 2025)

**Dataset Composition:**
```
Total: 471 samples
├── Vulnerable (Class 1): 233 samples (49.5%)
└── Secure (Class 0): 238 samples (50.5%)
```

**Train/Test Split (Proper):**
```
471 samples
├── Training: 376 samples (80%)
│   ├── Client 0: 126 samples (64 vuln, 62 secure)
│   ├── Client 1: 125 samples (58 vuln, 67 secure)
│   └── Client 2: 125 samples (64 vuln, 61 secure)
│
└── Test: 95 samples (20%) ← ISOLATED FROM TRAINING
    ├── Vulnerable: 47
    └── Secure: 48
```

**Label Encoding (CRITICAL):**
```
1 = Vulnerable / Error
0 = Secure / Good
```
✅ Consistent across: data_preprocessing.py, data_partitioner.py, fl_client.py, all tests

---

## 🚨 Critical Issue Fixed (Dec 9)

### The Bug That Was Caught
Initial FL results showed 94.7% accuracy → seemed too good  
Mathematical check: 646 client samples ≠ 471 total dataset  
**Root cause:** Test set contaminated with training data

### The Fix Applied
1. Split 471 → 376 train + 95 test FIRST
2. Partition only 376 to clients (125-126 each)
3. Keep 95 test completely separate

### The Lesson
✅ Always validate sample counts mathematically  
✅ Train/test split MUST come BEFORE client partitioning  
✅ Inflated accuracy (94.7%) was a red flag  
✅ Corrected accuracy (84.2%) is realistic for non-IID FL

---

## 📂 Most Important Files

```
SecureCode-FL/
├── config.py ........................ Central configuration
├── data/expanded_dataset_v2.csv .... Dataset: 471 samples
├── neural_network_models.py ........ Model architectures
├── federated/
│   ├── fl_simulation.py ............ CORRECTED FL implementation
│   ├── data_partitioner.py ......... Non-IID partitioning
│   └── fl_client.py ............... Client code
├── inference_server/server.py ...... Flask API for inference
├── vscode-extension/src/ ........... Extension source
├── models/federated/fl_global_model.keras .. Trained model
├── results/federated/fl_comparison_*.json .. Latest results
└── research_paper.tex .............. Paper UPDATED Dec 10
```

---

## 🔄 Workflow for Each Phase

### If Working on Phase 3 (Federated Learning)
```bash
# 1. Verify data integrity
python -c "import pandas as pd; df=pd.read_csv('data/expanded_dataset_v2.csv'); print(f'Total: {len(df)}, Vulnerable: {(df[\"label\"]==1).sum()}')"

# 2. Run FL simulation
python federated/fl_simulation.py

# 3. Check results
cat results/federated/fl_comparison_*.json | grep -E "accuracy|Difference"

# 4. Verify sample counts (CRUCIAL!)
python -c "from federated.fl_simulation import *; print(f'Clients: {sum([c[\"num_samples\"] for c in FLSimulation().prepare_data()])}')"
```

### If Working on Phase 4 (VS Code Extension)
```bash
# 1. Start inference server
python inference_server/server.py

# 2. Test API
curl -X POST http://localhost:5000/predict -d '{"code":"..."}' -H "Content-Type: application/json"

# 3. Package extension
npm install
npm run compile
code --install-extension securecode-fl-*.vsix
```

### If Working on Phase 5a (XAI)
```bash
# 1. Load trained FL model
python test_xai_step5_1.py

# 2. Generate SHAP explanations
# (Currently broken - needs debugging)

# 3. Visualize feature importance
# (Part of test_xai_step5_1.py when fixed)
```

---

## 💡 Quick Facts

### Model Performance Progression
```
Phase 1 (60 samples, TreeBased):
└── Gradient Boosting: 76.7%

Phase 2 (60 samples, Neural):
└── LSTM: 63.3%  (sacrifice 13% for FL compatibility)

Phase 2.5 (471 samples, Neural):
└── MLP_v3: 93.4% (baseline on training set)

Phase 3 (471 samples, Federated):
├── Federated: 84.2% (on 376 train, test on 95 held-out)
└── Centralized: 88.4% (control, same 376 train, test on 95)
    └── Difference: -4.2% (realistic federated overhead)
```

### Why Numbers Changed
- **60→471 samples:** Dataset expansion fixed small-sample problem
- **93.4%→84.2%:** FL (non-IID) vs Centralized (IID)
- **94.7%→84.2%:** Data leakage fixed (was 37% duplicated)

### Privacy-Accuracy Tradeoff
- **No privacy (IID):** 88.4%
- **With privacy (non-IID FL):** 84.2%
- **Cost:** 4.2% accuracy for completely privacy-preserving architecture

---

## 🎓 What Each Phase Teaches

| Phase | Lesson | Output |
|-------|--------|--------|
| 1 | Baseline matters - establishes truth | 76.7% benchmark |
| 2 | FL requires gradient-based models | LSTM 63.3% |
| 2.5 | Data size dramatically impacts NN | 471 samples, 93.4% |
| 3 | Train/test split timing is critical | 84.2% (corrected), not 94.7% |
| 4 | IDE integration requires fast inference | <50ms latency |
| 5a | SHAP explains model decisions | Feature importance |
| 5b | Privacy has a cost | Epsilon-accuracy tradeoff |
| 6 | Document the journey, including failures | Paper |

---

## 📋 Checklist for Paper Sections

### ✅ COMPLETE
- [x] Phase 1: Baseline Reproduction
  - ✅ 60-sample dataset results
  - ✅ 6 models trained
  - ✅ SHAP analysis
  
- [x] Phase 2: Neural Network Conversion
  - ✅ 5 architectures tested
  - ✅ LSTM selected (63.3%)
  - ✅ Model serialization
  
- [x] Phase 2.5: Dataset Expansion
  - ✅ 471-sample dataset created
  - ✅ OWASP vulnerability categories
  - ✅ MLP retraining (93.4%)
  
- [x] Phase 3: Federated Learning (UPDATED Dec 9-10)
  - ✅ FedAvg implementation
  - ✅ Data leakage fix
  - ✅ Train/test split verification
  - ✅ 84.2% accuracy (corrected)
  - ✅ -4.2% privacy cost explanation
  - ✅ Confusion matrix (80/95 correct)
  
- [x] Phase 4: VS Code Extension
  - ✅ Extension architecture
  - ✅ Inference server
  - ✅ Feedback system
  - ✅ Performance metrics

### 🔄 IN PROGRESS
- [ ] Phase 5a: Explainability (XAI)
  - ⏳ Debug test_xai_step5_1.py
  - ⏳ Generate SHAP explanations
  - ⏳ Feature importance rankings

- [ ] Phase 5b: Privacy (Differential Privacy)
  - ⏳ Implement DP-SGD
  - ⏳ Run privacy-accuracy experiments
  - ⏳ Document epsilon-delta tradeoffs

### ⏳ PENDING
- [ ] Phase 6: Evaluation & Final Documentation
  - ⏳ Aggregate all results
  - ⏳ Write evaluation section
  - ⏳ Final conclusions
  - ⏳ Submit paper

---

## 🎯 Next Action Items

### IMMEDIATE (This Week)
1. **Debug Phase 5a** - Fix test_xai_step5_1.py (exit code 1)
   - Check SHAP installation
   - Verify model path (use corrected FL model)
   - Test on single sample first

2. **Document Phase 5a Results** when working

### SOON (Next Week)
3. **Implement Phase 5b** - Differential Privacy
   - Use `tensorflow-privacy` library
   - Configure ε and δ values
   - Run privacy-accuracy curves

4. **Start Phase 6** - Evaluation & Paper Finalization
   - Collect all results
   - Write evaluation section
   - Finalize conclusions

---

## 🔗 Related Documents

- `PROJECT_PHASES_SUMMARY.md` ← You are here (comprehensive)
- `PHASE4_PAPER_READINESS.md` ← Phase 4 status (detailed)
- `RESEARCH_ROADMAP.md` ← Original roadmap (has Phase 1-2 details)
- `RESEARCH_DOCUMENTATION.md` ← Full technical specs
- `research_paper.tex` ← The paper itself (updated Dec 10)

---

**Last Updated:** December 10, 2025  
**For:** Switching contexts, remembering details, onboarding new researchers  
**Keep this nearby!** 📌
