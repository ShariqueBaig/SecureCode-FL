"""
Main Script - Vulnerability Detection Research Validation
Replicates the thesis: "Code Validation through Machine Learning - A Left Shift Focus Strategy"

This script:
1. Loads and preprocesses the OWASP API vulnerability dataset
2. Trains all ML models from the thesis
3. Validates results (expecting ~83.3% accuracy for Extra Trees)
4. Runs SHAP-based XAI analysis
5. Generates comprehensive reports
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import RESULTS_DIR, EXPECTED_RESULTS
from data_preprocessing import DataPreprocessor
from model_training import VulnerabilityDetectionModels
from xai.xai_analysis import ExplainableAI, SHAP_AVAILABLE


def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def validate_results(results, expected):
    """
    Validate that results match expected values from thesis.
    """
    print_header("VALIDATION AGAINST THESIS RESULTS")
    
    validation_passed = True
    
    for model_name, expected_accuracy in expected.items():
        if model_name in results:
            actual_accuracy = results[model_name]['accuracy']
            diff = abs(actual_accuracy - expected_accuracy)
            status = "[V] PASS" if diff < 0.1 else "[X] DIFF"  # Allow 10% tolerance
            
            print(f"\n{model_name}:")
            print(f"  Expected: {expected_accuracy*100:.1f}%")
            print(f"  Actual:   {actual_accuracy*100:.1f}%")
            print(f"  Status:   {status}")
            
            if diff >= 0.1:
                validation_passed = False
    
    return validation_passed


def generate_report(results, best_name, best_accuracy, preprocessor):
    """
    Generate comprehensive research validation report.
    """
    print_header("RESEARCH VALIDATION REPORT")
    
    report = []
    report.append("=" * 70)
    report.append("VULNERABILITY DETECTION - THESIS VALIDATION REPORT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 70)
    
    report.append("\n1. DATASET INFORMATION")
    report.append("-" * 40)
    report.append(f"Total samples: {len(preprocessor.df)}")
    report.append(f"Vulnerable samples: {sum(preprocessor.df['label'])}")
    report.append(f"Secure samples: {len(preprocessor.df) - sum(preprocessor.df['label'])}")
    report.append(f"Number of vulnerability types: {preprocessor.df['Primary Vulnerability'].nunique()}")
    
    report.append("\n2. VULNERABILITY DISTRIBUTION")
    report.append("-" * 40)
    for vuln, count in preprocessor.df['Primary Vulnerability'].value_counts().items():
        report.append(f"  {vuln}: {count}")
    
    report.append("\n3. MODEL PERFORMANCE SUMMARY")
    report.append("-" * 40)
    for name, metrics in sorted(results.items(), key=lambda x: x[1]['accuracy'], reverse=True):
        report.append(f"\n{name}:")
        report.append(f"  Accuracy:  {metrics['accuracy']*100:.1f}%")
        report.append(f"  Precision: {metrics['precision']:.4f}")
        report.append(f"  Recall:    {metrics['recall']:.4f}")
        report.append(f"  F1-Score:  {metrics['f1_score']:.4f}")
    
    report.append("\n4. BEST MODEL")
    report.append("-" * 40)
    report.append(f"Model: {best_name}")
    report.append(f"Accuracy: {best_accuracy*100:.1f}%")
    
    report.append("\n5. THESIS VALIDATION")
    report.append("-" * 40)
    report.append(f"Expected best model: Extra Trees (83.3%)")
    report.append(f"Actual best model: {best_name} ({best_accuracy*100:.1f}%)")
    
    report_text = "\n".join(report)
    
    # Save report
    os.makedirs(RESULTS_DIR, exist_ok=True)
    report_path = os.path.join(RESULTS_DIR, 'validation_report.txt')
    with open(report_path, 'w') as f:
        f.write(report_text)
    
    print(report_text)
    print(f"\nReport saved to: {report_path}")
    
    return report_text


def main():
    """
    Main execution function - validates the thesis research.
    """
    print_header("THESIS VALIDATION: Code Validation through Machine Learning")
    print("Replicating: 'A Left Shift Focus Strategy' by Syed Jehanzeb")
    print("Institute of Business Administration, Karachi")
    
    # =========================================================
    # STEP 1: DATA PREPARATION
    # =========================================================
    print_header("STEP 1: DATA PREPARATION")
    
    preprocessor = DataPreprocessor()
    X_train, X_test, y_train, y_test, vectorizer, feature_names = preprocessor.prepare_data()
    
    print(f"\nData preparation complete!")
    print(f"Training samples: {X_train.shape[0]}")
    print(f"Testing samples: {X_test.shape[0]}")
    print(f"Features: {X_train.shape[1]}")
    
    # =========================================================
    # STEP 2: MODEL TRAINING
    # =========================================================
    print_header("STEP 2: MODEL TRAINING")
    
    models = VulnerabilityDetectionModels()
    results = models.train_and_evaluate_all(X_train, X_test, y_train, y_test)
    
    # =========================================================
    # STEP 3: MODEL COMPARISON
    # =========================================================
    print_header("STEP 3: MODEL COMPARISON")
    
    summary = models.get_summary_table()
    print("\nModel Performance Summary:")
    print(summary.to_string(index=False))
    
    best_name, best_accuracy, best_model = models.get_best_model()
    print(f"\n* Best Model: {best_name} with {best_accuracy*100:.1f}% accuracy")
    
    # =========================================================
    # STEP 4: VALIDATION
    # =========================================================
    validation_passed = validate_results(results, EXPECTED_RESULTS)
    
    # =========================================================
    # STEP 5: XAI ANALYSIS (SHAP)
    # =========================================================
    if SHAP_AVAILABLE:
        print_header("STEP 5: EXPLAINABLE AI ANALYSIS (SHAP)")
        
        xai = ExplainableAI(best_model, feature_names, model_name=best_name)
        xai.create_explainer(X_train)
        xai.compute_shap_values(X_test)
        
        importance = xai.get_feature_importance(top_n=20)
        print("\nTop 20 Most Important Features:")
        print(importance.to_string(index=False))
        
        # Save feature importance
        importance.to_csv(os.path.join(RESULTS_DIR, 'feature_importance.csv'), index=False)
        
        # Try to generate plots
        try:
            xai.plot_bar(save_path=os.path.join(RESULTS_DIR, 'shap_feature_importance.png'))
        except Exception as e:
            print(f"Note: Could not generate SHAP plot: {e}")
    else:
        print_header("STEP 5: XAI ANALYSIS SKIPPED")
        print("SHAP not installed. Run: pip install shap")
    
    # =========================================================
    # STEP 6: SAVE MODELS AND GENERATE REPORT
    # =========================================================
    print_header("STEP 6: SAVING MODELS AND GENERATING REPORT")
    
    models.save_models(vectorizer, feature_names)
    generate_report(results, best_name, best_accuracy, preprocessor)
    
    # =========================================================
    # FINAL SUMMARY
    # =========================================================
    print_header("VALIDATION COMPLETE")
    
    print(f"""
Research Validation Summary:
============================
- Dataset: 60 samples (30 vulnerable, 30 secure)
- Vulnerability Types: 10 (OWASP API Security Top 10)
- Best Model: {best_name}
- Best Accuracy: {best_accuracy*100:.1f}%
- Thesis Expected: Extra Trees at 83.3%

Files saved in: {RESULTS_DIR}
Models saved in: models/

Next Steps for SecureCode-FL:
1. Implement Federated Learning framework
2. Create VS Code extension
3. Add real-time vulnerability detection
""")
    
    return results, models


if __name__ == "__main__":
    results, models = main()
