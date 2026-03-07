# Dataset Expansion Tools

Tools for expanding SecureCode-FL's vulnerability dataset from 471 → 2,000+ samples.

## Quick Start

### Step 1: GitHub Mining (generates paired vulnerable/secure samples)
```powershell
# In PowerShell (Recommended):
$env:GITHUB_TOKEN = "ghp_your_token_here"

# In CMD:
set GITHUB_TOKEN=ghp_your_token_here

# Run the miner
python tools/github_vuln_miner.py
# → Output: data/github_mined_samples.csv
```

**How labeling works**: Commits with messages like "fix sql injection" are found. The code *before* the fix = `Error` (vulnerable). The code *after* the fix = `Good` (secure). The commit message determines the OWASP category.

### Step 2: Bandit Scanning (generates vulnerable samples from real repos)
```bash
# Install Bandit
pip install bandit

# Option A: Scan a single repo
python tools/bandit_scanner.py --target <path_to_python_code>
# → Output: data/bandit_scanned_samples.csv

# Option B: Auto-clone and scan 15+ repos (including deliberately vulnerable apps)
python tools/clone_and_scan.py
# → Output: data/bandit_scanned_samples.csv
```

**How labeling works**: Bandit test IDs (e.g. B608 = SQL injection) are mapped to your OWASP categories. Only HIGH/MEDIUM confidence findings are used.

### Step 3: Merge Everything
```bash
python tools/merge_datasets.py
# → Output: data/merged_dataset.csv + data/merge_report.txt
```

### Step 4: Update Config & Retrain
```python
# In config.py, change:
DATASET_PATH = os.path.join(DATA_DIR, "merged_dataset.csv")
```
Then re-run your full pipeline.

## Labeling Approach (for the paper)

| Source | Labeling Method | Label Quality |
|--------|----------------|---------------|
| Original 471 | Manual expert review | High (ground truth) |
| GitHub mining | Before-fix/after-fix commit pairs | High (security commits are clear intent) |
| Bandit scanning | Automated SAST findings | Medium-High (verified by Bandit confidence levels) |

**For the paper**: Report that "X% of auto-collected samples were manually verified by two annotators, achieving Y% inter-annotator agreement." Manually verify ~20% of the auto-collected data.

## Notes
- GitHub API rate limit: 30 search requests/min (authenticated), 10/min (unauthenticated)
- Bandit scanning of large repos (Django, Home Assistant) may take several minutes
- The merge tool deduplicates using MD5 hashes of normalized code
