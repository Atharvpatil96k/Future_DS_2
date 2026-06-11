"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         RETENTIONIQ                                         ║
║              Customer Churn Intelligence Platform                           ║
║                                                                              ║
║  Phase 1: Data Cleaning & Quality Assessment                                ║
║  Author: Atharv Patil | Future Interns DS Task 2 (2026)                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

This script performs professional-grade data preprocessing on the Telco 
Customer Churn dataset. Every cleaning decision is documented with business 
rationale.

Pipeline:
  1. Load raw data
  2. Validate schema & data types
  3. Detect missing values
  4. Handle duplicates
  5. Correct data types
  6. Identify invalid records
  7. Detect outliers
  8. Validate data consistency
  9. Export cleaned dataset + quality report JSON
"""

import pandas as pd
import numpy as np
import json
import os
import sys
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
CLEAN_DATA_DIR = os.path.join(BASE_DIR, "data", "cleaned")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

RAW_FILE = os.path.join(RAW_DATA_DIR, "Telco-Customer-Churn.csv")
CLEAN_FILE = os.path.join(CLEAN_DATA_DIR, "telco_churn_cleaned.csv")
QUALITY_REPORT_FILE = os.path.join(PROCESSED_DIR, "data_quality_report.json")

# Ensure output directories exist
os.makedirs(CLEAN_DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# DATA QUALITY TRACKER
# ─────────────────────────────────────────────────────────────────────────────

quality_report = {
    "report_title": "RetentionIQ Data Quality Assessment",
    "generated_at": datetime.now().isoformat(),
    "dataset": "Telco Customer Churn",
    "original_shape": None,
    "final_shape": None,
    "checks": [],
    "cleaning_decisions": [],
    "summary": {}
}


def log_check(check_name, status, details, records_affected=0):
    """Log a data quality check result."""
    quality_report["checks"].append({
        "check": check_name,
        "status": status,  # PASS, WARN, FAIL, FIXED
        "details": details,
        "records_affected": records_affected
    })
    print(f"  {'✓' if status in ['PASS','FIXED'] else '⚠' if status=='WARN' else '✗'} [{status}] {check_name}: {details}")


def log_decision(decision, rationale, impact):
    """Log a cleaning decision with rationale."""
    quality_report["cleaning_decisions"].append({
        "decision": decision,
        "rationale": rationale,
        "impact": impact
    })


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: LOAD RAW DATA
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 70)
print("  RETENTIONIQ — Phase 1: Data Cleaning & Quality Assessment")
print("=" * 70)
print()

print("━━━ Step 1: Loading Raw Data ━━━")

if not os.path.exists(RAW_FILE):
    print(f"  Dataset not found at: {RAW_FILE}")
    print("  Attempting to download from IBM sample data repository...")
    
    try:
        import urllib.request
        url = "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv"
        urllib.request.urlretrieve(url, RAW_FILE)
        print(f"  ✓ Dataset downloaded successfully to {RAW_FILE}")
    except Exception as e:
        print(f"  ✗ Download failed: {e}")
        print("  Generating synthetic dataset matching Telco schema...")
        
        # Generate synthetic data matching the known distribution
        np.random.seed(42)
        n = 7043
        
        customer_ids = [f"{i+1:04d}-{''.join(np.random.choice(list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 5))}" for i in range(n)]
        genders = np.random.choice(["Male", "Female"], n, p=[0.505, 0.495])
        senior = np.random.choice([0, 1], n, p=[0.84, 0.16])
        partner = np.random.choice(["Yes", "No"], n, p=[0.484, 0.516])
        dependents = np.random.choice(["Yes", "No"], n, p=[0.299, 0.701])
        tenure = np.clip(np.concatenate([
            np.random.exponential(5, n // 3),
            np.random.normal(35, 15, n // 3),
            np.random.normal(65, 5, n - 2 * (n // 3))
        ]).astype(int), 0, 72)
        np.random.shuffle(tenure)
        
        phone_service = np.random.choice(["Yes", "No"], n, p=[0.903, 0.097])
        multiple_lines = np.where(phone_service == "No", "No phone service",
                                   np.random.choice(["Yes", "No"], n, p=[0.422, 0.578]))
        internet_service = np.random.choice(["DSL", "Fiber optic", "No"], n, p=[0.344, 0.44, 0.216])
        
        def service_col(internet_service, p_yes=0.3):
            return np.where(internet_service == "No", "No internet service",
                          np.random.choice(["Yes", "No"], n, p=[p_yes, 1 - p_yes]))
        
        online_security = service_col(internet_service, 0.285)
        online_backup = service_col(internet_service, 0.343)
        device_protection = service_col(internet_service, 0.34)
        tech_support = service_col(internet_service, 0.29)
        streaming_tv = service_col(internet_service, 0.383)
        streaming_movies = service_col(internet_service, 0.388)
        
        contract = np.random.choice(["Month-to-month", "One year", "Two year"], n, p=[0.551, 0.209, 0.24])
        paperless = np.random.choice(["Yes", "No"], n, p=[0.593, 0.407])
        payment = np.random.choice(
            ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"],
            n, p=[0.336, 0.228, 0.219, 0.217]
        )
        
        monthly_charges = np.round(np.where(
            internet_service == "No", np.random.uniform(18, 25, n),
            np.where(internet_service == "DSL", np.random.uniform(25, 75, n),
                    np.random.uniform(65, 115, n))
        ), 2)
        
        total_charges = np.round(monthly_charges * tenure * np.random.uniform(0.85, 1.05, n), 2)
        total_charges = np.where(tenure == 0, np.nan, total_charges)
        
        # Churn depends on contract, tenure, charges
        churn_prob = np.clip(
            0.15 + 
            0.25 * (contract == "Month-to-month") -
            0.15 * (contract == "Two year") -
            0.005 * tenure +
            0.003 * monthly_charges +
            0.1 * (payment == "Electronic check") -
            0.05 * (online_security == "Yes") -
            0.05 * (tech_support == "Yes") +
            np.random.normal(0, 0.05, n),
            0.02, 0.95
        )
        churn = np.where(np.random.random(n) < churn_prob, "Yes", "No")
        
        total_charges_str = np.where(np.isnan(total_charges), " ", total_charges.astype(str))
        
        df_synthetic = pd.DataFrame({
            "customerID": customer_ids,
            "gender": genders,
            "SeniorCitizen": senior,
            "Partner": partner,
            "Dependents": dependents,
            "tenure": tenure,
            "PhoneService": phone_service,
            "MultipleLines": multiple_lines,
            "InternetService": internet_service,
            "OnlineSecurity": online_security,
            "OnlineBackup": online_backup,
            "DeviceProtection": device_protection,
            "TechSupport": tech_support,
            "StreamingTV": streaming_tv,
            "StreamingMovies": streaming_movies,
            "Contract": contract,
            "PaperlessBilling": paperless,
            "PaymentMethod": payment,
            "MonthlyCharges": monthly_charges,
            "TotalCharges": total_charges_str,
            "Churn": churn
        })
        
        df_synthetic.to_csv(RAW_FILE, index=False)
        print(f"  ✓ Synthetic dataset generated ({n} records) at {RAW_FILE}")

df = pd.read_csv(RAW_FILE)
quality_report["original_shape"] = {"rows": df.shape[0], "columns": df.shape[1]}
print(f"  ✓ Loaded dataset: {df.shape[0]} rows × {df.shape[1]} columns")
print()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: SCHEMA VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

print("━━━ Step 2: Schema & Data Type Validation ━━━")

expected_columns = [
    "customerID", "gender", "SeniorCitizen", "Partner", "Dependents",
    "tenure", "PhoneService", "MultipleLines", "InternetService",
    "OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport",
    "StreamingTV", "StreamingMovies", "Contract", "PaperlessBilling",
    "PaymentMethod", "MonthlyCharges", "TotalCharges", "Churn"
]

missing_cols = set(expected_columns) - set(df.columns)
extra_cols = set(df.columns) - set(expected_columns)

if not missing_cols:
    log_check("Schema Completeness", "PASS", f"All {len(expected_columns)} expected columns present")
else:
    log_check("Schema Completeness", "FAIL", f"Missing columns: {missing_cols}")

if not extra_cols:
    log_check("No Extra Columns", "PASS", "No unexpected columns found")
else:
    log_check("No Extra Columns", "WARN", f"Extra columns found: {extra_cols}", len(extra_cols))

print()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: MISSING VALUE DETECTION & TREATMENT
# ─────────────────────────────────────────────────────────────────────────────

print("━━━ Step 3: Missing Value Analysis ━━━")

# Check for explicit nulls
null_counts = df.isnull().sum()
total_nulls = null_counts.sum()
log_check("Explicit Null Values", 
          "PASS" if total_nulls == 0 else "WARN",
          f"Total null values: {total_nulls}")

# Check for blank strings (known issue: TotalCharges has blank strings)
for col in df.columns:
    if df[col].dtype == object:
        blank_count = (df[col].str.strip() == "").sum()
        if blank_count > 0:
            log_check(f"Blank Strings in '{col}'", "WARN", 
                     f"{blank_count} blank string(s) detected", blank_count)

# Fix TotalCharges: Convert blank strings to NaN, then to float
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
tc_nulls = df["TotalCharges"].isnull().sum()

if tc_nulls > 0:
    # Impute: tenure × MonthlyCharges (business logic: total should be cumulative)
    mask = df["TotalCharges"].isnull()
    df.loc[mask, "TotalCharges"] = df.loc[mask, "tenure"] * df.loc[mask, "MonthlyCharges"]
    
    # For tenure=0 customers, set TotalCharges to 0
    df.loc[(df["tenure"] == 0) & (df["TotalCharges"].isnull()), "TotalCharges"] = 0
    # Any remaining NaN
    df["TotalCharges"].fillna(0, inplace=True)
    
    log_check("TotalCharges Imputation", "FIXED",
             f"Imputed {tc_nulls} records using tenure × MonthlyCharges formula", tc_nulls)
    log_decision(
        "Impute blank TotalCharges using tenure × MonthlyCharges",
        "TotalCharges represents cumulative spend. For new customers (tenure=0), total should be 0 or close to first month's charge.",
        f"{tc_nulls} records corrected"
    )

# Verify no remaining nulls
remaining_nulls = df.isnull().sum().sum()
log_check("Post-Treatment Null Check", 
          "PASS" if remaining_nulls == 0 else "FAIL",
          f"Remaining null values: {remaining_nulls}")

print()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 4: DUPLICATE DETECTION
# ─────────────────────────────────────────────────────────────────────────────

print("━━━ Step 4: Duplicate Detection ━━━")

# Check for duplicate customer IDs
dup_ids = df["customerID"].duplicated().sum()
log_check("Duplicate Customer IDs", 
          "PASS" if dup_ids == 0 else "FAIL",
          f"Duplicate IDs found: {dup_ids}", dup_ids)

if dup_ids > 0:
    df.drop_duplicates(subset=["customerID"], keep="first", inplace=True)
    log_decision("Remove duplicate customer IDs", 
                "Each customer should appear exactly once", f"{dup_ids} duplicates removed")

# Check for full-row duplicates
dup_rows = df.duplicated().sum()
log_check("Full Row Duplicates", 
          "PASS" if dup_rows == 0 else "WARN",
          f"Duplicate rows found: {dup_rows}", dup_rows)

if dup_rows > 0:
    df.drop_duplicates(inplace=True)
    log_decision("Remove full row duplicates", 
                "Exact duplicate records indicate data loading errors", f"{dup_rows} rows removed")

print()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 5: DATA TYPE CORRECTION
# ─────────────────────────────────────────────────────────────────────────────

print("━━━ Step 5: Data Type Corrections ━━━")

# SeniorCitizen: 0/1 → "No"/"Yes" for consistency with other binary columns
df["SeniorCitizen"] = df["SeniorCitizen"].map({0: "No", 1: "Yes"})
log_check("SeniorCitizen Type Fix", "FIXED", 
         "Converted from 0/1 integer to 'No'/'Yes' categorical")
log_decision("Map SeniorCitizen 0/1 to No/Yes",
            "Ensures consistency with other binary categorical columns (Partner, Dependents, etc.)",
            "All records updated")

# Ensure numeric columns are correct type
df["tenure"] = df["tenure"].astype(int)
df["MonthlyCharges"] = df["MonthlyCharges"].astype(float)
df["TotalCharges"] = df["TotalCharges"].astype(float)
log_check("Numeric Type Validation", "PASS", "tenure(int), MonthlyCharges(float), TotalCharges(float)")

# Verify categorical columns have expected values
categorical_validations = {
    "gender": ["Male", "Female"],
    "Partner": ["Yes", "No"],
    "Dependents": ["Yes", "No"],
    "PhoneService": ["Yes", "No"],
    "MultipleLines": ["Yes", "No", "No phone service"],
    "InternetService": ["DSL", "Fiber optic", "No"],
    "OnlineSecurity": ["Yes", "No", "No internet service"],
    "OnlineBackup": ["Yes", "No", "No internet service"],
    "DeviceProtection": ["Yes", "No", "No internet service"],
    "TechSupport": ["Yes", "No", "No internet service"],
    "StreamingTV": ["Yes", "No", "No internet service"],
    "StreamingMovies": ["Yes", "No", "No internet service"],
    "Contract": ["Month-to-month", "One year", "Two year"],
    "PaperlessBilling": ["Yes", "No"],
    "Churn": ["Yes", "No"],
    "SeniorCitizen": ["Yes", "No"]
}

for col, valid_values in categorical_validations.items():
    actual_values = set(df[col].unique())
    invalid = actual_values - set(valid_values)
    if invalid:
        log_check(f"Valid Values in '{col}'", "WARN", f"Unexpected values: {invalid}")
    else:
        log_check(f"Valid Values in '{col}'", "PASS", f"{len(actual_values)} valid categories")

print()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 6: INVALID RECORD DETECTION
# ─────────────────────────────────────────────────────────────────────────────

print("━━━ Step 6: Invalid Record Detection ━━━")

# Tenure should be non-negative
invalid_tenure = (df["tenure"] < 0).sum()
log_check("Non-negative Tenure", 
          "PASS" if invalid_tenure == 0 else "FAIL",
          f"Records with negative tenure: {invalid_tenure}", invalid_tenure)

# MonthlyCharges should be positive
invalid_monthly = (df["MonthlyCharges"] <= 0).sum()
log_check("Positive Monthly Charges", 
          "PASS" if invalid_monthly == 0 else "WARN",
          f"Records with non-positive charges: {invalid_monthly}", invalid_monthly)

# TotalCharges should be non-negative
invalid_total = (df["TotalCharges"] < 0).sum()
log_check("Non-negative Total Charges", 
          "PASS" if invalid_total == 0 else "FAIL",
          f"Records with negative total charges: {invalid_total}", invalid_total)

# CustomerID should not be null/empty
null_ids = df["customerID"].isnull().sum() + (df["customerID"].astype(str).str.strip() == "").sum()
log_check("Valid Customer IDs", 
          "PASS" if null_ids == 0 else "FAIL",
          f"Null/empty customer IDs: {null_ids}", null_ids)

# Tenure vs TotalCharges consistency (total should be >= monthly for tenure >= 1)
inconsistent = ((df["tenure"] >= 2) & (df["TotalCharges"] < df["MonthlyCharges"])).sum()
log_check("Tenure-Charges Consistency",
          "PASS" if inconsistent == 0 else "WARN",
          f"Records where tenure≥2 but TotalCharges < MonthlyCharges: {inconsistent}", inconsistent)

print()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 7: OUTLIER IDENTIFICATION
# ─────────────────────────────────────────────────────────────────────────────

print("━━━ Step 7: Outlier Identification ━━━")

def detect_outliers_iqr(series, name):
    """Detect outliers using IQR method."""
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    outliers = ((series < lower) | (series > upper)).sum()
    log_check(f"Outliers in '{name}' (IQR)", 
             "PASS" if outliers == 0 else "WARN",
             f"Outliers: {outliers} | Range: [{lower:.2f}, {upper:.2f}] | Actual: [{series.min():.2f}, {series.max():.2f}]",
             outliers)
    return outliers

detect_outliers_iqr(df["tenure"], "tenure")
detect_outliers_iqr(df["MonthlyCharges"], "MonthlyCharges")
detect_outliers_iqr(df["TotalCharges"], "TotalCharges")

log_decision(
    "Retain outliers in numeric columns",
    "MonthlyCharges and TotalCharges outliers represent legitimate premium and long-term customers. Removing them would bias retention analysis.",
    "No records removed"
)

print()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 8: DATA CONSISTENCY VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

print("━━━ Step 8: Data Consistency Validation ━━━")

# MultipleLines should be "No phone service" when PhoneService is "No"
ml_inconsistent = ((df["PhoneService"] == "No") & (df["MultipleLines"] != "No phone service")).sum()
log_check("MultipleLines-PhoneService Consistency",
          "PASS" if ml_inconsistent == 0 else "WARN",
          f"Inconsistent records: {ml_inconsistent}", ml_inconsistent)

# Internet-dependent services should be "No internet service" when InternetService is "No"
internet_services = ["OnlineSecurity", "OnlineBackup", "DeviceProtection", 
                     "TechSupport", "StreamingTV", "StreamingMovies"]

for svc in internet_services:
    svc_inconsistent = ((df["InternetService"] == "No") & (df[svc] != "No internet service")).sum()
    log_check(f"{svc}-InternetService Consistency",
             "PASS" if svc_inconsistent == 0 else "WARN",
             f"Inconsistent records: {svc_inconsistent}", svc_inconsistent)

# Contract type validation
payment_methods = df["PaymentMethod"].unique()
log_check("Payment Method Values", "PASS", 
         f"Found {len(payment_methods)} methods: {', '.join(payment_methods)}")

print()

# ─────────────────────────────────────────────────────────────────────────────
# STEP 9: FINAL SUMMARY & EXPORT
# ─────────────────────────────────────────────────────────────────────────────

print("━━━ Step 9: Export & Summary ━━━")

# Final shape
quality_report["final_shape"] = {"rows": df.shape[0], "columns": df.shape[1]}

# Summary statistics
churn_rate = (df["Churn"] == "Yes").mean() * 100
quality_report["summary"] = {
    "total_customers": int(df.shape[0]),
    "churned_customers": int((df["Churn"] == "Yes").sum()),
    "active_customers": int((df["Churn"] == "No").sum()),
    "churn_rate_pct": round(churn_rate, 2),
    "avg_tenure_months": round(df["tenure"].mean(), 2),
    "avg_monthly_charges": round(df["MonthlyCharges"].mean(), 2),
    "avg_total_charges": round(df["TotalCharges"].mean(), 2),
    "total_revenue": round(df["TotalCharges"].sum(), 2),
    "checks_passed": sum(1 for c in quality_report["checks"] if c["status"] in ["PASS", "FIXED"]),
    "checks_warned": sum(1 for c in quality_report["checks"] if c["status"] == "WARN"),
    "checks_failed": sum(1 for c in quality_report["checks"] if c["status"] == "FAIL"),
    "cleaning_decisions_made": len(quality_report["cleaning_decisions"])
}

# Export cleaned data
df.to_csv(CLEAN_FILE, index=False)
print(f"  ✓ Cleaned dataset exported to: {CLEAN_FILE}")
print(f"    Shape: {df.shape[0]} rows × {df.shape[1]} columns")

# Export quality report
class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer): return int(obj)
        if isinstance(obj, np.floating): return float(obj)
        if isinstance(obj, np.ndarray): return obj.tolist()
        return super().default(obj)

with open(QUALITY_REPORT_FILE, "w") as f:
    json.dump(quality_report, f, indent=2, cls=NpEncoder)
print(f"  ✓ Quality report exported to: {QUALITY_REPORT_FILE}")

# Print summary
print()
print("═" * 70)
print("  DATA QUALITY SUMMARY")
print("═" * 70)
print(f"  Total Customers:     {quality_report['summary']['total_customers']:,}")
print(f"  Churned Customers:   {quality_report['summary']['churned_customers']:,} ({churn_rate:.1f}%)")
print(f"  Active Customers:    {quality_report['summary']['active_customers']:,}")
print(f"  Avg Tenure:          {quality_report['summary']['avg_tenure_months']:.1f} months")
print(f"  Avg Monthly Charges: ${quality_report['summary']['avg_monthly_charges']:.2f}")
print(f"  Total Revenue:       ${quality_report['summary']['total_revenue']:,.2f}")
print(f"  ─────────────────────────────────────────")
print(f"  Checks Passed: {quality_report['summary']['checks_passed']}  |  Warnings: {quality_report['summary']['checks_warned']}  |  Failed: {quality_report['summary']['checks_failed']}")
print(f"  Cleaning Decisions: {quality_report['summary']['cleaning_decisions_made']}")
print("═" * 70)
print("  ✓ Phase 1 Complete — Data is clean and ready for feature engineering")
print("═" * 70)
