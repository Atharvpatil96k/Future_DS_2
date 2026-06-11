"""
RetentionIQ - Script 04: Advanced Analytics
Calculates key metrics, survival analysis, and distributions.
Exports results to data/processed/advanced_analytics.json
"""

import pandas as pd
import numpy as np
import json
import os
import warnings
warnings.filterwarnings('ignore')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

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
        return super().default(obj)

# --- Paths ---
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE, "data", "processed", "telco_churn_featured.csv")
OUTPUT_PATH = os.path.join(BASE, "data", "processed", "advanced_analytics.json")

# --- Load Data ---
df = pd.read_csv(DATA_PATH)
df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce').fillna(0)
df['Churn_Binary'] = (df['Churn'] == 'Yes').astype(int)
total = len(df)
churned = df['Churn_Binary'].sum()
active = total - churned

print("=" * 60)
print("  RetentionIQ - Advanced Analytics")
print("=" * 60)

# ============================================================
# KPI Metrics
# ============================================================
churn_rate = churned / total
retention_rate = 1 - churn_rate
# Approximate monthly churn rate assuming avg observation of ~32 months
avg_observation_months = df['tenure'].mean()
monthly_churn_rate = 1 - (1 - churn_rate) ** (1 / avg_observation_months) if avg_observation_months > 0 else 0

# CLV metrics
avg_monthly_charges = df['MonthlyCharges'].mean()
avg_tenure = df['tenure'].mean()
arpu = df['MonthlyCharges'].mean()

# CLV = ARPU × Average Lifetime (months) × Gross Margin (assume 70%)
gross_margin = 0.70
avg_lifetime_months = df[df['Churn'] == 'No']['tenure'].mean()  # Active customer avg tenure
clv_simple = arpu * avg_lifetime_months * gross_margin
clv_churned = df[df['Churn'] == 'Yes']['MonthlyCharges'].mean() * df[df['Churn'] == 'Yes']['tenure'].mean() * gross_margin
clv_active = df[df['Churn'] == 'No']['MonthlyCharges'].mean() * df[df['Churn'] == 'No']['tenure'].mean() * gross_margin

# Revenue at Risk
high_risk = df[df['RiskCategory'] == 'High Risk'] if 'RiskCategory' in df.columns else df[df['Churn_Binary'] == 1]
revenue_at_risk_monthly = high_risk['MonthlyCharges'].sum()
revenue_at_risk_annual = revenue_at_risk_monthly * 12

# Total revenue
total_revenue = df['TotalCharges'].sum()
churned_revenue = df[df['Churn'] == 'Yes']['TotalCharges'].sum()
active_revenue = df[df['Churn'] == 'No']['TotalCharges'].sum()

# Customer counts by risk
risk_dist = {}
if 'RiskCategory' in df.columns:
    risk_dist = df['RiskCategory'].value_counts().to_dict()

kpi_metrics = {
    "churn_rate": {
        "value": round(churn_rate * 100, 2),
        "label": "Overall Churn Rate",
        "unit": "%",
        "formula": "Churned Customers / Total Customers × 100",
        "interpretation": f"{churned} out of {total} customers have churned"
    },
    "retention_rate": {
        "value": round(retention_rate * 100, 2),
        "label": "Retention Rate",
        "unit": "%",
        "formula": "1 - Churn Rate",
        "interpretation": f"{active} customers retained out of {total}"
    },
    "monthly_churn_rate": {
        "value": round(monthly_churn_rate * 100, 4),
        "label": "Monthly Churn Rate",
        "unit": "%",
        "formula": "1 - (1 - Overall Churn Rate)^(1/Avg Tenure Months)",
        "interpretation": f"Estimated monthly churn rate assuming {avg_observation_months:.0f}-month average observation period"
    },
    "clv": {
        "value": round(clv_simple, 2),
        "label": "Average Customer Lifetime Value",
        "unit": "$",
        "formula": "ARPU × Avg Lifetime Months × Gross Margin (70%)",
        "breakdown": {
            "clv_active": round(clv_active, 2),
            "clv_churned": round(clv_churned, 2),
            "clv_difference": round(clv_active - clv_churned, 2)
        },
        "interpretation": f"Active customers generate ${clv_active:,.0f} vs ${clv_churned:,.0f} for churned — a ${clv_active - clv_churned:,.0f} gap"
    },
    "arpu": {
        "value": round(arpu, 2),
        "label": "Average Revenue Per User (Monthly)",
        "unit": "$",
        "formula": "Sum of Monthly Charges / Total Customers",
        "breakdown": {
            "arpu_active": round(df[df['Churn'] == 'No']['MonthlyCharges'].mean(), 2),
            "arpu_churned": round(df[df['Churn'] == 'Yes']['MonthlyCharges'].mean(), 2)
        }
    },
    "revenue_at_risk": {
        "monthly": round(revenue_at_risk_monthly, 2),
        "annual": round(revenue_at_risk_annual, 2),
        "label": "Revenue at Risk (High-Risk Customers)",
        "unit": "$",
        "formula": "Sum of Monthly Charges for High-Risk Customers",
        "customer_count": len(high_risk),
        "interpretation": f"{len(high_risk)} high-risk customers generating ${revenue_at_risk_monthly:,.0f}/month (${revenue_at_risk_annual:,.0f}/year)"
    },
    "total_revenue": {
        "total": round(total_revenue, 2),
        "churned_share": round(churned_revenue, 2),
        "active_share": round(active_revenue, 2),
        "churned_pct": round(churned_revenue / total_revenue * 100, 2) if total_revenue > 0 else 0
    }
}

print(f"\n  KPI Metrics:")
print(f"    Churn Rate:         {kpi_metrics['churn_rate']['value']}%")
print(f"    Retention Rate:     {kpi_metrics['retention_rate']['value']}%")
print(f"    Monthly Churn Rate: {kpi_metrics['monthly_churn_rate']['value']}%")
print(f"    CLV (Active):       ${clv_active:,.0f}")
print(f"    CLV (Churned):      ${clv_churned:,.0f}")
print(f"    ARPU:               ${arpu:.2f}/month")
print(f"    Revenue at Risk:    ${revenue_at_risk_monthly:,.0f}/month")

# ============================================================
# Survival Analysis
# ============================================================
print(f"\n  Running Survival Analysis...")

try:
    from lifelines import KaplanMeierFitter

    kmf = KaplanMeierFitter()
    T = df['tenure'].values
    E = df['Churn_Binary'].values

    kmf.fit(T, event_observed=E, label='Overall')

    timeline = kmf.survival_function_.index.tolist()
    survival_fn = kmf.survival_function_['Overall'].tolist()

    # Median survival time
    median_survival = kmf.median_survival_time_
    # Confidence intervals
    ci = kmf.confidence_interval_survival_function_
    ci_lower = ci.iloc[:, 0].tolist()
    ci_upper = ci.iloc[:, 1].tolist()

    # Survival by contract type
    survival_by_contract = {}
    for contract in df['Contract'].unique():
        mask = df['Contract'] == contract
        kmf_c = KaplanMeierFitter()
        kmf_c.fit(df.loc[mask, 'tenure'], event_observed=df.loc[mask, 'Churn_Binary'], label=contract)
        survival_by_contract[contract] = {
            "timeline": kmf_c.survival_function_.index.tolist(),
            "survival_function": kmf_c.survival_function_[contract].tolist(),
            "median_survival": float(kmf_c.median_survival_time_) if not np.isinf(kmf_c.median_survival_time_) else None
        }

    # Survival by internet service
    survival_by_internet = {}
    for svc in df['InternetService'].unique():
        mask = df['InternetService'] == svc
        kmf_s = KaplanMeierFitter()
        kmf_s.fit(df.loc[mask, 'tenure'], event_observed=df.loc[mask, 'Churn_Binary'], label=svc)
        survival_by_internet[svc] = {
            "timeline": kmf_s.survival_function_.index.tolist(),
            "survival_function": kmf_s.survival_function_[svc].tolist(),
            "median_survival": float(kmf_s.median_survival_time_) if not np.isinf(kmf_s.median_survival_time_) else None
        }

    survival_data = {
        "overall": {
            "timeline": timeline,
            "survival_function": survival_fn,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "median_survival_months": float(median_survival) if not np.isinf(median_survival) else None
        },
        "by_contract": survival_by_contract,
        "by_internet_service": survival_by_internet,
        "interpretation": f"Median survival time is {'%.0f months' % median_survival if not np.isinf(median_survival) else 'not reached (>50% survive full observation)'}. This means half of all customers are expected to churn by this tenure mark."
    }

    print(f"    Median Survival: {'%.0f months' % median_survival if not np.isinf(median_survival) else 'Not reached'}")
    for c, data in survival_by_contract.items():
        med = data['median_survival']
        print(f"    {c}: Median = {('%.0f months' % med) if med else 'Not reached'}")

except ImportError:
    print("    lifelines not installed. Installing...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'lifelines', '-q'])
    from lifelines import KaplanMeierFitter
    # Re-run the analysis
    kmf = KaplanMeierFitter()
    kmf.fit(df['tenure'].values, event_observed=df['Churn_Binary'].values, label='Overall')
    timeline = kmf.survival_function_.index.tolist()
    survival_fn = kmf.survival_function_['Overall'].tolist()
    median_survival = kmf.median_survival_time_
    survival_data = {
        "overall": {
            "timeline": timeline,
            "survival_function": survival_fn,
            "median_survival_months": float(median_survival) if not np.isinf(median_survival) else None
        },
        "by_contract": {},
        "by_internet_service": {}
    }
    print(f"    Median Survival: {'%.0f months' % median_survival if not np.isinf(median_survival) else 'Not reached'}")

# ============================================================
# Distribution Analysis
# ============================================================
print(f"\n  Computing Distributions...")

def compute_distribution(series, name):
    return {
        "name": name,
        "mean": round(float(series.mean()), 2),
        "median": round(float(series.median()), 2),
        "std": round(float(series.std()), 2),
        "min": round(float(series.min()), 2),
        "max": round(float(series.max()), 2),
        "q25": round(float(series.quantile(0.25)), 2),
        "q75": round(float(series.quantile(0.75)), 2),
        "skewness": round(float(series.skew()), 4),
        "kurtosis": round(float(series.kurtosis()), 4)
    }

# Customer Health Score distribution
health_dist = compute_distribution(df['CustomerHealthIndex'], 'Customer Health Index')
health_by_churn = {
    "churned": compute_distribution(df[df['Churn'] == 'Yes']['CustomerHealthIndex'], 'Health (Churned)'),
    "active": compute_distribution(df[df['Churn'] == 'No']['CustomerHealthIndex'], 'Health (Active)')
}

# Retention Score distribution
retention_dist = compute_distribution(df['RetentionScore'], 'Retention Score')
retention_by_churn = {
    "churned": compute_distribution(df[df['Churn'] == 'Yes']['RetentionScore'], 'Retention (Churned)'),
    "active": compute_distribution(df[df['Churn'] == 'No']['RetentionScore'], 'Retention (Active)')
}

# Monthly Charges distribution
monthly_dist = compute_distribution(df['MonthlyCharges'], 'Monthly Charges')
monthly_by_churn = {
    "churned": compute_distribution(df[df['Churn'] == 'Yes']['MonthlyCharges'], 'Monthly (Churned)'),
    "active": compute_distribution(df[df['Churn'] == 'No']['MonthlyCharges'], 'Monthly (Active)')
}

# Tenure distribution
tenure_dist = compute_distribution(df['tenure'], 'Tenure')
tenure_by_churn = {
    "churned": compute_distribution(df[df['Churn'] == 'Yes']['tenure'], 'Tenure (Churned)'),
    "active": compute_distribution(df[df['Churn'] == 'No']['tenure'], 'Tenure (Active)')
}

# CLV Estimate distribution
clv_dist = compute_distribution(df['CLV_Estimate'], 'CLV Estimate')
clv_by_churn = {
    "churned": compute_distribution(df[df['Churn'] == 'Yes']['CLV_Estimate'], 'CLV (Churned)'),
    "active": compute_distribution(df[df['Churn'] == 'No']['CLV_Estimate'], 'CLV (Active)')
}

# Engagement Score distribution
engagement_dist = compute_distribution(df['EngagementScore'], 'Engagement Score')

# Histograms for distributions
health_hist, health_bins = np.histogram(df['CustomerHealthIndex'].dropna(), bins=20)
retention_hist, retention_bins = np.histogram(df['RetentionScore'].dropna(), bins=20)

distributions = {
    "customer_health_index": {
        "overall": health_dist,
        "by_churn": health_by_churn,
        "histogram": {
            "counts": health_hist.tolist(),
            "bin_edges": health_bins.tolist()
        }
    },
    "retention_score": {
        "overall": retention_dist,
        "by_churn": retention_by_churn,
        "histogram": {
            "counts": retention_hist.tolist(),
            "bin_edges": retention_bins.tolist()
        }
    },
    "monthly_charges": {
        "overall": monthly_dist,
        "by_churn": monthly_by_churn
    },
    "tenure": {
        "overall": tenure_dist,
        "by_churn": tenure_by_churn
    },
    "clv_estimate": {
        "overall": clv_dist,
        "by_churn": clv_by_churn
    },
    "engagement_score": {
        "overall": engagement_dist
    }
}

print(f"    Health Index: Active avg={health_by_churn['active']['mean']}, Churned avg={health_by_churn['churned']['mean']}")
print(f"    Retention Score: Active avg={retention_by_churn['active']['mean']}, Churned avg={retention_by_churn['churned']['mean']}")

# ============================================================
# Formulas Reference
# ============================================================
formulas = [
    {"name": "Churn Rate", "formula": "Churned Customers / Total Customers × 100", "significance": "Core metric for measuring customer attrition over the observation period"},
    {"name": "Retention Rate", "formula": "1 - Churn Rate", "significance": "Inverse of churn, measures customer loyalty"},
    {"name": "Monthly Churn Rate", "formula": "1 - (1 - Overall Churn)^(1/Avg Tenure)", "significance": "Normalizes churn to a monthly rate for trend comparison"},
    {"name": "CLV (Customer Lifetime Value)", "formula": "ARPU × Avg Lifetime (months) × Gross Margin", "significance": "Estimates total revenue a customer generates over their relationship"},
    {"name": "ARPU", "formula": "Total Monthly Revenue / Total Customers", "significance": "Average monthly revenue contribution per customer"},
    {"name": "Revenue at Risk", "formula": "Sum(Monthly Charges) for High-Risk Customers", "significance": "Quantifies potential monthly revenue loss from at-risk segment"},
    {"name": "Customer Health Index", "formula": "Weighted composite of tenure, engagement, contract, and spending", "significance": "Holistic measure of customer relationship health (0-100)"},
    {"name": "Retention Score", "formula": "Weighted composite of loyalty, engagement, and risk factors", "significance": "Probability-like score of customer staying (0-100)"},
    {"name": "Kaplan-Meier Survival", "formula": "S(t) = ∏(1 - d_i/n_i) for all t_i ≤ t", "significance": "Non-parametric estimate of survival probability over time"}
]

# ============================================================
# Assemble Output
# ============================================================
output = {
    "kpi_metrics": kpi_metrics,
    "survival_data": survival_data,
    "distributions": distributions,
    "formulas": formulas,
    "risk_distribution": risk_dist
}

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, cls=NumpyEncoder, ensure_ascii=False)

print(f"\n{'=' * 60}")
print(f"  Advanced Analytics Complete!")
print(f"  Output: {OUTPUT_PATH}")
print(f"{'=' * 60}")
