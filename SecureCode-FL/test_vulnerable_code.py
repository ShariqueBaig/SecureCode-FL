"""
SecureCode-FL Test File - Vulnerable Code Examples
==================================================
This file contains intentionally vulnerable code patterns
to test the SecureCode-FL VS Code extension.

Expected detections: 15+ vulnerabilities across OWASP API Top 10
"""

import os
import requests
import subprocess

# =============================================================================
# 1. BROKEN AUTHENTICATION (OWASP API2)
# =============================================================================

# ⚠️ Hardcoded password
password = "admin123"
db_password = "SuperSecret123!"

# ⚠️ Hardcoded API keys
api_key = "sk-proj-abcdef123456789"
secret_key = "ghp_xxxxxxxxxxxxxxxxxxxx"
aws_secret = "AKIAIOSFODNN7EXAMPLE"

# ⚠️ Hardcoded token
auth_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"

# ⚠️ SSL verification disabled
response = requests.get("https://api.example.com", verify=False)


# =============================================================================
# 2. BROKEN OBJECT LEVEL AUTHORIZATION (OWASP API1) - SQL Injection
# =============================================================================

def get_user_unsafe(user_id):
    """⚠️ SQL Injection vulnerability"""
    query = "SELECT * FROM users WHERE id = " + user_id
    # cursor.execute(query)  # Dangerous!
    return query

def search_products(search_term):
    """⚠️ SQL Injection via string formatting"""
    query = "SELECT * FROM products WHERE name LIKE '%" + search_term + "%'"
    return query


# =============================================================================
# 3. UNSAFE CONSUMPTION OF APIs (OWASP API10)
# =============================================================================

def process_user_input(user_input):
    """⚠️ Dangerous eval() usage"""
    result = eval(user_input)
    return result

def run_command(cmd):
    """⚠️ Command injection via exec()"""
    exec(cmd)

def execute_system_command(user_cmd):
    """⚠️ Shell injection vulnerability"""
    subprocess.call(user_cmd, shell=True)


# =============================================================================
# 4. SECURITY MISCONFIGURATION (OWASP API8)
# =============================================================================

# ⚠️ Debug mode enabled
DEBUG = True
FLASK_DEBUG = True

# ⚠️ Insecure HTTP
API_URL = "http://api.example.com/v1/users"
WEBHOOK_URL = "http://hooks.example.com/notify"

# ⚠️ Permissive CORS (simulated)
# CORS(app, origins="*")  # Would allow all origins


# =============================================================================
# 5. UNRESTRICTED RESOURCE CONSUMPTION (OWASP API4)
# =============================================================================

def infinite_loop_risk():
    """⚠️ Potential DoS via infinite loop"""
    while True:
        pass  # No exit condition

def fixed_sleep():
    """⚠️ Fixed sleep can cause issues"""
    import time
    time.sleep(30)


# =============================================================================
# 6. SERVER SIDE REQUEST FORGERY (OWASP API7)
# =============================================================================

def fetch_url(url):
    """⚠️ SSRF - unvalidated URL from user"""
    response = requests.get(url)  # url could be internal like http://169.254.169.254
    return response.text


# =============================================================================
# 7. XSS Vulnerabilities (for JavaScript/Frontend)
# =============================================================================

# Simulated dangerous patterns that would be caught in JS files:
# element.innerHTML = userData;  // XSS risk
# document.write(userInput);     // XSS risk


# =============================================================================
# 8. Additional Vulnerable Patterns
# =============================================================================

def connect_database():
    """Multiple credential issues"""
    host = "localhost"
    user = "root"
    password = "root123"  # ⚠️ Hardcoded DB password
    database = "production_db"
    
    connection_string = f"mysql://{user}:{password}@{host}/{database}"
    return connection_string

def log_sensitive_data(user):
    """⚠️ Logging sensitive information"""
    print(f"User password: {user['password']}")  # Never log passwords!
    print(f"API Key: {api_key}")

def weak_crypto():
    """⚠️ Weak cryptographic practices"""
    import hashlib
    password = "user_password"
    # MD5 is weak for password hashing
    hashed = hashlib.md5(password.encode()).hexdigest()
    return hashed


# =============================================================================
# SUMMARY OF EXPECTED VULNERABILITIES
# =============================================================================
"""
Expected SecureCode-FL Detections:

1. Line 21: Hardcoded password (CWE-798) - HIGH
2. Line 22: Hardcoded password (CWE-798) - HIGH  
3. Line 25: Hardcoded API key (CWE-798) - HIGH
4. Line 26: Hardcoded secret (CWE-798) - HIGH
5. Line 27: Hardcoded AWS secret (CWE-798) - HIGH
6. Line 30: Hardcoded token (CWE-798) - HIGH
7. Line 33: SSL verification disabled (CWE-295) - HIGH
8. Line 41: SQL injection (CWE-89) - HIGH
9. Line 46: SQL injection (CWE-89) - HIGH
10. Line 55: eval() usage (CWE-95) - HIGH
11. Line 59: exec() usage (CWE-78) - HIGH
12. Line 63: Shell injection (CWE-78) - HIGH
13. Line 71: Debug mode enabled (CWE-489) - MEDIUM
14. Line 72: Debug mode enabled (CWE-489) - MEDIUM
15. Line 75: Insecure HTTP (CWE-319) - LOW
16. Line 76: Insecure HTTP (CWE-319) - LOW
17. Line 87: Infinite loop (CWE-835) - MEDIUM
18. Line 92: Fixed sleep (CWE-400) - LOW
19. Line 100: SSRF risk (CWE-918) - HIGH
20. Line 117: Hardcoded password (CWE-798) - HIGH

Total: 20+ vulnerabilities across multiple OWASP categories
"""

if __name__ == "__main__":
    print("This file contains intentionally vulnerable code for testing.")
    print("DO NOT use any of these patterns in production!")
