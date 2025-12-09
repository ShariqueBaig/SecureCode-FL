# SecureCode-FL: Privacy-Preserving Code Vulnerability Detection

A VS Code extension for real-time code vulnerability detection powered by **Federated Learning**. Your code stays private while the model continuously improves from user feedback across the community.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![TensorFlow](https://img.shields.io/badge/tensorflow-2.15+-orange)
![License](https://img.shields.io/badge/license-MIT-purple)

## 🌟 Features

### 🔍 Real-Time Vulnerability Detection

- Scans Python, JavaScript, TypeScript, Java, C#, and PHP
- Detects 50+ vulnerability patterns
- ML-powered detection with 94.7% accuracy
- OWASP API Top 10 coverage

### 🔒 Privacy-Preserving Federated Learning

- Your code **never leaves your machine**
- Only model weights are shared
- Distributed training across multiple users
- FedAvg aggregation strategy

### 💬 User Feedback System

- Mark false positives to improve accuracy
- Report missed vulnerabilities
- Confirm correct detections
- Local training on your corrections

### 📊 Vulnerability Categories (OWASP API Top 10)

1. Broken Object Level Authorization
2. Broken Authentication
3. Broken Object Property Level Authorization
4. Unrestricted Resource Consumption
5. Broken Function Level Authorization
6. Unrestricted Access to Sensitive Business Flows
7. Server Side Request Forgery
8. Security Misconfiguration
9. Improper Inventory Management
10. Unsafe Consumption of APIs

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- VS Code 1.85+

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/ShariqueBaig/SecureCode-FL.git
   cd SecureCode-FL
   ```

2. **Set up Python environment**

   ```bash
   python -m venv venv

   # Windows
   .\venv\Scripts\activate

   # Linux/Mac
   source venv/bin/activate

   pip install -r requirements.txt
   ```

3. **Install VS Code extension dependencies**
   ```bash
   cd vscode-extension
   npm install
   npm run compile
   cd ..
   ```

---

## 📖 Usage Instructions

### 1. Start the Inference Server

Open a terminal and run:

```bash
# Windows
.\venv\Scripts\python.exe inference_server\server.py

# Linux/Mac
python inference_server/server.py
```

You should see:

```
============================================================
  SecureCode-FL Inference Server
  With User Feedback System
============================================================
✓ Loaded model from: ...fl_global_model.keras
✓ Loaded vectorizer from: ...tfidf_vectorizer.pkl
✓ Feedback database initialized
📊 Feedback DB: X entries, X untrained

🚀 Starting server on http://localhost:5000
📋 Endpoints:
   GET  /health           - Health check
   POST /scan             - Scan code for vulnerabilities
   POST /feedback         - Submit user feedback
   GET  /feedback/stats   - Get feedback statistics
============================================================
```

### 2. Run the VS Code Extension

1. Open VS Code in the extension folder:

   ```bash
   code vscode-extension
   ```

2. Press **F5** to launch the Extension Development Host

3. In the new VS Code window, open any Python/JavaScript file

### 3. Scanning for Vulnerabilities

| Action                | How To                                                                    |
| --------------------- | ------------------------------------------------------------------------- |
| **Scan current file** | `Ctrl+Shift+S` or right-click → "SecureCode-FL: Scan Current File"        |
| **Scan workspace**    | Command Palette (`Ctrl+Shift+P`) → "SecureCode-FL: Scan Entire Workspace" |
| **Toggle real-time**  | Command Palette → "SecureCode-FL: Toggle Real-Time Scanning"              |
| **View dashboard**    | Command Palette → "SecureCode-FL: Show Vulnerability Dashboard"           |

### 4. Using the Feedback System

| Action                     | How To                                                             |
| -------------------------- | ------------------------------------------------------------------ |
| **Mark as False Positive** | Select code → right-click → "Mark Selection as False Positive"     |
| **Mark as Vulnerable**     | Select code → right-click → "Mark Selection as Vulnerable"         |
| **Quick Fix**              | Click the 💡 lightbulb on a detected vulnerability                 |
| **Confirm Vulnerability**  | Command Palette → "SecureCode-FL: Confirm Vulnerability at Cursor" |
| **View Stats**             | Command Palette → "SecureCode-FL: Show Feedback Statistics"        |

### 5. Train Model on Feedback

After collecting feedback, train the model locally:

```bash
# Windows
.\venv\Scripts\python.exe federated\fl_feedback_client.py --mode local

# Linux/Mac
python federated/fl_feedback_client.py --mode local
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        VS Code Extension                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Scanner   │  │ Diagnostics │  │   Feedback Manager      │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
│         │                │                      │                │
│         └────────────────┴──────────────────────┘                │
│                          │                                       │
└──────────────────────────┼───────────────────────────────────────┘
                           │ HTTP REST API
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Inference Server (Flask)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  ML Model   │  │  Patterns   │  │   Feedback Database     │  │
│  │ (TensorFlow)│  │  (Regex)    │  │   (SQLite)              │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
│         │                │                      │                │
│         └────────────────┴──────────────────────┘                │
└──────────────────────────┼───────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Federated Learning Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  FL Server  │◄─┤  FL Client  │◄─┤   Feedback Trainer      │  │
│  │  (Flower)   │  │  (Local)    │  │   (User Corrections)    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                                                                  │
│  Privacy: Only model weights shared, code stays LOCAL           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
SecureCode-FL/
├── inference_server/           # Flask API server
│   ├── server.py              # Main server with scan & feedback endpoints
│   └── feedback.py            # SQLite feedback database
│
├── federated/                  # Federated Learning
│   ├── fl_server.py           # Flower FL server
│   ├── fl_client.py           # Flower FL client
│   ├── fl_feedback_client.py  # FL client with user feedback
│   ├── fl_model.py            # Neural network model
│   ├── fl_config.py           # FL configuration
│   └── fl_simulation.py       # Local FL simulation
│
├── vscode-extension/           # VS Code Extension
│   ├── src/
│   │   ├── extension.ts       # Extension entry point
│   │   ├── scanner.ts         # Vulnerability scanner
│   │   ├── serverClient.ts    # Server communication
│   │   ├── diagnostics.ts     # VS Code diagnostics
│   │   ├── feedbackManager.ts # User feedback UI
│   │   └── dashboard.ts       # Vulnerability dashboard
│   └── package.json           # Extension manifest
│
├── models/                     # Trained models
│   ├── federated/
│   │   └── fl_global_model.keras
│   └── tfidf_vectorizer.pkl
│
├── data/                       # Data files
│   └── user_feedback.db       # Local feedback database
│
└── requirements.txt           # Python dependencies
```

---

## 🔧 API Reference

### Scan Endpoint

```http
POST /scan
Content-Type: application/json

{
  "code": "password = 'secret123'",
  "language": "python",
  "filename": "example.py"
}
```

### Feedback Endpoint

```http
POST /feedback
Content-Type: application/json

{
  "code_snippet": "password = os.environ.get('DB_PASS')",
  "user_label": "secure",
  "original_detection": "Broken Authentication",
  "notes": "Uses environment variable, not hardcoded",
  "file_path": "/project/config.py",
  "language": "python"
}
```

### Feedback Stats

```http
GET /feedback/stats

Response:
{
  "success": true,
  "stats": {
    "total": 10,
    "untrained": 5,
    "by_type": {"false_positive": 3, "missed_vulnerability": 2},
    "by_label": {"secure": 4, "vulnerable": 6}
  }
}
```

---

## 🧪 Testing

### Run API Tests

```bash
.\venv\Scripts\python.exe test_feedback_api.py
```

### Run FL Simulation

```bash
.\venv\Scripts\python.exe federated\fl_simulation.py
```

### Run Distributed FL Test

```bash
.\venv\Scripts\python.exe federated\test_distributed.py
```

---

## 📊 Model Performance

| Metric               | Value   |
| -------------------- | ------- |
| Accuracy             | 94.7%   |
| FL Rounds            | 20      |
| Clients              | 3       |
| Model Parameters     | 555,265 |
| Aggregation Strategy | FedAvg  |

---

## 🛡️ Detected Vulnerabilities

### High Severity

- Hardcoded passwords, API keys, secrets
- SQL injection (string concatenation)
- Code injection (eval, exec)
- Shell injection (os.system, subprocess with shell=True)
- Insecure deserialization (pickle, yaml.load)
- SSL verification disabled

### Medium Severity

- Debug mode enabled
- Weak cryptography (MD5, SHA1)
- XSS vulnerabilities (innerHTML)
- Permissive CORS
- Logging sensitive data
- SSRF risks

### Low Severity

- Insecure HTTP protocol
- Infinite loops
- Fixed sleep durations

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Sharique Baig**

- GitHub: [@ShariqueBaig](https://github.com/ShariqueBaig)

---

## 🙏 Acknowledgments

- OWASP for vulnerability categorization
- Flower framework for Federated Learning
- TensorFlow team for ML infrastructure
