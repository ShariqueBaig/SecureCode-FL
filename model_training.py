"""
Model Training Module
Implements all ML models from the thesis for vulnerability detection.
Models: Logistic Regression, Random Forest, SVM, Gradient Boosting, Extra Trees, XGBoost
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_auc_score
)
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("XGBoost not installed. Will skip XGBoost model.")

from config import MODELS_CONFIG, MODELS_DIR, RANDOM_STATE


class VulnerabilityDetectionModels:
    """
    Trains and evaluates multiple ML models for vulnerability detection.
    Replicates the thesis methodology.
    """
    
    def __init__(self):
        self.models = {}
        self.results = {}
        self.trained_models = {}
        
    def initialize_models(self):
        """
        Initialize all models with configurations from thesis.
        """
        print("=" * 60)
        print("INITIALIZING MODELS")
        print("=" * 60)
        
        # Logistic Regression
        self.models['Logistic Regression'] = LogisticRegression(
            **MODELS_CONFIG['Logistic Regression']
        )
        
        # Random Forest
        self.models['Random Forest'] = RandomForestClassifier(
            **MODELS_CONFIG['Random Forest']
        )
        
        # SVM with RBF kernel
        self.models['SVM'] = SVC(
            **MODELS_CONFIG['SVM']
        )
        
        # Gradient Boosting
        self.models['Gradient Boosting'] = GradientBoostingClassifier(
            **MODELS_CONFIG['Gradient Boosting']
        )
        
        # Extra Trees (Best performer in thesis - 83.3%)
        self.models['Extra Trees'] = ExtraTreesClassifier(
            **MODELS_CONFIG['Extra Trees']
        )
        
        # XGBoost
        if XGBOOST_AVAILABLE:
            self.models['XGBoost'] = XGBClassifier(
                **MODELS_CONFIG['XGBoost']
            )
        
        print(f"Initialized {len(self.models)} models:")
        for name in self.models.keys():
            print(f"  - {name}")
        
        return self.models
    
    def train_model(self, model, model_name, X_train, y_train):
        """
        Train a single model.
        """
        print(f"\nTraining {model_name}...")
        model.fit(X_train, y_train)
        self.trained_models[model_name] = model
        print(f"  {model_name} trained successfully!")
        return model
    
    def evaluate_model(self, model, model_name, X_test, y_test):
        """
        Evaluate a trained model and return metrics.
        """
        # Predictions
        y_pred = model.predict(X_test)
        
        # Probabilities (if available)
        if hasattr(model, 'predict_proba'):
            y_prob = model.predict_proba(X_test)[:, 1]
            roc_auc = roc_auc_score(y_test, y_prob)
        else:
            y_prob = None
            roc_auc = None
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        # Store results
        self.results[model_name] = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'roc_auc': roc_auc,
            'confusion_matrix': cm,
            'y_pred': y_pred,
            'y_prob': y_prob
        }
        
        return self.results[model_name]
    
    def train_and_evaluate_all(self, X_train, X_test, y_train, y_test):
        """
        Train and evaluate all models.
        """
        print("\n" + "=" * 60)
        print("TRAINING AND EVALUATING ALL MODELS")
        print("=" * 60)
        
        self.initialize_models()
        
        for name, model in self.models.items():
            # Train
            self.train_model(model, name, X_train, y_train)
            
            # Evaluate
            metrics = self.evaluate_model(model, name, X_test, y_test)
            
            # Print results
            print(f"\n{name} Results:")
            print(f"  Accuracy:  {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.1f}%)")
            print(f"  Precision: {metrics['precision']:.4f}")
            print(f"  Recall:    {metrics['recall']:.4f}")
            print(f"  F1-Score:  {metrics['f1_score']:.4f}")
            if metrics['roc_auc']:
                print(f"  ROC-AUC:   {metrics['roc_auc']:.4f}")
            print(f"  Confusion Matrix:")
            print(f"    {metrics['confusion_matrix']}")
        
        return self.results
    
    def get_summary_table(self):
        """
        Generate a summary table of all model results.
        """
        summary_data = []
        for name, metrics in self.results.items():
            summary_data.append({
                'Model': name,
                'Accuracy': f"{metrics['accuracy']*100:.1f}%",
                'Precision': f"{metrics['precision']:.4f}",
                'Recall': f"{metrics['recall']:.4f}",
                'F1-Score': f"{metrics['f1_score']:.4f}",
                'ROC-AUC': f"{metrics['roc_auc']:.4f}" if metrics['roc_auc'] else 'N/A'
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df = summary_df.sort_values('Accuracy', ascending=False)
        
        return summary_df
    
    def get_best_model(self):
        """
        Return the best performing model based on accuracy.
        """
        best_name = max(self.results.keys(), key=lambda k: self.results[k]['accuracy'])
        best_accuracy = self.results[best_name]['accuracy']
        best_model = self.trained_models[best_name]
        
        return best_name, best_accuracy, best_model
    
    def save_models(self, vectorizer=None, feature_names=None):
        """
        Save all trained models and the vectorizer.
        """
        print("\n" + "=" * 60)
        print("SAVING MODELS")
        print("=" * 60)
        
        os.makedirs(MODELS_DIR, exist_ok=True)
        
        # Save all models
        for name, model in self.trained_models.items():
            filename = name.lower().replace(' ', '_') + '.pkl'
            filepath = os.path.join(MODELS_DIR, filename)
            joblib.dump(model, filepath)
            print(f"Saved: {filename}")
        
        # Save vectorizer
        if vectorizer:
            joblib.dump(vectorizer, os.path.join(MODELS_DIR, 'tfidf_vectorizer.pkl'))
            print("Saved: tfidf_vectorizer.pkl")
        
        # Save feature names
        if feature_names is not None:
            joblib.dump(feature_names, os.path.join(MODELS_DIR, 'feature_names.pkl'))
            print("Saved: feature_names.pkl")
        
        # Save results
        results_df = self.get_summary_table()
        results_df.to_csv(os.path.join(MODELS_DIR, 'model_results.csv'), index=False)
        print("Saved: model_results.csv")
        
        print(f"\nAll models saved to: {MODELS_DIR}")
    
    def print_classification_reports(self, y_test):
        """
        Print detailed classification reports for all models.
        """
        print("\n" + "=" * 60)
        print("DETAILED CLASSIFICATION REPORTS")
        print("=" * 60)
        
        for name, metrics in self.results.items():
            print(f"\n{name}:")
            print("-" * 40)
            print(classification_report(
                y_test, 
                metrics['y_pred'],
                target_names=['Secure (0)', 'Vulnerable (1)']
            ))


def main():
    """Test the model training module"""
    from data_preprocessing import DataPreprocessor
    
    # Prepare data
    preprocessor = DataPreprocessor()
    X_train, X_test, y_train, y_test, vectorizer, feature_names = preprocessor.prepare_data()
    
    # Initialize and train models
    models = VulnerabilityDetectionModels()
    results = models.train_and_evaluate_all(X_train, X_test, y_train, y_test)
    
    # Print summary
    print("\n" + "=" * 60)
    print("MODEL COMPARISON SUMMARY")
    print("=" * 60)
    summary = models.get_summary_table()
    print(summary.to_string(index=False))
    
    # Get best model
    best_name, best_accuracy, best_model = models.get_best_model()
    print(f"\nBest Model: {best_name} with {best_accuracy*100:.1f}% accuracy")
    
    # Print classification reports
    models.print_classification_reports(y_test)
    
    # Save models
    models.save_models(vectorizer, feature_names)


if __name__ == "__main__":
    main()
