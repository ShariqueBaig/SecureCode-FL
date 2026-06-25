"""
Hyperparameter Tuning Module
Attempts to replicate thesis results through hyperparameter optimization.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold, GridSearchCV, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
import warnings
warnings.filterwarnings('ignore')

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

from config import RANDOM_STATE


def tune_extra_trees(X, y, cv=5):
    """
    Tune Extra Trees Classifier to match thesis results (83.3%)
    """
    print("\n" + "=" * 60)
    print("TUNING EXTRA TREES CLASSIFIER")
    print("=" * 60)
    
    # Parameter grid
    param_grid = {
        'n_estimators': [50, 100, 200, 300],
        'max_depth': [None, 10, 20, 30],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4],
        'max_features': ['sqrt', 'log2', None],
        'bootstrap': [True, False]
    }
    
    base_model = ExtraTreesClassifier(random_state=RANDOM_STATE, n_jobs=-1)
    
    # Use GridSearchCV
    grid_search = GridSearchCV(
        base_model, 
        param_grid, 
        cv=cv, 
        scoring='accuracy',
        n_jobs=-1,
        verbose=1
    )
    
    print("Running Grid Search...")
    grid_search.fit(X, y)
    
    print(f"\nBest Parameters: {grid_search.best_params_}")
    print(f"Best CV Score: {grid_search.best_score_*100:.1f}%")
    
    return grid_search.best_estimator_, grid_search.best_score_


def tune_all_models(X, y, cv=5):
    """
    Quick tune of all models with smaller grid
    """
    print("\n" + "=" * 60)
    print("QUICK HYPERPARAMETER TUNING")
    print("=" * 60)
    
    results = {}
    
    # Convert sparse to dense
    if hasattr(X, 'toarray'):
        X_dense = X.toarray()
    else:
        X_dense = X
    
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=RANDOM_STATE)
    
    # Extra Trees
    print("\n1. Extra Trees Classifier")
    print("-" * 40)
    et_params = {
        'n_estimators': [100, 200],
        'max_depth': [None, 20],
        'min_samples_split': [2, 5],
    }
    et_grid = GridSearchCV(
        ExtraTreesClassifier(random_state=RANDOM_STATE, n_jobs=-1),
        et_params, cv=skf, scoring='accuracy', n_jobs=-1
    )
    et_grid.fit(X_dense, y)
    results['Extra Trees'] = {
        'best_score': et_grid.best_score_,
        'best_params': et_grid.best_params_,
        'model': et_grid.best_estimator_
    }
    print(f"  Best Score: {et_grid.best_score_*100:.1f}%")
    print(f"  Best Params: {et_grid.best_params_}")
    
    # Random Forest
    print("\n2. Random Forest Classifier")
    print("-" * 40)
    rf_params = {
        'n_estimators': [100, 200],
        'max_depth': [None, 20],
        'min_samples_split': [2, 5],
    }
    rf_grid = GridSearchCV(
        RandomForestClassifier(random_state=RANDOM_STATE, n_jobs=-1),
        rf_params, cv=skf, scoring='accuracy', n_jobs=-1
    )
    rf_grid.fit(X_dense, y)
    results['Random Forest'] = {
        'best_score': rf_grid.best_score_,
        'best_params': rf_grid.best_params_,
        'model': rf_grid.best_estimator_
    }
    print(f"  Best Score: {rf_grid.best_score_*100:.1f}%")
    print(f"  Best Params: {rf_grid.best_params_}")
    
    # Gradient Boosting
    print("\n3. Gradient Boosting Classifier")
    print("-" * 40)
    gb_params = {
        'n_estimators': [100, 200],
        'learning_rate': [0.05, 0.1, 0.2],
        'max_depth': [3, 5, 7],
    }
    gb_grid = GridSearchCV(
        GradientBoostingClassifier(random_state=RANDOM_STATE),
        gb_params, cv=skf, scoring='accuracy', n_jobs=-1
    )
    gb_grid.fit(X_dense, y)
    results['Gradient Boosting'] = {
        'best_score': gb_grid.best_score_,
        'best_params': gb_grid.best_params_,
        'model': gb_grid.best_estimator_
    }
    print(f"  Best Score: {gb_grid.best_score_*100:.1f}%")
    print(f"  Best Params: {gb_grid.best_params_}")
    
    # XGBoost
    if XGBOOST_AVAILABLE:
        print("\n4. XGBoost Classifier")
        print("-" * 40)
        xgb_params = {
            'n_estimators': [100, 200],
            'learning_rate': [0.05, 0.1, 0.2],
            'max_depth': [3, 5, 7],
        }
        xgb_grid = GridSearchCV(
            XGBClassifier(random_state=RANDOM_STATE, use_label_encoder=False, eval_metric='logloss'),
            xgb_params, cv=skf, scoring='accuracy', n_jobs=-1
        )
        xgb_grid.fit(X_dense, y)
        results['XGBoost'] = {
            'best_score': xgb_grid.best_score_,
            'best_params': xgb_grid.best_params_,
            'model': xgb_grid.best_estimator_
        }
        print(f"  Best Score: {xgb_grid.best_score_*100:.1f}%")
        print(f"  Best Params: {xgb_grid.best_params_}")
    
    # Summary
    print("\n" + "=" * 60)
    print("TUNING SUMMARY")
    print("=" * 60)
    for name, res in sorted(results.items(), key=lambda x: x[1]['best_score'], reverse=True):
        print(f"{name}: {res['best_score']*100:.1f}%")
    
    return results


def try_different_tfidf_params(df):
    """
    Try different TF-IDF configurations to see which works best
    """
    print("\n" + "=" * 60)
    print("TESTING DIFFERENT TF-IDF CONFIGURATIONS")
    print("=" * 60)
    
    # Prepare labels
    y = df['Result'].apply(lambda x: 1 if str(x).strip().lower() == 'error' else 0).values
    codes = df['Code'].astype(str).values
    
    configs = [
        {'max_features': 500, 'ngram_range': (1, 1), 'name': 'Unigrams only (500)'},
        {'max_features': 1000, 'ngram_range': (1, 1), 'name': 'Unigrams only (1000)'},
        {'max_features': 500, 'ngram_range': (1, 2), 'name': 'Uni+Bigrams (500)'},
        {'max_features': 1000, 'ngram_range': (1, 2), 'name': 'Uni+Bigrams (1000)'},
        {'max_features': 2000, 'ngram_range': (1, 2), 'name': 'Uni+Bigrams (2000)'},
        {'max_features': 500, 'ngram_range': (1, 3), 'name': 'Uni+Bi+Trigrams (500)'},
    ]
    
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    results = []
    
    for config in configs:
        vectorizer = TfidfVectorizer(
            max_features=config['max_features'],
            ngram_range=config['ngram_range'],
            min_df=1,
            max_df=0.95
        )
        X = vectorizer.fit_transform(codes)
        
        # Test with Extra Trees
        et_model = ExtraTreesClassifier(n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1)
        scores = cross_val_score(et_model, X.toarray(), y, cv=skf, scoring='accuracy')
        
        results.append({
            'config': config['name'],
            'mean_accuracy': scores.mean(),
            'std': scores.std(),
            'scores': scores
        })
        
        print(f"\n{config['name']}:")
        print(f"  Mean Accuracy: {scores.mean()*100:.1f}% (±{scores.std()*100:.1f}%)")
        print(f"  Fold Scores: {[f'{s*100:.1f}%' for s in scores]}")
    
    # Best config
    best = max(results, key=lambda x: x['mean_accuracy'])
    print(f"\n★ Best Config: {best['config']} with {best['mean_accuracy']*100:.1f}%")
    
    return results


def main():
    """Main tuning function"""
    from data_preprocessing import DataPreprocessor
    from scipy.sparse import vstack
    
    # Load data
    preprocessor = DataPreprocessor()
    X_train, X_test, y_train, y_test, vectorizer, feature_names = preprocessor.prepare_data()
    
    # Combine for full CV
    X_full = vstack([X_train, X_test])
    y_full = np.concatenate([y_train, y_test])
    
    # Try different TF-IDF configurations
    try_different_tfidf_params(preprocessor.df)
    
    # Tune models with best config
    print("\n" + "=" * 60)
    print("HYPERPARAMETER TUNING WITH DEFAULT TF-IDF")
    print("=" * 60)
    results = tune_all_models(X_full, y_full, cv=5)
    
    # Get best model
    best_name = max(results.keys(), key=lambda k: results[k]['best_score'])
    best_score = results[best_name]['best_score']
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Best Model: {best_name}")
    print(f"Best Score: {best_score*100:.1f}%")
    print(f"Thesis Target: 83.3% (Extra Trees)")
    print(f"Gap: {(0.833 - best_score)*100:.1f}%")
    
    return results


if __name__ == "__main__":
    results = main()
