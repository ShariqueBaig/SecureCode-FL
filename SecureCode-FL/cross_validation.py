"""
Cross-Validation Training Module
Uses Stratified K-Fold Cross-Validation for more reliable results on small datasets.
This better replicates the thesis methodology.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.svm import SVC
from sklearn.model_selection import StratifiedKFold, cross_val_score, cross_val_predict
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

from config import MODELS_CONFIG, MODELS_DIR, RANDOM_STATE


class CrossValidationTrainer:
    """
    Trains models using Stratified K-Fold Cross-Validation.
    More reliable for small datasets like the 60-sample vulnerability dataset.
    """
    
    def __init__(self, n_splits=5):
        self.n_splits = n_splits
        self.models = {}
        self.results = {}
        self.cv_scores = {}
        self.trained_models = {}
        
    def initialize_models(self):
        """Initialize all models"""
        print("=" * 60)
        print("INITIALIZING MODELS FOR CROSS-VALIDATION")
        print("=" * 60)
        
        self.models = {
            'Logistic Regression': LogisticRegression(
                random_state=RANDOM_STATE, max_iter=1000, solver='lbfgs'
            ),
            'Random Forest': RandomForestClassifier(
                n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1
            ),
            'SVM': SVC(
                kernel='rbf', random_state=RANDOM_STATE, probability=True
            ),
            'Gradient Boosting': GradientBoostingClassifier(
                n_estimators=100, random_state=RANDOM_STATE, learning_rate=0.1
            ),
            'Extra Trees': ExtraTreesClassifier(
                n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1
            ),
        }
        
        if XGBOOST_AVAILABLE:
            self.models['XGBoost'] = XGBClassifier(
                n_estimators=100, random_state=RANDOM_STATE, 
                learning_rate=0.1, use_label_encoder=False, eval_metric='logloss'
            )
        
        print(f"Initialized {len(self.models)} models for {self.n_splits}-Fold CV")
        return self.models
    
    def cross_validate_all(self, X, y):
        """
        Perform cross-validation on all models.
        """
        print("\n" + "=" * 60)
        print(f"STRATIFIED {self.n_splits}-FOLD CROSS-VALIDATION")
        print("=" * 60)
        
        self.initialize_models()
        
        # Create stratified k-fold
        skf = StratifiedKFold(n_splits=self.n_splits, shuffle=True, random_state=RANDOM_STATE)
        
        # Convert sparse matrix to dense if needed
        if hasattr(X, 'toarray'):
            X_dense = X.toarray()
        else:
            X_dense = X
        
        for name, model in self.models.items():
            print(f"\n{name}:")
            print("-" * 40)
            
            # Cross-validation scores
            cv_accuracy = cross_val_score(model, X_dense, y, cv=skf, scoring='accuracy')
            cv_precision = cross_val_score(model, X_dense, y, cv=skf, scoring='precision')
            cv_recall = cross_val_score(model, X_dense, y, cv=skf, scoring='recall')
            cv_f1 = cross_val_score(model, X_dense, y, cv=skf, scoring='f1')
            
            try:
                cv_roc_auc = cross_val_score(model, X_dense, y, cv=skf, scoring='roc_auc')
            except:
                cv_roc_auc = np.array([0.0] * self.n_splits)
            
            # Cross-val predictions for confusion matrix
            y_pred_cv = cross_val_predict(model, X_dense, y, cv=skf)
            
            # Store results
            self.cv_scores[name] = {
                'accuracy_scores': cv_accuracy,
                'precision_scores': cv_precision,
                'recall_scores': cv_recall,
                'f1_scores': cv_f1,
                'roc_auc_scores': cv_roc_auc,
            }
            
            self.results[name] = {
                'accuracy': cv_accuracy.mean(),
                'accuracy_std': cv_accuracy.std(),
                'precision': cv_precision.mean(),
                'precision_std': cv_precision.std(),
                'recall': cv_recall.mean(),
                'recall_std': cv_recall.std(),
                'f1_score': cv_f1.mean(),
                'f1_std': cv_f1.std(),
                'roc_auc': cv_roc_auc.mean(),
                'roc_auc_std': cv_roc_auc.std(),
                'confusion_matrix': confusion_matrix(y, y_pred_cv),
                'y_pred': y_pred_cv
            }
            
            # Print results
            print(f"  Accuracy:  {cv_accuracy.mean()*100:.1f}% (±{cv_accuracy.std()*100:.1f}%)")
            print(f"  Precision: {cv_precision.mean():.4f} (±{cv_precision.std():.4f})")
            print(f"  Recall:    {cv_recall.mean():.4f} (±{cv_recall.std():.4f})")
            print(f"  F1-Score:  {cv_f1.mean():.4f} (±{cv_f1.std():.4f})")
            print(f"  ROC-AUC:   {cv_roc_auc.mean():.4f} (±{cv_roc_auc.std():.4f})")
            print(f"  Fold Accuracies: {[f'{s*100:.1f}%' for s in cv_accuracy]}")
        
        # Train final models on full data
        print("\n" + "-" * 40)
        print("Training final models on full dataset...")
        for name, model in self.models.items():
            model.fit(X_dense, y)
            self.trained_models[name] = model
            print(f"  {name} trained on full data")
        
        return self.results
    
    def get_summary_table(self):
        """Generate summary table with CV results"""
        summary_data = []
        for name, metrics in self.results.items():
            summary_data.append({
                'Model': name,
                'Accuracy': f"{metrics['accuracy']*100:.1f}% (±{metrics['accuracy_std']*100:.1f}%)",
                'Precision': f"{metrics['precision']:.4f}",
                'Recall': f"{metrics['recall']:.4f}",
                'F1-Score': f"{metrics['f1_score']:.4f}",
                'ROC-AUC': f"{metrics['roc_auc']:.4f}",
                'Mean Accuracy': metrics['accuracy']
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df = summary_df.sort_values('Mean Accuracy', ascending=False)
        
        return summary_df
    
    def get_best_model(self):
        """Get the best performing model"""
        best_name = max(self.results.keys(), key=lambda k: self.results[k]['accuracy'])
        best_accuracy = self.results[best_name]['accuracy']
        best_model = self.trained_models[best_name]
        return best_name, best_accuracy, best_model
    
    def save_models(self, vectorizer=None, feature_names=None):
        """Save all trained models"""
        print("\n" + "=" * 60)
        print("SAVING MODELS")
        print("=" * 60)
        
        os.makedirs(MODELS_DIR, exist_ok=True)
        
        for name, model in self.trained_models.items():
            filename = name.lower().replace(' ', '_') + '_cv.pkl'
            filepath = os.path.join(MODELS_DIR, filename)
            joblib.dump(model, filepath)
            print(f"Saved: {filename}")
        
        if vectorizer:
            joblib.dump(vectorizer, os.path.join(MODELS_DIR, 'tfidf_vectorizer.pkl'))
            print("Saved: tfidf_vectorizer.pkl")
        
        if feature_names is not None:
            joblib.dump(feature_names, os.path.join(MODELS_DIR, 'feature_names.pkl'))
            print("Saved: feature_names.pkl")
        
        # Save CV results
        results_df = self.get_summary_table()
        results_df.to_csv(os.path.join(MODELS_DIR, 'cv_results.csv'), index=False)
        print("Saved: cv_results.csv")


def main():
    """Run cross-validation training"""
    from data_preprocessing import DataPreprocessor
    
    # Prepare data
    print("Preparing data...")
    preprocessor = DataPreprocessor()
    X_train, X_test, y_train, y_test, vectorizer, feature_names = preprocessor.prepare_data()
    
    # Combine train and test for CV
    from scipy.sparse import vstack
    X_full = vstack([X_train, X_test])
    y_full = np.concatenate([y_train, y_test])
    
    print(f"\nFull dataset: {X_full.shape[0]} samples, {X_full.shape[1]} features")
    
    # Cross-validation
    trainer = CrossValidationTrainer(n_splits=5)
    results = trainer.cross_validate_all(X_full, y_full)
    
    # Summary
    print("\n" + "=" * 60)
    print("CROSS-VALIDATION SUMMARY")
    print("=" * 60)
    summary = trainer.get_summary_table()
    print(summary[['Model', 'Accuracy', 'Precision', 'Recall', 'F1-Score']].to_string(index=False))
    
    # Best model
    best_name, best_accuracy, best_model = trainer.get_best_model()
    print(f"\n★ Best Model: {best_name} with {best_accuracy*100:.1f}% accuracy")
    
    # Save models
    trainer.save_models(vectorizer, feature_names)
    
    return results, trainer


if __name__ == "__main__":
    results, trainer = main()
