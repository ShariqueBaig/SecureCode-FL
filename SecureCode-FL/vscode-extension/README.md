# SecureCode-FL VS Code Extension

🛡️ **Real-time code vulnerability detection powered by Federated Learning**

## Features

- **Real-time Scanning**: Automatically detects vulnerabilities as you type
- **OWASP Coverage**: Detects all OWASP API Top 10 vulnerabilities
- **Privacy-Preserving**: Built on Federated Learning - your code stays local
- **Multi-language Support**: Python, JavaScript, TypeScript, Java, C#, PHP
- **Detailed Diagnostics**: Shows severity, CWE IDs, and fix suggestions

## Screenshots

### Real-time Detection

![Real-time scanning](images/realtime-scan.png)

### Problems Panel

![Problems panel](images/problems-panel.png)

### Dashboard

![Dashboard](images/dashboard.png)

## Installation

### Option 1: Install from VSIX (Recommended)

1. Download `securecode-fl-1.0.0.vsix`
2. In VS Code: `Ctrl+Shift+P` → "Extensions: Install from VSIX"
3. Select the downloaded file

### Option 2: Build from Source

```bash
cd vscode-extension
npm install
npm run compile
npm run package
```

## Setup

### 1. Start the Inference Server

The extension requires a Python inference server:

```bash
# From the SecureCode-FL root directory
cd inference_server
pip install -r requirements.txt
python server.py
```

You should see:

```
============================================================
  SecureCode-FL Inference Server
============================================================
✓ Loaded model from: models/federated/fl_global_model.keras
✓ Loaded vectorizer from: models/tfidf_vectorizer.joblib

🚀 Starting server on http://localhost:5000
```

### 2. Configure Extension (Optional)

Default settings work out of the box. To customize:

1. Open VS Code Settings (`Ctrl+,`)
2. Search for "SecureCode-FL"
3. Adjust settings:

| Setting                  | Default                 | Description                                |
| ------------------------ | ----------------------- | ------------------------------------------ |
| `enableRealTimeScanning` | `true`                  | Scan as you type                           |
| `scanDelay`              | `1000`                  | Delay in ms before scanning                |
| `serverUrl`              | `http://localhost:5000` | Inference server URL                       |
| `minimumConfidence`      | `0.7`                   | Show vulnerabilities above this confidence |
| `showInlineHints`        | `true`                  | Show inline vulnerability hints            |

## Usage

### Commands

| Command           | Shortcut       | Description                       |
| ----------------- | -------------- | --------------------------------- |
| Scan Current File | `Ctrl+Shift+S` | Scan the active file              |
| Scan Workspace    | -              | Scan all supported files          |
| Toggle Real-Time  | -              | Enable/disable real-time scanning |
| Show Dashboard    | -              | Open vulnerability dashboard      |

### Status Bar

The status bar shows:

- 🛡️ **SecureCode-FL** - Extension active, no issues
- ⚠️ **3 issues** - Vulnerabilities detected
- 🔄 **Scanning...** - Analysis in progress
- ❌ **Error** - Server connection issue

### Problems Panel

Vulnerabilities appear in the Problems panel (`Ctrl+Shift+M`):

```
[SecureCode-FL] [Broken Authentication] Hardcoded password detected
💡 Store credentials in environment variables or use a secrets manager
```

## Detected Vulnerabilities

The extension detects OWASP API Top 10 vulnerabilities:

| #   | Vulnerability                              | Example                     |
| --- | ------------------------------------------ | --------------------------- |
| 1   | Broken Object Level Authorization          | SQL injection               |
| 2   | Broken Authentication                      | Hardcoded credentials       |
| 3   | Broken Object Property Level Authorization | Mass assignment             |
| 4   | Unrestricted Resource Consumption          | DoS vulnerabilities         |
| 5   | Broken Function Level Authorization        | Privilege escalation        |
| 6   | Unrestricted Access to Sensitive Flows     | Rate limiting issues        |
| 7   | Server Side Request Forgery                | SSRF attacks                |
| 8   | Security Misconfiguration                  | Debug mode, permissive CORS |
| 9   | Improper Inventory Management              | Exposed endpoints           |
| 10  | Unsafe Consumption of APIs                 | eval(), exec()              |

## Example Detections

### Python

```python
# ⚠️ HIGH: Hardcoded password detected
password = "admin123"

# ⚠️ HIGH: SQL injection risk
query = "SELECT * FROM users WHERE id = " + user_id

# ⚠️ HIGH: SSL verification disabled
requests.get(url, verify=False)
```

### JavaScript

```javascript
// ⚠️ HIGH: Use of eval()
eval(userInput);

// ⚠️ MEDIUM: innerHTML XSS risk
element.innerHTML = userData;

// ⚠️ LOW: Insecure HTTP
fetch("http://api.example.com/data");
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    VS Code Extension                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Scanner    │  │ Diagnostics │  │     Dashboard       │  │
│  │  (scanner.ts│  │ (diagnostics│  │   (dashboard.ts)    │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│         └────────────────┼─────────────────────┘             │
│                          │                                   │
│                    ┌─────▼─────┐                             │
│                    │  Server   │                             │
│                    │  Client   │                             │
│                    └─────┬─────┘                             │
└──────────────────────────┼───────────────────────────────────┘
                           │ HTTP
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                 Python Inference Server                       │
│  ┌─────────────────┐  ┌──────────────────────────────────┐  │
│  │  Pattern-Based  │  │         ML Model (FL)            │  │
│  │   Detection     │  │  ┌────────────────────────────┐  │  │
│  │                 │  │  │ TF-IDF → MLP → Prediction  │  │  │
│  │  (Regex rules)  │  │  │      94.7% Accuracy        │  │  │
│  └────────┬────────┘  │  └────────────────────────────┘  │  │
│           │           └──────────────┬───────────────────┘  │
│           └──────────────────────────┼───────────────────────│
│                                      │                       │
│                              ┌───────▼───────┐               │
│                              │    Results    │               │
│                              │  Aggregator   │               │
│                              └───────────────┘               │
└──────────────────────────────────────────────────────────────┘
```

## Troubleshooting

### "Cannot connect to server"

1. Ensure the inference server is running
2. Check the server URL in settings
3. Verify no firewall blocking port 5000

### Low accuracy

1. Ensure the FL model is loaded (check server startup logs)
2. The pattern-based fallback is used when ML model unavailable

### High false positives

1. Increase `minimumConfidence` setting
2. Use `// securecode-ignore` comment to suppress specific warnings

## Development

### Extension Development

```bash
cd vscode-extension
npm install
npm run watch  # Compile on save
# Press F5 in VS Code to launch Extension Host
```

### Server Development

```bash
cd inference_server
pip install -r requirements.txt
python server.py
```

### Testing

```bash
# Extension tests
npm test

# Server tests
pytest tests/
```

## License

MIT License - See LICENSE file

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Related

- [SecureCode-FL Main Repository](https://github.com/ShariqueBaig/SecureCode-FL)
- [Phase 3: Federated Learning](../docs/PHASE3_FEDERATED_LEARNING.md)
- [OWASP API Top 10](https://owasp.org/www-project-api-security/)
