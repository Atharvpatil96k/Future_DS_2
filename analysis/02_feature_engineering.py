"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         RETENTIONIQ                                         ║
║              Customer Churn Intelligence Platform                           ║
║                                                                              ║
║  Phase 2: Feature Engineering                                               ║
║  Author: Atharv Patil | Future Interns DS Task 2 (2026)                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

This script creates business-ready features that transform raw attributes into 
actionable intelligence for churn prediction and customer segmentation.

Engineered Features:
  1. TenureBucket       — Lifecycle stage segmentation
  2. SpendingCategory   — Revenue-tier classification
  3. AvgMonthlySpend    — Normalized spending metric
  4. ServiceCount       — Product engagement proxy
  5. EngagementScore    — Composite stickiness measure (0-100)
  6. CustomerHealthIndex— Overall health composite (0-100)
  7. RetentionScore     — Likelihood to stay (0-100)
  8. RiskCategory       — High/Medium/Low triage
  9. RevenueSegment     — Revenue tier label
  10. LoyaltySegment    — Lifecycle marketing label
  11. CLV_Estimate      — Customer Lifetime Value estimate
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_FILE = os.path.join(BASE_DIR, "data", "cleaned", "telco_churn_cleaned.csv")
FEATURED_FILE = os.path.join(BASE_DIR, "data", "processed", "telco_churn_featured.csv")
FEATURES_META = os.path.join(BASE_DIR, "data", "processed", "feature_metadata.json")

print("=" * 70)
print("  RETENTIONIQ — Phase 2: Feature Engineering")
print("=" * 70)
print()

# ─────────────────────────────────────────────────────────────────────────────
# LOAD CLEANED DATA
# ─────────────────────────────────────────────────────────────────────────────

df = pd.read_csv(CLEAN_FILE)
print(f"  ✓ Loaded cleaned dataset: {df.shape[0]} rows × {df.shape[1]} columns")
print()

feature_log = []

def log_feature(name, description, formula, rationale):
    feature_log.append({
        "name": name,
        "description": description,
        "formula": formula,
        "rationale": rationale
    })
    print(f"  ✓ Created: {name}")
    print(f"    └─ {description}")
    print()

# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 1: TENURE BUCKETS
# ─────────────────────────────────────────────────────────────────────────────

print("━━━ Creating Business Features ━━━")
print()

def tenure_bucket(t):
    if t <= 6: return "0-6 months"
    elif t <= 12: return "7-12 months"
    elif t <= 24: return "13-24 months"
    elif t <= 48: return "25-48 months"
    else: return "49-72 months"

df["TenureBucket"] = df["tenure"].apply(tenure_bucket)

log_feature(
    "TenureBucket",
    "Customer lifecycle stage segmentation",
    "0-6 | 7-12 | 13-24 | 25-48 | 49-72 months",
    "Enables lifecycle-based retention strategies. New customers (0-6mo) have different needs than mature ones (49-72mo). Critical for cohort analysis."
)

# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 2: SPENDING CATEGORY
# ─────────────────────────────────────────────────────────────────────────────

q25 = df["MonthlyCharges"].quantile(0.25)
q50 = df["MonthlyCharges"].quantile(0.50)
q75 = df["MonthlyCharges"].quantile(0.75)

def spending_cat(charge):
    if charge <= q25: return "Low"
    elif charge <= q50: return "Medium"
    elif charge <= q75: return "High"
    else: return "Premium"

df["SpendingCategory"] = df["MonthlyCharges"].apply(spending_cat)

log_feature(
    "SpendingCategory",
    "Revenue-tier classification based on monthly spend quartiles",
    f"Low (≤${q25:.0f}) | Medium (≤${q50:.0f}) | High (≤${q75:.0f}) | Premium (>${q75:.0f})",
    "Identifies high-value customers for prioritized retention. Revenue at risk varies dramatically across tiers."
)

# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 3: AVERAGE MONTHLY SPEND
# ─────────────────────────────────────────────────────────────────────────────

df["AvgMonthlySpend"] = np.round(df["TotalCharges"] / np.maximum(df["tenure"], 1), 2)

log_feature(
    "AvgMonthlySpend",
    "Normalized spending metric across customer lifetime",
    "TotalCharges / max(tenure, 1)",
    "Unlike MonthlyCharges (current rate), this reflects actual average spend. Useful for detecting customers who may have upgraded/downgraded over time."
)

# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 4: SERVICE COUNT
# ─────────────────────────────────────────────────────────────────────────────

service_columns = [
    "PhoneService", "MultipleLines", "InternetService",
    "OnlineSecurity", "OnlineBackup", "DeviceProtection",
    "TechSupport", "StreamingTV", "StreamingMovies"
]

def count_services(row):
    count = 0
    if row["PhoneService"] == "Yes": count += 1
    if row["MultipleLines"] == "Yes": count += 1
    if row["InternetService"] != "No": count += 1
    for svc in ["OnlineSecurity", "OnlineBackup", "DeviceProtection", 
                "TechSupport", "StreamingTV", "StreamingMovies"]:
        if row[svc] == "Yes": count += 1
    return count

df["ServiceCount"] = df.apply(count_services, axis=1)

log_feature(
    "ServiceCount",
    "Total number of active service subscriptions (0-9)",
    "Sum of active services across phone, internet, and add-ons",
    "Product stickiness proxy — customers using more services have higher switching costs and are less likely to churn."
)

# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 5: ENGAGEMENT SCORE (0-100)
# ─────────────────────────────────────────────────────────────────────────────

def engagement_score(row):
    score = 0.0
    
    # Services component (max 40 points)
    score += (row["ServiceCount"] / 9) * 40
    
    # Tenure component (max 25 points) — normalized to 72 months
    score += min(row["tenure"] / 72, 1.0) * 25
    
    # Contract commitment (max 20 points)
    contract_scores = {"Month-to-month": 5, "One year": 15, "Two year": 20}
    score += contract_scores.get(row["Contract"], 0)
    
    # Paperless billing (5 points) — indicates digital engagement
    if row["PaperlessBilling"] == "Yes":
        score += 5
    
    # Auto-payment (10 points) — indicates trust and stickiness
    if "automatic" in str(row["PaymentMethod"]).lower():
        score += 10
    
    return round(min(score, 100), 1)

df["EngagementScore"] = df.apply(engagement_score, axis=1)

log_feature(
    "EngagementScore",
    "Composite product stickiness measure (0-100)",
    "40% services + 25% tenure + 20% contract + 5% paperless + 10% auto-pay",
    "Combines multiple engagement signals into a single actionable metric. Low scores indicate customers with weak product attachment."
)

# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 6: CUSTOMER HEALTH INDEX (0-100)
# ─────────────────────────────────────────────────────────────────────────────

def health_index(row):
    score = 0.0
    
    # Tenure stability (max 30 points)
    score += min(row["tenure"] / 72, 1.0) * 30
    
    # Contract security (max 25 points)
    contract_health = {"Month-to-month": 5, "One year": 18, "Two year": 25}
    score += contract_health.get(row["Contract"], 0)
    
    # Service depth (max 20 points)
    score += (row["ServiceCount"] / 9) * 20
    
    # Support services (max 15 points) — protective factors
    protective_services = ["OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport"]
    protective_count = sum(1 for svc in protective_services if row[svc] == "Yes")
    score += (protective_count / 4) * 15
    
    # Payment reliability (max 10 points)
    if "automatic" in str(row["PaymentMethod"]).lower():
        score += 10
    elif row["PaymentMethod"] == "Mailed check":
        score += 6
    else:
        score += 3
    
    return round(min(score, 100), 1)

df["CustomerHealthIndex"] = df.apply(health_index, axis=1)

log_feature(
    "CustomerHealthIndex",
    "Overall customer relationship health score (0-100)",
    "30% tenure + 25% contract + 20% services + 15% protective services + 10% payment",
    "Executive-level metric summarizing customer health. Used in dashboards for quick triage and trend tracking."
)

# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 7: RETENTION SCORE (0-100)
# ─────────────────────────────────────────────────────────────────────────────

def retention_score(row):
    score = 50.0  # Base score
    
    # Positive factors (increase retention)
    if row["Contract"] == "Two year": score += 20
    elif row["Contract"] == "One year": score += 10
    
    score += min(row["tenure"] / 72, 1.0) * 15
    score += (row["ServiceCount"] / 9) * 10
    
    if row["OnlineSecurity"] == "Yes": score += 3
    if row["TechSupport"] == "Yes": score += 3
    if "automatic" in str(row["PaymentMethod"]).lower(): score += 4
    
    # Negative factors (decrease retention)
    if row["Contract"] == "Month-to-month": score -= 10
    if row["PaymentMethod"] == "Electronic check": score -= 5
    if row["MonthlyCharges"] > q75: score -= 3
    if row["tenure"] <= 6: score -= 8
    if row["InternetService"] == "Fiber optic" and row["ServiceCount"] < 4:
        score -= 5  # High price but low service adoption
    
    return round(max(min(score, 100), 0), 1)

df["RetentionScore"] = df.apply(retention_score, axis=1)

log_feature(
    "RetentionScore",
    "Predicted likelihood the customer will stay (0-100)",
    "Base 50 ± contract (±20) ± tenure (±15) ± services (±10) ± support (±6) ± payment (±9)",
    "Actionable retention metric. Customers below 40 should be flagged for immediate intervention. Used to prioritize retention spend."
)

# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 8: RISK CATEGORY
# ─────────────────────────────────────────────────────────────────────────────

def risk_category(score):
    if score >= 65: return "Low Risk"
    elif score >= 40: return "Medium Risk"
    else: return "High Risk"

df["RiskCategory"] = df["RetentionScore"].apply(risk_category)

log_feature(
    "RiskCategory",
    "Customer churn risk triage level",
    "High Risk (<40) | Medium Risk (40-64) | Low Risk (≥65)",
    "Enables rapid triage by customer success teams. High-risk customers require immediate outreach."
)

# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 9: REVENUE SEGMENT
# ─────────────────────────────────────────────────────────────────────────────

def revenue_segment(charge):
    if charge <= 30: return "Low Revenue"
    elif charge <= 55: return "Medium Revenue"
    elif charge <= 85: return "High Revenue"
    else: return "Premium Revenue"

df["RevenueSegment"] = df["MonthlyCharges"].apply(revenue_segment)

log_feature(
    "RevenueSegment",
    "Revenue tier classification by monthly spend",
    "Low (≤$30) | Medium ($30-55) | High ($55-85) | Premium (>$85)",
    "Aligns retention investment with revenue impact. Losing a premium customer costs 3-5x more than a low-revenue customer."
)

# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 10: LOYALTY SEGMENT
# ─────────────────────────────────────────────────────────────────────────────

def loyalty_segment(tenure):
    if tenure <= 6: return "New"
    elif tenure <= 18: return "Growing"
    elif tenure <= 48: return "Loyal"
    else: return "Champion"

df["LoyaltySegment"] = df["tenure"].apply(loyalty_segment)

log_feature(
    "LoyaltySegment",
    "Customer lifecycle stage based on tenure",
    "New (≤6mo) | Growing (7-18mo) | Loyal (19-48mo) | Champion (>48mo)",
    "Lifecycle marketing: New customers need onboarding, Growing need engagement, Loyal need appreciation, Champions need advocacy programs."
)

# ─────────────────────────────────────────────────────────────────────────────
# FEATURE 11: CLV ESTIMATE
# ─────────────────────────────────────────────────────────────────────────────

# Estimate expected remaining tenure based on retention score
def estimate_remaining_tenure(row):
    base_remaining = 36  # average expected months
    multiplier = row["RetentionScore"] / 50  # 1.0 at score=50
    return max(round(base_remaining * multiplier), 1)

df["ExpectedRemainingTenure"] = df.apply(estimate_remaining_tenure, axis=1)
df["CLV_Estimate"] = np.round(df["MonthlyCharges"] * (df["tenure"] + df["ExpectedRemainingTenure"]), 2)

log_feature(
    "CLV_Estimate",
    "Customer Lifetime Value estimate (total expected revenue)",
    "MonthlyCharges × (current_tenure + expected_remaining_tenure)",
    "Key business metric for ROI-based retention decisions. Shows how much revenue each customer represents over their lifetime."
)

# ─────────────────────────────────────────────────────────────────────────────
# EXPORT
# ─────────────────────────────────────────────────────────────────────────────

print("━━━ Export ━━━")

# Save featured dataset
df.to_csv(FEATURED_FILE, index=False)
print(f"  ✓ Feature-engineered dataset exported: {FEATURED_FILE}")
print(f"    Shape: {df.shape[0]} rows × {df.shape[1]} columns")
print(f"    New features: {df.shape[1] - 21}")

# Save feature metadata
metadata = {
    "generated_at": datetime.now().isoformat(),
    "total_features": df.shape[1],
    "original_features": 21,
    "engineered_features": df.shape[1] - 21,
    "features": feature_log
}

with open(FEATURES_META, "w") as f:
    json.dump(metadata, f, indent=2)
print(f"  ✓ Feature metadata exported: {FEATURES_META}")

print()
print("═" * 70)
print("  FEATURE ENGINEERING SUMMARY")
print("═" * 70)
print(f"  Original Features:    21")
print(f"  Engineered Features:  {df.shape[1] - 21}")
print(f"  Total Features:       {df.shape[1]}")
print()
for feat in feature_log:
    print(f"  • {feat['name']}: {feat['description']}")
print()
print("═" * 70)
print("  ✓ Phase 2 Complete — Features ready for analysis")
print("═" * 70)
