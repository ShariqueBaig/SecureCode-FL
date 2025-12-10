"""
Dataset Cleaning Script
=======================
Removes label-revealing function names and comments from code samples.

Leaking patterns to remove:
- "vulnerable_api" -> "api"
- "secure_api" -> "api"  
- "def vulnerable_" -> "def impl_"
- "route vulnerable" -> "route impl"
- Comments mentioning "vulnerable", "secure", "bypass", etc.
"""

import pandas as pd
import re
import os
from datetime import datetime

def clean_code_sample(code):
    """Remove label-revealing patterns from code."""
    
    # 1. Remove vulnerability-related comments
    # Remove lines that are pure comments mentioning vulnerabilities
    lines = code.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Skip comments that explicitly mention vulnerability status
        if '#' in line:
            comment_part = line.split('#')[1]
            # Check if comment is about vulnerability
            if any(word in comment_part.lower() for word in 
                   ['vulnerable', 'secure', 'safe', 'insecure', 'unsafe', 
                    'bypass', 'exploit', 'vulnerability']):
                # Remove the comment part, keep the code
                code_part = line.split('#')[0]
                if code_part.strip():
                    cleaned_lines.append(code_part)
            else:
                cleaned_lines.append(line)
        else:
            cleaned_lines.append(line)
    
    code = '\n'.join(cleaned_lines)
    
    # 2. Replace function names that reveal labels
    replacements = [
        # vulnerable_* -> impl_*
        (r'def\s+vulnerable_', 'def impl_'),
        (r'@app\.route\([\'"].*vulnerable', "@app.route('/impl"),
        (r'def\s+secure_', 'def impl_'),
        (r'@app\.route\([\'"].*secure', "@app.route('/impl"),
        
        # Direct name replacements
        ('vulnerable_api', 'api_endpoint'),
        ('secure_api', 'api_endpoint'),
        ('vulnerable_function', 'process_function'),
        ('secure_function', 'process_function'),
        
        # Route names
        ('/vulnerable', '/endpoint'),
        ('/secure', '/endpoint'),
    ]
    
    for pattern, replacement in replacements:
        code = re.sub(pattern, replacement, code, flags=re.IGNORECASE)
    
    # 3. Remove or anonymize variable names that reveal status
    # Variables like 'is_vulnerable', 'secure_check', etc.
    code = re.sub(r'\b(is_vulnerable|check_vulnerable|secure_check|unsafe_)\b', 
                  'check_status', code, flags=re.IGNORECASE)
    
    # 4. Handle string literals mentioning vulnerability
    # Replace in comments and docstrings
    code = re.sub(r'(#.*)(vulnerable|secure|unsafe|bypass|exploit)', 
                  lambda m: m.group(1) + 'issue', code, flags=re.IGNORECASE)
    
    return code

def clean_dataset(input_path, output_path):
    """Clean entire dataset."""
    
    print("="*70)
    print("DATASET CLEANING: Removing Label-Revealing Patterns")
    print("="*70)
    
    # Load dataset
    df = pd.read_csv(input_path)
    print(f"\n✓ Loaded dataset: {len(df)} rows")
    
    # Track changes
    changes_log = []
    
    # Clean each code sample
    original_codes = df['Code'].copy()
    df['Code'] = df['Code'].apply(clean_code_sample)
    
    # Log differences
    for idx in range(len(df)):
        if original_codes.iloc[idx] != df['Code'].iloc[idx]:
            changes_log.append({
                'row': idx,
                'vulnerability_type': df.iloc[idx]['Primary Vulnerability'],
                'original_length': len(original_codes.iloc[idx]),
                'cleaned_length': len(df['Code'].iloc[idx]),
                'bytes_removed': len(original_codes.iloc[idx]) - len(df['Code'].iloc[idx])
            })
    
    print(f"\n✓ Cleaned {len(changes_log)} code samples")
    print(f"  Total bytes removed: {sum(c['bytes_removed'] for c in changes_log)}")
    
    # Save cleaned dataset
    df.to_csv(output_path, index=False)
    print(f"\n✓ Saved cleaned dataset to: {output_path}")
    
    # Save change log
    log_df = pd.DataFrame(changes_log)
    log_path = output_path.replace('.csv', '_changelog.csv')
    log_df.to_csv(log_path, index=False)
    print(f"✓ Saved change log to: {log_path}")
    
    # Show summary of changes
    print("\n" + "="*70)
    print("CLEANING SUMMARY")
    print("="*70)
    
    vulnerability_counts = log_df['vulnerability_type'].value_counts()
    print(f"\nRows cleaned by vulnerability type:")
    for vuln_type, count in vulnerability_counts.items():
        print(f"  - {vuln_type}: {count} samples")
    
    return df, changes_log

if __name__ == "__main__":
    # Backup original
    original_path = 'data/expanded_dataset_v2.csv'
    backup_path = f'data/expanded_dataset_v2_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    print(f"\n📦 Creating backup: {backup_path}")
    os.system(f'copy "{original_path}" "{backup_path}"')
    
    # Clean dataset
    clean_df, changes = clean_dataset(original_path, original_path)
    
    print("\n" + "="*70)
    print("✓ CLEANING COMPLETE")
    print("="*70)
    print(f"Original backup saved: {backup_path}")
    print(f"Cleaned dataset saved: {original_path}")
    print(f"\nNext steps:")
    print("  1. Commit this cleanup")
    print("  2. Rebuild TF-IDF vectorizer from cleaned data")
    print("  3. Retrain all models")
    print("="*70)
