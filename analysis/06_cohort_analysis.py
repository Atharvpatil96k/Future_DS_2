"""
RetentionIQ - Script 06: Cohort Analysis
Simulates signup cohorts using tenure subtracted from reference date (2026-06-01).
Builds retention matrices, calculates cohort retention rates, and groups revenue by cohort.
Exports results to data/processed/cohort_analysis.json
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- Custom JSON Encoder ---
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return round(float(obj), 4)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (pd.Timestamp, datetime)):
            return str(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        return super().default(obj)

# --- Paths ---
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE, "data", "processed", "telco_churn_featured.csv")
OUTPUT_PATH = os.path.join(BASE, "data", "processed", "cohort_analysis.json")

# --- Load Data ---
df = pd.read_csv(DATA_PATH)
df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce').fillna(0)
df['Churn_Binary'] = (df['Churn'] == 'Yes').astype(int)
total = len(df)

print("=" * 60)
print("  RetentionIQ - Cohort Analysis")
print("=" * 60)

# ============================================================
# Simulate Signup Dates
# ============================================================
REFERENCE_DATE = pd.Timestamp('2026-06-01')
print(f"  Reference Date: {REFERENCE_DATE.strftime('%Y-%m-%d')}")

# Signup date = reference date - tenure months
df['SignupDate'] = df['tenure'].apply(lambda t: REFERENCE_DATE - relativedelta(months=int(t)))
df['SignupCohort'] = df['SignupDate'].apply(lambda d: d.strftime('%Y-%m'))

# Sort cohorts chronologically
all_cohorts = sorted(df['SignupCohort'].unique())
print(f"  Total Cohorts: {len(all_cohorts)} (from {all_cohorts[0]} to {all_cohorts[-1]})")

# ============================================================
# Quarterly Cohort Grouping (for manageable matrix size)
# ============================================================
# Group into quarterly cohorts for cleaner analysis
df['SignupQuarter'] = df['SignupDate'].apply(
    lambda d: f"{d.year}-Q{(d.month-1)//3 + 1}"
)
quarterly_cohorts = sorted(df['SignupQuarter'].unique())

print(f"  Quarterly Cohorts: {len(quarterly_cohorts)}")

# ============================================================
# Build Retention Matrix (Quarterly Cohorts × Periods)
# ============================================================
print(f"\n  Building Retention Matrix...")

# For each quarterly cohort, calculate retention at various period marks
period_marks = [0, 3, 6, 12, 18, 24, 36, 48, 60, 72]  # months
period_labels = ['M0', 'M3', 'M6', 'M12', 'M18', 'M24', 'M36', 'M48', 'M60', 'M72']

retention_matrix = []
cohort_summaries = []

for cohort in quarterly_cohorts:
    cohort_df = df[df['SignupQuarter'] == cohort]
    cohort_size = len(cohort_df)
    
    if cohort_size < 5:  # Skip very small cohorts
        continue
    
    max_tenure = cohort_df['tenure'].max()
    churned_count = cohort_df['Churn_Binary'].sum()
    churn_rate = cohort_df['Churn_Binary'].mean()
    
    retention_row = []
    for period in period_marks:
        if period > max_tenure:
            retention_row.append(None)  # Period not yet reached
        else:
            # Customers who survived past this period
            survived = (cohort_df['tenure'] > period).sum() if period > 0 else cohort_size
            # But also those who are still active (not churned) at or beyond this period
            # A customer survives period P if their tenure > P OR (tenure >= P and not churned)
            active_past_period = ((cohort_df['tenure'] > period) | 
                                  ((cohort_df['tenure'] >= period) & (cohort_df['Churn_Binary'] == 0))).sum()
            retention_rate = active_past_period / cohort_size if cohort_size > 0 else 0
            retention_row.append(round(retention_rate * 100, 2))
    
    retention_matrix.append(retention_row)
    
    cohort_summaries.append({
        "cohort": cohort,
        "size": cohort_size,
        "churned": churned_count,
        "active": cohort_size - churned_count,
        "churn_rate": round(churn_rate * 100, 2),
        "retention_rate": round((1 - churn_rate) * 100, 2),
        "avg_tenure": round(cohort_df['tenure'].mean(), 2),
        "max_tenure": int(max_tenure),
        "avg_monthly_charges": round(cohort_df['MonthlyCharges'].mean(), 2),
        "total_revenue": round(cohort_df['TotalCharges'].sum(), 2),
        "avg_health_score": round(cohort_df['CustomerHealthIndex'].mean(), 2)
    })

used_cohorts = [s['cohort'] for s in cohort_summaries]
print(f"  Cohorts with 5+ customers: {len(used_cohorts)}")

# Print a sample of the retention matrix
print(f"\n  Retention Matrix Sample (first 5 cohorts):")
print(f"  {'Cohort':<12} {'M0':>6} {'M3':>6} {'M6':>6} {'M12':>6} {'M24':>6} {'M36':>6}")
for i, (cohort, row) in enumerate(zip(used_cohorts[:5], retention_matrix[:5])):
    vals = [f"{v:.0f}%" if v is not None else "  -" for v in row]
    print(f"  {cohort:<12} {vals[0]:>6} {vals[1]:>6} {vals[2]:>6} {vals[3]:>6} {vals[5]:>6} {vals[6]:>6}")

# ============================================================
# Revenue by Cohort
# ============================================================
print(f"\n  Computing Revenue by Cohort...")

revenue_cohorts = []
for cohort in quarterly_cohorts:
    cohort_df = df[df['SignupQuarter'] == cohort]
    if len(cohort_df) < 5:
        continue
    
    revenue_cohorts.append({
        "cohort": cohort,
        "customer_count": len(cohort_df),
        "total_revenue": round(cohort_df['TotalCharges'].sum(), 2),
        "avg_revenue_per_customer": round(cohort_df['TotalCharges'].mean(), 2),
        "monthly_revenue": round(cohort_df['MonthlyCharges'].sum(), 2),
        "avg_monthly_per_customer": round(cohort_df['MonthlyCharges'].mean(), 2),
        "churned_revenue": round(cohort_df[cohort_df['Churn'] == 'Yes']['TotalCharges'].sum(), 2),
        "active_revenue": round(cohort_df[cohort_df['Churn'] == 'No']['TotalCharges'].sum(), 2),
        "revenue_retention_pct": round(
            cohort_df[cohort_df['Churn'] == 'No']['TotalCharges'].sum() / 
            cohort_df['TotalCharges'].sum() * 100, 2
        ) if cohort_df['TotalCharges'].sum() > 0 else 0
    })

# ============================================================
# Yearly Cohort Summary
# ============================================================
df['SignupYear'] = df['SignupDate'].dt.year
yearly_summary = []
for year in sorted(df['SignupYear'].unique()):
    year_df = df[df['SignupYear'] == year]
    yearly_summary.append({
        "year": int(year),
        "customers": len(year_df),
        "churned": int(year_df['Churn_Binary'].sum()),
        "churn_rate": round(year_df['Churn_Binary'].mean() * 100, 2),
        "avg_monthly_charges": round(year_df['MonthlyCharges'].mean(), 2),
        "total_revenue": round(year_df['TotalCharges'].sum(), 2),
        "avg_tenure": round(year_df['tenure'].mean(), 2)
    })

print(f"\n  Yearly Summary:")
for y in yearly_summary:
    print(f"    {y['year']}: {y['customers']} customers, {y['churn_rate']}% churn, ${y['total_revenue']:,.0f} revenue")

# ============================================================
# Cohort Insights
# ============================================================
best_retention_cohort = min(cohort_summaries, key=lambda x: x['churn_rate'])
worst_retention_cohort = max(cohort_summaries, key=lambda x: x['churn_rate'])
highest_revenue_cohort = max(cohort_summaries, key=lambda x: x['total_revenue'])

insights = {
    "best_retention_cohort": {
        "cohort": best_retention_cohort['cohort'],
        "retention_rate": best_retention_cohort['retention_rate'],
        "size": best_retention_cohort['size']
    },
    "worst_retention_cohort": {
        "cohort": worst_retention_cohort['cohort'],
        "retention_rate": worst_retention_cohort['retention_rate'],
        "size": worst_retention_cohort['size']
    },
    "highest_revenue_cohort": {
        "cohort": highest_revenue_cohort['cohort'],
        "total_revenue": highest_revenue_cohort['total_revenue'],
        "size": highest_revenue_cohort['size']
    },
    "avg_cohort_churn_rate": round(np.mean([s['churn_rate'] for s in cohort_summaries]), 2),
    "total_cohorts_analyzed": len(cohort_summaries)
}

# ============================================================
# Export
# ============================================================
output = {
    "cohort_matrix": {
        "cohorts": used_cohorts,
        "periods": period_labels,
        "period_months": period_marks,
        "retention_rates": retention_matrix
    },
    "cohort_summary": cohort_summaries,
    "revenue_cohorts": revenue_cohorts,
    "yearly_summary": yearly_summary,
    "insights": insights
}

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, cls=NumpyEncoder, ensure_ascii=False)

print(f"\n{'=' * 60}")
print(f"  Cohort Analysis Complete!")
print(f"  {len(cohort_summaries)} cohorts analyzed")
print(f"  Best Retention: {best_retention_cohort['cohort']} ({best_retention_cohort['retention_rate']}%)")
print(f"  Worst Retention: {worst_retention_cohort['cohort']} ({worst_retention_cohort['retention_rate']}%)")
print(f"  Output: {OUTPUT_PATH}")
print(f"{'=' * 60}")
