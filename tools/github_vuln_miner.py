"""
GitHub Vulnerability Miner for SecureCode-FL Dataset Expansion
==============================================================
Mines GitHub security-related commits in Python repos to extract
vulnerable (before-fix) and secure (after-fix) code pairs.

Labels are derived automatically:
  - Code BEFORE the security fix → Result = "Error" (Vulnerable)
  - Code AFTER the security fix  → Result = "Good"  (Secure)
  - The commit message is used to classify the OWASP vulnerability type.

Usage:
  1. Set your GitHub token:
     - PowerShell: $env:GITHUB_TOKEN = "ghp_xxxx"
     - CMD: set GITHUB_TOKEN=ghp_xxxx
  2. Run: python tools/github_vuln_miner.py
  3. Output: data/github_mined_samples.csv

The output CSV matches the existing dataset schema:
  S.No, Primary Vulnerability, Exploit, Result, Code
"""

import os
import re
import csv
import time
import json
import requests
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
HEADERS = {
    "Accept": "application/vnd.github+json",
}

def verify_token():
    """Verify if the token is valid and report who we are."""
    if not GITHUB_TOKEN:
        return False
    
    auth_headers = HEADERS.copy()
    auth_headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    
    try:
        resp = requests.get("https://api.github.com/user", headers=auth_headers, timeout=10)
        if resp.status_code == 200:
            user = resp.json().get("login")
            print(f"  ✓ Authenticated as: {user}")
            return True
        else:
            print(f"  ⚠ Token provided but verification failed ({resp.status_code}).")
            print(f"    Check permissions or if the token is expired.")
            return False
    except Exception:
        return False

# Detect and Verify Token
IS_AUTHENTICATED = False
if GITHUB_TOKEN:
    if verify_token():
        HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"
        IS_AUTHENTICATED = True

OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "github_mined_samples.csv"

# Rate limiting
API_DELAY = 2.0  # seconds between API calls (GitHub rate limit: 30 req/min for search)

# ── OWASP Mapping ─────────────────────────────────────────────
# Maps keywords found in commit messages to your OWASP vulnerability categories

VULN_KEYWORD_MAP = {
    "Broken Authentication": [
        "hardcoded password", "hardcoded credential", "hardcoded secret",
        "weak password", "plaintext password", "auth bypass", "authentication fix",
        "session fixation", "brute force", "credential", "login bypass",
        "jwt", "token leak", "api key exposed", "secret key",
    ],
    "Broken Object Level Authorization": [
        "idor", "insecure direct object", "object reference",
        "authorization check", "access control", "permission check",
        "ownership check", "bola", "unauthorized access to resource",
    ],
    "Broken Object Property Level Authorization": [
        "mass assignment", "property injection", "field filtering",
        "object property", "unfiltered update", "overposting",
    ],
    "Unrestricted Resource Consumption": [
        "rate limit", "dos", "denial of service", "resource limit",
        "file size", "upload limit", "memory limit", "throttle",
        "max file", "unlimited", "unbounded",
    ],
    "Broken Function Level Authorization": [
        "missing role check", "admin endpoint", "privilege escalation",
        "role based", "rbac", "function level auth", "admin access",
        "missing permission", "horizontal privilege",
    ],
    "Server Side Request Forgery": [
        "ssrf", "server side request", "url validation",
        "internal network", "localhost", "127.0.0.1", "metadata endpoint",
        "url whitelist", "url allowlist",
    ],
    "Security Misconfiguration": [
        "debug mode", "cors", "security header", "x-frame",
        "content-type-options", "hsts", "misconfiguration",
        "default credential", "verbose error", "stack trace",
        "logging sensitive", "xss", "cross site scripting",
    ],
    "Unsafe Consumption of APIs": [
        "sql injection", "sqli", "command injection", "code injection",
        "os.system", "subprocess", "eval(", "exec(", "pickle",
        "deserialization", "yaml.load", "unsanitized input",
        "input validation", "parameterized query", "prepared statement",
        "shell injection", "rce", "remote code execution",
    ],
}


def classify_vulnerability(commit_message: str) -> tuple[str, str]:
    """
    Classify a commit message into an OWASP category.
    Returns (Primary Vulnerability, Exploit description).
    """
    msg_lower = commit_message.lower()

    for category, keywords in VULN_KEYWORD_MAP.items():
        for keyword in keywords:
            if keyword in msg_lower:
                # Create a human-readable exploit description from the commit
                exploit = commit_message.strip()
                if len(exploit) > 80:
                    exploit = exploit[:77] + "..."
                return category, exploit

    return None, None  # Couldn't classify


# ── GitHub Search Queries ─────────────────────────────────────
# These target Python repos with security-related commit messages

SEARCH_QUERIES = [
    "fix sql injection language:python",
    "fix ssrf language:python",
    "fix authentication bypass language:python",
    "fix hardcoded password language:python",
    "fix hardcoded credential language:python",
    "fix command injection language:python",
    "fix xss language:python",
    "fix cors misconfiguration language:python",
    "fix debug mode production language:python",
    "fix rate limiting language:python",
    "fix idor language:python",
    "fix insecure deserialization language:python",
    "fix authorization check language:python",
    "fix access control language:python",
    "fix mass assignment language:python",
    "security fix flask language:python",
    "security fix django language:python",
    "security fix fastapi language:python",
    "fix eval injection language:python",
    "fix pickle vulnerability language:python",
    "fix yaml.load language:python",
    "remove hardcoded secret language:python",
    "fix privilege escalation language:python",
]


def search_commits(query: str, per_page: int = 30) -> list:
    """Search GitHub for commits matching the query."""
    url = "https://api.github.com/search/commits"
    params = {
        "q": query,
        "per_page": per_page,
        "sort": "committer-date",
        "order": "desc",
    }
    HEADERS["Accept"] = "application/vnd.github.cloak-preview+json"

    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if resp.status_code == 403:
            print(f"  ⚠ Rate limited. Waiting 60s...")
            time.sleep(60)
            resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if resp.status_code != 200:
            print(f"  ✗ Search failed ({resp.status_code}): {resp.text[:200]}")
            return []
        data = resp.json()
        return data.get("items", [])
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return []


def get_commit_diff(repo_full_name: str, sha: str) -> dict | None:
    """Get the diff for a specific commit. Returns parsed file changes."""
    url = f"https://api.github.com/repos/{repo_full_name}/commits/{sha}"
    HEADERS["Accept"] = "application/vnd.github+json"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception:
        return None


def extract_python_functions_from_patch(patch: str) -> tuple[str, str]:
    """
    Extract the before (vulnerable) and after (secure) code from a unified diff patch.
    Returns (before_code, after_code).
    """
    if not patch:
        return "", ""

    before_lines = []
    after_lines = []

    for line in patch.split("\n"):
        if line.startswith("@@"):
            continue
        elif line.startswith("-") and not line.startswith("---"):
            before_lines.append(line[1:])  # Remove the leading '-'
            # Don't add to after (this line was removed)
        elif line.startswith("+") and not line.startswith("+++"):
            after_lines.append(line[1:])  # Remove the leading '+'
            # Don't add to before (this line was added)
        else:
            # Context line (unchanged)
            clean = line[1:] if line.startswith(" ") else line
            before_lines.append(clean)
            after_lines.append(clean)

    before_code = "\n".join(before_lines).strip()
    after_code = "\n".join(after_lines).strip()

    return before_code, after_code


def is_meaningful_sample(code: str) -> bool:
    """Check if the code snippet is long enough to be meaningful."""
    if not code:
        return False
    lines = [l for l in code.split("\n") if l.strip()]
    # Require at least 5 meaningful lines
    return len(lines) >= 5


def mine_samples() -> list[dict]:
    """Main mining loop. Returns list of samples in dataset format."""
    all_samples = []
    seen_codes = set()  # Deduplicate
    serial = 1

    print("=" * 60)
    print("GitHub Vulnerability Miner for SecureCode-FL")
    print("=" * 60)

    if not IS_AUTHENTICATED:
        print("\n⚠ WARNING: No Valid GITHUB_TOKEN detected.")
        print("  You are running unauthenticated (10 search req/min limit).")
        print("  How to fix in PowerShell:")
        print('  $env:GITHUB_TOKEN = "your_token_here"')
    else:
        print("\n✓ Running with Authentication (30 search req/min limit).")

    for i, query in enumerate(SEARCH_QUERIES):
        print(f"\n[{i+1}/{len(SEARCH_QUERIES)}] Searching: {query}")
        commits = search_commits(query, per_page=30)
        print(f"  Found {len(commits)} commits")

        for commit_item in commits:
            commit_msg = commit_item.get("commit", {}).get("message", "")
            repo_name = commit_item.get("repository", {}).get("full_name", "")
            sha = commit_item.get("sha", "")

            # Classify the vulnerability type from commit message
            vuln_type, exploit_desc = classify_vulnerability(commit_msg)
            if not vuln_type:
                continue  # Skip unclassifiable commits

            # Get the commit diff
            time.sleep(API_DELAY)
            commit_data = get_commit_diff(repo_name, sha)
            if not commit_data:
                continue

            files = commit_data.get("files", [])
            for f in files:
                filename = f.get("filename", "")
                if not filename.endswith(".py"):
                    continue

                patch = f.get("patch", "")
                if not patch:
                    continue

                # Extract before/after code
                before_code, after_code = extract_python_functions_from_patch(patch)

                # Add the VULNERABLE (before-fix) sample
                if is_meaningful_sample(before_code):
                    code_hash = hash(before_code)
                    if code_hash not in seen_codes:
                        seen_codes.add(code_hash)
                        all_samples.append({
                            "S.No": serial,
                            "Primary Vulnerability": vuln_type,
                            "Exploit": exploit_desc,
                            "Result": "Error",  # Vulnerable
                            "Code": before_code,
                        })
                        serial += 1

                # Add the SECURE (after-fix) sample
                if is_meaningful_sample(after_code):
                    code_hash = hash(after_code)
                    if code_hash not in seen_codes:
                        seen_codes.add(code_hash)
                        all_samples.append({
                            "S.No": serial,
                            "Primary Vulnerability": vuln_type,
                            "Exploit": f"Secure: {exploit_desc}",
                            "Result": "Good",  # Secure
                            "Code": after_code,
                        })
                        serial += 1

            print(f"  Collected {len(all_samples)} samples so far...")

        time.sleep(API_DELAY)

    return all_samples


def save_samples(samples: list[dict]):
    """Save mined samples to CSV in the same format as the existing dataset."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["S.No", "Primary Vulnerability", "Exploit", "Result", "Code"])
        writer.writeheader()
        writer.writerows(samples)

    print(f"\n✓ Saved {len(samples)} samples to {OUTPUT_FILE}")


def print_summary(samples: list[dict]):
    """Print a summary of mined data."""
    from collections import Counter

    print("\n" + "=" * 60)
    print("MINING COMPLETE — SUMMARY")
    print("=" * 60)
    print(f"Total samples: {len(samples)}")

    result_counts = Counter(s["Result"] for s in samples)
    print(f"  Vulnerable (Error): {result_counts.get('Error', 0)}")
    print(f"  Secure (Good):      {result_counts.get('Good', 0)}")

    print("\nBy vulnerability type:")
    vuln_counts = Counter(s["Primary Vulnerability"] for s in samples)
    for vuln_type, count in vuln_counts.most_common():
        print(f"  {vuln_type}: {count}")


if __name__ == "__main__":
    samples = mine_samples()
    if samples:
        save_samples(samples)
        print_summary(samples)
    else:
        print("\n✗ No samples collected. Check your GITHUB_TOKEN and internet connection.")
