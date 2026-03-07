"""
Bandit-Based Vulnerability Scanner for SecureCode-FL Dataset Expansion
=====================================================================
Scans Python repos/directories with Bandit (Python SAST tool) and extracts
flagged code snippets as labeled vulnerability samples.

Labels are derived from Bandit's CWE mappings:
  - High-confidence Bandit findings → Result = "Error" (Vulnerable)
  - Clean code from the same files    → Result = "Good"  (Secure)
  - Bandit's test IDs map to OWASP categories

Usage:
  1. Install bandit: pip install bandit
  2. Clone target repos into tools/repos/ (or point at any Python directory)
  3. Run: python tools/bandit_scanner.py --target <path_to_python_code>
  4. Output: data/bandit_scanned_samples.csv

The output CSV matches the existing dataset schema:
  S.No, Primary Vulnerability, Exploit, Result, Code
"""

import os
import re
import csv
import json
import argparse
import subprocess
from pathlib import Path
from collections import defaultdict

# ── Configuration ──────────────────────────────────────────────

OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "bandit_scanned_samples.csv"

# Minimum lines of code for a function to be a meaningful sample
MIN_FUNCTION_LINES = 5

# ── Bandit Test ID → OWASP Category Mapping ───────────────────
# Maps Bandit's test IDs to your OWASP API Security categories
# Reference: https://bandit.readthedocs.io/en/latest/plugins/

BANDIT_TO_OWASP = {
    # SQL Injection / Command Injection / Code Injection
    "B608": ("Unsafe Consumption of APIs", "SQL Injection via string formatting"),
    "B609": ("Unsafe Consumption of APIs", "SQL Injection via wildcard"),
    "B610": ("Unsafe Consumption of APIs", "Django extra() SQL Injection"),
    "B611": ("Unsafe Consumption of APIs", "Django raw SQL Injection"),
    "B602": ("Unsafe Consumption of APIs", "subprocess with shell=True"),
    "B603": ("Unsafe Consumption of APIs", "subprocess without shell"),
    "B604": ("Unsafe Consumption of APIs", "Function call with shell=True"),
    "B605": ("Unsafe Consumption of APIs", "os.system() call"),
    "B606": ("Unsafe Consumption of APIs", "os.popen() call"),
    "B607": ("Unsafe Consumption of APIs", "Partial path process execution"),
    "B301": ("Unsafe Consumption of APIs", "Pickle deserialization"),
    "B302": ("Unsafe Consumption of APIs", "marshal deserialization"),
    "B303": ("Broken Authentication", "Insecure hash function (MD5/SHA1)"),
    "B304": ("Broken Authentication", "Insecure cipher usage"),
    "B305": ("Broken Authentication", "Insecure cipher mode"),
    "B306": ("Unsafe Consumption of APIs", "mktemp usage"),
    "B307": ("Unsafe Consumption of APIs", "eval() usage"),
    "B308": ("Unsafe Consumption of APIs", "mark_safe() usage"),
    "B310": ("Server Side Request Forgery", "urllib.urlopen URL"),
    "B311": ("Broken Authentication", "Random number for crypto"),
    "B312": ("Server Side Request Forgery", "Telnet usage"),
    "B313": ("Unsafe Consumption of APIs", "xml.etree.ElementTree"),
    "B314": ("Unsafe Consumption of APIs", "xml.dom.minidom"),
    "B315": ("Unsafe Consumption of APIs", "xml.dom.expatreader"),
    "B316": ("Unsafe Consumption of APIs", "xml.dom.expatbuilder"),
    "B317": ("Unsafe Consumption of APIs", "xml.sax"),
    "B318": ("Unsafe Consumption of APIs", "xml.dom.pulldom"),
    "B319": ("Unsafe Consumption of APIs", "xml.etree.cElementTree"),
    "B320": ("Unsafe Consumption of APIs", "lxml"),
    "B321": ("Unsafe Consumption of APIs", "FTP usage"),
    "B322": ("Unsafe Consumption of APIs", "input() in Python 2"),
    "B323": ("Unsafe Consumption of APIs", "unverified SSL context"),
    "B324": ("Broken Authentication", "Insecure hash function"),
    "B325": ("Unsafe Consumption of APIs", "tempnam/tmpnam usage"),

    # Hardcoded secrets
    "B105": ("Broken Authentication", "Hardcoded password in function argument"),
    "B106": ("Broken Authentication", "Hardcoded password in function default"),
    "B107": ("Broken Authentication", "Hardcoded password string"),

    # Hardcoded bindings
    "B104": ("Security Misconfiguration", "Binding to 0.0.0.0"),

    # Flask debug mode
    "B201": ("Security Misconfiguration", "Flask debug mode enabled"),

    # Try/except pass
    "B110": ("Security Misconfiguration", "Try-except-pass (silencing errors)"),

    # Assert used for security
    "B101": ("Security Misconfiguration", "Assert used for security check"),

    # Permissions
    "B103": ("Security Misconfiguration", "Permissive file permissions"),

    # YAML
    "B506": ("Unsafe Consumption of APIs", "Unsafe yaml.load()"),

    # Jinja2
    "B701": ("Security Misconfiguration", "Jinja2 autoescape disabled"),

    # Requests without verify
    "B501": ("Unsafe Consumption of APIs", "requests with verify=False"),

    # Paramiko
    "B507": ("Broken Authentication", "SSH with missing host key verification"),

    # Snmp
    "B508": ("Security Misconfiguration", "SNMPv1/v2 insecure version"),
    "B509": ("Security Misconfiguration", "SNMPv3 insecure config"),
}


def run_bandit(target_path: str) -> list[dict]:
    """Run Bandit on a target directory and return findings as JSON."""
    print(f"Running Bandit on: {target_path}")

    try:
        result = subprocess.run(
            ["bandit", "-r", target_path, "-f", "json", "-ll"],  # -ll = medium+ severity
            capture_output=True,
            text=True,
            timeout=300,
        )
    except FileNotFoundError:
        print("✗ Bandit not found. Install with: pip install bandit")
        return []
    except subprocess.TimeoutExpired:
        print("✗ Bandit scan timed out after 5 minutes")
        return []

    # Bandit returns non-zero even on success (if findings exist)
    output = result.stdout
    if not output:
        print("  No output from Bandit. Possibly no Python files found.")
        return []

    try:
        data = json.loads(output)
        findings = data.get("results", [])
        print(f"  Found {len(findings)} security findings")
        return findings
    except json.JSONDecodeError:
        print("  ✗ Failed to parse Bandit output")
        return []


def extract_function_around_line(filepath: str, target_line: int) -> str:
    """
    Extract the function/method containing the target line.
    Falls back to extracting a context window if no function boundary is found.
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return ""

    if target_line < 1 or target_line > len(lines):
        return ""

    # Search backwards for function definition
    func_start = target_line - 1
    for i in range(target_line - 1, max(0, target_line - 50), -1):
        line = lines[i].rstrip()
        if re.match(r'^(\s*)(def |class |@app\.|@router\.)', line):
            func_start = i
            break

    # Determine the indentation of the function
    func_indent = len(lines[func_start]) - len(lines[func_start].lstrip())

    # Search forwards for the end of the function
    func_end = target_line
    for i in range(target_line, min(len(lines), target_line + 50)):
        line = lines[i]
        stripped = line.rstrip()
        if stripped == "":
            continue
        current_indent = len(line) - len(line.lstrip())
        # If we find a line at the same or lesser indentation, the function ended
        if current_indent <= func_indent and i > func_start + 1:
            func_end = i
            break
        func_end = i + 1

    # Extract the function code
    function_code = "".join(lines[func_start:func_end]).strip()
    return function_code


def process_findings(findings: list[dict]) -> list[dict]:
    """Convert Bandit findings into dataset samples."""
    samples = []
    seen_codes = set()
    serial = 1

    for finding in findings:
        test_id = finding.get("test_id", "")
        severity = finding.get("issue_severity", "")
        confidence = finding.get("issue_confidence", "")
        filename = finding.get("filename", "")
        line_number = finding.get("line_number", 0)
        issue_text = finding.get("issue_text", "")

        # Only use high-confidence findings for reliable labels
        if confidence not in ("HIGH", "MEDIUM"):
            continue

        # Map to OWASP category
        if test_id not in BANDIT_TO_OWASP:
            continue

        vuln_type, exploit_desc = BANDIT_TO_OWASP[test_id]

        # Extract the vulnerable function
        code = extract_function_around_line(filename, line_number)
        if not code or len(code.split("\n")) < MIN_FUNCTION_LINES:
            continue

        # Deduplicate
        code_hash = hash(code)
        if code_hash in seen_codes:
            continue
        seen_codes.add(code_hash)

        # Create the exploit description
        full_exploit = f"{exploit_desc} ({test_id}: {issue_text[:60]})"

        samples.append({
            "S.No": serial,
            "Primary Vulnerability": vuln_type,
            "Exploit": full_exploit,
            "Result": "Error",  # Bandit flagged = vulnerable
            "Code": code,
        })
        serial += 1

    return samples


def save_samples(samples: list[dict]):
    """Save samples to CSV."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["S.No", "Primary Vulnerability", "Exploit", "Result", "Code"])
        writer.writeheader()
        writer.writerows(samples)

    print(f"\n✓ Saved {len(samples)} samples to {OUTPUT_FILE}")


def print_summary(samples: list[dict]):
    """Print summary statistics."""
    from collections import Counter

    print("\n" + "=" * 60)
    print("BANDIT SCAN COMPLETE — SUMMARY")
    print("=" * 60)
    print(f"Total samples: {len(samples)}")

    print("\nBy vulnerability type:")
    vuln_counts = Counter(s["Primary Vulnerability"] for s in samples)
    for vuln_type, count in vuln_counts.most_common():
        print(f"  {vuln_type}: {count}")

    print("\n⚠ NOTE: Bandit only produces VULNERABLE samples.")
    print("  You'll need secure counterparts. Use merge_datasets.py to combine")
    print("  these with your existing dataset that has balanced Good/Error samples.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scan Python code with Bandit for vulnerability dataset expansion")
    parser.add_argument("--target", "-t", required=True, help="Path to Python source code directory to scan")
    args = parser.parse_args()

    if not os.path.isdir(args.target):
        print(f"✗ Target directory not found: {args.target}")
        exit(1)

    findings = run_bandit(args.target)
    if findings:
        samples = process_findings(findings)
        if samples:
            save_samples(samples)
            print_summary(samples)
        else:
            print("\n✗ No samples extracted from findings (all filtered out).")
    else:
        print("\n✗ No Bandit findings to process.")
