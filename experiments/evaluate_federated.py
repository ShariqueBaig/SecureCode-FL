import numpy as np
import pandas as pd
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from tensorflow import keras
import sys

# Add parent directory to path to import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_preprocessing import DataPreprocessor

def main():
    print("Loading data and model...")
    # 1. Init preprocessor and get data
    preprocessor = DataPreprocessor()
    X_train, X_test, y_train, y_test, _, _ = preprocessor.prepare_data()
    
    # 2. Get the categories for X_test
    # Since prepare_data uses train_test_split with random_state=42 and stratify=y
    # We can do the exact same split on the dataframe to get the aligned rows
    _, df_test = train_test_split(
        preprocessor.df,
        test_size=0.2,
        random_state=42,
        stratify=preprocessor.df['label'].values
    )
    
    # Verify alignment
    assert len(df_test) == len(y_test), "Mismatch in test set sizes"
    assert np.array_equal(df_test['label'].values, y_test), "Mismatch in test set labels"
    
    # 3. Load model and predict
    print("Loading FL model...")
    model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models', 'federated', 'fl_global_model.keras')
    model = keras.models.load_model(model_path)
    
    print("Predicting...")
    # Handle sparse matrices if returned by vectorizer
    X_test_arr = X_test.toarray() if hasattr(X_test, 'toarray') else X_test
    y_pred_probs = model.predict(X_test_arr)
    y_pred = (y_pred_probs > 0.5).astype(int).flatten()
    
    # 4. Generate report
    print("Generating report...")
    report = []
    report.append("======================================================================")
    report.append(" FEDERATED MODEL EVALUATION - GROUND TRUTH RESULTS")
    report.append("======================================================================\n")
    
    report.append("1. OVERALL CONFUSION MATRIX & METRICS")
    report.append("-" * 40)
    cm = confusion_matrix(y_test, y_pred)
    report.append(f"Confusion Matrix:\n{cm}")
    report.append(f"True Positives (Vulnerable [1]): {cm[1][1]}")
    report.append(f"True Negatives (Secure [0]): {cm[0][0]}")
    report.append(f"False Positives: {cm[0][1]}")
    report.append(f"False Negatives: {cm[1][0]}")
    
    acc = accuracy_score(y_test, y_pred)
    report.append(f"\nOverall Accuracy: {acc*100:.2f}%")
    report.append("\nClassification Report:")
    report.append(classification_report(y_test, y_pred))
    
    report.append("\n2. PER-CATEGORY PERFORMANCE")
    report.append("-" * 40)
    df_test = df_test.copy()
    df_test['y_pred'] = y_pred
    df_test['y_true'] = y_test
    
    # Fix spelling error in category
    df_test['Primary Vulnerability'] = df_test['Primary Vulnerability'].replace(
        'Broken Object Level Authorizatio', 'Broken Object Level Authorization'
    )
    
    # Compute accuracy per category
    categories = df_test['Primary Vulnerability'].unique()
    cat_results = []
    for cat in categories:
        cat_df = df_test[df_test['Primary Vulnerability'] == cat]
        cat_acc = accuracy_score(cat_df['y_true'], cat_df['y_pred'])
        cat_results.append({
            'Category': cat,
            'Samples': len(cat_df),
            'Accuracy': f"{cat_acc*100:.2f}%",
            'Correct': sum(cat_df['y_true'] == cat_df['y_pred']),
            'Total': len(cat_df)
        })
    
    # Sort by samples descending
    cat_results.sort(key=lambda x: x['Samples'], reverse=True)
    
    # Format as table
    report.append(f"{'Category':<50} | {'Samples':<10} | {'Accuracy':<10} | {'Correct/Total'}")
    report.append("-" * 90)
    for res in cat_results:
        report.append(f"{res['Category']:<50} | {res['Samples']:<10} | {res['Accuracy']:<10} | {res['Correct']}/{res['Total']}")
    
    # Save to file
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results', 'federated')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'fl_evaluation_evidence.txt')
    
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"\nEvaluation complete. Results saved to {out_path}")

if __name__ == '__main__':
    main()
