# Quick Start Guide: Reproducing Phase 3 Results

## ⏱️ Time Required: ~5 minutes

This guide helps you reproduce our Federated Learning results (94.7% accuracy).

## 📋 Prerequisites

- Python 3.10+
- pip package manager
- ~2GB disk space

## 🚀 Step-by-Step Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/ShariqueBaig/SecureCode-FL.git
cd SecureCode-FL
git checkout phase-3-federated-learning
```

### 2. Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Dataset

```bash
python -c "import pandas as pd; df = pd.read_excel('data/expanded_dataset_v2.xlsx'); print(f'Dataset: {len(df)} samples')"
```

Expected output: `Dataset: 471 samples`

### 5. Run Federated Learning Simulation

```bash
python -m federated.fl_simulation
```

### 6. Verify Results

After completion, check:

```bash
# View comparison results
type results\federated\fl_comparison_*.json
```

Expected output:
```json
{
  "federated_accuracy": 0.947,
  "centralized_accuracy": 0.947,
  ...
}
```

## ✅ Success Criteria

Your run is successful if:
- [ ] Federated Accuracy ≥ 90%
- [ ] Accuracy difference from centralized ≤ 5%
- [ ] `fl_global_model.keras` file created
- [ ] No errors during 20 FL rounds

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Low accuracy | Increase `fl_rounds` in `federated/fl_config.py` |
| Memory error | Reduce `batch_size` to 8 |

## 📞 Support

Open an issue on GitHub if you encounter problems.
