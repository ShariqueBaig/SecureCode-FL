# SecureCode-FL: Complete User Guide

This guide covers all features and commands for using SecureCode-FL, from starting the server to retraining models with your feedback.

---

## Table of Contents

1. [Starting the Server](#1-starting-the-server)
2. [Running the VS Code Extension](#2-running-the-vs-code-extension)
3. [Scanning for Vulnerabilities](#3-scanning-for-vulnerabilities)
4. [Providing Feedback](#4-providing-feedback)
5. [Viewing the Feedback Database](#5-viewing-the-feedback-database)
6. [Retraining the Model](#6-retraining-the-model)
7. [Federated Learning Commands](#7-federated-learning-commands)
8. [API Endpoints Reference](#8-api-endpoints-reference)
9. [Keyboard Shortcuts](#9-keyboard-shortcuts)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Starting the Server

The inference server must be running for vulnerability detection to work.

### Windows (PowerShell)

```powershell
cd "C:\path\to\SecureCode-FL"
.\venv\Scripts\python.exe inference_server\server.py
```

### Windows (Command Prompt)

```cmd
cd C:\path\to\SecureCode-FL
venv\Scripts\python.exe inference_server\server.py
```

### Linux/Mac

```bash
cd /path/to/SecureCode-FL
source venv/bin/activate
python inference_server/server.py
```

### With Custom Port

```bash
python inference_server/server.py --port 5001
```

### Expected Output

```
============================================================
  SecureCode-FL Inference Server
  With User Feedback System
============================================================
✓ Loaded model from: .../fl_global_model.keras
✓ Loaded vectorizer from: .../tfidf_vectorizer.pkl
✓ Feedback database initialized
📊 Feedback DB: X entries, X untrained

🚀 Starting server on http://localhost:5000
```

---

## 2. Running the VS Code Extension

### Option A: Development Mode (F5)

1. Open VS Code in the extension folder:
   ```bash
   code vscode-extension
   ```
2. Press **F5** to launch Extension Development Host
3. A new VS Code window opens with the extension active

### Option B: Install from VSIX

```bash
cd vscode-extension
npm run package
# Install the generated .vsix file in VS Code
```

---

## 3. Scanning for Vulnerabilities

### Scan Current File

| Method          | Action                                                |
| --------------- | ----------------------------------------------------- |
| Keyboard        | `Ctrl+Shift+S` (Windows/Linux) or `Cmd+Shift+S` (Mac) |
| Context Menu    | Right-click → "SecureCode-FL: Scan Current File"      |
| Command Palette | `Ctrl+Shift+P` → "SecureCode-FL: Scan Current File"   |

### Scan Entire Workspace

| Method          | Action                                                  |
| --------------- | ------------------------------------------------------- |
| Command Palette | `Ctrl+Shift+P` → "SecureCode-FL: Scan Entire Workspace" |

### Toggle Real-Time Scanning

| Method          | Action                                                      |
| --------------- | ----------------------------------------------------------- |
| Command Palette | `Ctrl+Shift+P` → "SecureCode-FL: Toggle Real-Time Scanning" |

### View Dashboard

| Method          | Action                                                         |
| --------------- | -------------------------------------------------------------- |
| Command Palette | `Ctrl+Shift+P` → "SecureCode-FL: Show Vulnerability Dashboard" |

---

## 4. Providing Feedback

Feedback helps improve the model. Your code stays private - only model weights are shared.

### Mark Code as Vulnerable (Missed Detection)

1. **Select** the vulnerable code in the editor
2. **Right-click** → "SecureCode-FL: Mark Selection as Vulnerable"
3. **Choose** vulnerability type:
   - Broken Object Level Authorization
   - Broken Authentication
   - SQL Injection
   - XSS
   - etc.
4. **Select** severity: high / medium / low
5. **Describe** the vulnerability (optional)

### Mark as False Positive (Wrong Detection)

1. **Select** the flagged code
2. **Right-click** → "SecureCode-FL: Mark Selection as False Positive"
3. **Explain** why it's not vulnerable (optional)

### Confirm a Detection

1. **Place cursor** on a detected vulnerability
2. **Command Palette** → "SecureCode-FL: Confirm Vulnerability at Cursor"

### Quick Fix (Lightbulb Menu)

1. **Click** the 💡 lightbulb on a detected vulnerability
2. Choose:
   - "✗ Mark as False Positive"
   - "✓ Confirm Vulnerability"

### View Feedback Statistics

| Method          | Action                                                     |
| --------------- | ---------------------------------------------------------- |
| Command Palette | `Ctrl+Shift+P` → "SecureCode-FL: Show Feedback Statistics" |

---

## 5. Viewing the Feedback Database

### Using Python Script

```bash
cd SecureCode-FL
.\venv\Scripts\python.exe -c "
import sqlite3
conn = sqlite3.connect('data/user_feedback.db')
conn.row_factory = sqlite3.Row
rows = conn.execute('SELECT * FROM feedback').fetchall()
print(f'Total entries: {len(rows)}')
for r in rows:
    print(f'ID: {r[\"id\"]} | Type: {r[\"feedback_type\"]} | Label: {r[\"user_label\"]}')
    print(f'   Code: {r[\"code_snippet\"][:50]}...')
    print()
"
```

### Using SQLite CLI

```bash
sqlite3 data/user_feedback.db
```

```sql
-- View all feedback
SELECT * FROM feedback;

-- View untrained feedback
SELECT * FROM feedback WHERE trained = 0;

-- View statistics
SELECT feedback_type, COUNT(*) FROM feedback GROUP BY feedback_type;

-- Exit
.quit
```

### Using VS Code SQLite Extension

1. Install "SQLite Viewer" extension
2. Open `data/user_feedback.db`
3. Click on `feedback` table

### Using API Endpoint

```bash
# Get statistics
curl http://localhost:5000/feedback/stats

# List all feedback
curl http://localhost:5000/feedback/list

# Get untrained feedback
curl http://localhost:5000/feedback/untrained
```

---

## 6. Retraining the Model

After collecting feedback, retrain the model to learn from your corrections.

### Local Training (Single User)

```bash
cd SecureCode-FL

# Windows
.\venv\Scripts\python.exe federated\fl_feedback_client.py --mode local

# Linux/Mac
python federated/fl_feedback_client.py --mode local
```

### Expected Output

```
============================================================
  SecureCode-FL: Training on User Feedback
============================================================
✓ Loaded model from: .../fl_global_model.keras
✓ Loaded vectorizer from: .../tfidf_vectorizer.pkl
✓ Loaded 10 feedback entries
  - Vulnerable: 6
  - Secure: 4

🎯 Training on 10 feedback samples...
   Epochs: 5, Batch size: 32

Epoch 1/5 - loss: 0.4532 - accuracy: 0.7800
Epoch 2/5 - loss: 0.3210 - accuracy: 0.8500
...

✓ Training complete!
  Final Loss: 0.1234
  Final Accuracy: 0.9200
✓ Saved model to: .../model_feedback_20251203_123456.keras
✓ Updated main model
✓ Marked 10 feedback entries as trained
============================================================
```

### Reload Model in Server (Without Restart)

```bash
curl -X POST http://localhost:5000/model/reload
```

---

## 7. Federated Learning Commands

For distributed training across multiple users/machines.

### Start FL Server

```bash
cd SecureCode-FL

# Windows
.\venv\Scripts\python.exe federated\fl_server.py

# Linux/Mac
python federated/fl_server.py
```

### Connect as FL Client

```bash
# Windows
.\venv\Scripts\python.exe federated\fl_feedback_client.py --mode fl --server localhost:8080

# Linux/Mac
python federated/fl_feedback_client.py --mode fl --server localhost:8080
```

### Run FL Simulation (Local Testing)

```bash
# Windows
.\venv\Scripts\python.exe federated\fl_simulation.py

# Linux/Mac
python federated/fl_simulation.py
```

### Run Distributed FL Test

```bash
# Windows
.\venv\Scripts\python.exe federated\test_distributed.py

# Linux/Mac
python federated/test_distributed.py
```

---

## 8. API Endpoints Reference

| Endpoint                 | Method | Description                   |
| ------------------------ | ------ | ----------------------------- |
| `/health`                | GET    | Health check                  |
| `/scan`                  | POST   | Scan code for vulnerabilities |
| `/model/info`            | GET    | Get model information         |
| `/model/reload`          | POST   | Reload model from disk        |
| `/vulnerability-types`   | GET    | List vulnerability types      |
| `/feedback`              | POST   | Submit user feedback          |
| `/feedback/stats`        | GET    | Get feedback statistics       |
| `/feedback/list`         | GET    | List all feedback             |
| `/feedback/untrained`    | GET    | Get untrained feedback        |
| `/feedback/mark-trained` | POST   | Mark feedback as trained      |
| `/feedback/<id>`         | DELETE | Delete feedback entry         |

### Example: Scan Code

```bash
curl -X POST http://localhost:5000/scan \
  -H "Content-Type: application/json" \
  -d '{"code": "password = \"secret123\"", "language": "python", "filename": "test.py"}'
```

### Example: Submit Feedback

```bash
curl -X POST http://localhost:5000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "code_snippet": "password = os.environ.get(\"DB_PASS\")",
    "user_label": "secure",
    "original_detection": "Broken Authentication",
    "notes": "Uses environment variable",
    "file_path": "/project/config.py",
    "language": "python"
  }'
```

---

## 9. Keyboard Shortcuts

| Shortcut       | Action                                 |
| -------------- | -------------------------------------- |
| `Ctrl+Shift+S` | Scan current file                      |
| `Ctrl+Shift+P` | Open Command Palette                   |
| `Ctrl+.`       | Open Quick Fix menu (on vulnerability) |

---

## 10. Troubleshooting

### Server Connection Errors

```
Error: Cannot connect to SecureCode-FL server
```

**Solution:** Make sure the server is running:

```bash
.\venv\Scripts\python.exe inference_server\server.py
```

### Model Not Loading

```
⚠ No model found, using pattern-based detection only
```

**Solution:** Check model path exists:

```bash
ls models/federated/fl_global_model.keras
```

### Extension Not Working

**Solution:** Rebuild and restart:

```bash
cd vscode-extension
npm run compile
# Press F5 to restart extension
```

### Feedback Not Saving

**Solution:** Check database permissions:

```bash
ls -la data/user_feedback.db
```

### Port Already in Use

```
OSError: [Errno 98] Address already in use
```

**Solution:** Use a different port:

```bash
python inference_server/server.py --port 5001
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                    SecureCode-FL Commands                    │
├─────────────────────────────────────────────────────────────┤
│ START SERVER                                                 │
│   .\venv\Scripts\python.exe inference_server\server.py      │
│                                                              │
│ SCAN CODE                                                    │
│   Ctrl+Shift+S  or  Right-click → Scan Current File        │
│                                                              │
│ MARK AS VULNERABLE                                           │
│   Select code → Right-click → Mark Selection as Vulnerable  │
│                                                              │
│ MARK AS FALSE POSITIVE                                       │
│   Select code → Right-click → Mark as False Positive        │
│                                                              │
│ RETRAIN MODEL                                                │
│   .\venv\Scripts\python.exe federated\fl_feedback_client.py │
│                                                              │
│ VIEW FEEDBACK                                                │
│   curl http://localhost:5000/feedback/list                  │
└─────────────────────────────────────────────────────────────┘
```
