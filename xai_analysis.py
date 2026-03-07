"""
Explainable AI (XAI) Module
Implements SHAP analysis for model interpretability.
Based on thesis methodology for feature importance analysis.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import warnings
warnings.filterwarnings('ignore')

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("SHAP not installed. Run: pip install shap")

from config import RESULTS_DIR


class ExplainableAI:
    """
    Implements SHAP-based explainability for vulnerability detection models.
    Replicates the XAI methodology from the thesis.
    """
    
    def __init__(self, model, feature_names, model_name="Model"):
        self.model = model
        self.feature_names = feature_names
        self.model_name = model_name
        self.explainer = None
        self.shap_values = None
        
    def create_explainer(self, X_train):
        """
        Create SHAP explainer based on model type.
        """
        if not SHAP_AVAILABLE:
            print("SHAP not available. Please install with: pip install shap")
            return None
        
        print(f"\nCreating SHAP explainer for {self.model_name}...")
        
        # Use TreeExplainer for tree-based models
        tree_models = ['RandomForest', 'ExtraTrees', 'GradientBoosting', 'XGBoost']
        
        if any(m in str(type(self.model)) for m in tree_models):
            self.explainer = shap.TreeExplainer(self.model)
        else:
            # Use KernelExplainer for other models (slower but universal)
            # Sample background data for efficiency
            if hasattr(X_train, 'toarray'):
                background = shap.sample(X_train.toarray(), min(100, X_train.shape[0]))
            else:
                background = shap.sample(X_train, min(100, X_train.shape[0]))
            
            self.explainer = shap.KernelExplainer(
                self.model.predict_proba if hasattr(self.model, 'predict_proba') else self.model.predict,
                background
            )
        
        print(f"  Explainer created successfully!")
        return self.explainer
    
    def compute_shap_values(self, X_test):
        """
        Compute SHAP values for test data.
        """
        if self.explainer is None:
            print("Explainer not created. Call create_explainer first.")
            return None
        
        print(f"Computing SHAP values for {X_test.shape[0]} samples...")
        
        # Convert sparse matrix if needed
        if hasattr(X_test, 'toarray'):
            X_dense = X_test.toarray()
        else:
            X_dense = X_test
        
        self.shap_values = self.explainer.shap_values(X_dense)
        
        # Handle multi-output (binary classification)
        if isinstance(self.shap_values, list):
            # Use SHAP values for class 1 (vulnerable)
            self.shap_values = self.shap_values[1]
        
        print(f"  SHAP values computed! Shape: {self.shap_values.shape}")
        return self.shap_values
    
    def get_feature_importance(self, top_n=20):
        """
        Get top N most important features based on mean absolute SHAP values.
        """
        if self.shap_values is None:
            print("SHAP values not computed. Call compute_shap_values first.")
            return None
        
        # Calculate mean absolute SHAP values
        mean_shap = np.abs(self.shap_values).mean(axis=0)
        
        # Create DataFrame
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': mean_shap
        })
        
        importance_df = importance_df.sort_values('importance', ascending=False)
        
        return importance_df.head(top_n)
    
    def plot_summary(self, X_test, save_path=None):
        """
        Create SHAP summary plot.
        """
        if self.shap_values is None:
            print("SHAP values not computed.")
            return
        
        # Convert sparse matrix if needed
        if hasattr(X_test, 'toarray'):
            X_dense = X_test.toarray()
        else:
            X_dense = X_test
        
        plt.figure(figsize=(12, 8))
        shap.summary_plot(
            self.shap_values, 
            X_dense,
            feature_names=self.feature_names,
            show=False,
            max_display=20
        )
        plt.title(f"SHAP Summary Plot - {self.model_name}")
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Saved: {save_path}")
        
        plt.show()
    
    def plot_bar(self, save_path=None):
        """
        Create SHAP bar plot showing feature importance.
        """
        if self.shap_values is None:
            print("SHAP values not computed.")
            return
        
        plt.figure(figsize=(12, 8))
        shap.summary_plot(
            self.shap_values,
            feature_names=self.feature_names,
            plot_type="bar",
            show=False,
            max_display=20
        )
        plt.title(f"Feature Importance (SHAP) - {self.model_name}")
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Saved: {save_path}")
        
        plt.show()
    
    def explain_single_prediction(self, X_single, sample_idx=0):
        """
        Explain a single prediction using SHAP.
        """
        if self.explainer is None:
            print("Explainer not created.")
            return
        
        # Convert sparse matrix if needed
        if hasattr(X_single, 'toarray'):
            X_dense = X_single.toarray()
        else:
            X_dense = X_single
        
        # Get single sample
        if len(X_dense.shape) == 1:
            sample = X_dense.reshape(1, -1)
        else:
            sample = X_dense[sample_idx:sample_idx+1]
        
        # Compute SHAP values for single sample
        shap_values_single = self.explainer.shap_values(sample)
        
        if isinstance(shap_values_single, list):
            shap_values_single = shap_values_single[1]
        
        # Create force plot
        plt.figure(figsize=(14, 3))
        shap.force_plot(
            self.explainer.expected_value[1] if isinstance(self.explainer.expected_value, np.ndarray) 
            else self.explainer.expected_value,
            shap_values_single[0],
            sample[0],
            feature_names=self.feature_names,
            matplotlib=True,
            show=False
        )
        plt.title(f"SHAP Force Plot - Sample {sample_idx}")
        plt.tight_layout()
        plt.show()
    
    def generate_xai_report(self, X_train, X_test):
        """
        Generate complete XAI analysis report.
        """
        print("\n" + "=" * 60)
        print(f"EXPLAINABLE AI ANALYSIS - {self.model_name}")
        print("=" * 60)
        
        # Create explainer
        self.create_explainer(X_train)
        
        # Compute SHAP values
        self.compute_shap_values(X_test)
        
        # Get feature importance
        print("\n" + "-" * 40)
        print("TOP 20 MOST IMPORTANT FEATURES")
        print("-" * 40)
        importance = self.get_feature_importance(top_n=20)
        print(importance.to_string(index=False))
        
        # Save results
        os.makedirs(RESULTS_DIR, exist_ok=True)
        importance.to_csv(
            os.path.join(RESULTS_DIR, f'feature_importance_{self.model_name.lower().replace(" ", "_")}.csv'),
            index=False
        )
        
        # Generate plots
        try:
            self.plot_bar(save_path=os.path.join(RESULTS_DIR, f'shap_bar_{self.model_name.lower().replace(" ", "_")}.png'))
        except Exception as e:
            print(f"Could not generate bar plot: {e}")
        
        try:
            self.plot_summary(X_test, save_path=os.path.join(RESULTS_DIR, f'shap_summary_{self.model_name.lower().replace(" ", "_")}.png'))
        except Exception as e:
            print(f"Could not generate summary plot: {e}")
        
        return importance


def analyze_all_models(models_dict, X_train, X_test, feature_names):
    """
    Run XAI analysis on all trained models.
    """
    results = {}
    
    for name, model in models_dict.items():
        try:
            xai = ExplainableAI(model, feature_names, model_name=name)
            importance = xai.generate_xai_report(X_train, X_test)
            results[name] = importance
        except Exception as e:
            print(f"Error analyzing {name}: {e}")
            continue
    
    return results


def main():
    """Test XAI module with Extra Trees (best model from thesis)"""
    from data_preprocessing import DataPreprocessor
    from model_training import VulnerabilityDetectionModels
    
    # Prepare data
    print("Preparing data...")
    preprocessor = DataPreprocessor()
    X_train, X_test, y_train, y_test, vectorizer, feature_names = preprocessor.prepare_data()
    
    # Train models
    print("\nTraining models...")
    models = VulnerabilityDetectionModels()
    models.train_and_evaluate_all(X_train, X_test, y_train, y_test)
    
    # Get best model (Extra Trees expected)
    best_name, best_accuracy, best_model = models.get_best_model()
    print(f"\nBest Model: {best_name} ({best_accuracy*100:.1f}% accuracy)")
    
    # XAI Analysis on best model
    xai = ExplainableAI(best_model, feature_names, model_name=best_name)
    importance = xai.generate_xai_report(X_train, X_test)
    
    print("\n" + "=" * 60)
    print("XAI ANALYSIS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
