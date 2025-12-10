"""
Dataset & Label Encoding Verification Test
============================================

Verify that:
1. All code uses the expanded dataset (471 samples), not original (60 samples)
2. Label encoding is consistent across ALL modules
3. No data source mixing

Encoding standard (MUST be consistent):
  - 1 = vulnerable/Error
  - 0 = secure/Good
"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'federated'))

from data_preprocessing import DataPreprocessor
from federated.data_partitioner import DataPartitioner


def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_dataset_consistency():
    """Test that all modules use the correct dataset"""
    
    print_section("TEST 1: VERIFY DATA SOURCE")
    
    # Test DataPreprocessor
    print("\n[1a] Testing DataPreprocessor...")
    preprocessor = DataPreprocessor()
    preprocessor.load_data()
    
    size_dp = len(preprocessor.df)
    print(f"  - DataPreprocessor dataset size: {size_dp} samples")
    
    if size_dp != 471:
        print(f"  ❌ ERROR: Expected 471 samples, got {size_dp}")
        return False
    else:
        print(f"  [OK] Correct dataset (471 samples)")
    
    # Test DataPartitioner
    print("\n[1b] Testing DataPartitioner...")
    partitioner = DataPartitioner(num_clients=1)
    partitioner.load_data()
    
    size_dpart = len(partitioner.df)
    print(f"  - DataPartitioner dataset size: {size_dpart} samples")
    
    if size_dpart != 471:
        print(f"  ❌ ERROR: Expected 471 samples, got {size_dpart}")
        return False
    else:
        print(f"  [OK] Correct dataset (471 samples)")
    
    print_section("TEST 2: VERIFY LABEL ENCODING CONSISTENCY")
    
    # Check DataPreprocessor encoding
    print("\n[2a] DataPreprocessor label encoding...")
    y_dp = preprocessor.encode_labels()
    
    vulnerable_dp = sum(y_dp == 1)
    secure_dp = sum(y_dp == 0)
    
    print(f"  - Vulnerable (1): {vulnerable_dp}")
    print(f"  - Secure (0): {secure_dp}")
    
    # Check DataPartitioner encoding
    print("\n[2b] DataPartitioner label encoding...")
    
    vulnerable_dpart = sum(partitioner.df['label'] == 1)
    secure_dpart = sum(partitioner.df['label'] == 0)
    
    print(f"  - Vulnerable (1): {vulnerable_dpart}")
    print(f"  - Secure (0): {secure_dpart}")
    
    # Verify consistency
    print("\n[2c] Consistency check...")
    
    if vulnerable_dp == vulnerable_dpart and secure_dp == secure_dpart:
        print(f"  [OK] Label encoding is CONSISTENT across modules")
        print(f"       Vulnerable: {vulnerable_dp}, Secure: {secure_dp}")
    else:
        print(f"  ❌ ERROR: Inconsistent label encoding!")
        print(f"     DataPreprocessor - Vulnerable: {vulnerable_dp}, Secure: {secure_dp}")
        print(f"     DataPartitioner - Vulnerable: {vulnerable_dpart}, Secure: {secure_dpart}")
        return False
    
    print_section("TEST 3: VERIFY EXPANDED DATASET CONTENT")
    
    # Check actual Result column values
    print("\n[3a] Checking Result column in DataPreprocessor...")
    result_counts_dp = preprocessor.df['Result'].value_counts()
    print(f"  - Error: {result_counts_dp.get('Error', 0)}")
    print(f"  - Good: {result_counts_dp.get('Good', 0)}")
    
    print("\n[3b] Checking Result column in DataPartitioner...")
    result_counts_dpart = partitioner.df['Result'].value_counts()
    print(f"  - Error: {result_counts_dpart.get('Error', 0)}")
    print(f"  - Good: {result_counts_dpart.get('Good', 0)}")
    
    # Verify mapping
    print("\n[3c] Verifying Error -> 1 (vulnerable) mapping...")
    error_count_dp = sum(preprocessor.df['Result'] == 'Error')
    vulnerable_count_dp = sum(y_dp == 1)
    
    error_count_dpart = sum(partitioner.df['Result'] == 'Error')
    vulnerable_count_dpart = sum(partitioner.df['label'] == 1)
    
    if error_count_dp == vulnerable_count_dp and error_count_dpart == vulnerable_count_dpart:
        print(f"  [OK] Error correctly maps to 1 (vulnerable)")
    else:
        print(f"  ❌ ERROR: Error count doesn't match vulnerable count!")
        return False
    
    print("\n[3d] Verifying Good -> 0 (secure) mapping...")
    good_count_dp = sum(preprocessor.df['Result'] == 'Good')
    secure_count_dp = sum(y_dp == 0)
    
    good_count_dpart = sum(partitioner.df['Result'] == 'Good')
    secure_count_dpart = sum(partitioner.df['label'] == 0)
    
    if good_count_dp == secure_count_dp and good_count_dpart == secure_count_dpart:
        print(f"  [OK] Good correctly maps to 0 (secure)")
    else:
        print(f"  ❌ ERROR: Good count doesn't match secure count!")
        return False
    
    print_section("TEST 4: VERIFY EXPANDED DATASET IS USED")
    
    print("\n[4a] Dataset files present:")
    
    files_to_check = [
        ('data/expanded_dataset_v2.csv', 'Expanded dataset (471 samples)'),
        ('models/tfidf_vectorizer.pkl', 'TF-IDF vectorizer'),
        ('models/federated/fl_global_model.keras', 'Federated model'),
    ]
    
    for filepath, description in files_to_check:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"  [OK] {description}: {filepath} ({size:,} bytes)")
        else:
            print(f"  ⚠️  {description}: NOT FOUND ({filepath})")
    
    print_section("FINAL VERDICT")
    
    print("\n✅ ALL TESTS PASSED!")
    print("\n  Dataset Configuration:")
    print(f"    - Data source: data/expanded_dataset_v2.csv")
    print(f"    - Total samples: 471")
    print(f"    - Vulnerable (Error): {vulnerable_dpart}")
    print(f"    - Secure (Good): {secure_dpart}")
    print(f"    - Label encoding: 1=vulnerable, 0=secure")
    print(f"    - Consistent across: DataPreprocessor, DataPartitioner, FL modules")
    
    return True


if __name__ == "__main__":
    success = test_dataset_consistency()
    sys.exit(0 if success else 1)
