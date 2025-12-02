"""
Vulnerability Detection Data Analysis Script
This script analyzes the Excel data containing vulnerability information and prepares it for ML training.
"""

import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.naive_bayes import MultinomialNB
import joblib
import warnings
warnings.filterwarnings('ignore')

class VulnerabilityDataAnalyzer:
    def __init__(self, excel_file_path):
        """
        Initialize the analyzer with the Excel file path
        """
        self.excel_file_path = excel_file_path
        self.df = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.vectorizer = None
        self.label_encoder = None
        self.models = {}
        
    def load_data(self):
        """
        Load and examine the Excel data
        """
        try:
            self.df = pd.read_excel(self.excel_file_path)
            print("Data loaded successfully!")
            print(f"Dataset shape: {self.df.shape}")
            print("\nColumn names:")
            print(self.df.columns.tolist())
            print("\nFirst few rows:")
            print(self.df.head())
            print("\nData types:")
            print(self.df.dtypes)
            print("\nMissing values:")
            print(self.df.isnull().sum())
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def clean_and_preprocess(self):
        """
        Clean and preprocess the data
        """
        if self.df is None:
            print("No data loaded. Please load data first.")
            return False
            
        # Remove rows with missing critical values
        initial_shape = self.df.shape[0]
        self.df = self.df.dropna(subset=['Code', 'Result'])
        print(f"Removed {initial_shape - self.df.shape[0]} rows with missing Code or Result")
        
        # Clean the code column - remove extra whitespace and normalize
        self.df['Code'] = self.df['Code'].astype(str).str.strip()
        self.df['Code'] = self.df['Code'].str.replace('\n', ' ').str.replace('\t', ' ')
        self.df['Code'] = self.df['Code'].str.replace(r'\s+', ' ', regex=True)
        
        # Clean the result column
        self.df['Result'] = self.df['Result'].astype(str).str.strip().str.lower()
        
        # Map results to binary classification
        # Assuming 'good' means secure and 'error' means vulnerable
        self.df['is_vulnerable'] = self.df['Result'].map({'error': 1, 'good': 0})
        
        # Fill missing vulnerabilities and exploits with 'unknown'
        self.df['Primary Vulnerability'] = self.df['Primary Vulnerability'].fillna('unknown')
        self.df['Exploit'] = self.df['Exploit'].fillna('unknown')
        
        print(f"Final dataset shape: {self.df.shape}")
        print("\nClass distribution:")
        print(self.df['is_vulnerable'].value_counts())
        print("\nVulnerability types:")
        print(self.df['Primary Vulnerability'].value_counts())
        
        return True
    
    def feature_engineering(self):
        """
        Extract features from the code for ML training
        """
        # Code length features
        self.df['code_length'] = self.df['Code'].str.len()
        self.df['line_count'] = self.df['Code'].str.count('\n') + 1
        self.df['word_count'] = self.df['Code'].str.split().str.len()
        
        # Security-related keyword features
        security_keywords = [
            'eval', 'exec', 'system', 'shell_exec', 'passthru', 'input', 'raw_input',
            'subprocess', 'os.system', 'os.popen', 'pickle.loads', 'marshal.loads',
            'sql', 'query', 'select', 'insert', 'delete', 'update', 'union', 'drop',
            'password', 'secret', 'key', 'token', 'auth', 'login', 'session',
            'md5', 'sha1', 'hash', 'encrypt', 'decrypt', 'base64', 'urlencode',
            'file_get_contents', 'fopen', 'file', 'include', 'require', 'import',
            'document.write', 'innerHTML', 'eval', 'setTimeout', 'setInterval'
        ]
        
        for keyword in security_keywords:
            self.df[f'has_{keyword}'] = self.df['Code'].str.lower().str.contains(keyword, regex=False).astype(int)
        
        # Pattern-based features
        patterns = {
            'has_quotes': r'["\']',
            'has_brackets': r'[\[\]{}()]',
            'has_special_chars': r'[<>&|;$`]',
            'has_url_pattern': r'https?://|www\.',
            'has_email_pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'has_ip_pattern': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            'has_file_extension': r'\.\w{2,4}\b'
        }
        
        for feature, pattern in patterns.items():
            self.df[feature] = self.df['Code'].str.contains(pattern, regex=True).astype(int)
        
        print("Feature engineering completed!")
        print(f"Total features created: {len([col for col in self.df.columns if col.startswith('has_') or col.endswith('_count') or col.endswith('_length')])}")
        
    def prepare_ml_data(self):
        """
        Prepare data for machine learning training
        """
        # Text vectorization using TF-IDF
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8
        )
        
        # Vectorize the code
        code_vectors = self.vectorizer.fit_transform(self.df['Code'])
        
        # Get numerical features
        feature_columns = [col for col in self.df.columns if 
                          col.startswith('has_') or col.endswith('_count') or col.endswith('_length')]
        
        numerical_features = self.df[feature_columns].values
        
        # Combine text and numerical features
        from scipy.sparse import hstack
        X = hstack([code_vectors, numerical_features])
        y = self.df['is_vulnerable'].values
        
        # Split the data
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"Training set shape: {self.X_train.shape}")
        print(f"Test set shape: {self.X_test.shape}")
        print(f"Training set class distribution: {np.bincount(self.y_train)}")
        print(f"Test set class distribution: {np.bincount(self.y_test)}")
        
    def train_models(self):
        """
        Train multiple ML models for vulnerability detection
        """
        # Define models to train
        models_to_train = {
            'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
            'SVM': SVC(random_state=42, probability=True),
            'Naive Bayes': MultinomialNB()
        }
        
        print("Training models...")
        
        for name, model in models_to_train.items():
            print(f"Training {name}...")
            model.fit(self.X_train, self.y_train)
            
            # Make predictions
            y_pred = model.predict(self.X_test)
            y_pred_proba = model.predict_proba(self.X_test)[:, 1] if hasattr(model, 'predict_proba') else None
            
            # Store model and results
            self.models[name] = {
                'model': model,
                'predictions': y_pred,
                'probabilities': y_pred_proba,
                'accuracy': np.mean(y_pred == self.y_test)
            }
            
            print(f"{name} Accuracy: {self.models[name]['accuracy']:.4f}")
            print(f"{name} Classification Report:")
            print(classification_report(self.y_test, y_pred))
            print("-" * 50)
    
    def save_models(self, output_dir="models"):
        """
        Save trained models and vectorizer
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Save vectorizer
        joblib.dump(self.vectorizer, f"{output_dir}/vectorizer.pkl")
        
        # Save the best performing model (highest accuracy)
        best_model_name = max(self.models.keys(), key=lambda k: self.models[k]['accuracy'])
        best_model = self.models[best_model_name]['model']
        
        joblib.dump(best_model, f"{output_dir}/best_model.pkl")
        
        # Save feature names
        feature_columns = [col for col in self.df.columns if 
                          col.startswith('has_') or col.endswith('_count') or col.endswith('_length')]
        joblib.dump(feature_columns, f"{output_dir}/feature_columns.pkl")
        
        print(f"Models saved to {output_dir}/")
        print(f"Best model: {best_model_name} (Accuracy: {self.models[best_model_name]['accuracy']:.4f})")
        
        return best_model_name, self.models[best_model_name]['accuracy']
    
    def generate_report(self):
        """
        Generate a comprehensive analysis report
        """
        print("\n" + "="*60)
        print("VULNERABILITY DETECTION ANALYSIS REPORT")
        print("="*60)
        
        print(f"\nDataset Overview:")
        print(f"- Total samples: {len(self.df)}")
        print(f"- Vulnerable samples: {sum(self.df['is_vulnerable'])}")
        print(f"- Secure samples: {len(self.df) - sum(self.df['is_vulnerable'])}")
        print(f"- Vulnerability rate: {sum(self.df['is_vulnerable'])/len(self.df)*100:.2f}%")
        
        print(f"\nTop Vulnerability Types:")
        vuln_counts = self.df['Primary Vulnerability'].value_counts().head(10)
        for vuln, count in vuln_counts.items():
            print(f"- {vuln}: {count}")
        
        print(f"\nModel Performance Summary:")
        for name, results in self.models.items():
            print(f"- {name}: {results['accuracy']:.4f}")
        
        best_model = max(self.models.keys(), key=lambda k: self.models[k]['accuracy'])
        print(f"\nBest performing model: {best_model}")
        print(f"Best accuracy: {self.models[best_model]['accuracy']:.4f}")

def main():
    # Initialize analyzer
    excel_file = "Unsecured Codes.xlsx"  # Update this path
    analyzer = VulnerabilityDataAnalyzer(excel_file)
    
    # Load and analyze data
    if not analyzer.load_data():
        print("Failed to load data. Please check the file path.")
        return
    
    # Clean and preprocess
    if not analyzer.clean_and_preprocess():
        print("Failed to preprocess data.")
        return
    
    # Feature engineering
    analyzer.feature_engineering()
    
    # Prepare ML data
    analyzer.prepare_ml_data()
    
    # Train models
    analyzer.train_models()
    
    # Save models
    analyzer.save_models()
    
    # Generate report
    analyzer.generate_report()

if __name__ == "__main__":
    main()