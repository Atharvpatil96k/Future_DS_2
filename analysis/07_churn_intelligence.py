"""
RetentionIQ - Script 07: Churn Intelligence
Identifies churn drivers, profiles loyal vs high-churn customers,
calculates revenue impact, and finds behavioral patterns.
Exports results to data/processed/churn_intelligence.json
"""

import pandas as pd
import numpy as np
import json
import os
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

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
OUTPUT_PATH = os.path.join(BASE, "data", "processed", "churn_intelligence.json")

# --- Load Data ---
df = pd.read_csv(DATA_PATH)
df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce').fillna(0)
df['Churn_Binary'] = (df['Churn'] == 'Yes').astype(int)
total = len(df)
overall_churn_rate = df['Churn_Binary'].mean()

print("=" * 60)
print("  RetentionIQ - Churn Intelligence")
print("=" * 60)

# ============================================================
# 1. Point-Biserial Correlation Analysis
# ============================================================
print("\n  [1/5] Computing Correlations...")

numeric_cols = ['tenure', 'MonthlyCharges', 'TotalCharges', 'ServiceCount',
                'EngagementScore', 'CustomerHealthIndex', 'RetentionScore',
                'CLV_Estimate', 'AvgMonthlySpend', 'ExpectedRemainingTenure']

categorical_cols = ['gender', 'SeniorCitizen', 'Partner', 'Dependents', 'PhoneService',
                    'MultipleLines', 'InternetService', 'OnlineSecurity', 'OnlineBackup',
                    'DeviceProtection', 'TechSupport', 'StreamingTV', 'StreamingMovies',
                    'Contract', 'PaperlessBilling', 'PaymentMethod']

# Point-biserial for numeric features
correlations = []
for col in numeric_cols:
    if col in df.columns:
        valid = df[[col, 'Churn_Binary']].dropna()
        if len(valid) > 2:
            corr, pval = stats.pointbiserialr(valid['Churn_Binary'], valid[col])
            correlations.append({
                "factor": col,
                "type": "numeric",
                "correlation": round(float(corr), 4),
                "abs_correlation": round(abs(float(corr)), 4),
                "p_value": float(pval),
                "significant": pval < 0.05,
                "direction": "positive" if corr > 0 else "negative",
                "interpretation": f"{'Higher' if corr > 0 else 'Lower'} {col} is associated with higher churn"
            })

# For categorical features: encode and compute correlations + churn rates
categorical_analysis = []
for col in categorical_cols:
    if col not in df.columns:
        continue
    
    categories = df[col].unique()
    cat_churn_rates = []
    
    for cat in categories:
        mask = df[col] == cat
        n = mask.sum()
        if n > 0:
            cr = df.loc[mask, 'Churn_Binary'].mean()
            cat_churn_rates.append({
                "category": str(cat),
                "count": int(n),
                "churn_rate": round(cr * 100, 2),
                "churn_count": int(df.loc[mask, 'Churn_Binary'].sum()),
                "index_vs_avg": round(cr / overall_churn_rate, 2) if overall_churn_rate > 0 else 0
            })
    
    # Sort by churn rate descending
    cat_churn_rates.sort(key=lambda x: x['churn_rate'], reverse=True)
    
    # Compute Cramér's V for association strength
    contingency = pd.crosstab(df[col], df['Churn_Binary'])
    chi2, p_val, dof, expected = stats.chi2_contingency(contingency)
    n_obs = contingency.sum().sum()
    min_dim = min(contingency.shape) - 1
    cramers_v = np.sqrt(chi2 / (n_obs * min_dim)) if min_dim > 0 else 0
    
    max_churn = max(cat_churn_rates, key=lambda x: x['churn_rate'])
    min_churn = min(cat_churn_rates, key=lambda x: x['churn_rate'])
    spread = max_churn['churn_rate'] - min_churn['churn_rate']
    
    categorical_analysis.append({
        "factor": col,
        "type": "categorical",
        "cramers_v": round(float(cramers_v), 4),
        "chi2_p_value": float(p_val),
        "significant": p_val < 0.05,
        "churn_rate_spread": round(spread, 2),
        "highest_churn_category": max_churn['category'],
        "highest_churn_rate": max_churn['churn_rate'],
        "lowest_churn_category": min_churn['category'],
        "lowest_churn_rate": min_churn['churn_rate'],
        "categories": cat_churn_rates
    })
    
    # Add to correlations list using cramers_v as impact score
    correlations.append({
        "factor": col,
        "type": "categorical",
        "correlation": round(float(cramers_v), 4),
        "abs_correlation": round(float(cramers_v), 4),
        "p_value": float(p_val),
        "significant": p_val < 0.05,
        "direction": f"'{max_churn['category']}' has highest churn ({max_churn['churn_rate']}%)",
        "interpretation": f"{col} shows {spread:.1f}pp churn spread across categories"
    })

# Sort by absolute correlation/impact
correlations.sort(key=lambda x: x['abs_correlation'], reverse=True)

# Top 10 churn drivers
top_10_drivers = []
for i, driver in enumerate(correlations[:10], 1):
    # Compute churn rate for this factor
    if driver['type'] == 'numeric':
        # For numeric: use above/below median as proxy
        median_val = df[driver['factor']].median()
        above_churn = df[df[driver['factor']] > median_val]['Churn_Binary'].mean() * 100
        below_churn = df[df[driver['factor']] <= median_val]['Churn_Binary'].mean() * 100
        churn_rate_display = round(max(above_churn, below_churn), 2)
    else:
        # For categorical: use highest churn rate
        cat_info = next((c for c in categorical_analysis if c['factor'] == driver['factor']), None)
        churn_rate_display = cat_info['highest_churn_rate'] if cat_info else overall_churn_rate * 100
    
    top_10_drivers.append({
        "rank": i,
        "factor": driver['factor'],
        "impact_score": driver['abs_correlation'],
        "churn_rate": churn_rate_display,
        "direction": driver['direction'],
        "type": driver['type'],
        "significant": driver['significant']
    })

print(f"    Top 5 Churn Drivers:")
for d in top_10_drivers[:5]:
    print(f"      #{d['rank']}: {d['factor']} (impact={d['impact_score']:.3f}, churn={d['churn_rate']:.1f}%)")

# ============================================================
# 2. Customer Profiles: Most Loyal vs High Churn
# ============================================================
print(f"\n  [2/5] Profiling Customer Segments...")

loyal_mask = (df['Churn'] == 'No') & (df['tenure'] > 48)
high_churn_mask = (df['Churn'] == 'Yes') & (df['tenure'] < 12)

loyal_df = df[loyal_mask]
high_churn_df = df[high_churn_mask]

def build_profile(segment_df, name):
    n = len(segment_df)
    if n == 0:
        return {"name": name, "count": 0}
    
    # Contract distribution
    contract_dist = segment_df['Contract'].value_counts(normalize=True).to_dict()
    payment_dist = segment_df['PaymentMethod'].value_counts(normalize=True).to_dict()
    internet_dist = segment_df['InternetService'].value_counts(normalize=True).to_dict()
    
    # Service adoption
    services = ['OnlineSecurity', 'OnlineBackup', 'DeviceProtection', 'TechSupport',
                'StreamingTV', 'StreamingMovies']
    service_adoption = {}
    for svc in services:
        if svc in segment_df.columns:
            service_adoption[svc] = round((segment_df[svc] == 'Yes').mean() * 100, 2)
    
    return {
        "name": name,
        "count": n,
        "pct_of_total": round(n / total * 100, 2),
        "avg_tenure": round(segment_df['tenure'].mean(), 2),
        "median_tenure": round(segment_df['tenure'].median(), 2),
        "avg_monthly_charges": round(segment_df['MonthlyCharges'].mean(), 2),
        "avg_total_charges": round(segment_df['TotalCharges'].mean(), 2),
        "total_monthly_revenue": round(segment_df['MonthlyCharges'].sum(), 2),
        "avg_service_count": round(segment_df['ServiceCount'].mean(), 2),
        "avg_engagement_score": round(segment_df['EngagementScore'].mean(), 2),
        "avg_health_score": round(segment_df['CustomerHealthIndex'].mean(), 2),
        "avg_retention_score": round(segment_df['RetentionScore'].mean(), 2),
        "avg_clv": round(segment_df['CLV_Estimate'].mean(), 2),
        "senior_citizen_pct": round((segment_df['SeniorCitizen'] == 'Yes').mean() * 100, 2),
        "partner_pct": round((segment_df['Partner'] == 'Yes').mean() * 100, 2),
        "dependents_pct": round((segment_df['Dependents'] == 'Yes').mean() * 100, 2),
        "paperless_billing_pct": round((segment_df['PaperlessBilling'] == 'Yes').mean() * 100, 2),
        "contract_distribution": {k: round(v * 100, 2) for k, v in contract_dist.items()},
        "payment_distribution": {k: round(v * 100, 2) for k, v in payment_dist.items()},
        "internet_distribution": {k: round(v * 100, 2) for k, v in internet_dist.items()},
        "service_adoption": service_adoption
    }

loyal_profile = build_profile(loyal_df, "Most Loyal Customers (No Churn, Tenure > 48)")
high_churn_profile = build_profile(high_churn_df, "High Churn Customers (Churned, Tenure < 12)")

# Compute key differences
profile_comparison = []
if loyal_profile['count'] > 0 and high_churn_profile['count'] > 0:
    compare_metrics = [
        ('avg_tenure', 'Avg Tenure (months)'),
        ('avg_monthly_charges', 'Avg Monthly Charges ($)'),
        ('avg_service_count', 'Avg Service Count'),
        ('avg_engagement_score', 'Avg Engagement Score'),
        ('avg_health_score', 'Avg Health Score'),
        ('avg_clv', 'Avg CLV ($)'),
        ('senior_citizen_pct', 'Senior Citizen %'),
        ('partner_pct', 'Partner %'),
        ('paperless_billing_pct', 'Paperless Billing %')
    ]
    for key, label in compare_metrics:
        loyal_val = loyal_profile.get(key, 0)
        churn_val = high_churn_profile.get(key, 0)
        diff = loyal_val - churn_val
        profile_comparison.append({
            "metric": label,
            "loyal_value": loyal_val,
            "high_churn_value": churn_val,
            "difference": round(diff, 2),
            "pct_difference": round(diff / churn_val * 100, 2) if churn_val != 0 else 0
        })

print(f"    Most Loyal: {loyal_profile['count']} customers, avg tenure={loyal_profile.get('avg_tenure', 0):.0f}mo")
print(f"    High Churn: {high_churn_profile['count']} customers, avg tenure={high_churn_profile.get('avg_tenure', 0):.0f}mo")

# ============================================================
# 3. Revenue Impact by Churn Driver
# ============================================================
print(f"\n  [3/5] Computing Revenue Impact...")

revenue_impact = []

# Contract type revenue impact
for contract in df['Contract'].unique():
    mask = (df['Contract'] == contract) & (df['Churn'] == 'Yes')
    lost_monthly = df.loc[mask, 'MonthlyCharges'].sum()
    lost_total = df.loc[mask, 'TotalCharges'].sum()
    n_churned = mask.sum()
    revenue_impact.append({
        "driver": f"Contract: {contract}",
        "factor": "Contract",
        "category": contract,
        "churned_customers": int(n_churned),
        "monthly_revenue_lost": round(float(lost_monthly), 2),
        "annual_revenue_lost": round(float(lost_monthly * 12), 2),
        "total_revenue_lost": round(float(lost_total), 2)
    })

# Internet service revenue impact
for svc in df['InternetService'].unique():
    mask = (df['InternetService'] == svc) & (df['Churn'] == 'Yes')
    lost_monthly = df.loc[mask, 'MonthlyCharges'].sum()
    lost_total = df.loc[mask, 'TotalCharges'].sum()
    n_churned = mask.sum()
    revenue_impact.append({
        "driver": f"Internet: {svc}",
        "factor": "InternetService",
        "category": svc,
        "churned_customers": int(n_churned),
        "monthly_revenue_lost": round(float(lost_monthly), 2),
        "annual_revenue_lost": round(float(lost_monthly * 12), 2),
        "total_revenue_lost": round(float(lost_total), 2)
    })

# Payment method revenue impact
for pm in df['PaymentMethod'].unique():
    mask = (df['PaymentMethod'] == pm) & (df['Churn'] == 'Yes')
    lost_monthly = df.loc[mask, 'MonthlyCharges'].sum()
    lost_total = df.loc[mask, 'TotalCharges'].sum()
    n_churned = mask.sum()
    revenue_impact.append({
        "driver": f"Payment: {pm}",
        "factor": "PaymentMethod",
        "category": pm,
        "churned_customers": int(n_churned),
        "monthly_revenue_lost": round(float(lost_monthly), 2),
        "annual_revenue_lost": round(float(lost_monthly * 12), 2),
        "total_revenue_lost": round(float(lost_total), 2)
    })

# Sort by monthly revenue lost
revenue_impact.sort(key=lambda x: x['monthly_revenue_lost'], reverse=True)

total_monthly_lost = sum(r['monthly_revenue_lost'] for r in revenue_impact[:len(df['Contract'].unique())])  # just contract
print(f"    Top Revenue Losses (by monthly impact):")
for r in revenue_impact[:5]:
    print(f"      {r['driver']}: ${r['monthly_revenue_lost']:,.0f}/month ({r['churned_customers']} customers)")

# ============================================================
# 4. Behavioral Risk Patterns
# ============================================================
print(f"\n  [4/5] Identifying Risk Patterns...")

risk_patterns = []

# Pattern 1: Month-to-month + Electronic check + No online security
p1_mask = ((df['Contract'] == 'Month-to-month') & 
           (df['PaymentMethod'] == 'Electronic check') & 
           (df['OnlineSecurity'] == 'No'))
p1_df = df[p1_mask]
if len(p1_df) > 0:
    risk_patterns.append({
        "pattern": "Month-to-month + Electronic check + No online security",
        "attributes": ["Contract: Month-to-month", "PaymentMethod: Electronic check", "OnlineSecurity: No"],
        "customer_count": len(p1_df),
        "churn_rate": round(p1_df['Churn_Binary'].mean() * 100, 2),
        "churn_index": round(p1_df['Churn_Binary'].mean() / overall_churn_rate, 2),
        "monthly_revenue_at_risk": round(p1_df[p1_df['Churn'] == 'No']['MonthlyCharges'].sum(), 2),
        "avg_monthly_charges": round(p1_df['MonthlyCharges'].mean(), 2),
        "severity": "Critical"
    })

# Pattern 2: Fiber optic + No tech support + tenure < 12
p2_mask = ((df['InternetService'] == 'Fiber optic') & 
           (df['TechSupport'] == 'No') & 
           (df['tenure'] < 12))
p2_df = df[p2_mask]
if len(p2_df) > 0:
    risk_patterns.append({
        "pattern": "Fiber optic + No tech support + Short tenure (<12 mo)",
        "attributes": ["InternetService: Fiber optic", "TechSupport: No", "Tenure: < 12 months"],
        "customer_count": len(p2_df),
        "churn_rate": round(p2_df['Churn_Binary'].mean() * 100, 2),
        "churn_index": round(p2_df['Churn_Binary'].mean() / overall_churn_rate, 2),
        "monthly_revenue_at_risk": round(p2_df[p2_df['Churn'] == 'No']['MonthlyCharges'].sum(), 2),
        "avg_monthly_charges": round(p2_df['MonthlyCharges'].mean(), 2),
        "severity": "Critical"
    })

# Pattern 3: Senior citizen + Month-to-month + High monthly charges
p3_mask = ((df['SeniorCitizen'] == 'Yes') & 
           (df['Contract'] == 'Month-to-month') & 
           (df['MonthlyCharges'] > 70))
p3_df = df[p3_mask]
if len(p3_df) > 0:
    risk_patterns.append({
        "pattern": "Senior citizen + Month-to-month + High charges (>$70)",
        "attributes": ["SeniorCitizen: Yes", "Contract: Month-to-month", "MonthlyCharges: > $70"],
        "customer_count": len(p3_df),
        "churn_rate": round(p3_df['Churn_Binary'].mean() * 100, 2),
        "churn_index": round(p3_df['Churn_Binary'].mean() / overall_churn_rate, 2),
        "monthly_revenue_at_risk": round(p3_df[p3_df['Churn'] == 'No']['MonthlyCharges'].sum(), 2),
        "avg_monthly_charges": round(p3_df['MonthlyCharges'].mean(), 2),
        "severity": "High"
    })

# Pattern 4: No partner + No dependents + Fiber optic + Month-to-month
p4_mask = ((df['Partner'] == 'No') & 
           (df['Dependents'] == 'No') & 
           (df['InternetService'] == 'Fiber optic') & 
           (df['Contract'] == 'Month-to-month'))
p4_df = df[p4_mask]
if len(p4_df) > 0:
    risk_patterns.append({
        "pattern": "Single (no partner/dependents) + Fiber optic + Month-to-month",
        "attributes": ["Partner: No", "Dependents: No", "InternetService: Fiber optic", "Contract: Month-to-month"],
        "customer_count": len(p4_df),
        "churn_rate": round(p4_df['Churn_Binary'].mean() * 100, 2),
        "churn_index": round(p4_df['Churn_Binary'].mean() / overall_churn_rate, 2),
        "monthly_revenue_at_risk": round(p4_df[p4_df['Churn'] == 'No']['MonthlyCharges'].sum(), 2),
        "avg_monthly_charges": round(p4_df['MonthlyCharges'].mean(), 2),
        "severity": "High"
    })

# Pattern 5: Paperless billing + Electronic check + No online backup
p5_mask = ((df['PaperlessBilling'] == 'Yes') & 
           (df['PaymentMethod'] == 'Electronic check') & 
           (df['OnlineBackup'] == 'No'))
p5_df = df[p5_mask]
if len(p5_df) > 0:
    risk_patterns.append({
        "pattern": "Paperless billing + Electronic check + No online backup",
        "attributes": ["PaperlessBilling: Yes", "PaymentMethod: Electronic check", "OnlineBackup: No"],
        "customer_count": len(p5_df),
        "churn_rate": round(p5_df['Churn_Binary'].mean() * 100, 2),
        "churn_index": round(p5_df['Churn_Binary'].mean() / overall_churn_rate, 2),
        "monthly_revenue_at_risk": round(p5_df[p5_df['Churn'] == 'No']['MonthlyCharges'].sum(), 2),
        "avg_monthly_charges": round(p5_df['MonthlyCharges'].mean(), 2),
        "severity": "High"
    })

# Pattern 6: Long tenure + Two year contract + Multiple services (LOYAL pattern)
p6_mask = ((df['tenure'] > 48) & 
           (df['Contract'] == 'Two year') & 
           (df['ServiceCount'] >= 4))
p6_df = df[p6_mask]
if len(p6_df) > 0:
    risk_patterns.append({
        "pattern": "Long tenure + Two year contract + Multi-service (LOYAL)",
        "attributes": ["Tenure: > 48 months", "Contract: Two year", "ServiceCount: >= 4"],
        "customer_count": len(p6_df),
        "churn_rate": round(p6_df['Churn_Binary'].mean() * 100, 2),
        "churn_index": round(p6_df['Churn_Binary'].mean() / overall_churn_rate, 2),
        "monthly_revenue_at_risk": round(p6_df[p6_df['Churn'] == 'No']['MonthlyCharges'].sum(), 2),
        "avg_monthly_charges": round(p6_df['MonthlyCharges'].mean(), 2),
        "severity": "Low (Loyal)"
    })

# Pattern 7: High monthly charges + Low engagement + Short tenure
p7_mask = ((df['MonthlyCharges'] > 80) & 
           (df['EngagementScore'] < 40) & 
           (df['tenure'] < 12))
p7_df = df[p7_mask]
if len(p7_df) > 0:
    risk_patterns.append({
        "pattern": "High charges + Low engagement + Short tenure",
        "attributes": ["MonthlyCharges: > $80", "EngagementScore: < 40", "Tenure: < 12 months"],
        "customer_count": len(p7_df),
        "churn_rate": round(p7_df['Churn_Binary'].mean() * 100, 2),
        "churn_index": round(p7_df['Churn_Binary'].mean() / overall_churn_rate, 2),
        "monthly_revenue_at_risk": round(p7_df[p7_df['Churn'] == 'No']['MonthlyCharges'].sum(), 2),
        "avg_monthly_charges": round(p7_df['MonthlyCharges'].mean(), 2),
        "severity": "Critical"
    })

# Sort patterns by churn rate
risk_patterns.sort(key=lambda x: x['churn_rate'], reverse=True)

print(f"    Identified {len(risk_patterns)} behavioral patterns:")
for p in risk_patterns[:5]:
    print(f"      {p['pattern']}: {p['churn_rate']}% churn ({p['customer_count']} customers)")

# ============================================================
# 5. Actionable Intelligence Summary
# ============================================================
print(f"\n  [5/5] Generating Intelligence Summary...")

# Service-level churn analysis
services = ['OnlineSecurity', 'OnlineBackup', 'DeviceProtection', 'TechSupport',
            'StreamingTV', 'StreamingMovies']
service_impact = []
for svc in services:
    if svc in df.columns:
        yes_churn = df[df[svc] == 'Yes']['Churn_Binary'].mean() * 100
        no_churn = df[df[svc] == 'No']['Churn_Binary'].mean() * 100
        service_impact.append({
            "service": svc,
            "with_service_churn": round(yes_churn, 2),
            "without_service_churn": round(no_churn, 2),
            "churn_reduction": round(no_churn - yes_churn, 2),
            "protective_effect": round((no_churn - yes_churn) / no_churn * 100, 2) if no_churn > 0 else 0
        })

service_impact.sort(key=lambda x: x['churn_reduction'], reverse=True)

intelligence_summary = {
    "overall_churn_rate": round(overall_churn_rate * 100, 2),
    "total_customers_analyzed": total,
    "top_driver": top_10_drivers[0]['factor'] if top_10_drivers else None,
    "highest_risk_pattern": risk_patterns[0]['pattern'] if risk_patterns else None,
    "highest_risk_churn_rate": risk_patterns[0]['churn_rate'] if risk_patterns else None,
    "most_protective_service": service_impact[0]['service'] if service_impact else None,
    "protective_effect_pct": service_impact[0]['churn_reduction'] if service_impact else None,
    "loyal_vs_churn_tenure_gap": round(loyal_profile.get('avg_tenure', 0) - high_churn_profile.get('avg_tenure', 0), 2),
    "key_actionable_insights": [
        f"Top churn driver: {top_10_drivers[0]['factor']} (impact score: {top_10_drivers[0]['impact_score']:.3f})" if top_10_drivers else "",
        f"Highest risk pattern ({risk_patterns[0]['churn_rate']}% churn): {risk_patterns[0]['pattern']}" if risk_patterns else "",
        f"Most protective service: {service_impact[0]['service']} reduces churn by {service_impact[0]['churn_reduction']:.1f}pp" if service_impact else "",
        f"Loyal customers avg {loyal_profile.get('avg_service_count', 0):.1f} services vs {high_churn_profile.get('avg_service_count', 0):.1f} for high-churn",
        f"Contract commitment reduces churn by {(df[df['Contract']=='Month-to-month']['Churn_Binary'].mean() - df[df['Contract']=='Two year']['Churn_Binary'].mean())*100:.1f}pp"
    ]
}

# ============================================================
# Export
# ============================================================
output = {
    "churn_drivers": top_10_drivers,
    "all_correlations": correlations,
    "categorical_analysis": categorical_analysis,
    "loyal_profile": loyal_profile,
    "high_churn_profile": high_churn_profile,
    "profile_comparison": profile_comparison,
    "revenue_impact": revenue_impact,
    "risk_patterns": risk_patterns,
    "service_impact": service_impact,
    "intelligence_summary": intelligence_summary
}

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, cls=NumpyEncoder, ensure_ascii=False)

print(f"\n{'=' * 60}")
print(f"  Churn Intelligence Complete!")
print(f"  Top 3 Drivers: {', '.join([d['factor'] for d in top_10_drivers[:3]])}")
print(f"  Risk Patterns: {len(risk_patterns)} identified")
print(f"  Most Protective Service: {service_impact[0]['service'] if service_impact else 'N/A'} (-{service_impact[0]['churn_reduction']:.1f}pp)")
print(f"  Output: {OUTPUT_PATH}")
print(f"{'=' * 60}")
