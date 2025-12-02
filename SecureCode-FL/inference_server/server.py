"""
SecureCode-FL Inference Server
Flask-based REST API for vulnerability detection
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import tensorflow as tf
import joblib
import os
import time
import re
from typing import List, Dict, Any

app = Flask(__name__)
CORS(app)

# Global model and vectorizer
model = None
vectorizer = None
MODEL_VERSION = "1.0.0-fl"

# OWASP API Top 10 Categories
VULNERABILITY_TYPES = [
    "Broken Object Level Authorization",
    "Broken Authentication", 
    "Broken Object Property Level Authorization",
    "Unrestricted Resource Consumption",
    "Broken Function Level Authorization",
    "Unrestricted Access to Sensitive Business Flows",
    "Server Side Request Forgery",
    "Security Misconfiguration",
    "Improper Inventory Management",
    "Unsafe Consumption of APIs"
]

# Vulnerability patterns for enhanced detection
VULNERABILITY_PATTERNS = {
    "Broken Authentication": [
        # Hardcoded credentials - various patterns
        (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password", "high", "CWE-798"),
        (r'passwd\s*=\s*["\'][^"\']+["\']', "Hardcoded password", "high", "CWE-798"),
        (r'pwd\s*=\s*["\'][^"\']+["\']', "Hardcoded password", "high", "CWE-798"),
        (r'db_password\s*=\s*["\'][^"\']+["\']', "Hardcoded database password", "high", "CWE-798"),
        (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key", "high", "CWE-798"),
        (r'apikey\s*=\s*["\'][^"\']+["\']', "Hardcoded API key", "high", "CWE-798"),
        (r'secret[_-]?key\s*=\s*["\'][^"\']+["\']', "Hardcoded secret key", "high", "CWE-798"),
        (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret", "high", "CWE-798"),
        (r'aws[_-]?secret\s*=\s*["\'][^"\']+["\']', "Hardcoded AWS secret", "high", "CWE-798"),
        (r'auth[_-]?token\s*=\s*["\'][^"\']+["\']', "Hardcoded auth token", "high", "CWE-798"),
        (r'token\s*=\s*["\'](eyJ|ghp_|sk-|AKIA)[^"\']+["\']', "Hardcoded token/key", "high", "CWE-798"),
        (r'private[_-]?key\s*=\s*["\'][^"\']+["\']', "Hardcoded private key", "high", "CWE-798"),
        (r'verify\s*=\s*False', "SSL verification disabled", "high", "CWE-295"),
        (r'VERIFY_SSL\s*=\s*False', "SSL verification disabled", "high", "CWE-295"),
    ],
    "Broken Object Level Authorization": [
        # SQL injection - more permissive patterns
        (r'SELECT\s+.+\s+FROM\s+.+\s*\+', "SQL injection risk - string concatenation", "high", "CWE-89"),
        (r'SELECT\s+.+\s+WHERE\s+.+\s*\+', "SQL injection risk - string concatenation", "high", "CWE-89"),
        (r'INSERT\s+INTO\s+.+\s*\+', "SQL injection risk - string concatenation", "high", "CWE-89"),
        (r'UPDATE\s+.+\s+SET\s+.+\s*\+', "SQL injection risk - string concatenation", "high", "CWE-89"),
        (r'DELETE\s+FROM\s+.+\s*\+', "SQL injection risk - string concatenation", "high", "CWE-89"),
        (r'execute\s*\(\s*["\'].*%', "SQL injection via string format", "high", "CWE-89"),
        (r'cursor\.execute\s*\([^,]*\+', "SQL injection in cursor.execute", "high", "CWE-89"),
        (r'query\s*=\s*["\']SELECT.+\+', "SQL injection - query concatenation", "high", "CWE-89"),
        (r'query\s*=\s*f["\']SELECT', "SQL injection - f-string query", "high", "CWE-89"),
        (r'\.format\s*\(.+\).*(?:SELECT|INSERT|UPDATE|DELETE)', "SQL injection via format()", "medium", "CWE-89"),
    ],
    "Unsafe Consumption of APIs": [
        (r'eval\s*\(', "Use of eval() - code injection risk", "high", "CWE-95"),
        (r'exec\s*\(', "Use of exec() - code injection risk", "high", "CWE-78"),
        (r'compile\s*\(.+\)\s*$', "Dynamic code compilation", "medium", "CWE-95"),
        (r'\.innerHTML\s*=', "innerHTML assignment (XSS risk)", "medium", "CWE-79"),
        (r'document\.write\s*\(', "document.write (XSS risk)", "medium", "CWE-79"),
        (r'outerHTML\s*=', "outerHTML assignment (XSS risk)", "medium", "CWE-79"),
        (r'subprocess\.call\s*\(.+shell\s*=\s*True', "Shell injection risk", "high", "CWE-78"),
        (r'subprocess\.run\s*\(.+shell\s*=\s*True', "Shell injection risk", "high", "CWE-78"),
        (r'subprocess\.Popen\s*\(.+shell\s*=\s*True', "Shell injection risk", "high", "CWE-78"),
        (r'os\.system\s*\(', "OS command execution risk", "high", "CWE-78"),
        (r'os\.popen\s*\(', "OS command execution risk", "high", "CWE-78"),
        (r'pickle\.loads?\s*\(', "Insecure deserialization", "high", "CWE-502"),
        (r'yaml\.load\s*\([^,]+\)', "Unsafe YAML load", "high", "CWE-502"),
        (r'marshal\.loads?\s*\(', "Insecure deserialization", "high", "CWE-502"),
    ],
    "Security Misconfiguration": [
        (r'DEBUG\s*=\s*True', "Debug mode enabled", "medium", "CWE-489"),
        (r'FLASK_DEBUG\s*=\s*True', "Flask debug mode enabled", "medium", "CWE-489"),
        (r'debug\s*=\s*True', "Debug mode enabled", "medium", "CWE-489"),
        (r'http://(?!localhost|127\.0\.0\.1)', "Insecure HTTP protocol", "low", "CWE-319"),
        (r'CORS\s*\([^)]*origins\s*=\s*["\']\*["\']', "Permissive CORS - all origins", "medium", "CWE-942"),
        (r'allow_all_origins\s*=\s*True', "All origins allowed", "medium", "CWE-942"),
        (r'Access-Control-Allow-Origin.*\*', "Permissive CORS header", "medium", "CWE-942"),
    ],
    "Unrestricted Resource Consumption": [
        (r'while\s+True\s*:', "Infinite loop - potential DoS", "medium", "CWE-835"),
        (r'while\s+1\s*:', "Infinite loop - potential DoS", "medium", "CWE-835"),
        (r'for\s+.+\s+in\s+range\s*\(\s*\d{6,}\s*\)', "Very large loop iteration", "medium", "CWE-400"),
        (r'time\.sleep\s*\(\s*\d+\s*\)', "Fixed sleep duration", "low", "CWE-400"),
        (r'\.read\s*\(\s*\)', "Unbounded read - potential memory issue", "medium", "CWE-400"),
        (r'\.readlines\s*\(\s*\)', "Reading all lines - potential memory issue", "low", "CWE-400"),
    ],
    "Server Side Request Forgery": [
        (r'requests\.(get|post|put|delete|patch)\s*\(\s*[a-zA-Z_][a-zA-Z0-9_]*\s*[,)]', "SSRF risk - unvalidated URL variable", "high", "CWE-918"),
        (r'requests\.(get|post|put|delete|patch)\s*\(\s*f["\']', "SSRF risk - f-string URL", "medium", "CWE-918"),
        (r'urllib\.(request\.)?urlopen\s*\(\s*[a-zA-Z_]', "SSRF risk in urllib", "high", "CWE-918"),
        (r'httplib\.HTTPConnection\s*\(\s*[a-zA-Z_]', "SSRF risk - unvalidated host", "high", "CWE-918"),
    ],
    "Improper Inventory Management": [
        (r'print\s*\(.*password', "Logging sensitive data - password", "medium", "CWE-532"),
        (r'print\s*\(.*secret', "Logging sensitive data - secret", "medium", "CWE-532"),
        (r'print\s*\(.*api_key', "Logging sensitive data - API key", "medium", "CWE-532"),
        (r'print\s*\(.*token', "Logging sensitive data - token", "medium", "CWE-532"),
        (r'logging\..+password', "Logging sensitive data - password", "medium", "CWE-532"),
        (r'console\.log\s*\(.*(password|secret|key|token)', "Logging sensitive data", "medium", "CWE-532"),
    ],
    "Broken Function Level Authorization": [
        (r'@app\.route.+methods\s*=\s*\[[^\]]*["\']GET["\'][^\]]*["\']POST["\']', "Mixed HTTP methods on endpoint", "low", "CWE-285"),
        (r'if\s+.*==\s*["\']admin["\']', "Hardcoded role check", "low", "CWE-285"),
    ],
    "Cryptographic Failures": [
        (r'hashlib\.md5\s*\(', "Weak hash algorithm - MD5", "medium", "CWE-328"),
        (r'hashlib\.sha1\s*\(', "Weak hash algorithm - SHA1", "medium", "CWE-328"),
        (r'DES\s*\(', "Weak encryption - DES", "high", "CWE-327"),
        (r'random\.(random|randint|choice)\s*\(', "Insecure random for crypto", "medium", "CWE-330"),
    ]
}


def load_model():
    """Load the trained FL model and vectorizer"""
    global model, vectorizer
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Try to load FL model first, then fall back to regular model
    model_paths = [
        os.path.join(base_path, "models", "federated", "fl_global_model.keras"),
        os.path.join(base_path, "models", "mlp_v3_expanded.keras"),
        os.path.join(base_path, "models", "neural", "mlp_model.keras"),
    ]
    
    for model_path in model_paths:
        if os.path.exists(model_path):
            model = tf.keras.models.load_model(model_path)
            print(f"✓ Loaded model from: {model_path}")
            break
    else:
        print("⚠ No model found, using pattern-based detection only")
    
    # Load vectorizer
    vectorizer_paths = [
        os.path.join(base_path, "models", "tfidf_vectorizer.joblib"),
        os.path.join(base_path, "models", "neural", "tfidf_vectorizer.joblib"),
    ]
    
    for vec_path in vectorizer_paths:
        if os.path.exists(vec_path):
            vectorizer = joblib.load(vec_path)
            print(f"✓ Loaded vectorizer from: {vec_path}")
            break
    else:
        print("⚠ No vectorizer found, using pattern-based detection only")


def analyze_code_with_model(code: str) -> Dict[str, Any]:
    """Analyze code using the ML model"""
    if model is None or vectorizer is None:
        return {"is_vulnerable": False, "confidence": 0.0, "vulnerability_type": None}
    
    try:
        # Vectorize the code
        code_vector = vectorizer.transform([code]).toarray()
        
        # Get prediction
        prediction = model.predict(code_vector, verbose=0)[0][0]
        is_vulnerable = prediction > 0.5
        confidence = float(prediction) if is_vulnerable else float(1 - prediction)
        
        return {
            "is_vulnerable": is_vulnerable,
            "confidence": confidence,
            "vulnerability_type": "General Vulnerability" if is_vulnerable else None
        }
    except Exception as e:
        print(f"Model prediction error: {e}")
        return {"is_vulnerable": False, "confidence": 0.0, "vulnerability_type": None}


def analyze_code_with_patterns(code: str, language: str) -> List[Dict[str, Any]]:
    """Analyze code using regex patterns for specific vulnerabilities"""
    vulnerabilities = []
    lines = code.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        for vuln_type, patterns in VULNERABILITY_PATTERNS.items():
            for pattern, message, severity, cwe_id in patterns:
                matches = list(re.finditer(pattern, line, re.IGNORECASE))
                for match in matches:
                    vulnerabilities.append({
                        "line": line_num,
                        "column": match.start(),
                        "endLine": line_num,
                        "endColumn": match.end(),
                        "vulnerability_type": vuln_type,
                        "confidence": 0.90,
                        "severity": severity,
                        "message": message,
                        "suggestion": get_suggestion(vuln_type, cwe_id),
                        "cwe_id": cwe_id,
                        "owasp_category": vuln_type
                    })
    
    return vulnerabilities


def get_suggestion(vuln_type: str, cwe_id: str) -> str:
    """Get remediation suggestion based on vulnerability type"""
    suggestions = {
        "CWE-798": "Store credentials in environment variables or use a secrets manager",
        "CWE-295": "Enable SSL/TLS certificate verification",
        "CWE-89": "Use parameterized queries or prepared statements",
        "CWE-95": "Avoid eval() - use safer alternatives like ast.literal_eval()",
        "CWE-78": "Validate and sanitize all user inputs before command execution",
        "CWE-79": "Sanitize HTML output or use textContent instead of innerHTML",
        "CWE-489": "Disable debug mode in production environments",
        "CWE-319": "Use HTTPS instead of HTTP for secure communication",
        "CWE-942": "Configure CORS to allow only trusted origins",
        "CWE-835": "Add proper exit conditions to loops",
        "CWE-400": "Implement timeouts and resource limits",
        "CWE-918": "Validate and whitelist allowed URLs for external requests",
    }
    return suggestions.get(cwe_id, f"Review code for {vuln_type} vulnerabilities")


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model_loaded": model is not None,
        "vectorizer_loaded": vectorizer is not None,
        "version": MODEL_VERSION
    })


@app.route('/scan', methods=['POST'])
def scan_code():
    """Main endpoint to scan code for vulnerabilities"""
    start_time = time.time()
    
    data = request.get_json()
    if not data or 'code' not in data:
        return jsonify({"error": "No code provided"}), 400
    
    code = data['code']
    language = data.get('language', 'python')
    filename = data.get('filename', 'unknown')
    
    vulnerabilities = []
    
    # 1. Pattern-based detection (always runs)
    pattern_vulns = analyze_code_with_patterns(code, language)
    vulnerabilities.extend(pattern_vulns)
    
    # 2. ML model detection (if available)
    if model is not None and vectorizer is not None:
        # Analyze code blocks/functions separately
        code_blocks = extract_code_blocks(code)
        for block in code_blocks:
            ml_result = analyze_code_with_model(block['code'])
            if ml_result['is_vulnerable'] and ml_result['confidence'] > 0.7:
                # Check if this vulnerability is not already detected by patterns
                existing = any(
                    v['line'] == block['start_line'] 
                    for v in vulnerabilities
                )
                if not existing:
                    vulnerabilities.append({
                        "line": block['start_line'],
                        "column": 0,
                        "endLine": block['end_line'],
                        "endColumn": len(code.split('\n')[block['end_line']-1]) if block['end_line'] <= len(code.split('\n')) else 0,
                        "vulnerability_type": "ML-Detected Vulnerability",
                        "confidence": ml_result['confidence'],
                        "severity": "medium",
                        "message": "Potential vulnerability detected by ML model",
                        "suggestion": "Review this code block for security issues",
                        "cwe_id": None,
                        "owasp_category": "General"
                    })
    
    # Remove duplicates and sort by line number
    seen = set()
    unique_vulns = []
    for v in vulnerabilities:
        key = (v['line'], v['column'], v['vulnerability_type'])
        if key not in seen:
            seen.add(key)
            unique_vulns.append(v)
    
    unique_vulns.sort(key=lambda x: (x['line'], x['column']))
    
    scan_time = (time.time() - start_time) * 1000  # Convert to ms
    
    return jsonify({
        "success": True,
        "vulnerabilities": unique_vulns,
        "scan_time_ms": round(scan_time, 2),
        "model_version": MODEL_VERSION,
        "file": filename,
        "language": language
    })


def extract_code_blocks(code: str) -> List[Dict[str, Any]]:
    """Extract meaningful code blocks for ML analysis"""
    blocks = []
    lines = code.split('\n')
    
    # Simple block extraction: functions, classes, and significant code chunks
    current_block = []
    start_line = 1
    
    for i, line in enumerate(lines, 1):
        # Detect block boundaries
        if re.match(r'^(def |class |async def |function |const |let |var |public |private )', line.strip()):
            if current_block:
                blocks.append({
                    'code': '\n'.join(current_block),
                    'start_line': start_line,
                    'end_line': i - 1
                })
            current_block = [line]
            start_line = i
        else:
            current_block.append(line)
    
    # Add last block
    if current_block:
        blocks.append({
            'code': '\n'.join(current_block),
            'start_line': start_line,
            'end_line': len(lines)
        })
    
    # If no blocks detected, treat whole code as one block
    if not blocks:
        blocks.append({
            'code': code,
            'start_line': 1,
            'end_line': len(lines)
        })
    
    return blocks


@app.route('/model/info', methods=['GET'])
def model_info():
    """Get information about the loaded model"""
    info = {
        "version": MODEL_VERSION,
        "type": "Federated Learning MLP",
        "accuracy": 0.947,
        "training_method": "FedAvg",
        "num_clients": 3,
        "fl_rounds": 20,
        "model_loaded": model is not None,
        "vectorizer_loaded": vectorizer is not None,
        "supported_languages": ["python", "javascript", "typescript", "java", "csharp", "php"],
        "vulnerability_categories": VULNERABILITY_TYPES
    }
    
    if model is not None:
        info["model_params"] = int(model.count_params())
    
    return jsonify(info)


@app.route('/vulnerability-types', methods=['GET'])
def get_vulnerability_types():
    """Get list of supported vulnerability types"""
    return jsonify({
        "types": VULNERABILITY_TYPES,
        "count": len(VULNERABILITY_TYPES)
    })


if __name__ == '__main__':
    print("=" * 60)
    print("  SecureCode-FL Inference Server")
    print("=" * 60)
    
    load_model()
    
    print("\n🚀 Starting server on http://localhost:5000")
    print("📋 Endpoints:")
    print("   GET  /health           - Health check")
    print("   POST /scan             - Scan code for vulnerabilities")
    print("   GET  /model/info       - Get model information")
    print("   GET  /vulnerability-types - Get supported vulnerability types")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=False)
