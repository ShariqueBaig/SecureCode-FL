"""
Data Preprocessing Module
Handles loading and preprocessing of the vulnerability dataset
Based on thesis methodology: TF-IDF vectorization for code representation
"""

import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

from config import DATASET_PATH, TFIDF_CONFIG, RANDOM_STATE, TEST_SIZE


class DataPreprocessor:
    """
    Preprocesses code vulnerability dataset for ML training.
    Implements the methodology from the thesis.
    """
    
    def __init__(self, dataset_path=DATASET_PATH):
        self.dataset_path = dataset_path
        self.df = None
        self.vectorizer = None
        self.label_encoder = None
        self.feature_names = None
        
    def load_data(self):
        """Load the expanded CSV dataset"""
        print("=" * 60)
        print("LOADING DATASET (EXPANDED - 471 SAMPLES)")
        print("=" * 60)
        
        # Load CSV (expanded dataset) instead of Excel (original 60 samples)
        if self.dataset_path.endswith('.csv'):
            self.df = pd.read_csv(self.dataset_path)
        else:
            self.df = pd.read_excel(self.dataset_path)
        
        # Keep only relevant columns
        relevant_cols = ['S.No', 'Primary Vulnerability', 'Exploit', 'Result', 'Code']
        self.df = self.df[relevant_cols]
        
        print(f"Dataset loaded successfully!")
        print(f"Shape: {self.df.shape}")
        print(f"\nColumns: {self.df.columns.tolist()}")
        print(f"\nClass Distribution:")
        print(self.df['Result'].value_counts())
        print(f"\nVulnerability Types:")
        print(self.df['Primary Vulnerability'].value_counts())
        
        return self.df
    
    def preprocess_code(self, code):
        """
        Preprocess code snippets for feature extraction.
        Based on thesis methodology.
        """
        if pd.isna(code):
            return ""
        
        code = str(code)
        
        # Normalize whitespace
        code = re.sub(r'\s+', ' ', code)
        
        # Keep code structure but normalize
        code = code.strip()
        
        return code
    
    def extract_features(self):
        """
        Extract features using TF-IDF vectorization.
        This is the core feature representation from the thesis.
        """
        print("\n" + "=" * 60)
        print("FEATURE EXTRACTION (TF-IDF)")
        print("=" * 60)
        
        # Preprocess code
        self.df['processed_code'] = self.df['Code'].apply(self.preprocess_code)
        
        # Initialize TF-IDF Vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=TFIDF_CONFIG['max_features'],
            ngram_range=TFIDF_CONFIG['ngram_range'],
            min_df=TFIDF_CONFIG['min_df'],
            max_df=TFIDF_CONFIG['max_df'],
            stop_words=TFIDF_CONFIG['stop_words'],
            token_pattern=r'(?u)\b\w+\b'  # Include single character tokens
        )
        
        # Fit and transform
        X = self.vectorizer.fit_transform(self.df['processed_code'])
        self.feature_names = self.vectorizer.get_feature_names_out()
        
        print(f"TF-IDF Features extracted: {X.shape[1]}")
        print(f"Top 20 features: {list(self.feature_names[:20])}")
        
        return X
    
    def encode_labels(self):
        """
        Encode labels: Error -> 1 (Vulnerable), Good -> 0 (Secure)
        """
        print("\n" + "=" * 60)
        print("LABEL ENCODING")
        print("=" * 60)
        
        # Binary encoding: Error = 1 (Vulnerable), Good = 0 (Secure)
        self.df['label'] = self.df['Result'].apply(
            lambda x: 1 if str(x).strip().lower() == 'error' else 0
        )
        
        y = self.df['label'].values
        
        print(f"Label encoding: Error -> 1 (Vulnerable), Good -> 0 (Secure)")
        print(f"Vulnerable samples: {sum(y)}")
        print(f"Secure samples: {len(y) - sum(y)}")
        
        return y
    
    def split_data(self, X, y):
        """
        Split data into training and testing sets.
        Following thesis methodology with stratified split.
        """
        print("\n" + "=" * 60)
        print("DATA SPLITTING")
        print("=" * 60)
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, 
            test_size=TEST_SIZE, 
            random_state=RANDOM_STATE,
            stratify=y
        )
        
        print(f"Test size: {TEST_SIZE * 100}%")
        print(f"Random state: {RANDOM_STATE}")
        print(f"Training samples: {X_train.shape[0]}")
        print(f"Testing samples: {X_test.shape[0]}")
        print(f"Training class distribution: {np.bincount(y_train)}")
        print(f"Testing class distribution: {np.bincount(y_test)}")
        
        return X_train, X_test, y_train, y_test
    
    def prepare_data(self):
        """
        Complete data preparation pipeline.
        """
        # Load data
        self.load_data()
        
        # Extract features
        X = self.extract_features()
        
        # Encode labels
        y = self.encode_labels()
        
        # Split data
        X_train, X_test, y_train, y_test = self.split_data(X, y)
        
        return X_train, X_test, y_train, y_test, self.vectorizer, self.feature_names


def main():
    """Test the data preprocessing module"""
    preprocessor = DataPreprocessor()
    X_train, X_test, y_train, y_test, vectorizer, feature_names = preprocessor.prepare_data()
    
    print("\n" + "=" * 60)
    print("DATA PREPARATION COMPLETE")
    print("=" * 60)
    print(f"X_train shape: {X_train.shape}")
    print(f"X_test shape: {X_test.shape}")
    print(f"y_train shape: {y_train.shape}")
    print(f"y_test shape: {y_test.shape}")


if __name__ == "__main__":
    main()
