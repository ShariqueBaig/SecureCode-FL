# SecureCode-FL: Federated Learning for Privacy-Preserving Code Vulnerability Detection

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![TensorFlow 2.15+](https://img.shields.io/badge/tensorflow-2.15+-orange.svg)](https://www.tensorflow.org/)
[![Flower 1.5+](https://img.shields.io/badge/flower-1.5+-green.svg)](https://flower.ai/)
[![License: MIT](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)

This repository contains the source code, dataset, and experimental pipeline for the paper:

> **SecureCode-FL: Federated Learning for Privacy-Preserving Code Vulnerability Detection**  
> Sharique Baig, Faisal Iradat, Waseem Iqbal, Maira Aijaz  
> *Institute of Business Administration, Karachi & Sultan Qaboos University, Muscat*

---

## Table of Contents

- [Abstract](#abstract)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Reproducing Results](#reproducing-results)
  - [Step 1 — Centralized Baseline](#step-1--centralized-baseline-table-4)
  - [Step 2 — Cross-Validation](#step-2--cross-validation-table-4)
  - [Step 3 — Federated Learning Simulation](#step-3--federated-learning-simulation-table-5)
  - [Step 4 — Differential Privacy Experiment](#step-4--differential-privacy-experiment-table-8)
  - [Step 5 — Generate Paper Figures](#step-5--generate-paper-figures)
- [Dataset](#dataset)
- [Key Results Summary](#key-results-summary)
- [System Demo — VS Code Extension](#system-demo--vs-code-extension)
- [Configuration Reference](#configuration-reference)
- [Troubleshooting](#troubleshooting)
- [Citation](#citation)
- [License](#license)

---

## Abstract

SecureCode-FL demonstrates that federated learning is feasible for privacy-preserving code vulnerability detection. The system allows multiple organizations to cooperatively train detection models without exchanging proprietary source code. Four integrated components comprise the system: (1) a deep neural network trained on a 471-sample dataset covering OWASP API Top 10 vulnerability categories, (2) a federated learning infrastructure using the Flower framework, (3) a real-time detection pipeline with VS Code IDE integration, and (4) differential privacy integration for privacy-utility tradeoff analysis.

**Key finding:** The federated model achieves **80.00% accuracy** compared to **86.32% centralized baseline** — only a 6.32 percentage point difference — while source code never leaves local machines.

---

## Repository Structure

```
SecureCode-FL/
│
├── data/
│   └── expanded_dataset.xlsx          # Curated 471-sample vulnerability dataset
│
├── config.py                          # Central configuration (paths, hyperparams, TF-IDF)
├── data_preprocessing.py              # Data loading, TF-IDF vectorization, train/test split
├── model_training.py                  # Centralized ML model training (6 classifiers)
├── cross_validation.py                # 5-fold stratified cross-validation
├── main.py                           # Full centralized pipeline (Steps 1-5 combined)
├── neural_network_models.py           # MLP, LSTM, CNN architectures for FL
├── generate_paper_figures.py          # Generates all publication figures
│
├── experiments/                       # Miscellaneous tuning and timing scripts
│   ├── hyperparameter_tuning.py
│   ├── nn_hyperparameter_tuning.py
│   ├── analyze_token_distribution.py
│   ├── measure_timing.py
│   └── train_best_model.py
│
├── xai/                               # Explainable AI standalone scripts
│   ├── xai_analysis.py                # SHAP-based explainability analysis
│   └── xai_explainer.py               # Explainable AI helper module
│
├── paper/                             # LaTeX paper sources and templates
│   ├── sn-securecode-fl.tex           # Paper source (Springer Nature LaTeX)
│   ├── sn-jnl.cls                     # Springer Nature journal class file
│   ├── sn-basic.bst                   # Bibliography style
│   └── sn-article-template/           # Original SN template (reference)
│
├── federated/                         # Federated Learning subsystem
│   ├── fl_config.py                   # FL hyperparameters (rounds, clients, DP settings)
│   ├── fl_model.py                    # Neural network model + FedAvg aggregation
│   ├── fl_server.py                   # Flower FL server
│   ├── fl_client.py                   # Flower FL client
│   ├── fl_simulation.py              # Local FL simulation (no network needed)
│   ├── data_partitioner.py            # IID / Non-IID data partitioning
│   ├── dp_model.py                    # Differential privacy model wrapper
│   ├── dp_privacy.py                  # DP noise mechanisms
│   ├── dp_fl_simulation.py            # DP-FL experiment runner
│   ├── fl_feedback_client.py          # Continuous learning via user feedback
│   └── test_distributed.py            # Distributed FL test
│
├── inference_server/                  # Real-time detection API
│   ├── server.py                      # Flask REST API server
│   ├── feedback.py                    # SQLite feedback database
│   ├── start_server.bat               # Windows startup script
│   ├── start_server.ps1               # PowerShell startup script
│   └── requirements.txt              # Server-specific dependencies
│
├── vscode-extension/                  # VS Code IDE integration
│   ├── src/                           # TypeScript source (scanner, diagnostics, etc.)
│   ├── package.json                   # Extension manifest
│   └── tsconfig.json                  # TypeScript config
│
├── tools/                             # Dataset creation utilities
│   ├── bandit_scanner.py              # Bandit-based vulnerability scanner
│   ├── github_vuln_miner.py           # GitHub repo vulnerability miner
│   ├── clone_and_scan.py              # Clone repos and scan for vulns
│   └── merge_datasets.py             # Merge scan results into dataset
│
├── checkpoints/                       # Research progress checkpoints
├── docs/                              # Project documentation (25 documents)
├── results/                           # Saved experiment results (JSON, CSV, PNG)
│
├── requirements.txt                   # Python dependencies
└── README.md                          # This file
```

---

## Prerequisites

| Requirement | Version | Purpose |
|---|---|---|
| **Python** | 3.10+ | Core runtime |
| **pip** | latest | Package manager |
| **TensorFlow** | 2.15+ | Neural network training |
| **NVIDIA GPU** *(optional)* | CUDA 11.8+ | Accelerated training |
| **Node.js** | 18+ | VS Code extension only |
| **LaTeX** *(optional)* | TeX Live / MiKTeX | Compiling the paper |

**Tested on:** Intel Core i5 (7th gen), 16 GB DDR4, NVIDIA GeForce 930MX (2 GB) — Windows 10/11.

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/ShariqueBaig/SecureCode-FL.git
cd SecureCode-FL

# 2. Create and activate a virtual environment
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

# 3. Install core research dependencies
pip install -r requirements.txt

# 4. Install FL and deep learning dependencies
pip install tensorflow>=2.15.0 flwr>=1.5.0 flask>=3.0.0 flask-cors>=4.0.0
```

> **Note:** If you only want to reproduce the centralized ML experiments (Tables 4–6 in the paper), `requirements.txt` alone is sufficient. TensorFlow and Flower are needed only for the federated learning experiments (Tables 5, 7, 8).

---

## Reproducing Results

All experiments use **random seed 42** for reproducibility. The dataset (`data/expanded_dataset.xlsx`) is included in the repository.

### Step 1 — Centralized Baseline (Table 4)

Train all six ML classifiers (Logistic Regression, Random Forest, SVM, Gradient Boosting, Extra Trees, XGBoost) on the full dataset with a standard 80/20 stratified split:

```bash
python main.py
```

**What it does:**
1. Loads and preprocesses `data/expanded_dataset.xlsx` (471 samples)
2. Extracts TF-IDF features (1,000 features, unigram + bigram)
3. Trains 6 classifiers, evaluates on the held-out 20% test set
4. Runs SHAP explainability analysis
5. Saves models to `models/` and results to `results/`

**Expected output:** Validation report saved to `results/validation_report.txt`  
**Expected runtime:** ~2 minutes on CPU

### Step 2 — Cross-Validation (Table 4)

Run 5-fold stratified cross-validation across all models:

```bash
python cross_validation.py
```

**Expected output:** Per-model accuracy ± std, saved to `models/cv_results.csv`  
**Expected runtime:** ~3 minutes on CPU

### Step 3 — Federated Learning Simulation (Table 5)

Simulate federated training with 3 clients (non-IID partitioning) over 20 rounds:

```bash
python federated/fl_simulation.py
```

**What it does:**
1. Splits data: 80% train / 20% test (stratified, **global** test set)
2. Partitions the training data into 3 non-overlapping client shards
3. Runs 20 rounds of FedAvg (3 local epochs per round, batch size 16)
4. Evaluates the global model on the held-out test set after each round
5. Compares with centralized baseline trained for equivalent total epochs
6. Saves the global model to `models/federated/fl_global_model.keras`

**Expected output:**
```
Federated Accuracy:   ~80.0%
Centralized Accuracy: ~86.3%
Difference:           ~-6.3%
```

**Expected runtime:** ~10-15 minutes on CPU; ~3-5 minutes with GPU

### Step 4 — Differential Privacy Experiment (Table 8)

Run the DP-FL simulation with varying noise levels:

```bash
python federated/dp_fl_simulation.py
```

**What it does:**
1. Runs FL with Gaussian noise injection at multiple ε values
2. Reports accuracy at each privacy budget level
3. Demonstrates the privacy-accuracy tradeoff

**Expected runtime:** ~20-30 minutes on CPU

### Step 5 — Generate Paper Figures

Generate all publication-quality figures (confusion matrix, FL convergence, privacy tradeoff, feature importance):

```bash
python generate_paper_figures.py
```


**Output:** All figures saved to `figures/` directory as both `.png` (300 DPI) and `.pdf`.

---

## Dataset

The curated dataset is located at `data/expanded_dataset.xlsx`.

| Property | Value |
|---|---|
| Total samples | 471 |
| Vulnerable (class 1) | 233 (49.5%) |
| Secure (class 0) | 238 (50.5%) |
| Vulnerability categories | 8 (OWASP API Top 10 subset) |
| Language | Python |
| Labeling | Manual, by two authors with security expertise |

**Vulnerability categories covered:**
1. Injection (SQL/Command) — 67 samples
2. Broken Authentication — 65 samples
3. Security Misconfiguration — 63 samples
4. SSRF — 58 samples
5. Broken Object Level Authorization — 56 samples
6. Broken Function Level Authorization — 54 samples
7. Unrestricted Resource Consumption — 53 samples
8. Broken Object Property Authorization — 55 samples

**Dataset columns:**
| Column | Description |
|---|---|
| `S.No` | Sample ID |
| `Primary Vulnerability` | OWASP vulnerability category |
| `Exploit` | Description of the exploit |
| `Result` | `Error` (vulnerable) or `Good` (secure) |
| `Code` | Python code snippet |

---

## Key Results Summary

### Centralized vs Federated (Table 5 in paper)

| Metric | Centralized | Federated (3 clients) | Difference |
|---|---|---|---|
| Accuracy | 86.32% | 80.00% | −6.32 pp |
| Precision | 90.48% | 86.84% | −3.64 pp |
| Recall | 80.85% | 70.21% | −10.64 pp |
| F1-Score | 85.39% | 77.65% | −7.74 pp |

### 5-Fold Cross-Validation

| Metric | Value |
|---|---|
| CV Accuracy | 89.50% ± 2.10% |
| 95% Confidence Interval | [87.40%, 91.60%] |

### Differential Privacy Tradeoff (Table 8 in paper)

| Privacy Budget (ε) | Accuracy |
|---|---|
| ∞ (No DP) | 80.00% |
| 60.18 | 53.68% |
| 30.1 | 50.5% |

> **Note:** DP accuracy is limited by the small dataset size (471 samples). The paper discusses that larger datasets (10K+) are needed for practical privacy-accuracy tradeoffs.

---

## System Demo — VS Code Extension

The inference server and VS Code extension provide a working proof-of-concept for real-time vulnerability detection. This is **not required for reproducing paper results** but demonstrates the end-to-end system.

### Start the Inference Server

```bash
# Install server dependencies
pip install -r inference_server/requirements.txt

# Start the server (loads the trained FL global model)
python inference_server/server.py
```

The server runs at `http://localhost:5000` with these endpoints:
- `GET /health` — Health check
- `POST /scan` — Scan code for vulnerabilities
- `POST /feedback` — Submit user feedback
- `GET /feedback/stats` — Feedback statistics

### Run the VS Code Extension

```bash
cd vscode-extension
npm install
npm run compile
```

Then open the `vscode-extension/` folder in VS Code and press **F5** to launch the Extension Development Host.

---

## Configuration Reference

### Core Configuration (`config.py`)

| Parameter | Value | Description |
|---|---|---|
| `RANDOM_STATE` | 42 | Random seed for reproducibility |
| `TEST_SIZE` | 0.2 | Train/test split ratio |
| `TFIDF_CONFIG.max_features` | 1000 | TF-IDF vocabulary size |
| `TFIDF_CONFIG.ngram_range` | (1, 2) | Unigrams + bigrams |

### Federated Learning Configuration (`federated/fl_config.py`)

| Parameter | Value | Description |
|---|---|---|
| `NUM_CLIENTS` | 3 | Simulated organizations |
| `NUM_ROUNDS` | 20 | FL training rounds |
| `LOCAL_EPOCHS` | 3 | Epochs per client per round |
| `BATCH_SIZE` | 16 | Mini-batch size |
| `LEARNING_RATE` | 0.005 | Adam optimizer LR |
| `TFIDF_MAX_FEATURES` | 2000 | TF-IDF features for FL model |
| `HIDDEN_LAYERS` | [128, 64, 32] | MLP architecture |
| `DROPOUT_RATES` | [0.3, 0.2, 0.1] | Per-layer dropout |
| `L2_REGULARIZATION` | 0.01 | Weight decay |
| `DATA_DISTRIBUTION` | non_iid | Client data partitioning |

> **Note on TF-IDF features:** The centralized baseline uses 1,000 features (`config.py`), while the FL model uses 2,000 features (`fl_config.py`). This is because the FL model's MLP architecture (267K params) was optimized with 2,000-dimensional input as described in the paper.

---

## Troubleshooting

| Issue | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'tensorflow'` | Install TensorFlow: `pip install tensorflow>=2.15.0` |
| `ModuleNotFoundError: No module named 'flwr'` | Install Flower: `pip install flwr>=1.5.0` |
| `ModuleNotFoundError: No module named 'xgboost'` | Install XGBoost: `pip install xgboost>=1.7.0` (optional; script skips XGBoost if missing) |
| CUDA/GPU errors | Set `CUDA_VISIBLE_DEVICES=""` to force CPU mode |
| `PermissionError` on Windows | Run terminal as Administrator, or ensure `venv/` is writable |

---

## Citation

If you use this code or dataset in your research, please cite:

```bibtex
@article{baig2025securecodefl,
  title     = {SecureCode-FL: Federated Learning for Privacy-Preserving Code Vulnerability Detection},
  author    = {Baig, Sharique and Iradat, Faisal and Iqbal, Waseem and Aijaz, Maira},
  year      = {2025},
  note      = {Manuscript under review}
}
```

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [OWASP](https://owasp.org/) for the API Security Top 10 vulnerability taxonomy
- [Flower](https://flower.ai/) framework for federated learning infrastructure
- [TensorFlow](https://www.tensorflow.org/) for deep learning
- [Springer Nature](https://www.springernature.com/) for the LaTeX article template
