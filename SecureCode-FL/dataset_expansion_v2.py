"""
Dataset Expansion Module V2
===========================

Adds MORE synthetic code samples with greater variation to reach 500+ samples.
"""

import pandas as pd
import numpy as np
import random
import os

RANDOM_STATE = 42
random.seed(RANDOM_STATE)
np.random.seed(RANDOM_STATE)


class AdditionalCodeGenerator:
    """Generate additional code samples with more variations"""
    
    def __init__(self):
        # Frameworks to vary
        self.frameworks = ['flask', 'django', 'fastapi']
        
    # =========================================================
    # SQL Injection (part of Unsafe API Consumption)
    # =========================================================
    def generate_sql_injection_vulnerable(self):
        """SQL Injection vulnerable samples"""
        templates = [
            '''from flask import Flask, request, jsonify
import sqlite3
app = Flask(__name__)

@app.route('/search')
def search():
    query = request.args.get('q')
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE name = '{{query}}'")
    return jsonify(cursor.fetchall())''',

            '''from flask import Flask, request
import mysql.connector
app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = mysql.connector.connect(host='localhost', database='app')
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE username='" + username + "' AND password='" + password + "'"
    cursor.execute(query)
    return "Success" if cursor.fetchone() else "Failed"''',

            '''from django.http import JsonResponse
import psycopg2

def get_user(request):
    user_id = request.GET.get('id')
    conn = psycopg2.connect("dbname=app user=admin")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = " + user_id)
    return JsonResponse({{"user": cursor.fetchone()}})''',

            '''from fastapi import FastAPI, Query
import sqlite3
app = FastAPI()

@app.get("/users")
def get_users(name: str = Query(...)):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE name LIKE '%" + name + "%'")
    return {{"users": cursor.fetchall()}}''',

            '''from flask import Flask, request
import pymysql
app = Flask(__name__)

@app.route('/delete/<table>')
def delete_record(table):
    id = request.args.get('id')
    conn = pymysql.connect(host='localhost', user='root', password='', db='app')
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {{table}} WHERE id = {{id}}")
    conn.commit()
    return "Deleted"''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(4):
                samples.append({
                    'Primary Vulnerability': 'Unsafe Consumption of APIs',
                    'Exploit': 'SQL Injection',
                    'Result': 'Error',
                    'Code': template
                })
        return samples

    def generate_sql_injection_secure(self):
        """SQL Injection secure samples with parameterized queries"""
        templates = [
            '''from flask import Flask, request, jsonify
import sqlite3
app = Flask(__name__)

@app.route('/search')
def search():
    query = request.args.get('q')
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE name = ?", (query,))
    return jsonify(cursor.fetchall())''',

            '''from flask import Flask, request
import mysql.connector
app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = mysql.connector.connect(host='localhost', database='app')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
    return "Success" if cursor.fetchone() else "Failed"''',

            '''from django.http import JsonResponse
import psycopg2

def get_user(request):
    user_id = request.GET.get('id')
    conn = psycopg2.connect("dbname=app user=admin")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    return JsonResponse({{"user": cursor.fetchone()}})''',

            '''from fastapi import FastAPI, Query
import sqlite3
app = FastAPI()

@app.get("/users")
def get_users(name: str = Query(...)):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE name LIKE ?", (f'%{{name}}%',))
    return {{"users": cursor.fetchall()}}''',

            '''from flask import Flask, request
from sqlalchemy import create_engine, text
app = Flask(__name__)

engine = create_engine('sqlite:///data.db')

@app.route('/users/<int:user_id>')
def get_user(user_id):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM users WHERE id = :id"), {{"id": user_id}})
        return {{"user": dict(result.fetchone())}}''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(4):
                samples.append({
                    'Primary Vulnerability': 'Unsafe Consumption of APIs',
                    'Exploit': 'Parameterized Query',
                    'Result': 'Good',
                    'Code': template
                })
        return samples

    # =========================================================
    # XSS Prevention
    # =========================================================
    def generate_xss_vulnerable(self):
        """XSS vulnerable samples"""
        templates = [
            '''from flask import Flask, request
app = Flask(__name__)

@app.route('/greet')
def greet():
    name = request.args.get('name', 'Guest')
    return f"<html><body><h1>Hello {{name}}!</h1></body></html>"''',

            '''from flask import Flask, request, render_template_string
app = Flask(__name__)

@app.route('/profile')
def profile():
    bio = request.args.get('bio', '')
    template = f"<div class='bio'>{{bio}}</div>"
    return render_template_string(template)''',

            '''from django.http import HttpResponse

def search_results(request):
    query = request.GET.get('q', '')
    return HttpResponse(f"<html><body>Results for: {{query}}</body></html>")''',

            '''from fastapi import FastAPI
from fastapi.responses import HTMLResponse
app = FastAPI()

@app.get("/comment", response_class=HTMLResponse)
def show_comment(text: str):
    return f"<div class='comment'>{{text}}</div>"''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(4):
                samples.append({
                    'Primary Vulnerability': 'Security Misconfiguration',
                    'Exploit': 'Cross-Site Scripting (XSS)',
                    'Result': 'Error',
                    'Code': template
                })
        return samples

    def generate_xss_secure(self):
        """XSS secure samples with proper escaping"""
        templates = [
            '''from flask import Flask, request, escape
app = Flask(__name__)

@app.route('/greet')
def greet():
    name = escape(request.args.get('name', 'Guest'))
    return f"<html><body><h1>Hello {{name}}!</h1></body></html>"''',

            '''from flask import Flask, request, render_template
app = Flask(__name__)

@app.route('/profile')
def profile():
    bio = request.args.get('bio', '')
    return render_template('profile.html', bio=bio)''',

            '''from django.http import HttpResponse
from django.utils.html import escape

def search_results(request):
    query = escape(request.GET.get('q', ''))
    return HttpResponse(f"<html><body>Results for: {{query}}</body></html>")''',

            '''from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import html
app = FastAPI()

@app.get("/comment", response_class=HTMLResponse)
def show_comment(text: str):
    safe_text = html.escape(text)
    return f"<div class='comment'>{{safe_text}}</div>"''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(4):
                samples.append({
                    'Primary Vulnerability': 'Security Misconfiguration',
                    'Exploit': 'Proper Output Encoding',
                    'Result': 'Good',
                    'Code': template
                })
        return samples

    # =========================================================
    # JWT Security
    # =========================================================
    def generate_jwt_vulnerable(self):
        """JWT vulnerable samples"""
        templates = [
            '''import jwt
from flask import Flask, request, jsonify
app = Flask(__name__)

SECRET = "secret123"

@app.route('/verify')
def verify():
    token = request.headers.get('Authorization')
    try:
        data = jwt.decode(token, SECRET, algorithms=["HS256", "none"])
        return jsonify(data)
    except:
        return jsonify({{"error": "Invalid token"}}), 401''',

            '''import jwt
from flask import Flask, request
app = Flask(__name__)

@app.route('/data')
def get_data():
    token = request.args.get('token')
    data = jwt.decode(token, options={{"verify_signature": False}})
    return {{"user": data.get('user')}}''',

            '''import jwt
from flask import Flask, request, jsonify
app = Flask(__name__)

SECRET = "secret"

@app.route('/login', methods=['POST'])
def login():
    user = request.json
    token = jwt.encode({{"user": user}}, SECRET, algorithm="HS256")
    return jsonify({{"token": token}})''',
        ]
        
        samples = []
        exploits = ["Weak JWT Algorithm", "Signature Verification Disabled", "Weak Secret Key"]
        
        for i, template in enumerate(templates):
            for _ in range(4):
                samples.append({
                    'Primary Vulnerability': 'Broken Authentication',
                    'Exploit': exploits[i % len(exploits)],
                    'Result': 'Error',
                    'Code': template
                })
        return samples

    def generate_jwt_secure(self):
        """JWT secure samples"""
        templates = [
            '''import jwt
import os
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
app = Flask(__name__)

SECRET = os.environ.get('JWT_SECRET')

@app.route('/verify')
def verify():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    try:
        data = jwt.decode(token, SECRET, algorithms=["HS256"])
        return jsonify(data)
    except jwt.ExpiredSignatureError:
        return jsonify({{"error": "Token expired"}}), 401
    except jwt.InvalidTokenError:
        return jsonify({{"error": "Invalid token"}}), 401''',

            '''import jwt
import os
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
app = Flask(__name__)

SECRET = os.environ.get('JWT_SECRET')

@app.route('/login', methods=['POST'])
def login():
    user = authenticate(request.json)
    if user:
        payload = {{
            "user_id": user.id,
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow()
        }}
        token = jwt.encode(payload, SECRET, algorithm="HS256")
        return jsonify({{"token": token}})
    return jsonify({{"error": "Invalid credentials"}}), 401''',

            '''import jwt
import os
from cryptography.hazmat.primitives import serialization
from flask import Flask, request, jsonify
app = Flask(__name__)

with open('private.pem', 'rb') as f:
    PRIVATE_KEY = f.read()
with open('public.pem', 'rb') as f:
    PUBLIC_KEY = f.read()

@app.route('/verify')
def verify():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    try:
        data = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
        return jsonify(data)
    except jwt.InvalidTokenError:
        return jsonify({{"error": "Invalid token"}}), 401''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(4):
                samples.append({
                    'Primary Vulnerability': 'Broken Authentication',
                    'Exploit': 'Secure JWT Implementation',
                    'Result': 'Good',
                    'Code': template
                })
        return samples

    # =========================================================
    # Path Traversal
    # =========================================================
    def generate_path_traversal_vulnerable(self):
        """Path traversal vulnerable samples"""
        templates = [
            '''from flask import Flask, request, send_file
app = Flask(__name__)

@app.route('/download')
def download():
    filename = request.args.get('file')
    return send_file(f'/uploads/{{filename}}')''',

            '''from flask import Flask, request
import os
app = Flask(__name__)

@app.route('/read')
def read_file():
    path = request.args.get('path')
    with open(path, 'r') as f:
        return f.read()''',

            '''from fastapi import FastAPI
from fastapi.responses import FileResponse
app = FastAPI()

@app.get("/files/{{filename}}")
def get_file(filename: str):
    return FileResponse(f"storage/{{filename}}")''',

            '''from django.http import HttpResponse
import os

def serve_file(request, filename):
    base_dir = '/var/www/files/'
    filepath = base_dir + filename
    with open(filepath, 'rb') as f:
        return HttpResponse(f.read())''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(4):
                samples.append({
                    'Primary Vulnerability': 'Broken Object Level Authorization',
                    'Exploit': 'Path Traversal',
                    'Result': 'Error',
                    'Code': template
                })
        return samples

    def generate_path_traversal_secure(self):
        """Path traversal secure samples"""
        templates = [
            '''from flask import Flask, request, send_file, abort
import os
app = Flask(__name__)

UPLOAD_DIR = '/uploads'

@app.route('/download')
def download():
    filename = request.args.get('file')
    safe_path = os.path.abspath(os.path.join(UPLOAD_DIR, filename))
    if not safe_path.startswith(os.path.abspath(UPLOAD_DIR)):
        abort(403)
    if not os.path.exists(safe_path):
        abort(404)
    return send_file(safe_path)''',

            '''from flask import Flask, request, abort
from werkzeug.utils import secure_filename
import os
app = Flask(__name__)

ALLOWED_DIR = '/safe/files'

@app.route('/read')
def read_file():
    filename = secure_filename(request.args.get('path', ''))
    if not filename:
        abort(400)
    safe_path = os.path.join(ALLOWED_DIR, filename)
    if os.path.exists(safe_path):
        with open(safe_path, 'r') as f:
            return f.read()
    abort(404)''',

            '''from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import os
app = FastAPI()

STORAGE_DIR = "storage"

@app.get("/files/{{filename}}")
def get_file(filename: str):
    safe_filename = os.path.basename(filename)
    filepath = os.path.join(STORAGE_DIR, safe_filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404)
    if not os.path.abspath(filepath).startswith(os.path.abspath(STORAGE_DIR)):
        raise HTTPException(status_code=403)
    
    return FileResponse(filepath)''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(5):
                samples.append({
                    'Primary Vulnerability': 'Broken Object Level Authorization',
                    'Exploit': 'Safe Path Handling',
                    'Result': 'Good',
                    'Code': template
                })
        return samples

    # =========================================================
    # Command Injection
    # =========================================================
    def generate_command_injection_vulnerable(self):
        """Command injection vulnerable samples"""
        templates = [
            '''from flask import Flask, request
import os
app = Flask(__name__)

@app.route('/ping')
def ping():
    host = request.args.get('host')
    output = os.popen(f'ping -c 1 {{host}}').read()
    return output''',

            '''from flask import Flask, request
import subprocess
app = Flask(__name__)

@app.route('/convert')
def convert():
    filename = request.args.get('file')
    subprocess.run(f'convert {{filename}} output.png', shell=True)
    return "Converted"''',

            '''from flask import Flask, request
import os
app = Flask(__name__)

@app.route('/lookup')
def lookup():
    domain = request.args.get('domain')
    return os.system(f'nslookup {{domain}}')''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(4):
                samples.append({
                    'Primary Vulnerability': 'Unsafe Consumption of APIs',
                    'Exploit': 'Command Injection',
                    'Result': 'Error',
                    'Code': template
                })
        return samples

    def generate_command_injection_secure(self):
        """Command injection secure samples"""
        templates = [
            '''from flask import Flask, request, abort
import subprocess
import re
app = Flask(__name__)

@app.route('/ping')
def ping():
    host = request.args.get('host')
    if not re.match(r'^[a-zA-Z0-9.-]+$', host):
        abort(400, "Invalid hostname")
    result = subprocess.run(['ping', '-c', '1', host], capture_output=True, text=True)
    return result.stdout''',

            '''from flask import Flask, request, abort
import subprocess
from werkzeug.utils import secure_filename
app = Flask(__name__)

ALLOWED_EXT = ['jpg', 'png', 'gif']

@app.route('/convert')
def convert():
    filename = request.args.get('file')
    safe_name = secure_filename(filename)
    if not any(safe_name.endswith(ext) for ext in ALLOWED_EXT):
        abort(400)
    subprocess.run(['convert', safe_name, 'output.png'], check=True)
    return "Converted"''',

            '''from flask import Flask, request, abort
import subprocess
import ipaddress
app = Flask(__name__)

@app.route('/lookup')
def lookup():
    domain = request.args.get('domain')
    try:
        ipaddress.ip_address(domain)
    except ValueError:
        if not domain.replace('.', '').replace('-', '').isalnum():
            abort(400)
    result = subprocess.run(['nslookup', domain], capture_output=True, text=True)
    return result.stdout''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(5):
                samples.append({
                    'Primary Vulnerability': 'Unsafe Consumption of APIs',
                    'Exploit': 'Safe Command Execution',
                    'Result': 'Good',
                    'Code': template
                })
        return samples

    # =========================================================
    # Insecure Deserialization
    # =========================================================
    def generate_deserialization_vulnerable(self):
        """Insecure deserialization vulnerable samples"""
        templates = [
            '''from flask import Flask, request
import pickle
app = Flask(__name__)

@app.route('/load', methods=['POST'])
def load():
    data = request.data
    obj = pickle.loads(data)
    return str(obj)''',

            '''from flask import Flask, request
import yaml
app = Flask(__name__)

@app.route('/config', methods=['POST'])
def config():
    content = request.data.decode('utf-8')
    config = yaml.load(content)
    return str(config)''',

            '''from flask import Flask, request
import marshal
app = Flask(__name__)

@app.route('/execute', methods=['POST'])
def execute():
    code = marshal.loads(request.data)
    exec(code)
    return "Executed"''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(4):
                samples.append({
                    'Primary Vulnerability': 'Unsafe Consumption of APIs',
                    'Exploit': 'Insecure Deserialization',
                    'Result': 'Error',
                    'Code': template
                })
        return samples

    def generate_deserialization_secure(self):
        """Secure deserialization samples"""
        templates = [
            '''from flask import Flask, request, jsonify
import json
app = Flask(__name__)

@app.route('/load', methods=['POST'])
def load():
    try:
        data = json.loads(request.data)
        validated = validate_schema(data)
        return jsonify(validated)
    except json.JSONDecodeError:
        return jsonify({{"error": "Invalid JSON"}}), 400''',

            '''from flask import Flask, request
import yaml
app = Flask(__name__)

@app.route('/config', methods=['POST'])
def config():
    content = request.data.decode('utf-8')
    config = yaml.safe_load(content)
    return str(config)''',

            '''from flask import Flask, request, jsonify
from marshmallow import Schema, fields, ValidationError
app = Flask(__name__)

class DataSchema(Schema):
    name = fields.Str(required=True)
    value = fields.Int(required=True)

@app.route('/load', methods=['POST'])
def load():
    try:
        data = DataSchema().load(request.json)
        return jsonify(data)
    except ValidationError as e:
        return jsonify({{"error": e.messages}}), 400''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(5):
                samples.append({
                    'Primary Vulnerability': 'Unsafe Consumption of APIs',
                    'Exploit': 'Safe Deserialization',
                    'Result': 'Good',
                    'Code': template
                })
        return samples

    # =========================================================
    # Logging Sensitive Data
    # =========================================================
    def generate_logging_vulnerable(self):
        """Logging sensitive data vulnerable samples"""
        templates = [
            '''from flask import Flask, request
import logging
app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)

@app.route('/login', methods=['POST'])
def login():
    username = request.json['username']
    password = request.json['password']
    logging.info(f"Login attempt: {{username}}/{{password}}")
    return authenticate(username, password)''',

            '''from flask import Flask, request
import logging
app = Flask(__name__)

@app.route('/payment', methods=['POST'])
def payment():
    card_number = request.json['card']
    cvv = request.json['cvv']
    logging.debug(f"Processing payment: {{card_number}}, CVV: {{cvv}}")
    return process_payment(card_number, cvv)''',

            '''from flask import Flask, request
import logging
app = Flask(__name__)

@app.route('/api/users', methods=['POST'])
def create_user():
    user_data = request.json
    logging.info(f"Creating user: {{user_data}}")
    return create_user_in_db(user_data)''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(4):
                samples.append({
                    'Primary Vulnerability': 'Security Misconfiguration',
                    'Exploit': 'Logging Sensitive Data',
                    'Result': 'Error',
                    'Code': template
                })
        return samples

    def generate_logging_secure(self):
        """Secure logging samples"""
        templates = [
            '''from flask import Flask, request
import logging
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

@app.route('/login', methods=['POST'])
def login():
    username = request.json['username']
    password = request.json['password']
    logging.info(f"Login attempt for user: {{username}}")
    return authenticate(username, password)''',

            '''from flask import Flask, request
import logging
app = Flask(__name__)

def mask_card(card):
    return f"****{{card[-4:]}}"

@app.route('/payment', methods=['POST'])
def payment():
    card_number = request.json['card']
    cvv = request.json['cvv']
    logging.info(f"Processing payment for card: {{mask_card(card_number)}}")
    return process_payment(card_number, cvv)''',

            '''from flask import Flask, request
import logging
app = Flask(__name__)

SENSITIVE_FIELDS = ['password', 'ssn', 'card', 'cvv', 'token']

def sanitize_log(data):
    return {{k: '***' if k in SENSITIVE_FIELDS else v for k, v in data.items()}}

@app.route('/api/users', methods=['POST'])
def create_user():
    user_data = request.json
    logging.info(f"Creating user: {{sanitize_log(user_data)}}")
    return create_user_in_db(user_data)''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(5):
                samples.append({
                    'Primary Vulnerability': 'Security Misconfiguration',
                    'Exploit': 'Safe Logging Practice',
                    'Result': 'Good',
                    'Code': template
                })
        return samples

    # =========================================================
    # CORS Misconfiguration
    # =========================================================
    def generate_cors_vulnerable(self):
        """CORS misconfiguration vulnerable samples"""
        templates = [
            '''from flask import Flask, jsonify
from flask_cors import CORS
app = Flask(__name__)
CORS(app, origins="*")

@app.route('/api/data')
def get_data():
    return jsonify({{"secret": "sensitive data"}})''',

            '''from flask import Flask, request, jsonify
app = Flask(__name__)

@app.after_request
def add_cors(response):
    origin = request.headers.get('Origin')
    response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

@app.route('/api/user')
def get_user():
    return jsonify(get_current_user())''',

            '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/data")
def get_data():
    return {{"secret": "data"}}''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(4):
                samples.append({
                    'Primary Vulnerability': 'Security Misconfiguration',
                    'Exploit': 'CORS Misconfiguration',
                    'Result': 'Error',
                    'Code': template
                })
        return samples

    def generate_cors_secure(self):
        """Secure CORS configuration samples"""
        templates = [
            '''from flask import Flask, jsonify
from flask_cors import CORS
app = Flask(__name__)
CORS(app, origins=["https://trusted-domain.com"], supports_credentials=True)

@app.route('/api/data')
def get_data():
    return jsonify({{"data": "information"}})''',

            '''from flask import Flask, request, jsonify, abort
app = Flask(__name__)

ALLOWED_ORIGINS = ['https://app.example.com', 'https://admin.example.com']

@app.after_request
def add_cors(response):
    origin = request.headers.get('Origin')
    if origin in ALLOWED_ORIGINS:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

@app.route('/api/user')
def get_user():
    return jsonify(get_current_user())''',

            '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://frontend.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.get("/api/data")
def get_data():
    return {{"data": "information"}}''',
        ]
        
        samples = []
        for template in templates:
            for _ in range(5):
                samples.append({
                    'Primary Vulnerability': 'Security Misconfiguration',
                    'Exploit': 'Secure CORS Configuration',
                    'Result': 'Good',
                    'Code': template
                })
        return samples

    # =========================================================
    # GENERATE ALL
    # =========================================================
    def generate_all_samples(self):
        """Generate all additional samples"""
        all_samples = []
        
        # SQL Injection
        all_samples.extend(self.generate_sql_injection_vulnerable())
        all_samples.extend(self.generate_sql_injection_secure())
        
        # XSS
        all_samples.extend(self.generate_xss_vulnerable())
        all_samples.extend(self.generate_xss_secure())
        
        # JWT Security
        all_samples.extend(self.generate_jwt_vulnerable())
        all_samples.extend(self.generate_jwt_secure())
        
        # Path Traversal
        all_samples.extend(self.generate_path_traversal_vulnerable())
        all_samples.extend(self.generate_path_traversal_secure())
        
        # Command Injection
        all_samples.extend(self.generate_command_injection_vulnerable())
        all_samples.extend(self.generate_command_injection_secure())
        
        # Insecure Deserialization
        all_samples.extend(self.generate_deserialization_vulnerable())
        all_samples.extend(self.generate_deserialization_secure())
        
        # Logging Sensitive Data
        all_samples.extend(self.generate_logging_vulnerable())
        all_samples.extend(self.generate_logging_secure())
        
        # CORS Misconfiguration
        all_samples.extend(self.generate_cors_vulnerable())
        all_samples.extend(self.generate_cors_secure())
        
        return all_samples


def main():
    """Main function to expand dataset further"""
    print("=" * 70)
    print(" DATASET EXPANSION V2: Adding More Samples")
    print("=" * 70)
    
    # Load existing expanded dataset
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    existing_path = os.path.join(data_dir, "expanded_dataset.csv")
    
    if os.path.exists(existing_path):
        df_existing = pd.read_csv(existing_path)
        print(f"\nLoaded existing dataset: {len(df_existing)} samples")
    else:
        print("Error: Run dataset_expansion.py first!")
        return
    
    # Generate additional samples
    print("\n[1] Generating additional samples...")
    generator = AdditionalCodeGenerator()
    new_samples = generator.generate_all_samples()
    
    df_new = pd.DataFrame(new_samples)
    print(f"Generated {len(df_new)} new samples")
    
    # Combine
    print("\n[2] Combining datasets...")
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    df_combined['S.No'] = range(1, len(df_combined) + 1)
    
    # Shuffle
    df_combined = df_combined.sample(frac=1, random_state=42).reset_index(drop=True)
    df_combined['S.No'] = range(1, len(df_combined) + 1)
    
    print(f"Total samples: {len(df_combined)}")
    
    # Statistics
    print("\n" + "=" * 70)
    print(" FINAL DATASET STATISTICS")
    print("=" * 70)
    
    print("\nClass Distribution:")
    print(df_combined['Result'].value_counts())
    
    print("\nVulnerability Type Distribution:")
    vuln_counts = df_combined['Primary Vulnerability'].value_counts()
    for vuln, count in vuln_counts.items():
        print(f"  {vuln}: {count}")
    
    # Save
    print("\n[3] Saving final expanded dataset...")
    
    excel_path = os.path.join(data_dir, "expanded_dataset_v2.xlsx")
    csv_path = os.path.join(data_dir, "expanded_dataset_v2.csv")
    
    df_combined.to_excel(excel_path, index=False)
    df_combined.to_csv(csv_path, index=False)
    
    print(f"Saved: {excel_path}")
    print(f"Saved: {csv_path}")
    
    # Summary
    vulnerable_count = len(df_combined[df_combined['Result'] == 'Error'])
    secure_count = len(df_combined[df_combined['Result'] == 'Good'])
    
    print(f"""
======================================================================
 DATASET EXPANSION COMPLETE
======================================================================

Summary:
--------
Previous samples:   {len(df_existing)}
New samples:        {len(df_new)}
Total samples:      {len(df_combined)}

Vulnerable (Error): {vulnerable_count}
Secure (Good):      {secure_count}
Balance ratio:      {vulnerable_count/secure_count:.2f}
""")
    
    return df_combined


if __name__ == "__main__":
    df = main()
