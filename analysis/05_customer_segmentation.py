"""
RetentionIQ - Script 05: Customer Segmentation
Identifies 8 customer segments with detailed profiles and recommendations.
Exports results to data/processed/segmentation_results.json
"""

import pandas as pd
import numpy as np
import json
import os

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
OUTPUT_PATH = os.path.join(BASE, "data", "processed", "segmentation_results.json")

# --- Load Data ---
df = pd.read_csv(DATA_PATH)
df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce').fillna(0)
df['Churn_Binary'] = (df['Churn'] == 'Yes').astype(int)
total = len(df)

print("=" * 60)
print("  RetentionIQ - Customer Segmentation")
print("=" * 60)
print(f"  Dataset: {total} customers")
print("-" * 60)

# ============================================================
# Define 8 Segments
# ============================================================
segment_definitions = [
    {
        "name": "Loyal Customers",
        "description": "Long-tenure customers with committed contracts",
        "criteria": "tenure > 48 AND Contract != 'Month-to-month'",
        "mask": (df['tenure'] > 48) & (df['Contract'] != 'Month-to-month'),
        "priority": "Maintain",
        "color": "#2ecc71",
        "recommendation": "Reward loyalty with exclusive perks, priority support, and referral bonuses. These are brand ambassadors — leverage them for testimonials and word-of-mouth marketing. Offer upgrade paths to premium services at discounted rates."
    },
    {
        "name": "At-Risk Customers",
        "description": "Customers flagged as high risk by the risk model",
        "criteria": "RiskCategory == 'High Risk'",
        "mask": df['RiskCategory'] == 'High Risk',
        "priority": "Urgent Retention",
        "color": "#e74c3c",
        "recommendation": "Immediate intervention required. Assign dedicated retention agents for personal outreach. Offer contract incentives, service upgrades, or billing credits. Investigate and resolve any service issues proactively."
    },
    {
        "name": "High-Value Customers",
        "description": "High spenders with established tenure",
        "criteria": "SpendingCategory in ['High', 'Premium'] AND tenure > 24",
        "mask": (df['SpendingCategory'].isin(['High', 'Premium'])) & (df['tenure'] > 24),
        "priority": "VIP Treatment",
        "color": "#f39c12",
        "recommendation": "White-glove service with dedicated account managers. Offer exclusive loyalty programs, early access to new features, and premium support. Prevent competitor poaching with value-locked benefits."
    },
    {
        "name": "Low-Value Customers",
        "description": "Low spenders with short tenure",
        "criteria": "SpendingCategory == 'Low' AND tenure <= 12",
        "mask": (df['SpendingCategory'] == 'Low') & (df['tenure'] <= 12),
        "priority": "Nurture/Upsell",
        "color": "#95a5a6",
        "recommendation": "Focus on engagement and upselling. Send personalized offers for service bundles. Educate on value of additional services. Use automated nurture campaigns with progressive discount offers."
    },
    {
        "name": "New Customers",
        "description": "Recently onboarded customers in their first 6 months",
        "criteria": "tenure <= 6",
        "mask": df['tenure'] <= 6,
        "priority": "Onboarding Focus",
        "color": "#3498db",
        "recommendation": "Intensive onboarding program: welcome calls, guided setup, 30/60/90-day check-ins. Provide self-service resources and community forums. Offer a '6-month satisfaction guarantee' to build trust and reduce early churn."
    },
    {
        "name": "Dormant Customers",
        "description": "Low engagement customers with minimal service usage",
        "criteria": "ServiceCount <= 2 AND EngagementScore < 30",
        "mask": (df['ServiceCount'] <= 2) & (df['EngagementScore'] < 30),
        "priority": "Re-Engage",
        "color": "#9b59b6",
        "recommendation": "Launch re-engagement campaigns with compelling offers. Show value of unused services through personalized demos. Consider 'win-back' pricing for service additions. Schedule proactive check-in calls."
    },
    {
        "name": "Long-Term Subscribers",
        "description": "Customers with over 3 years of tenure",
        "criteria": "tenure > 36",
        "mask": df['tenure'] > 36,
        "priority": "Retain & Reward",
        "color": "#1abc9c",
        "recommendation": "Recognize their loyalty with milestone rewards (3-year, 5-year anniversaries). Offer them beta access to new services. Create a loyalty tier system with increasing benefits. Prevent complacency — don't take them for granted."
    },
    {
        "name": "Premium Customers",
        "description": "Multi-service, high-spend power users",
        "criteria": "ServiceCount >= 6 AND MonthlyCharges > 80",
        "mask": (df['ServiceCount'] >= 6) & (df['MonthlyCharges'] > 80),
        "priority": "Maximize Value",
        "color": "#e67e22",
        "recommendation": "Offer premium bundle discounts to lock in their full service suite. Provide concierge-level support. Cross-sell complementary services. Create 'all-in-one' plans with price advantage over à la carte pricing."
    }
]

# ============================================================
# Build Segment Profiles
# ============================================================
segments = []

for seg_def in segment_definitions:
    mask = seg_def['mask']
    seg_df = df[mask]
    n = len(seg_df)
    
    if n == 0:
        print(f"  ⚠ {seg_def['name']}: 0 customers (skipping)")
        continue
    
    churn_count = seg_df['Churn_Binary'].sum()
    churn_rate = seg_df['Churn_Binary'].mean()
    
    # Top contract types
    contract_dist = seg_df['Contract'].value_counts(normalize=True).to_dict()
    
    # Top payment methods
    payment_dist = seg_df['PaymentMethod'].value_counts(normalize=True).head(3).to_dict()
    
    # Internet service dist
    internet_dist = seg_df['InternetService'].value_counts(normalize=True).to_dict()
    
    # Demographics
    senior_pct = (seg_df['SeniorCitizen'] == 'Yes').mean() if 'SeniorCitizen' in seg_df.columns else 0
    partner_pct = (seg_df['Partner'] == 'Yes').mean() if 'Partner' in seg_df.columns else 0
    dependents_pct = (seg_df['Dependents'] == 'Yes').mean() if 'Dependents' in seg_df.columns else 0
    
    segment_profile = {
        "name": seg_def['name'],
        "description": seg_def['description'],
        "criteria": seg_def['criteria'],
        "priority": seg_def['priority'],
        "color": seg_def['color'],
        "size": n,
        "pct_of_total": round(n / total * 100, 2),
        "churn_rate": round(churn_rate * 100, 2),
        "churned_count": churn_count,
        "active_count": n - churn_count,
        "avg_monthly_charges": round(seg_df['MonthlyCharges'].mean(), 2),
        "median_monthly_charges": round(seg_df['MonthlyCharges'].median(), 2),
        "total_monthly_revenue": round(seg_df['MonthlyCharges'].sum(), 2),
        "avg_total_charges": round(seg_df['TotalCharges'].mean(), 2),
        "avg_tenure": round(seg_df['tenure'].mean(), 2),
        "median_tenure": round(seg_df['tenure'].median(), 2),
        "avg_health_score": round(seg_df['CustomerHealthIndex'].mean(), 2),
        "avg_retention_score": round(seg_df['RetentionScore'].mean(), 2),
        "avg_engagement_score": round(seg_df['EngagementScore'].mean(), 2),
        "avg_service_count": round(seg_df['ServiceCount'].mean(), 2),
        "avg_clv": round(seg_df['CLV_Estimate'].mean(), 2),
        "demographics": {
            "senior_citizen_pct": round(senior_pct * 100, 2),
            "partner_pct": round(partner_pct * 100, 2),
            "dependents_pct": round(dependents_pct * 100, 2)
        },
        "contract_distribution": {k: round(v * 100, 2) for k, v in contract_dist.items()},
        "payment_distribution": {k: round(v * 100, 2) for k, v in payment_dist.items()},
        "internet_distribution": {k: round(v * 100, 2) for k, v in internet_dist.items()},
        "recommendation": seg_def['recommendation']
    }
    
    segments.append(segment_profile)
    
    print(f"\n  📊 {seg_def['name']}:")
    print(f"     Size: {n} ({n/total*100:.1f}%) | Churn: {churn_rate*100:.1f}% | Avg Revenue: ${seg_df['MonthlyCharges'].mean():.2f}/mo")
    print(f"     Avg Tenure: {seg_df['tenure'].mean():.0f} mo | Health: {seg_df['CustomerHealthIndex'].mean():.1f} | CLV: ${seg_df['CLV_Estimate'].mean():,.0f}")

# ============================================================
# Overlap Analysis
# ============================================================
print(f"\n  Computing Segment Overlaps...")

overlap_matrix = {}
for i, seg_i in enumerate(segment_definitions):
    row = {}
    for j, seg_j in enumerate(segment_definitions):
        overlap = (seg_i['mask'] & seg_j['mask']).sum()
        row[seg_j['name']] = int(overlap)
    overlap_matrix[seg_i['name']] = row

# ============================================================
# Summary Statistics
# ============================================================
segment_names = [s['name'] for s in segments]
segment_sizes = [s['size'] for s in segments]
segment_churn_rates = [s['churn_rate'] for s in segments]
segment_revenues = [s['avg_monthly_charges'] for s in segments]

# Total unique customers across all segments
all_masks = pd.Series(False, index=df.index)
for seg_def in segment_definitions:
    all_masks = all_masks | seg_def['mask']
covered_customers = all_masks.sum()

summary = {
    "total_segments": len(segments),
    "total_customers": total,
    "customers_covered": int(covered_customers),
    "coverage_pct": round(covered_customers / total * 100, 2),
    "highest_churn_segment": segments[np.argmax(segment_churn_rates)]['name'] if segments else None,
    "lowest_churn_segment": segments[np.argmin(segment_churn_rates)]['name'] if segments else None,
    "largest_segment": segments[np.argmax(segment_sizes)]['name'] if segments else None,
    "highest_revenue_segment": segments[np.argmax(segment_revenues)]['name'] if segments else None,
    "segment_overview": [
        {"name": s['name'], "size": s['size'], "churn_rate": s['churn_rate'], "avg_revenue": s['avg_monthly_charges']}
        for s in segments
    ]
}

# ============================================================
# Export
# ============================================================
output = {
    "segments": segments,
    "overlap_matrix": overlap_matrix,
    "summary": summary
}

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, cls=NumpyEncoder, ensure_ascii=False)

print(f"\n{'=' * 60}")
print(f"  Segmentation Complete! {len(segments)} segments identified.")
print(f"  Coverage: {covered_customers}/{total} customers ({covered_customers/total*100:.1f}%)")
print(f"  Output: {OUTPUT_PATH}")
print(f"{'=' * 60}")
