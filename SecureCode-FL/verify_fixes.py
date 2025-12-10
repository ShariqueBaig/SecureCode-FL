"""
VERIFICATION CHECKLIST - DATA INTEGRITY FIX
===========================================

This checklist confirms all fixes have been applied and verified.
Run this to ensure dataset is correct for all future tests.

✅ = Fixed and verified
⚠️  = Needs attention
❌ = Not done
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'federated'))


def check_all():
    """Run all verification checks"""
    
    print("\n" + "=" * 80)
    print("  VERIFICATION CHECKLIST - DATA INTEGRITY FIX")
    print("=" * 80)
    
    checks = []
    
    # Check 1: Config file uses expanded dataset
    print("\n[1/10] Checking config.py...")
    try:
        from config import DATASET_PATH, DATA_DIR
        if 'expanded_dataset_v2.csv' in DATASET_PATH:
            print("  ✅ config.DATASET_PATH = expanded_dataset_v2.csv")
            checks.append(True)
        else:
            print(f"  ❌ config.DATASET_PATH = {DATASET_PATH} (WRONG!)")
            checks.append(False)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        checks.append(False)
    
    # Check 2: Expanded dataset exists
    print("\n[2/10] Checking expanded dataset file...")
    if os.path.exists('data/expanded_dataset_v2.csv'):
        size = os.path.getsize('data/expanded_dataset_v2.csv')
        print(f"  ✅ data/expanded_dataset_v2.csv exists ({size:,} bytes)")
        checks.append(True)
    else:
        print("  ❌ data/expanded_dataset_v2.csv NOT FOUND")
        checks.append(False)
    
    # Check 3: DataPreprocessor loads expanded dataset
    print("\n[3/10] Checking DataPreprocessor...")
    try:
        from data_preprocessing import DataPreprocessor
        dp = DataPreprocessor()
        dp.load_data()
        if len(dp.df) == 471:
            print(f"  ✅ DataPreprocessor loads 471 samples")
            checks.append(True)
        else:
            print(f"  ❌ DataPreprocessor loads {len(dp.df)} samples (expected 471)")
            checks.append(False)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        checks.append(False)
    
    # Check 4: DataPartitioner loads expanded dataset
    print("\n[4/10] Checking DataPartitioner...")
    try:
        from federated.data_partitioner import DataPartitioner
        dp_part = DataPartitioner()
        dp_part.load_data()
        if len(dp_part.df) == 471:
            print(f"  ✅ DataPartitioner loads 471 samples")
            checks.append(True)
        else:
            print(f"  ❌ DataPartitioner loads {len(dp_part.df)} samples (expected 471)")
            checks.append(False)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        checks.append(False)
    
    # Check 5: Label encoding DataPreprocessor
    print("\n[5/10] Checking DataPreprocessor label encoding...")
    try:
        from data_preprocessing import DataPreprocessor
        dp = DataPreprocessor()
        dp.load_data()
        y = dp.encode_labels()
        vulnerable = sum(y == 1)
        secure = sum(y == 0)
        if vulnerable == 233 and secure == 238:
            print(f"  ✅ Labels correct: 233 vulnerable (1), 238 secure (0)")
            checks.append(True)
        else:
            print(f"  ❌ Labels wrong: {vulnerable} vulnerable, {secure} secure")
            checks.append(False)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        checks.append(False)
    
    # Check 6: Label encoding DataPartitioner
    print("\n[6/10] Checking DataPartitioner label encoding...")
    try:
        from federated.data_partitioner import DataPartitioner
        dp_part = DataPartitioner()
        dp_part.load_data()
        vulnerable = sum(dp_part.df['label'] == 1)
        secure = sum(dp_part.df['label'] == 0)
        if vulnerable == 233 and secure == 238:
            print(f"  ✅ Labels correct: 233 vulnerable (1), 238 secure (0)")
            checks.append(True)
        else:
            print(f"  ❌ Labels wrong: {vulnerable} vulnerable, {secure} secure")
            checks.append(False)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        checks.append(False)
    
    # Check 7: Files have been fixed
    print("\n[7/10] Checking file fixes...")
    files_to_check = [
        ('config.py', 'expanded_dataset_v2.csv'),
        ('data_preprocessing.py', 'pd.read_csv'),
        ('federated/data_partitioner.py', "{'Error': 1"),
        ('federated/fl_client.py', 'Vulnerable (1)'),
        ('federated/fl_feedback_client.py', 'Vulnerable (1)'),
    ]
    
    all_fixed = True
    for filename, keyword in files_to_check:
        filepath = filename if filename.startswith('federated') else filename
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                if keyword in content:
                    print(f"  ✅ {filename} contains '{keyword}'")
                else:
                    print(f"  ❌ {filename} missing '{keyword}'")
                    all_fixed = False
        except:
            print(f"  ❌ {filename} not found")
            all_fixed = False
    
    checks.append(all_fixed)
    
    # Check 8: Test files exist
    print("\n[8/10] Checking test files...")
    test_files = [
        'test_clean_baseline.py',
        'test_expanded_dataset_only.py',
        'test_dataset_consistency.py',
    ]
    
    all_exist = True
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"  ✅ {test_file} exists")
        else:
            print(f"  ⚠️  {test_file} not found (optional)")
            all_exist = False
    
    checks.append(all_exist)
    
    # Check 9: No old dataset references
    print("\n[9/10] Checking for old dataset references...")
    old_refs = [
        ('Unsecured Codes.xlsx', 'Old Excel dataset'),
        ('../Previous/', 'Old data directory'),
    ]
    
    has_old_refs = False
    for old_ref, description in old_refs:
        # Quick check in main files
        try:
            for pyfile in ['config.py', 'data_preprocessing.py']:
                with open(pyfile, 'r') as f:
                    if old_ref in f.read():
                        print(f"  ⚠️  Found '{old_ref}' in {pyfile}")
                        has_old_refs = True
        except:
            pass
    
    if not has_old_refs:
        print(f"  ✅ No old dataset references found")
        checks.append(True)
    else:
        print(f"  ❌ Old dataset references still exist")
        checks.append(False)
    
    # Check 10: Summary
    print("\n[10/10] Overall Status...")
    passed = sum(checks)
    total = len(checks)
    
    print(f"\n" + "=" * 80)
    print(f"  RESULTS: {passed}/{total} checks passed")
    print("=" * 80)
    
    if passed == total:
        print("\n✅ ALL CHECKS PASSED - DATASET & LABELS ARE CORRECT!")
        print("\nYou can now safely:")
        print("  1. Run Phase 4 federated learning tests")
        print("  2. Implement Phase 5 (XAI & Privacy)")
        print("  3. Trust that models are trained on correct data")
        return True
    else:
        print(f"\n⚠️  {total - passed} checks failed - review above")
        return False


if __name__ == "__main__":
    success = check_all()
    sys.exit(0 if success else 1)
