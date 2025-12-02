"""
Dataset Expansion Module
========================

Expands the original 60-sample dataset to improve neural network training.
Generates synthetic vulnerable and secure code samples based on OWASP API Security Top 10.

Target: 500-1000 samples for better ML/DL performance.
"""

import pandas as pd
import numpy as np
import random
import os
from config import MODELS_DIR, RESULTS_DIR, RANDOM_STATE

# Set seed for reproducibility
random.seed(RANDOM_STATE)
np.random.seed(RANDOM_STATE)


class VulnerableCodeGenerator:
    """
    Generates synthetic vulnerable and secure Python code samples
    based on OWASP API Security Top 10 vulnerabilities.
    """
    
    def __init__(self):
        self.vulnerability_types = [
            "Broken Object Level Authorization",
            "Broken Authentication", 
            "Broken Function Level Authorization",
            "Unrestricted Access to Sensitive Business Flows",
            "Server Side Request Forgery",
            "Unrestricted Resource Consumption",
            "Security Misconfiguration",
            "Broken Object Property Level Authorization",
            "Unsafe Consumption of APIs",
            "Improper Inventory Management"
        ]
        
        # Variable name pools for variation
        self.user_vars = ['user', 'current_user', 'logged_user', 'auth_user', 'request_user', 'active_user']
        self.id_vars = ['user_id', 'id', 'uid', 'account_id', 'profile_id', 'record_id']
        self.data_vars = ['data', 'payload', 'request_data', 'body', 'params', 'input_data']
        self.resource_vars = ['resource', 'item', 'record', 'document', 'entry', 'object']
        
    # =========================================================
    # API1: Broken Object Level Authorization (BOLA)
    # =========================================================
    def generate_bola_vulnerable(self):
        """Generate BOLA vulnerable code samples"""
        templates = [
            # Template 1: Direct object access without authorization
            '''from flask import Flask, request, jsonify
app = Flask(__name__)

{resource_db} = {{1: {{"name": "Alice", "email": "alice@example.com", "balance": 5000}},
              2: {{"name": "Bob", "email": "bob@example.com", "balance": 3000}}}}

@app.route('/{endpoint}/<int:{id_var}>', methods=['GET'])
def get_{resource}({id_var}):
    {resource} = {resource_db}.get({id_var})
    if {resource}:
        return jsonify({resource})
    return jsonify({{"error": "Not found"}}), 404

if __name__ == '__main__':
    app.run(debug=True)''',
    
            # Template 2: Update without ownership check
            '''from flask import Flask, request, jsonify
app = Flask(__name__)

{resource_db} = {{1: {{"owner": 1, "content": "Private data"}},
              2: {{"owner": 2, "content": "Secret info"}}}}

@app.route('/{endpoint}/<int:{id_var}>', methods=['PUT'])
def update_{resource}({id_var}):
    if {id_var} in {resource_db}:
        {resource_db}[{id_var}].update(request.json)
        return jsonify({{"success": "Updated"}})
    return jsonify({{"error": "Not found"}}), 404

if __name__ == '__main__':
    app.run(debug=True)''',

            # Template 3: Delete without authorization
            '''from flask import Flask, request, jsonify
app = Flask(__name__)

{resource_db} = {{}}

@app.route('/{endpoint}/<int:{id_var}>', methods=['DELETE'])
def delete_{resource}({id_var}):
    if {id_var} in {resource_db}:
        del {resource_db}[{id_var}]
        return jsonify({{"success": "Deleted"}})
    return jsonify({{"error": "Not found"}}), 404

if __name__ == '__main__':
    app.run()''',

            # Template 4: List all records without filtering
            '''from flask import Flask, jsonify
app = Flask(__name__)

{resource_db} = [
    {{"id": 1, "user_id": 1, "data": "User 1 private"}},
    {{"id": 2, "user_id": 2, "data": "User 2 private"}}
]

@app.route('/{endpoint}', methods=['GET'])
def list_{resource}s():
    return jsonify({resource_db})

if __name__ == '__main__':
    app.run()''',
        ]
        
        samples = []
        exploits = [
            "Inadequate User Validation",
            "Lack of Ownership Verification", 
            "Missing Role-Based Access Control",
            "Direct Object Reference Without Auth",
            "Unfiltered Resource Access"
        ]
        
        for template in templates:
            for _ in range(3):  # Generate 3 variations per template
                code = template.format(
                    resource=random.choice(['user', 'account', 'profile', 'record', 'document']),
                    resource_db=random.choice(['users', 'accounts', 'profiles', 'records', 'database']),
                    endpoint=random.choice(['user', 'account', 'profile', 'api/user', 'api/account']),
                    id_var=random.choice(self.id_vars)
                )
                samples.append({
                    'Primary Vulnerability': 'Broken Object Level Authorization',
                    'Exploit': random.choice(exploits),
                    'Result': 'Error',
                    'Code': code
                })
        
        return samples
    
    def generate_bola_secure(self):
        """Generate BOLA secure code samples"""
        templates = [
            # Template 1: With authorization check
            '''from flask import Flask, request, jsonify
app = Flask(__name__)

users = {{1: {{"name": "Alice", "email": "alice@example.com"}},
         2: {{"name": "Bob", "email": "bob@example.com"}}}}
api_keys = {{"key_alice": 1, "key_bob": 2}}

def get_user_from_token(token):
    return api_keys.get(token)

@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({{"error": "Missing authorization"}}), 401
    
    requesting_user = get_user_from_token(token)
    if requesting_user != user_id:
        return jsonify({{"error": "Unauthorized"}}), 403
    
    user = users.get(user_id)
    if user:
        return jsonify(user)
    return jsonify({{"error": "Not found"}}), 404

if __name__ == '__main__':
    app.run()''',

            # Template 2: With ownership verification
            '''from flask import Flask, request, jsonify
app = Flask(__name__)

records = {{1: {{"owner_id": 1, "data": "Private"}},
           2: {{"owner_id": 2, "data": "Secret"}}}}

def get_current_user():
    token = request.headers.get('Authorization')
    return verify_token(token)

@app.route('/record/<int:record_id>', methods=['PUT'])
def update_record(record_id):
    current_user = get_current_user()
    if not current_user:
        return jsonify({{"error": "Unauthorized"}}), 401
    
    record = records.get(record_id)
    if not record:
        return jsonify({{"error": "Not found"}}), 404
    
    if record['owner_id'] != current_user['id']:
        return jsonify({{"error": "Forbidden"}}), 403
    
    records[record_id].update(request.json)
    return jsonify({{"success": "Updated"}})

if __name__ == '__main__':
    app.run()''',

            # Template 3: Role-based access control
            '''from flask import Flask, request, jsonify
from functools import wraps
app = Flask(__name__)

def require_role(role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = get_current_user()
            if not user or user.get('role') != role:
                return jsonify({{"error": "Forbidden"}}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

@app.route('/admin/users', methods=['GET'])
@require_role('admin')
def list_all_users():
    return jsonify(users)

if __name__ == '__main__':
    app.run()''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(4):
                samples.append({
                    'Primary Vulnerability': 'Broken Object Level Authorization',
                    'Exploit': 'Proper Authorization Check',
                    'Result': 'Good',
                    'Code': template
                })
        
        return samples

    # =========================================================
    # API2: Broken Authentication
    # =========================================================
    def generate_auth_vulnerable(self):
        """Generate Broken Authentication vulnerable code samples"""
        templates = [
            # Template 1: Hardcoded credentials
            '''from flask import Flask, request, jsonify
app = Flask(__name__)

USERNAME = "admin"
PASSWORD = "password123"

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    
    if username == USERNAME and password == PASSWORD:
        return jsonify({{"token": "admin_token_12345"}})
    return jsonify({{"error": "Invalid credentials"}}), 401

if __name__ == '__main__':
    app.run(debug=True)''',

            # Template 2: No rate limiting
            '''from flask import Flask, request, jsonify
app = Flask(__name__)

users = {{"admin": "secret123", "user": "pass456"}}

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    
    if users.get(username) == password:
        return jsonify({{"success": True, "token": generate_token()}})
    return jsonify({{"error": "Invalid"}})

if __name__ == '__main__':
    app.run()''',

            # Template 3: Insecure session management
            '''from flask import Flask, request, session
app = Flask(__name__)
app.secret_key = 'secret'

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    session['user'] = username
    session['logged_in'] = True
    return "Logged in"

@app.route('/dashboard')
def dashboard():
    if session.get('logged_in'):
        return f"Welcome {{session['user']}}"
    return "Please login"

if __name__ == '__main__':
    app.run()''',

            # Template 4: Weak password validation
            '''from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.json.get('username')
    password = request.json.get('password')
    
    if len(password) >= 4:
        save_user(username, password)
        return jsonify({{"success": True}})
    return jsonify({{"error": "Password too short"}})

if __name__ == '__main__':
    app.run()''',

            # Template 5: Token in URL
            '''from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/api/data')
def get_data():
    token = request.args.get('token')
    if validate_token(token):
        return jsonify({{"data": "sensitive info"}})
    return jsonify({{"error": "Invalid token"}}), 401

if __name__ == '__main__':
    app.run()''',
        ]
        
        samples = []
        exploits = [
            "Hardcoded Credentials",
            "Missing Rate Limiting",
            "Insecure Session Management",
            "Weak Password Policy",
            "Token Exposure in URL"
        ]
        
        for i, template in enumerate(templates):
            for _ in range(2):
                samples.append({
                    'Primary Vulnerability': 'Broken Authentication',
                    'Exploit': exploits[i % len(exploits)],
                    'Result': 'Error',
                    'Code': template
                })
        
        return samples

    def generate_auth_secure(self):
        """Generate Broken Authentication secure code samples"""
        templates = [
            # Template 1: Secure authentication with hashing
            '''from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

users_db = {}

@app.route('/register', methods=['POST'])
def register():
    username = request.json.get('username')
    password = request.json.get('password')
    
    if len(password) < 12:
        return jsonify({{"error": "Password must be at least 12 characters"}}), 400
    
    hashed = generate_password_hash(password)
    users_db[username] = hashed
    return jsonify({{"success": True}})

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    
    stored_hash = users_db.get(username)
    if stored_hash and check_password_hash(stored_hash, password):
        token = generate_secure_token(username)
        return jsonify({{"token": token}})
    return jsonify({{"error": "Invalid credentials"}}), 401

if __name__ == '__main__':
    app.run()''',

            # Template 2: With rate limiting
            '''from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
limiter = Limiter(app, key_func=get_remote_address)

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    
    user = authenticate_user(username, password)
    if user:
        return jsonify({{"token": create_jwt_token(user)}})
    return jsonify({{"error": "Invalid credentials"}}), 401

if __name__ == '__main__':
    app.run()''',

            # Template 3: Secure session management
            '''from flask import Flask, request, session, jsonify
from datetime import timedelta
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

@app.route('/login', methods=['POST'])
def login():
    if authenticate(request.json):
        session.permanent = True
        session['user_id'] = request.json['user_id']
        session.regenerate()
        return jsonify({{"success": True}})
    return jsonify({{"error": "Failed"}}), 401

if __name__ == '__main__':
    app.run()''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(3):
                samples.append({
                    'Primary Vulnerability': 'Broken Authentication',
                    'Exploit': 'Secure Authentication Implementation',
                    'Result': 'Good',
                    'Code': template
                })
        
        return samples

    # =========================================================
    # API3: Broken Object Property Level Authorization
    # =========================================================
    def generate_property_auth_vulnerable(self):
        """Generate Broken Object Property Level Authorization vulnerable samples"""
        templates = [
            # Mass assignment vulnerability
            '''from flask import Flask, request, jsonify
app = Flask(__name__)

users = {{1: {{"name": "Alice", "email": "alice@test.com", "role": "user", "balance": 100}}}}

@app.route('/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    if user_id in users:
        users[user_id].update(request.json)
        return jsonify({{"success": True}})
    return jsonify({{"error": "Not found"}}), 404

if __name__ == '__main__':
    app.run()''',

            # Exposing sensitive fields
            '''from flask import Flask, jsonify
app = Flask(__name__)

users = {{
    1: {{"name": "Alice", "email": "alice@test.com", "password_hash": "abc123", "ssn": "123-45-6789"}}
}}

@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    return jsonify(users.get(user_id, {{}}))

if __name__ == '__main__':
    app.run()''',

            # Unvalidated property update
            '''from flask import Flask, request, jsonify
app = Flask(__name__)

products = {{1: {{"name": "Item", "price": 100, "discount": 0}}}}

@app.route('/product/<int:id>', methods=['PATCH'])
def update_product(id):
    for key, value in request.json.items():
        products[id][key] = value
    return jsonify(products[id])

if __name__ == '__main__':
    app.run()''',
        ]
        
        samples = []
        exploits = ["Mass Assignment", "Sensitive Data Exposure", "Unvalidated Property Update"]
        
        for i, template in enumerate(templates):
            for _ in range(3):
                samples.append({
                    'Primary Vulnerability': 'Broken Object Property Level Authorization',
                    'Exploit': exploits[i],
                    'Result': 'Error',
                    'Code': template
                })
        
        return samples

    def generate_property_auth_secure(self):
        """Generate Broken Object Property Level Authorization secure samples"""
        templates = [
            # Whitelist allowed fields
            '''from flask import Flask, request, jsonify
app = Flask(__name__)

ALLOWED_UPDATE_FIELDS = ['name', 'email']

users = {{1: {{"name": "Alice", "email": "alice@test.com", "role": "user"}}}}

@app.route('/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    if user_id not in users:
        return jsonify({{"error": "Not found"}}), 404
    
    update_data = {{k: v for k, v in request.json.items() if k in ALLOWED_UPDATE_FIELDS}}
    users[user_id].update(update_data)
    return jsonify({{"success": True}})

if __name__ == '__main__':
    app.run()''',

            # Filter sensitive fields in response
            '''from flask import Flask, jsonify
app = Flask(__name__)

SAFE_FIELDS = ['name', 'email', 'created_at']

users = {{
    1: {{"name": "Alice", "email": "alice@test.com", "password_hash": "abc", "ssn": "123"}}
}}

@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = users.get(user_id)
    if user:
        safe_user = {{k: v for k, v in user.items() if k in SAFE_FIELDS}}
        return jsonify(safe_user)
    return jsonify({{"error": "Not found"}}), 404

if __name__ == '__main__':
    app.run()''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(4):
                samples.append({
                    'Primary Vulnerability': 'Broken Object Property Level Authorization',
                    'Exploit': 'Proper Field Filtering',
                    'Result': 'Good',
                    'Code': template
                })
        
        return samples

    # =========================================================
    # API4: Unrestricted Resource Consumption
    # =========================================================
    def generate_resource_vulnerable(self):
        """Generate Unrestricted Resource Consumption vulnerable samples"""
        templates = [
            # Unrestricted file upload
            '''from flask import Flask, request
app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    file.save(f'/uploads/{{file.filename}}')
    return "Uploaded"

if __name__ == '__main__':
    app.run()''',

            # Unrestricted loop
            '''from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process():
    count = int(request.json.get('count', 0))
    result = []
    for i in range(count):
        result.append(expensive_operation(i))
    return jsonify(result)

if __name__ == '__main__':
    app.run()''',

            # Unrestricted database query
            '''from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    limit = request.args.get('limit', 1000000)
    results = database.query(f"SELECT * FROM items WHERE name LIKE '%{{query}}%' LIMIT {{limit}}")
    return jsonify(results)

if __name__ == '__main__':
    app.run()''',

            # No pagination
            '''from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/items', methods=['GET'])
def get_all_items():
    items = database.get_all_items()
    return jsonify(items)

if __name__ == '__main__':
    app.run()''',
        ]
        
        samples = []
        exploits = ["Unrestricted File Upload", "Unrestricted Loop", "Unrestricted Database Query", "Missing Pagination"]
        
        for i, template in enumerate(templates):
            for _ in range(2):
                samples.append({
                    'Primary Vulnerability': 'Unrestricted Resource Consumption',
                    'Exploit': exploits[i],
                    'Result': 'Error',
                    'Code': template
                })
        
        return samples

    def generate_resource_secure(self):
        """Generate Unrestricted Resource Consumption secure samples"""
        templates = [
            # Restricted file upload
            '''from flask import Flask, request, jsonify
import os
app = Flask(__name__)

ALLOWED_EXTENSIONS = {{'png', 'jpg', 'jpeg', 'gif'}}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if not file:
        return jsonify({{"error": "No file"}}), 400
    
    if not allowed_file(file.filename):
        return jsonify({{"error": "Invalid file type"}}), 400
    
    file.seek(0, os.SEEK_END)
    if file.tell() > MAX_FILE_SIZE:
        return jsonify({{"error": "File too large"}}), 400
    file.seek(0)
    
    secure_filename = werkzeug.utils.secure_filename(file.filename)
    file.save(os.path.join('/uploads', secure_filename))
    return jsonify({{"success": True}})

if __name__ == '__main__':
    app.run()''',

            # With pagination and limits
            '''from flask import Flask, request, jsonify
app = Flask(__name__)

MAX_LIMIT = 100
DEFAULT_LIMIT = 20

@app.route('/items', methods=['GET'])
def get_items():
    page = max(1, int(request.args.get('page', 1)))
    limit = min(MAX_LIMIT, int(request.args.get('limit', DEFAULT_LIMIT)))
    offset = (page - 1) * limit
    
    items = database.query(f"SELECT * FROM items LIMIT {{limit}} OFFSET {{offset}}")
    total = database.count("items")
    
    return jsonify({{
        "items": items,
        "page": page,
        "limit": limit,
        "total": total
    }})

if __name__ == '__main__':
    app.run()''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(4):
                samples.append({
                    'Primary Vulnerability': 'Unrestricted Resource Consumption',
                    'Exploit': 'Proper Resource Limits',
                    'Result': 'Good',
                    'Code': template
                })
        
        return samples

    # =========================================================
    # API5: Broken Function Level Authorization
    # =========================================================
    def generate_function_auth_vulnerable(self):
        """Generate Broken Function Level Authorization vulnerable samples"""
        templates = [
            # No authorization check
            '''from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/admin/users', methods=['GET'])
def get_all_users():
    users = database.get_all_users()
    return jsonify(users)

@app.route('/admin/delete/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    database.delete_user(user_id)
    return jsonify({{"success": True}})

if __name__ == '__main__':
    app.run()''',

            # Missing role check
            '''from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/api/settings', methods=['PUT'])
def update_settings():
    settings = request.json
    database.update_settings(settings)
    return jsonify({{"success": True}})

if __name__ == '__main__':
    app.run()''',

            # Predictable admin URL
            '''from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/admin_panel', methods=['GET'])
def admin_panel():
    return jsonify(get_admin_data())

@app.route('/admin_panel/config', methods=['POST'])
def update_config():
    return jsonify(update_system_config())

if __name__ == '__main__':
    app.run()''',
        ]
        
        samples = []
        exploits = ["No Authorization Check", "Missing Role Check", "Predictable Admin URL"]
        
        for i, template in enumerate(templates):
            for _ in range(3):
                samples.append({
                    'Primary Vulnerability': 'Broken Function Level Authorization',
                    'Exploit': exploits[i],
                    'Result': 'Error',
                    'Code': template
                })
        
        return samples

    def generate_function_auth_secure(self):
        """Generate Broken Function Level Authorization secure samples"""
        templates = [
            # With role-based access
            '''from flask import Flask, request, jsonify
from functools import wraps
app = Flask(__name__)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        user = verify_token(token)
        if not user or user.get('role') != 'admin':
            return jsonify({{"error": "Admin access required"}}), 403
        return f(*args, **kwargs)
    return decorated

@app.route('/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    users = database.get_all_users()
    return jsonify(users)

@app.route('/admin/delete/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    database.delete_user(user_id)
    return jsonify({{"success": True}})

if __name__ == '__main__':
    app.run()''',

            # Permission-based access
            '''from flask import Flask, request, jsonify
from functools import wraps
app = Flask(__name__)

def require_permission(permission):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = get_current_user()
            if not user or permission not in user.get('permissions', []):
                return jsonify({{"error": "Permission denied"}}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

@app.route('/api/settings', methods=['PUT'])
@require_permission('settings:write')
def update_settings():
    settings = request.json
    database.update_settings(settings)
    return jsonify({{"success": True}})

if __name__ == '__main__':
    app.run()''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(4):
                samples.append({
                    'Primary Vulnerability': 'Broken Function Level Authorization',
                    'Exploit': 'Proper Function Authorization',
                    'Result': 'Good',
                    'Code': template
                })
        
        return samples

    # =========================================================
    # API6: Unrestricted Access to Sensitive Business Flows
    # =========================================================
    def generate_business_flow_vulnerable(self):
        """Generate Unrestricted Access to Sensitive Business Flows vulnerable samples"""
        templates = [
            # Unprotected financial operation
            '''from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/transfer', methods=['POST'])
def transfer_money():
    from_account = request.json['from']
    to_account = request.json['to']
    amount = request.json['amount']
    
    execute_transfer(from_account, to_account, amount)
    return jsonify({{"success": True}})

if __name__ == '__main__':
    app.run()''',

            # Unprotected data export
            '''from flask import Flask, request, send_file
app = Flask(__name__)

@app.route('/export', methods=['GET'])
def export_data():
    format = request.args.get('format', 'csv')
    data = database.export_all_data()
    return send_file(create_export(data, format))

if __name__ == '__main__':
    app.run()''',

            # Admin operations without verification
            '''from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/admin/reset-password', methods=['POST'])
def reset_password():
    user_id = request.json['user_id']
    new_password = request.json['new_password']
    database.update_password(user_id, new_password)
    return jsonify({{"success": True}})

if __name__ == '__main__':
    app.run()''',
        ]
        
        samples = []
        exploits = ["Unprotected Financial Operation", "Unrestricted Data Export", "Admin Operation Without Verification"]
        
        for i, template in enumerate(templates):
            for _ in range(3):
                samples.append({
                    'Primary Vulnerability': 'Unrestricted Access to Sensitive Business Flows',
                    'Exploit': exploits[i],
                    'Result': 'Error',
                    'Code': template
                })
        
        return samples

    def generate_business_flow_secure(self):
        """Generate Unrestricted Access to Sensitive Business Flows secure samples"""
        templates = [
            # Protected financial operation with verification
            '''from flask import Flask, request, jsonify
from functools import wraps
app = Flask(__name__)

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = authenticate_request(request)
        if not user:
            return jsonify({{"error": "Unauthorized"}}), 401
        return f(*args, **kwargs)
    return decorated

def require_2fa(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        otp = request.headers.get('X-OTP')
        if not verify_otp(get_current_user(), otp):
            return jsonify({{"error": "2FA required"}}), 403
        return f(*args, **kwargs)
    return decorated

@app.route('/transfer', methods=['POST'])
@require_auth
@require_2fa
def transfer_money():
    user = get_current_user()
    from_account = request.json['from']
    
    if not user_owns_account(user, from_account):
        return jsonify({{"error": "Forbidden"}}), 403
    
    amount = request.json['amount']
    if amount > get_daily_limit(user):
        return jsonify({{"error": "Exceeds daily limit"}}), 400
    
    execute_transfer(from_account, request.json['to'], amount)
    log_transaction(user, from_account, request.json['to'], amount)
    return jsonify({{"success": True}})

if __name__ == '__main__':
    app.run()''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(8):
                samples.append({
                    'Primary Vulnerability': 'Unrestricted Access to Sensitive Business Flows',
                    'Exploit': 'Protected Business Flow',
                    'Result': 'Good',
                    'Code': template
                })
        
        return samples

    # =========================================================
    # API7: Server Side Request Forgery (SSRF)
    # =========================================================
    def generate_ssrf_vulnerable(self):
        """Generate SSRF vulnerable samples"""
        templates = [
            # Basic SSRF
            '''from flask import Flask, request, jsonify
import requests
app = Flask(__name__)

@app.route('/fetch', methods=['POST'])
def fetch_url():
    url = request.json.get('url')
    response = requests.get(url)
    return jsonify({{"content": response.text}})

if __name__ == '__main__':
    app.run()''',

            # SSRF with redirects
            '''from flask import Flask, request, jsonify
import urllib.request
app = Flask(__name__)

@app.route('/proxy', methods=['GET'])
def proxy():
    url = request.args.get('url')
    with urllib.request.urlopen(url) as response:
        return response.read()

if __name__ == '__main__':
    app.run()''',

            # SSRF in image processing
            '''from flask import Flask, request, jsonify
import requests
from PIL import Image
from io import BytesIO
app = Flask(__name__)

@app.route('/process-image', methods=['POST'])
def process_image():
    image_url = request.json.get('image_url')
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    return jsonify({{"size": img.size}})

if __name__ == '__main__':
    app.run()''',
        ]
        
        samples = []
        exploits = ["Basic SSRF", "SSRF with Redirects", "SSRF in Image Processing"]
        
        for i, template in enumerate(templates):
            for _ in range(3):
                samples.append({
                    'Primary Vulnerability': 'Server Side Request Forgery',
                    'Exploit': exploits[i],
                    'Result': 'Error',
                    'Code': template
                })
        
        return samples

    def generate_ssrf_secure(self):
        """Generate SSRF secure samples"""
        templates = [
            # URL validation and allowlist
            '''from flask import Flask, request, jsonify
import requests
from urllib.parse import urlparse
app = Flask(__name__)

ALLOWED_HOSTS = ['api.trusted.com', 'cdn.example.com']

def is_safe_url(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ['http', 'https']:
            return False
        if parsed.hostname not in ALLOWED_HOSTS:
            return False
        if parsed.port and parsed.port not in [80, 443]:
            return False
        return True
    except:
        return False

@app.route('/fetch', methods=['POST'])
def fetch_url():
    url = request.json.get('url')
    
    if not is_safe_url(url):
        return jsonify({{"error": "URL not allowed"}}), 400
    
    response = requests.get(url, allow_redirects=False, timeout=5)
    return jsonify({{"content": response.text}})

if __name__ == '__main__':
    app.run()''',

            # Block internal IPs
            '''from flask import Flask, request, jsonify
import requests
import ipaddress
from urllib.parse import urlparse
import socket
app = Flask(__name__)

def is_internal_ip(hostname):
    try:
        ip = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved
    except:
        return True

@app.route('/fetch', methods=['POST'])
def fetch_url():
    url = request.json.get('url')
    parsed = urlparse(url)
    
    if is_internal_ip(parsed.hostname):
        return jsonify({{"error": "Internal URLs not allowed"}}), 400
    
    response = requests.get(url, allow_redirects=False, timeout=5)
    return jsonify({{"content": response.text}})

if __name__ == '__main__':
    app.run()''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(4):
                samples.append({
                    'Primary Vulnerability': 'Server Side Request Forgery',
                    'Exploit': 'URL Validation and Allowlist',
                    'Result': 'Good',
                    'Code': template
                })
        
        return samples

    # =========================================================
    # API8: Security Misconfiguration
    # =========================================================
    def generate_misconfig_vulnerable(self):
        """Generate Security Misconfiguration vulnerable samples"""
        templates = [
            # Debug mode in production
            '''from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Hello World"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')''',

            # Default secret key
            '''from flask import Flask, session
app = Flask(__name__)
app.secret_key = 'secret'

@app.route('/login')
def login():
    session['user'] = 'admin'
    return "Logged in"

if __name__ == '__main__':
    app.run()''',

            # Insecure headers
            '''from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/api/data')
def get_data():
    response = jsonify({{"data": "sensitive"}})
    return response

if __name__ == '__main__':
    app.run()''',

            # Verbose error messages
            '''from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/user/<int:id>')
def get_user(id):
    try:
        user = database.get_user(id)
        return jsonify(user)
    except Exception as e:
        return jsonify({{"error": str(e), "traceback": traceback.format_exc()}}), 500

if __name__ == '__main__':
    app.run()''',
        ]
        
        samples = []
        exploits = ["Debug Mode Enabled", "Default Secret Key", "Missing Security Headers", "Verbose Error Messages"]
        
        for i, template in enumerate(templates):
            for _ in range(2):
                samples.append({
                    'Primary Vulnerability': 'Security Misconfiguration',
                    'Exploit': exploits[i],
                    'Result': 'Error',
                    'Code': template
                })
        
        return samples

    def generate_misconfig_secure(self):
        """Generate Security Misconfiguration secure samples"""
        templates = [
            # Secure configuration
            '''from flask import Flask
import os
app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['DEBUG'] = False
app.config['TESTING'] = False

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response

@app.route('/')
def home():
    return "Hello World"

if __name__ == '__main__':
    app.run(host='127.0.0.1')''',

            # Proper error handling
            '''from flask import Flask, jsonify
import os
import logging
app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
logging.basicConfig(level=logging.ERROR)

@app.errorhandler(Exception)
def handle_error(e):
    logging.error(f"Error: {{e}}")
    return jsonify({{"error": "An error occurred"}}), 500

@app.route('/user/<int:id>')
def get_user(id):
    user = database.get_user(id)
    return jsonify(user)

if __name__ == '__main__':
    app.run()''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(4):
                samples.append({
                    'Primary Vulnerability': 'Security Misconfiguration',
                    'Exploit': 'Secure Configuration',
                    'Result': 'Good',
                    'Code': template
                })
        
        return samples

    # =========================================================
    # API9: Improper Inventory Management
    # =========================================================
    def generate_inventory_vulnerable(self):
        """Generate Improper Inventory Management vulnerable samples"""
        templates = [
            # Exposed API documentation
            '''from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/api/v1/internal/users')
def internal_users():
    return jsonify(database.get_all_internal_users())

@app.route('/api/v2/users')
def v2_users():
    return jsonify(database.get_users())

@app.route('/api/beta/experimental')
def beta_endpoint():
    return jsonify({{"data": "experimental feature"}})

if __name__ == '__main__':
    app.run()''',

            # Deprecated endpoint still active
            '''from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/api/v1/login', methods=['POST'])
def old_login():
    # Deprecated: uses weak auth
    if request.json['pass'] == 'admin':
        return jsonify({{"token": "weak_token"}})
    return jsonify({{"error": "Invalid"}}), 401

@app.route('/api/v2/login', methods=['POST'])
def new_login():
    return authenticate_properly(request.json)

if __name__ == '__main__':
    app.run()''',
        ]
        
        samples = []
        exploits = ["Exposed Internal Endpoints", "Deprecated Endpoint Active"]
        
        for i, template in enumerate(templates):
            for _ in range(4):
                samples.append({
                    'Primary Vulnerability': 'Improper Inventory Management',
                    'Exploit': exploits[i % len(exploits)],
                    'Result': 'Error',
                    'Code': template
                })
        
        return samples

    def generate_inventory_secure(self):
        """Generate Improper Inventory Management secure samples"""
        templates = [
            # Proper API versioning
            '''from flask import Flask, jsonify, request
from functools import wraps
import os
app = Flask(__name__)

ACTIVE_VERSIONS = ['v2', 'v3']

def version_check(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        version = request.path.split('/')[2] if len(request.path.split('/')) > 2 else None
        if version not in ACTIVE_VERSIONS:
            return jsonify({{"error": "API version deprecated or not found"}}), 404
        return f(*args, **kwargs)
    return decorated

@app.route('/api/v2/users')
@version_check
def get_users():
    return jsonify(database.get_users())

@app.route('/api/v3/users')
@version_check  
def get_users_v3():
    return jsonify(database.get_users_paginated())

if __name__ == '__main__':
    app.run()''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(8):
                samples.append({
                    'Primary Vulnerability': 'Improper Inventory Management',
                    'Exploit': 'Proper API Versioning',
                    'Result': 'Good',
                    'Code': template
                })
        
        return samples

    # =========================================================
    # API10: Unsafe Consumption of APIs
    # =========================================================
    def generate_unsafe_api_vulnerable(self):
        """Generate Unsafe Consumption of APIs vulnerable samples"""
        templates = [
            # No input validation from external API
            '''from flask import Flask, jsonify
import requests
app = Flask(__name__)

@app.route('/user-info/<username>')
def get_external_user(username):
    response = requests.get(f'https://external-api.com/users/{{username}}')
    user_data = response.json()
    database.save_user(user_data)
    return jsonify(user_data)

if __name__ == '__main__':
    app.run()''',

            # Trusting external data
            '''from flask import Flask, jsonify
import requests
app = Flask(__name__)

@app.route('/product/<id>')
def get_product(id):
    response = requests.get(f'https://partner-api.com/products/{{id}}')
    product = response.json()
    
    # Directly using external data in SQL
    database.execute(f"INSERT INTO products VALUES ('{{product['name']}}', {{product['price']}})")
    return jsonify(product)

if __name__ == '__main__':
    app.run()''',

            # No HTTPS verification
            '''from flask import Flask, jsonify
import requests
app = Flask(__name__)

@app.route('/external-data')
def get_external():
    response = requests.get('http://api.example.com/data', verify=False)
    return jsonify(response.json())

if __name__ == '__main__':
    app.run()''',
        ]
        
        samples = []
        exploits = ["No Input Validation", "Trusting External Data", "No HTTPS Verification"]
        
        for i, template in enumerate(templates):
            for _ in range(3):
                samples.append({
                    'Primary Vulnerability': 'Unsafe Consumption of APIs',
                    'Exploit': exploits[i],
                    'Result': 'Error',
                    'Code': template
                })
        
        return samples

    def generate_unsafe_api_secure(self):
        """Generate Unsafe Consumption of APIs secure samples"""
        templates = [
            # Validate and sanitize external data
            '''from flask import Flask, jsonify
import requests
from marshmallow import Schema, fields, ValidationError
app = Flask(__name__)

class UserSchema(Schema):
    username = fields.Str(required=True, validate=lambda x: len(x) <= 50)
    email = fields.Email(required=True)
    
user_schema = UserSchema()

@app.route('/user-info/<username>')
def get_external_user(username):
    try:
        response = requests.get(
            f'https://external-api.com/users/{{username}}',
            timeout=5,
            verify=True
        )
        response.raise_for_status()
        
        user_data = user_schema.load(response.json())
        database.save_user_safe(user_data)
        return jsonify(user_data)
    except ValidationError as e:
        return jsonify({{"error": "Invalid data from external API"}}), 400
    except requests.RequestException as e:
        return jsonify({{"error": "External API error"}}), 502

if __name__ == '__main__':
    app.run()''',

            # Secure external API consumption
            '''from flask import Flask, jsonify
import requests
import os
app = Flask(__name__)

EXTERNAL_API_KEY = os.environ.get('EXTERNAL_API_KEY')
TRUSTED_HOSTS = ['api.trusted-partner.com']

@app.route('/external-data')
def get_external():
    try:
        response = requests.get(
            'https://api.trusted-partner.com/data',
            headers={{'Authorization': f'Bearer {{EXTERNAL_API_KEY}}'}},
            timeout=10,
            verify=True
        )
        response.raise_for_status()
        
        data = response.json()
        validated_data = validate_and_sanitize(data)
        return jsonify(validated_data)
    except Exception as e:
        logging.error(f"External API error: {{e}}")
        return jsonify({{"error": "Service unavailable"}}), 503

if __name__ == '__main__':
    app.run()''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(4):
                samples.append({
                    'Primary Vulnerability': 'Unsafe Consumption of APIs',
                    'Exploit': 'Validated External API Usage',
                    'Result': 'Good',
                    'Code': template
                })
        
        return samples

    # =========================================================
    # MAIN GENERATION METHOD
    # =========================================================
    def generate_all_samples(self):
        """Generate all samples for all vulnerability types"""
        all_samples = []
        
        # API1: Broken Object Level Authorization
        all_samples.extend(self.generate_bola_vulnerable())
        all_samples.extend(self.generate_bola_secure())
        
        # API2: Broken Authentication
        all_samples.extend(self.generate_auth_vulnerable())
        all_samples.extend(self.generate_auth_secure())
        
        # API3: Broken Object Property Level Authorization
        all_samples.extend(self.generate_property_auth_vulnerable())
        all_samples.extend(self.generate_property_auth_secure())
        
        # API4: Unrestricted Resource Consumption
        all_samples.extend(self.generate_resource_vulnerable())
        all_samples.extend(self.generate_resource_secure())
        
        # API5: Broken Function Level Authorization
        all_samples.extend(self.generate_function_auth_vulnerable())
        all_samples.extend(self.generate_function_auth_secure())
        
        # API6: Unrestricted Access to Sensitive Business Flows
        all_samples.extend(self.generate_business_flow_vulnerable())
        all_samples.extend(self.generate_business_flow_secure())
        
        # API7: Server Side Request Forgery
        all_samples.extend(self.generate_ssrf_vulnerable())
        all_samples.extend(self.generate_ssrf_secure())
        
        # API8: Security Misconfiguration
        all_samples.extend(self.generate_misconfig_vulnerable())
        all_samples.extend(self.generate_misconfig_secure())
        
        # API9: Improper Inventory Management
        all_samples.extend(self.generate_inventory_vulnerable())
        all_samples.extend(self.generate_inventory_secure())
        
        # API10: Unsafe Consumption of APIs
        all_samples.extend(self.generate_unsafe_api_vulnerable())
        all_samples.extend(self.generate_unsafe_api_secure())
        
        return all_samples


def main():
    """Main function to generate expanded dataset"""
    print("=" * 70)
    print(" DATASET EXPANSION: Generating Synthetic Code Samples")
    print("=" * 70)
    
    # Initialize generator
    generator = VulnerableCodeGenerator()
    
    # Generate all samples
    print("\n[1] Generating synthetic code samples...")
    samples = generator.generate_all_samples()
    
    # Create DataFrame
    df_new = pd.DataFrame(samples)
    df_new['S.No'] = range(1, len(df_new) + 1)
    
    # Reorder columns
    df_new = df_new[['S.No', 'Primary Vulnerability', 'Exploit', 'Result', 'Code']]
    
    print(f"\n[2] Generated {len(df_new)} new samples")
    
    # Load original dataset
    print("\n[3] Loading original dataset...")
    original_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                  "Previous", "Unsecured Codes.xlsx")
    df_original = pd.read_excel(original_path)
    df_original = df_original[['S.No', 'Primary Vulnerability', 'Exploit', 'Result', 'Code']]
    
    print(f"Original dataset: {len(df_original)} samples")
    
    # Combine datasets
    print("\n[4] Combining datasets...")
    df_combined = pd.concat([df_original, df_new], ignore_index=True)
    df_combined['S.No'] = range(1, len(df_combined) + 1)
    
    # Shuffle the dataset
    df_combined = df_combined.sample(frac=1, random_state=RANDOM_STATE).reset_index(drop=True)
    df_combined['S.No'] = range(1, len(df_combined) + 1)
    
    print(f"Combined dataset: {len(df_combined)} samples")
    
    # Statistics
    print("\n" + "=" * 70)
    print(" DATASET STATISTICS")
    print("=" * 70)
    
    print("\nClass Distribution:")
    print(df_combined['Result'].value_counts())
    
    print("\nVulnerability Type Distribution:")
    print(df_combined['Primary Vulnerability'].value_counts())
    
    # Save expanded dataset
    print("\n[5] Saving expanded dataset...")
    
    # Create data directory
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Save as Excel
    excel_path = os.path.join(data_dir, "expanded_dataset.xlsx")
    df_combined.to_excel(excel_path, index=False)
    print(f"Saved: {excel_path}")
    
    # Save as CSV
    csv_path = os.path.join(data_dir, "expanded_dataset.csv")
    df_combined.to_csv(csv_path, index=False)
    print(f"Saved: {csv_path}")
    
    # Summary
    print("\n" + "=" * 70)
    print(" DATASET EXPANSION COMPLETE")
    print("=" * 70)
    
    vulnerable_count = len(df_combined[df_combined['Result'] == 'Error'])
    secure_count = len(df_combined[df_combined['Result'] == 'Good'])
    
    print(f"""
Summary:
--------
Original samples:  60
New samples:       {len(df_new)}
Total samples:     {len(df_combined)}

Vulnerable (Error): {vulnerable_count}
Secure (Good):      {secure_count}
Balance ratio:      {vulnerable_count/secure_count:.2f}

Files saved:
- {excel_path}
- {csv_path}
""")
    
    return df_combined


if __name__ == "__main__":
    df = main()
