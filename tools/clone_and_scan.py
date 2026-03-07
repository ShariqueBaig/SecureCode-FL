"""
Target Repos for Bandit Scanning
=================================
Clone these repos and scan them with bandit_scanner.py to extract
vulnerable Python code samples for dataset expansion.

Usage:
  python tools/clone_and_scan.py

This script will:
  1. Clone each repo into tools/repos/
  2. Run Bandit on each
  3. Collect all findings into data/bandit_scanned_samples.csv
"""

import os
import subprocess
from pathlib import Path

REPOS_DIR = Path(__file__).parent / "repos"

# Repos with known history of Python security issues
# Selected for: Flask/Django/FastAPI apps with security-relevant code
TARGET_REPOS = [
    # Popular Flask apps (many security patterns)
    "https://github.com/pallets/flask.git",
    "https://github.com/miguelgrinberg/flasky.git",
    "https://github.com/flaskbb/flaskbb.git",
    "https://github.com/honmaple/flask-blog.git",

    # Django apps
    "https://github.com/django/django.git",
    "https://github.com/wsvincent/djangoforbeginners.git",
    "https://github.com/justdjango/django-ecommerce.git",

    # FastAPI apps
    "https://github.com/fastapi/fastapi.git",
    "https://github.com/tiangolo/full-stack-fastapi-template.git",

    # Deliberately vulnerable Python apps (great for labeled vuln samples)
    "https://github.com/stamparm/DSVW.git",                     # Damn Small Vulnerable Web
    "https://github.com/anxolerd/dvpwa.git",                    # Damn Vulnerable Python Web App
    "https://github.com/fportantier/vulpy.git",                 # Vulnerable Python app

    # Security-related Python projects
    "https://github.com/PyCQA/bandit.git",                      # Bandit itself (has test cases!)
    "https://github.com/sqlmapproject/sqlmap.git",               # SQL injection tool (vuln patterns)
    "https://github.com/swisskyrepo/PayloadsAllTheThings.git",  # Security payloads

    # IoT / embedded Python
    "https://github.com/home-assistant/core.git",               # Home Assistant (IoT)
    "https://github.com/esphome/esphome.git",                   # ESP Home (IoT firmware)
]


def clone_repo(repo_url: str) -> str | None:
    """Clone a repo into the repos directory. Returns the local path."""
    REPOS_DIR.mkdir(parents=True, exist_ok=True)

    repo_name = repo_url.split("/")[-1].replace(".git", "")
    local_path = REPOS_DIR / repo_name

    if local_path.exists():
        print(f"  ⏭ {repo_name} already cloned")
        return str(local_path)

    print(f"  ⬇ Cloning {repo_name}...")
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(local_path)],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            print(f"  ✓ Cloned {repo_name}")
            return str(local_path)
        else:
            print(f"  ✗ Failed to clone {repo_name}: {result.stderr[:200]}")
            return None
    except Exception as e:
        print(f"  ✗ Error cloning {repo_name}: {e}")
        return None


def main():
    print("=" * 60)
    print("Clone & Scan Pipeline")
    print("=" * 60)
    print(f"Target: {len(TARGET_REPOS)} repositories\n")

    # Import the scanner
    from bandit_scanner import run_bandit, process_findings, save_samples, print_summary

    all_samples = []

    for i, repo_url in enumerate(TARGET_REPOS):
        print(f"\n[{i+1}/{len(TARGET_REPOS)}] {repo_url}")

        # Clone
        local_path = clone_repo(repo_url)
        if not local_path:
            continue

        # Scan
        findings = run_bandit(local_path)
        if findings:
            samples = process_findings(findings)
            # Re-number relative to all samples
            for s in samples:
                s["S.No"] = len(all_samples) + s["S.No"]
            all_samples.extend(samples)
            print(f"  → {len(samples)} samples from this repo ({len(all_samples)} total)")

    if all_samples:
        # Re-number cleanly
        for i, s in enumerate(all_samples):
            s["S.No"] = i + 1
        save_samples(all_samples)
        print_summary(all_samples)
    else:
        print("\n✗ No samples collected from any repo.")

    print("\n" + "=" * 60)
    print("NEXT STEP: Run merge_datasets.py to combine with original dataset")
    print("=" * 60)


if __name__ == "__main__":
    main()
