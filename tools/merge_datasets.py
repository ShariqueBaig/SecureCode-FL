"""
Dataset Merge Tool for SecureCode-FL
====================================
Merges the original dataset with newly mined/scanned samples.
Performs deduplication, rebalancing, and quality checks.

Usage:
  python tools/merge_datasets.py

Output: data/merged_dataset.csv (ready to use as the new training dataset)
"""

import os
import re
import csv
import hashlib
import pandas as pd
import numpy as np
from pathlib import Path
from collections import Counter

# ── Configuration ──────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / "data"
ORIGINAL_DATASET = DATA_DIR / "expanded_dataset.xlsx"
GITHUB_MINED = DATA_DIR / "github_mined_samples.csv"
BANDIT_SCANNED = DATA_DIR / "bandit_scanned_samples.csv"
OUTPUT_FILE = DATA_DIR / "merged_dataset.csv"
REPORT_FILE = DATA_DIR / "merge_report.txt"

# Your OWASP categories (must match existing dataset)
VALID_CATEGORIES = [
    "Broken Authentication",
    "Broken Object Level Authorization",
    "Broken Object Property Level Authorization",
    "Unrestricted Resource Consumption",
    "Broken Function Level Authorization",
    "Server Side Request Forgery",
    "Security Misconfiguration",
    "Unsafe Consumption of APIs",
    "Improper Inventory Management",
    "Unrestricted Access to Sensitive Business Flows",
]

MIN_CODE_LINES = 5
MAX_CODE_LINES = 200  # Filter out overly long samples


def normalize_code(code: str) -> str:
    """Normalize code for deduplication comparison."""
    if pd.isna(code):
        return ""
    code = str(code)
    # Remove comments
    code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
    # Normalize whitespace
    code = re.sub(r'\s+', ' ', code)
    return code.strip().lower()


def code_hash(code: str) -> str:
    """Create a hash of normalized code for deduplication."""
    normalized = normalize_code(code)
    return hashlib.md5(normalized.encode()).hexdigest()


def load_dataset(path: Path, source_name: str) -> pd.DataFrame:
    """Load a CSV dataset and tag with source."""
    if not path.exists():
        print(f"  ⚠ {source_name}: File not found at {path}")
        return pd.DataFrame()

    df = pd.read_csv(path, encoding="utf-8")
    df["_source"] = source_name
    print(f"  ✓ {source_name}: {len(df)} samples loaded")
    return df


def validate_sample(row) -> bool:
    """Check if a sample is valid for inclusion."""
    code = str(row.get("Code", ""))
    result = str(row.get("Result", ""))
    vuln_type = str(row.get("Primary Vulnerability", ""))

    # Must have valid code
    if not code or code == "nan":
        return False

    # Must have valid label
    if result not in ("Error", "Good"):
        return False

    # Must be reasonable length
    lines = [l for l in code.split("\n") if l.strip()]
    if len(lines) < MIN_CODE_LINES or len(lines) > MAX_CODE_LINES:
        return False

    return True


def merge_and_deduplicate(datasets: list[pd.DataFrame]) -> pd.DataFrame:
    """Merge datasets and remove duplicates based on code content."""
    # Concatenate all datasets
    combined = pd.concat(datasets, ignore_index=True)
    print(f"\nTotal samples after concatenation: {len(combined)}")

    # Validate samples
    valid_mask = combined.apply(validate_sample, axis=1)
    combined = combined[valid_mask].copy()
    print(f"After validation filter: {len(combined)}")

    # Deduplicate based on code hash
    combined["_hash"] = combined["Code"].apply(code_hash)
    before_dedup = len(combined)
    combined = combined.drop_duplicates(subset="_hash", keep="first")
    print(f"After deduplication: {len(combined)} (removed {before_dedup - len(combined)} duplicates)")

    # Clean up temporary columns
    combined = combined.drop(columns=["_hash", "_source"], errors="ignore")

    # Re-number
    combined["S.No"] = range(1, len(combined) + 1)

    return combined


def print_report(df: pd.DataFrame, report_lines: list):
    """Print and save a detailed merge report."""
    report_lines.append("=" * 60)
    report_lines.append("MERGED DATASET REPORT")
    report_lines.append("=" * 60)
    report_lines.append(f"Total samples: {len(df)}")

    # Class balance
    result_counts = df["Result"].value_counts()
    report_lines.append(f"\nClass Distribution:")
    for result, count in result_counts.items():
        pct = count / len(df) * 100
        report_lines.append(f"  {result}: {count} ({pct:.1f}%)")

    imbalance = abs(result_counts.get("Error", 0) - result_counts.get("Good", 0))
    if imbalance > len(df) * 0.15:
        report_lines.append(f"\n  ⚠ WARNING: Class imbalance detected ({imbalance} sample difference)")
        report_lines.append(f"  Consider adding more {'secure' if result_counts.get('Error', 0) > result_counts.get('Good', 0) else 'vulnerable'} samples")

    # Per-category breakdown
    report_lines.append(f"\nPer-Category Breakdown:")
    vuln_counts = df["Primary Vulnerability"].value_counts()
    for vuln_type, count in vuln_counts.items():
        error_count = len(df[(df["Primary Vulnerability"] == vuln_type) & (df["Result"] == "Error")])
        good_count = len(df[(df["Primary Vulnerability"] == vuln_type) & (df["Result"] == "Good")])
        report_lines.append(f"  {vuln_type}: {count} total (Error: {error_count}, Good: {good_count})")

    # Quality checks
    report_lines.append(f"\nQuality Checks:")
    avg_length = df["Code"].apply(lambda x: len(str(x).split("\n"))).mean()
    report_lines.append(f"  Average code length: {avg_length:.1f} lines")

    min_length = df["Code"].apply(lambda x: len(str(x).split("\n"))).min()
    max_length = df["Code"].apply(lambda x: len(str(x).split("\n"))).max()
    report_lines.append(f"  Min/Max code length: {min_length}/{max_length} lines")

    # Train/test split projection
    test_size = int(len(df) * 0.2)
    train_size = len(df) - test_size
    report_lines.append(f"\nProjected Split (80/20):")
    report_lines.append(f"  Training: {train_size} samples")
    report_lines.append(f"  Testing:  {test_size} samples")
    report_lines.append(f"  → 1 test sample ≈ {100/test_size:.2f}% accuracy change")

    report_text = "\n".join(report_lines)
    print(report_text)

    # Save report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"\n✓ Report saved to {REPORT_FILE}")


def main():
    print("=" * 60)
    print("SecureCode-FL Dataset Merge Tool")
    print("=" * 60)

    # Load all available datasets
    print("\nLoading datasets:")
    datasets = []

    original = load_dataset(ORIGINAL_DATASET, "original")
    if len(original) > 0:
        datasets.append(original)

    github = load_dataset(GITHUB_MINED, "github_mined")
    if len(github) > 0:
        datasets.append(github)

    bandit = load_dataset(BANDIT_SCANNED, "bandit_scanned")
    if len(bandit) > 0:
        datasets.append(bandit)

    if not datasets:
        print("\n✗ No datasets found. Run the mining/scanning tools first.")
        return

    # Merge
    merged = merge_and_deduplicate(datasets)

    # Save
    merged.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"\n✓ Merged dataset saved to {OUTPUT_FILE}")

    # Report
    report_lines = []
    print_report(merged, report_lines)

    # Instructions
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("1. Review the merged dataset for quality")
    print("2. Update config.py to point to the new dataset:")
    print(f'   DATASET_PATH = os.path.join(DATA_DIR, "merged_dataset.csv")')
    print("3. Re-run training: python main.py")
    print("4. Re-run FL simulation: python federated/fl_simulation.py")
    print("5. Re-run DP experiments: python federated/dp_fl_simulation.py")


if __name__ == "__main__":
    main()
