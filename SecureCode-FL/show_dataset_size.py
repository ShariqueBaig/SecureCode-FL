import pandas as pd

df = pd.read_csv('data/expanded_dataset_v2.csv')

print("="*70)
print("DATASET COMPOSITION FOR TRAINING")
print("="*70)

print(f"\nTOTAL DATASET:")
print(f"  Total samples: {len(df)}")
print(f"  Vulnerable (Error): {(df['Result']=='Error').sum()}")
print(f"  Secure (Good): {(df['Result']=='Good').sum()}")

print(f"\n80/20 TRAIN/TEST SPLIT:")
train_count = int(len(df) * 0.8)
test_count = len(df) - train_count
print(f"  Training samples: {train_count} (80%)")
print(f"    - Vulnerable: {int((df['Result']=='Error').sum() * 0.8)}")
print(f"    - Secure: {int((df['Result']=='Good').sum() * 0.8)}")
print(f"  Test samples: {test_count} (20%)")
print(f"    - Vulnerable: {int((df['Result']=='Error').sum() * 0.2)}")
print(f"    - Secure: {int((df['Result']=='Good').sum() * 0.2)}")

print(f"\nFEDERATED LEARNING DISTRIBUTION (3 clients):")
vuln_count = (df['Result']=='Error').sum()
secure_count = (df['Result']=='Good').sum()
vuln_per_client = int(vuln_count * 0.8 / 3)
secure_per_client = int(secure_count * 0.8 / 3)
total_per_client = vuln_per_client + secure_per_client

print(f"  Training data distributed to 3 clients:")
print(f"  Client 0: {total_per_client} samples ({vuln_per_client} vulnerable, {secure_per_client} secure)")
print(f"  Client 1: {total_per_client} samples ({vuln_per_client} vulnerable, {secure_per_client} secure)")
print(f"  Client 2: {total_per_client} samples ({vuln_per_client} vulnerable, {secure_per_client} secure)")
print(f"  Total FL training: {total_per_client * 3} samples")

print(f"\n  Test data (isolated, not distributed):")
print(f"  {test_count} samples (kept separate)")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"\n✓ Available for training: {train_count} samples")
print(f"✓ Available for testing: {test_count} samples")
print(f"✓ Balanced distribution: {(df['Result']=='Error').sum()} vulnerable, {(df['Result']=='Good').sum()} secure")
