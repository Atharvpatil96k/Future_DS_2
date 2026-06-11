"""
RetentionIQ - Script 08: ML Churn Prediction
Trains Logistic Regression + Random Forest classifiers.
Evaluates model performance and extracts feature importances.
Exports results to data/processed/ml_results.json
"""

import pandas as pd
import numpy as np
import json
import os
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix,
    classification_report
)
from sklearn.pipeline import Pipeline

# --- Custom JSON Encoder ---
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return round(float(obj), 4)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return str(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        return super().default(obj)

# --- Paths ---
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE, "data", "processed", "telco_churn_featured.csv")
OUTPUT_PATH = os.path.join(BASE, "data", "processed", "ml_results.json")

print("=" * 60)
print("  RetentionIQ - ML Churn Prediction")
print("=" * 60)

# --- Load Data ---
df = pd.read_csv(DATA_PATH)
df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce').fillna(0)
df['Churn_Binary'] = (df['Churn'] == 'Yes').astype(int)
total = len(df)
print(f"  Dataset: {total} customers")

# ============================================================
# 1. Feature Preparation
# ============================================================
print("\n  [1/5] Preparing Features...")

# Select features for ML
feature_cols = [
    'tenure', 'MonthlyCharges', 'TotalCharges',
    'gender', 'SeniorCitizen', 'Partner', 'Dependents',
    'PhoneService', 'MultipleLines', 'InternetService',
    'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
    'TechSupport', 'StreamingTV', 'StreamingMovies',
    'Contract', 'PaperlessBilling', 'PaymentMethod'
]

# Add engineered features if they exist
for col in ['ServiceCount', 'EngagementScore', 'CustomerHealthIndex', 'RetentionScore']:
    if col in df.columns:
        feature_cols.append(col)

# Keep only available columns
feature_cols = [c for c in feature_cols if c in df.columns]

X_raw = df[feature_cols].copy()

# Encode categorical variables
label_encoders = {}
for col in X_raw.select_dtypes(include=['object']).columns:
    le = LabelEncoder()
    X_raw[col] = le.fit_transform(X_raw[col].astype(str))
    label_encoders[col] = le

X = X_raw.values
y = df['Churn_Binary'].values

print(f"  Features used: {len(feature_cols)}")
print(f"  Target distribution: {y.sum()} churned ({y.mean()*100:.1f}%), {(~y.astype(bool)).sum()} active")

# ============================================================
# 2. Train / Test Split
# ============================================================
print("\n  [2/5] Splitting Data...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"  Train: {len(X_train)} | Test: {len(X_test)}")

# ============================================================
# 3. Logistic Regression
# ============================================================
print("\n  [3/5] Training Logistic Regression...")

lr_pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('model', LogisticRegression(
        max_iter=1000,
        C=1.0,
        random_state=42,
        class_weight='balanced'
    ))
])

lr_pipeline.fit(X_train, y_train)
lr_pred = lr_pipeline.predict(X_test)
lr_prob = lr_pipeline.predict_proba(X_test)[:, 1]

# Cross validation
lr_cv_scores = cross_val_score(lr_pipeline, X, y, cv=5, scoring='roc_auc')

lr_metrics = {
    "model_name": "Logistic Regression",
    "accuracy": round(accuracy_score(y_test, lr_pred) * 100, 2),
    "precision": round(precision_score(y_test, lr_pred) * 100, 2),
    "recall": round(recall_score(y_test, lr_pred) * 100, 2),
    "f1_score": round(f1_score(y_test, lr_pred) * 100, 2),
    "roc_auc": round(roc_auc_score(y_test, lr_prob) * 100, 2),
    "cv_auc_mean": round(lr_cv_scores.mean() * 100, 2),
    "cv_auc_std": round(lr_cv_scores.std() * 100, 2),
    "confusion_matrix": confusion_matrix(y_test, lr_pred).tolist()
}

print(f"  LR  →  Accuracy: {lr_metrics['accuracy']}%  |  AUC: {lr_metrics['roc_auc']}%  |  F1: {lr_metrics['f1_score']}%")

# LR feature coefficients
lr_model = lr_pipeline.named_steps['model']
lr_coef = lr_model.coef_[0]
lr_feature_importance = sorted(
    [{"feature": feature_cols[i], "coefficient": round(float(lr_coef[i]), 4),
      "abs_importance": round(abs(float(lr_coef[i])), 4),
      "direction": "increases churn" if lr_coef[i] > 0 else "decreases churn"}
     for i in range(len(feature_cols))],
    key=lambda x: x["abs_importance"], reverse=True
)

# ============================================================
# 4. Random Forest
# ============================================================
print("\n  [4/5] Training Random Forest...")

rf_model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    class_weight='balanced',
    n_jobs=-1
)

rf_model.fit(X_train, y_train)
rf_pred = rf_model.predict(X_test)
rf_prob = rf_model.predict_proba(X_test)[:, 1]

rf_cv_scores = cross_val_score(rf_model, X, y, cv=5, scoring='roc_auc')

rf_metrics = {
    "model_name": "Random Forest",
    "accuracy": round(accuracy_score(y_test, rf_pred) * 100, 2),
    "precision": round(precision_score(y_test, rf_pred) * 100, 2),
    "recall": round(recall_score(y_test, rf_pred) * 100, 2),
    "f1_score": round(f1_score(y_test, rf_pred) * 100, 2),
    "roc_auc": round(roc_auc_score(y_test, rf_prob) * 100, 2),
    "cv_auc_mean": round(rf_cv_scores.mean() * 100, 2),
    "cv_auc_std": round(rf_cv_scores.std() * 100, 2),
    "confusion_matrix": confusion_matrix(y_test, rf_pred).tolist()
}

print(f"  RF  →  Accuracy: {rf_metrics['accuracy']}%  |  AUC: {rf_metrics['roc_auc']}%  |  F1: {rf_metrics['f1_score']}%")

# RF feature importances
rf_importances = rf_model.feature_importances_
rf_feature_importance = sorted(
    [{"feature": feature_cols[i],
      "importance": round(float(rf_importances[i]), 4),
      "importance_pct": round(float(rf_importances[i]) * 100, 2)}
     for i in range(len(feature_cols))],
    key=lambda x: x["importance"], reverse=True
)

print(f"  Top 5 RF Features:")
for feat in rf_feature_importance[:5]:
    print(f"    {feat['feature']}: {feat['importance_pct']}%")

# ============================================================
# 5. Model Comparison & Selection
# ============================================================
print("\n  [5/5] Comparing Models...")

best_model = "Random Forest" if rf_metrics['roc_auc'] >= lr_metrics['roc_auc'] else "Logistic Regression"
print(f"  Best Model: {best_model} (AUC: {max(rf_metrics['roc_auc'], lr_metrics['roc_auc'])}%)")

# Build ROC curve data points (simplified, 10 threshold points)
thresholds = np.linspace(0, 1, 50)
roc_points = []
for thresh in thresholds:
    preds = (rf_prob >= thresh).astype(int)
    if preds.sum() == 0 or preds.sum() == len(preds):
        continue
    tp = ((preds == 1) & (y_test == 1)).sum()
    fp = ((preds == 1) & (y_test == 0)).sum()
    tn = ((preds == 0) & (y_test == 0)).sum()
    fn = ((preds == 0) & (y_test == 1)).sum()
    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    roc_points.append({"fpr": round(float(fpr), 4), "tpr": round(float(tpr), 4)})

# Churn probability distribution on test set
churned_probs = rf_prob[y_test == 1].tolist()
active_probs = rf_prob[y_test == 0].tolist()

# Probability histogram
prob_bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
prob_labels = ["0-10%", "10-20%", "20-30%", "30-40%", "40-50%", "50-60%", "60-70%", "70-80%", "80-90%", "90-100%"]
churned_hist = np.histogram(churned_probs, bins=prob_bins)[0].tolist()
active_hist = np.histogram(active_probs, bins=prob_bins)[0].tolist()

# ============================================================
# Export
# ============================================================
output = {
    "logistic_regression": {
        "metrics": lr_metrics,
        "feature_importance": lr_feature_importance[:15]
    },
    "random_forest": {
        "metrics": rf_metrics,
        "feature_importance": rf_feature_importance[:15]
    },
    "model_comparison": {
        "best_model": best_model,
        "comparison_table": [
            {"metric": "Accuracy", "logistic_regression": lr_metrics["accuracy"], "random_forest": rf_metrics["accuracy"]},
            {"metric": "Precision", "logistic_regression": lr_metrics["precision"], "random_forest": rf_metrics["precision"]},
            {"metric": "Recall", "logistic_regression": lr_metrics["recall"], "random_forest": rf_metrics["recall"]},
            {"metric": "F1 Score", "logistic_regression": lr_metrics["f1_score"], "random_forest": rf_metrics["f1_score"]},
            {"metric": "ROC-AUC", "logistic_regression": lr_metrics["roc_auc"], "random_forest": rf_metrics["roc_auc"]},
            {"metric": "CV AUC (5-fold)", "logistic_regression": lr_metrics["cv_auc_mean"], "random_forest": rf_metrics["cv_auc_mean"]},
        ]
    },
    "roc_curve": roc_points,
    "probability_distribution": {
        "labels": prob_labels,
        "churned": churned_hist,
        "active": active_hist
    },
    "features_used": feature_cols,
    "dataset_split": {
        "train_size": len(X_train),
        "test_size": len(X_test),
        "churn_rate_train": round(y_train.mean() * 100, 2),
        "churn_rate_test": round(y_test.mean() * 100, 2)
    }
}

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, cls=NumpyEncoder, ensure_ascii=False)

print(f"\n{'=' * 60}")
print(f"  ML Prediction Complete!")
print(f"  Best Model: {best_model}")
print(f"  Best AUC: {max(rf_metrics['roc_auc'], lr_metrics['roc_auc'])}%")
print(f"  Output: {OUTPUT_PATH}")
print(f"{'=' * 60}")
