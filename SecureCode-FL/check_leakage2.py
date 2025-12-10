import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib

# Load dataset
df = pd.read_csv('data/expanded_dataset_v2.csv')

print("="*70)
print("CHECKING TFIDF VOCABULARY FOR LABEL LEAKAGE")
print("="*70)

# Load actual vectorizer
try:
    vectorizer = joblib.load('models/tfidf_vectorizer.pkl')
    feature_names = vectorizer.get_feature_names_out()
    
    print(f"\nTotal features in vectorizer: {len(feature_names)}")
    
    # Check for vulnerability-related keywords
    vuln_keywords = ['vulnerable', 'vulnerability', 'vulnerable_api', 'secure', 'safe', 
                     'broken', 'authentication', 'authorization', 'injection', 'xss', 'exploit']
    
    found_keywords = []
    for keyword in vuln_keywords:
        matches = [f for f in feature_names if keyword in f.lower()]
        if matches:
            found_keywords.extend(matches)
            print(f"\n✓ '{keyword}': Found {len(matches)} features")
            for match in matches[:3]:  # Show first 3
                print(f"  - {match}")
    
    if found_keywords:
        print(f"\n⚠️  {len(found_keywords)} POTENTIALLY LEAKING FEATURES FOUND")
        print("These could be inflating feature importance!")
    else:
        print("\n✓ NO LABEL LEAKAGE KEYWORDS in vectorizer features")
        
except Exception as e:
    print(f"Could not load vectorizer: {e}")

print("\n" + "="*70)
print("CHECKING DATASET COLUMN STRUCTURE")
print("="*70)

print(f"\nDataset shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")

# Look at code samples
print("\n" + "="*70)
print("SAMPLE CODE ANALYSIS")
print("="*70)

for i in range(3):
    code = df.iloc[i]['Code']
    vuln_type = df.iloc[i]['Primary Vulnerability']
    
    print(f"\n--- Row {i} ---")
    print(f"Vulnerability Type: {vuln_type}")
    
    # Check if vulnerability type appears in code
    if vuln_type.lower() in code.lower():
        print("⚠️  LEAKAGE: Vulnerability type mentioned in code!")
    
    # Print first 300 chars
    print(f"Code (first 300 chars):")
    print(code[:300])
    print("...")
