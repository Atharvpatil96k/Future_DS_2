"""
RetentionIQ - Script 03: Exploratory Data Analysis
Performs 10 key analyses on the telco churn dataset.
Each analysis includes: Observation, Business Impact, Recommendation.
Exports results to data/processed/eda_results.json
"""

import pandas as pd
import numpy as np
import json
import os
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
OUTPUT_PATH = os.path.join(BASE, "data", "processed", "eda_results.json")

# --- Load Data ---
df = pd.read_csv(DATA_PATH)
df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce').fillna(0)
df['Churn_Binary'] = (df['Churn'] == 'Yes').astype(int)
total = len(df)
churned = df['Churn_Binary'].sum()
active = total - churned

print("=" * 60)
print("  RetentionIQ - Exploratory Data Analysis")
print("=" * 60)
print(f"  Dataset: {total} customers | {churned} churned ({churned/total*100:.1f}%) | {active} active")
print("=" * 60)

analyses = []

# ============================================================
# 1. Overall Churn Rate
# ============================================================
churn_dist = df['Churn'].value_counts().to_dict()
churn_pct = df['Churn'].value_counts(normalize=True).to_dict()

analyses.append({
    "title": "Overall Churn Rate",
    "category": "Overview",
    "observation": f"Out of {total} customers, {churned} ({churn_pct.get('Yes',0)*100:.1f}%) have churned while {active} ({churn_pct.get('No',0)*100:.1f}%) remain active. This represents a significant churn rate that exceeds the typical telecom industry benchmark of 15-25%.",
    "business_impact": f"At an average monthly charge of ${df['MonthlyCharges'].mean():.2f}, the churned customers represent approximately ${df[df['Churn']=='Yes']['MonthlyCharges'].sum():,.0f} in monthly recurring revenue loss.",
    "recommendation": "Implement a proactive retention program targeting at-risk customers before they churn. Focus resources on the highest-value customers showing early warning signs.",
    "chart_data": {
        "type": "pie",
        "labels": list(churn_dist.keys()),
        "values": list(churn_dist.values()),
        "percentages": {k: round(v * 100, 2) for k, v in churn_pct.items()}
    }
})
print(f"\n[1/10] Overall Churn Rate: {churn_pct.get('Yes',0)*100:.1f}% churned")

# ============================================================
# 2. Churn by Contract Type
# ============================================================
contract_churn = df.groupby('Contract').agg(
    total=('Churn_Binary', 'count'),
    churned=('Churn_Binary', 'sum'),
    churn_rate=('Churn_Binary', 'mean'),
    avg_monthly=('MonthlyCharges', 'mean'),
    avg_tenure=('tenure', 'mean')
).reset_index()

highest_churn_contract = contract_churn.loc[contract_churn['churn_rate'].idxmax()]
lowest_churn_contract = contract_churn.loc[contract_churn['churn_rate'].idxmin()]

analyses.append({
    "title": "Churn by Contract Type",
    "category": "Contract",
    "observation": f"Month-to-month contracts show the highest churn rate at {highest_churn_contract['churn_rate']*100:.1f}%, while {lowest_churn_contract['Contract']} contracts have the lowest at {lowest_churn_contract['churn_rate']*100:.1f}%. This {highest_churn_contract['churn_rate']/lowest_churn_contract['churn_rate']:.1f}x difference highlights contract type as a critical churn predictor.",
    "business_impact": f"Month-to-month customers represent {contract_churn[contract_churn['Contract']=='Month-to-month']['total'].values[0]} customers with {contract_churn[contract_churn['Contract']=='Month-to-month']['churned'].values[0]} churned, creating the largest revenue vulnerability.",
    "recommendation": "Design incentive programs to migrate month-to-month customers to annual or two-year contracts. Offer discounts of 10-15% for contract commitments, and introduce loyalty rewards for long-term subscribers.",
    "chart_data": {
        "type": "bar",
        "categories": contract_churn['Contract'].tolist(),
        "total_customers": contract_churn['total'].tolist(),
        "churned_customers": contract_churn['churned'].tolist(),
        "churn_rates": contract_churn['churn_rate'].tolist(),
        "avg_monthly_charges": contract_churn['avg_monthly'].tolist()
    }
})
print(f"[2/10] Contract: Highest churn = {highest_churn_contract['Contract']} ({highest_churn_contract['churn_rate']*100:.1f}%)")

# ============================================================
# 3. Churn by Payment Method
# ============================================================
payment_churn = df.groupby('PaymentMethod').agg(
    total=('Churn_Binary', 'count'),
    churned=('Churn_Binary', 'sum'),
    churn_rate=('Churn_Binary', 'mean'),
    avg_monthly=('MonthlyCharges', 'mean')
).reset_index().sort_values('churn_rate', ascending=False)

top_payment = payment_churn.iloc[0]
bot_payment = payment_churn.iloc[-1]

analyses.append({
    "title": "Churn by Payment Method",
    "category": "Payment",
    "observation": f"Electronic check users have the highest churn rate at {top_payment['churn_rate']*100:.1f}%, significantly above the average. Automatic payment methods (bank transfer, credit card) show much lower churn rates (~{bot_payment['churn_rate']*100:.1f}%), suggesting that manual payment methods correlate with lower customer commitment.",
    "business_impact": f"Electronic check users represent {top_payment['total']} customers with {top_payment['churned']} churned. Converting these to auto-pay could prevent a significant portion of churn.",
    "recommendation": "Incentivize customers to switch to automatic payment methods by offering a small monthly discount ($2-5/month). Simplify the autopay enrollment process and send targeted campaigns to electronic check users.",
    "chart_data": {
        "type": "bar",
        "categories": payment_churn['PaymentMethod'].tolist(),
        "total_customers": payment_churn['total'].tolist(),
        "churned_customers": payment_churn['churned'].tolist(),
        "churn_rates": payment_churn['churn_rate'].tolist()
    }
})
print(f"[3/10] Payment: Highest churn = {top_payment['PaymentMethod']} ({top_payment['churn_rate']*100:.1f}%)")

# ============================================================
# 4. Churn by Internet Service
# ============================================================
internet_churn = df.groupby('InternetService').agg(
    total=('Churn_Binary', 'count'),
    churned=('Churn_Binary', 'sum'),
    churn_rate=('Churn_Binary', 'mean'),
    avg_monthly=('MonthlyCharges', 'mean')
).reset_index().sort_values('churn_rate', ascending=False)

top_internet = internet_churn.iloc[0]

analyses.append({
    "title": "Churn by Internet Service",
    "category": "Service",
    "observation": f"Fiber optic customers have the highest churn rate at {top_internet['churn_rate']*100:.1f}%, despite paying higher monthly charges (avg ${top_internet['avg_monthly']:.2f}). This suggests potential issues with fiber optic service quality, pricing perception, or competitive alternatives.",
    "business_impact": f"Fiber optic is a premium service segment with {top_internet['total']} customers. Losing {top_internet['churned']} of these high-value customers significantly impacts revenue.",
    "recommendation": "Investigate fiber optic service quality issues (speed consistency, downtime). Benchmark pricing against competitors. Consider bundling value-added services (security, backup) with fiber plans at discounted rates.",
    "chart_data": {
        "type": "bar",
        "categories": internet_churn['InternetService'].tolist(),
        "total_customers": internet_churn['total'].tolist(),
        "churned_customers": internet_churn['churned'].tolist(),
        "churn_rates": internet_churn['churn_rate'].tolist(),
        "avg_monthly_charges": internet_churn['avg_monthly'].tolist()
    }
})
print(f"[4/10] Internet: Highest churn = {top_internet['InternetService']} ({top_internet['churn_rate']*100:.1f}%)")

# ============================================================
# 5. Churn by Gender
# ============================================================
gender_churn = df.groupby('gender').agg(
    total=('Churn_Binary', 'count'),
    churned=('Churn_Binary', 'sum'),
    churn_rate=('Churn_Binary', 'mean')
).reset_index()

diff_gender = abs(gender_churn['churn_rate'].max() - gender_churn['churn_rate'].min()) * 100

analyses.append({
    "title": "Churn by Gender",
    "category": "Demographics",
    "observation": f"Churn rates are nearly identical across genders with only a {diff_gender:.1f} percentage point difference. Male churn: {gender_churn[gender_churn['gender']=='Male']['churn_rate'].values[0]*100:.1f}%, Female churn: {gender_churn[gender_churn['gender']=='Female']['churn_rate'].values[0]*100:.1f}%. Gender is not a significant churn predictor.",
    "business_impact": "Since gender does not significantly influence churn, retention strategies should not be gender-differentiated. Resources are better allocated to other more predictive factors.",
    "recommendation": "Focus retention efforts on behavioral and service-related factors rather than demographics. Use contract type, payment method, and service usage as primary segmentation variables.",
    "chart_data": {
        "type": "bar",
        "categories": gender_churn['gender'].tolist(),
        "total_customers": gender_churn['total'].tolist(),
        "churned_customers": gender_churn['churned'].tolist(),
        "churn_rates": gender_churn['churn_rate'].tolist()
    }
})
print(f"[5/10] Gender: Difference = {diff_gender:.1f}pp (not significant)")

# ============================================================
# 6. Churn by Senior Citizen Status
# ============================================================
senior_churn = df.groupby('SeniorCitizen').agg(
    total=('Churn_Binary', 'count'),
    churned=('Churn_Binary', 'sum'),
    churn_rate=('Churn_Binary', 'mean'),
    avg_monthly=('MonthlyCharges', 'mean')
).reset_index()

sr_yes = senior_churn[senior_churn['SeniorCitizen'] == 'Yes']
sr_no = senior_churn[senior_churn['SeniorCitizen'] == 'No']

sr_yes_rate = sr_yes['churn_rate'].values[0] if len(sr_yes) > 0 else 0
sr_no_rate = sr_no['churn_rate'].values[0] if len(sr_no) > 0 else 0

analyses.append({
    "title": "Churn by Senior Citizen Status",
    "category": "Demographics",
    "observation": f"Senior citizens churn at {sr_yes_rate*100:.1f}% compared to {sr_no_rate*100:.1f}% for non-seniors — nearly {sr_yes_rate/sr_no_rate:.1f}x higher. Despite being a smaller group, seniors represent a disproportionately high churn segment.",
    "business_impact": f"Senior citizens ({sr_yes['total'].values[0] if len(sr_yes) > 0 else 0} customers) have higher avg monthly charges (${sr_yes['avg_monthly'].values[0] if len(sr_yes) > 0 else 0:.2f}), making their churn more costly per customer.",
    "recommendation": "Create senior-specific retention programs: simplified billing, dedicated support lines, senior discount plans, and proactive outreach. Ensure digital tools are accessible for older users.",
    "chart_data": {
        "type": "bar",
        "categories": senior_churn['SeniorCitizen'].tolist(),
        "total_customers": senior_churn['total'].tolist(),
        "churned_customers": senior_churn['churned'].tolist(),
        "churn_rates": senior_churn['churn_rate'].tolist()
    }
})
print(f"[6/10] Senior Citizen: Seniors churn at {sr_yes_rate*100:.1f}% vs {sr_no_rate*100:.1f}%")

# ============================================================
# 7. Churn by Monthly Charges
# ============================================================
bins_monthly = [0, 30, 50, 70, 90, 120]
labels_monthly = ['$0-30', '$30-50', '$50-70', '$70-90', '$90-120']
df['MonthlyBin'] = pd.cut(df['MonthlyCharges'], bins=bins_monthly, labels=labels_monthly, include_lowest=True)

monthly_churn = df.groupby('MonthlyBin', observed=False).agg(
    total=('Churn_Binary', 'count'),
    churned=('Churn_Binary', 'sum'),
    churn_rate=('Churn_Binary', 'mean'),
    avg_charges=('MonthlyCharges', 'mean')
).reset_index()

high_charge_churn = monthly_churn.iloc[-1]
low_charge_churn = monthly_churn.iloc[0]

# Stats for churned vs active
churned_avg_monthly = df[df['Churn'] == 'Yes']['MonthlyCharges'].mean()
active_avg_monthly = df[df['Churn'] == 'No']['MonthlyCharges'].mean()

analyses.append({
    "title": "Churn by Monthly Charges",
    "category": "Revenue",
    "observation": f"Churned customers have higher average monthly charges (${churned_avg_monthly:.2f}) compared to active customers (${active_avg_monthly:.2f}). The highest charge bracket ({high_charge_churn['MonthlyBin']}) shows a {high_charge_churn['churn_rate']*100:.1f}% churn rate, versus {low_charge_churn['churn_rate']*100:.1f}% for the lowest bracket ({low_charge_churn['MonthlyBin']}).",
    "business_impact": f"Higher-paying customers are more likely to churn, indicating possible price sensitivity or higher expectations. Each churned high-value customer costs ~${high_charge_churn['avg_charges']:.0f}/month in lost revenue.",
    "recommendation": "Review pricing for high-spend tiers. Introduce value-based pricing with clear ROI communication. Offer loyalty discounts or service upgrades to justify premium pricing. Consider price-lock guarantees for long-term customers.",
    "chart_data": {
        "type": "bar",
        "categories": monthly_churn['MonthlyBin'].astype(str).tolist(),
        "total_customers": monthly_churn['total'].tolist(),
        "churned_customers": monthly_churn['churned'].tolist(),
        "churn_rates": monthly_churn['churn_rate'].tolist(),
        "churned_avg": churned_avg_monthly,
        "active_avg": active_avg_monthly
    }
})
print(f"[7/10] Monthly Charges: Churned avg ${churned_avg_monthly:.2f} vs Active avg ${active_avg_monthly:.2f}")

# ============================================================
# 8. Churn by Total Charges
# ============================================================
bins_total = [0, 500, 1500, 3000, 5000, 9000]
labels_total = ['$0-500', '$500-1.5K', '$1.5K-3K', '$3K-5K', '$5K-9K']
df['TotalBin'] = pd.cut(df['TotalCharges'], bins=bins_total, labels=labels_total, include_lowest=True)

total_churn = df.groupby('TotalBin', observed=False).agg(
    total=('Churn_Binary', 'count'),
    churned=('Churn_Binary', 'sum'),
    churn_rate=('Churn_Binary', 'mean'),
    avg_charges=('TotalCharges', 'mean')
).reset_index()

churned_avg_total = df[df['Churn'] == 'Yes']['TotalCharges'].mean()
active_avg_total = df[df['Churn'] == 'No']['TotalCharges'].mean()

analyses.append({
    "title": "Churn by Total Charges",
    "category": "Revenue",
    "observation": f"Customers with lower total charges (shorter tenure) churn more. Churned customers avg total charges: ${churned_avg_total:,.0f} vs active: ${active_avg_total:,.0f}. The lowest total charge bracket shows {total_churn.iloc[0]['churn_rate']*100:.1f}% churn, while the highest shows {total_churn.iloc[-1]['churn_rate']*100:.1f}%.",
    "business_impact": f"Low total charge customers represent early-tenure customers who leave before generating significant lifetime value. The revenue gap between churned (${churned_avg_total:,.0f}) and active (${active_avg_total:,.0f}) customers highlights the cost of early churn.",
    "recommendation": "Focus onboarding efforts in the first 3-6 months. Implement early engagement programs, welcome calls, and guided setup assistance. Create milestone rewards at 6, 12, and 24-month marks.",
    "chart_data": {
        "type": "bar",
        "categories": total_churn['TotalBin'].astype(str).tolist(),
        "total_customers": total_churn['total'].tolist(),
        "churned_customers": total_churn['churned'].tolist(),
        "churn_rates": total_churn['churn_rate'].tolist(),
        "churned_avg": churned_avg_total,
        "active_avg": active_avg_total
    }
})
print(f"[8/10] Total Charges: Churned avg ${churned_avg_total:,.0f} vs Active avg ${active_avg_total:,.0f}")

# ============================================================
# 9. Churn by Tenure
# ============================================================
tenure_churn = df.groupby('tenure').agg(
    total=('Churn_Binary', 'count'),
    churned=('Churn_Binary', 'sum'),
    churn_rate=('Churn_Binary', 'mean')
).reset_index()

# Also by TenureBucket
bucket_churn = df.groupby('TenureBucket').agg(
    total=('Churn_Binary', 'count'),
    churned=('Churn_Binary', 'sum'),
    churn_rate=('Churn_Binary', 'mean'),
    avg_monthly=('MonthlyCharges', 'mean')
).reset_index()

early_churn = df[df['tenure'] <= 6]['Churn_Binary'].mean()
mid_churn = df[(df['tenure'] > 6) & (df['tenure'] <= 24)]['Churn_Binary'].mean()
late_churn = df[df['tenure'] > 48]['Churn_Binary'].mean()

analyses.append({
    "title": "Churn by Tenure",
    "category": "Lifecycle",
    "observation": f"Churn rate decreases dramatically with tenure. First 6 months: {early_churn*100:.1f}%, 6-24 months: {mid_churn*100:.1f}%, 48+ months: {late_churn*100:.1f}%. The first year is the critical window for customer retention — customers who survive past it become progressively more loyal.",
    "business_impact": f"The early-tenure churn spike means the company is spending on customer acquisition but losing a large proportion before recouping those costs. Each early churner represents a net loss on acquisition investment.",
    "recommendation": "Create a structured onboarding journey for the first 12 months with regular touchpoints. Assign dedicated success managers to high-value new customers. Implement a '90-day guarantee' program with exclusive perks.",
    "chart_data": {
        "type": "line",
        "tenure_months": tenure_churn['tenure'].tolist(),
        "churn_rates": tenure_churn['churn_rate'].tolist(),
        "customer_counts": tenure_churn['total'].tolist(),
        "bucket_data": {
            "buckets": bucket_churn['TenureBucket'].tolist(),
            "churn_rates": bucket_churn['churn_rate'].tolist(),
            "totals": bucket_churn['total'].tolist()
        }
    }
})
print(f"[9/10] Tenure: 0-6mo={early_churn*100:.1f}%, 6-24mo={mid_churn*100:.1f}%, 48+mo={late_churn*100:.1f}%")

# ============================================================
# 10. Customer Segment Analysis
# ============================================================
risk_churn = df.groupby('RiskCategory').agg(
    total=('Churn_Binary', 'count'),
    churned=('Churn_Binary', 'sum'),
    churn_rate=('Churn_Binary', 'mean'),
    avg_monthly=('MonthlyCharges', 'mean'),
    avg_tenure=('tenure', 'mean'),
    avg_health=('CustomerHealthIndex', 'mean')
).reset_index()

rev_churn = df.groupby('RevenueSegment').agg(
    total=('Churn_Binary', 'count'),
    churned=('Churn_Binary', 'sum'),
    churn_rate=('Churn_Binary', 'mean'),
    avg_monthly=('MonthlyCharges', 'mean'),
    total_revenue=('MonthlyCharges', 'sum')
).reset_index()

high_risk = risk_churn[risk_churn['RiskCategory'] == 'High Risk']
hr_rate = high_risk['churn_rate'].values[0] if len(high_risk) > 0 else 0

analyses.append({
    "title": "Customer Segment Analysis",
    "category": "Segmentation",
    "observation": f"High-risk customers churn at {hr_rate*100:.1f}%, validating the risk model. Revenue segments show varying churn rates with distinct profiles. The combination of risk category and revenue segment provides a powerful targeting matrix for retention efforts.",
    "business_impact": f"High-risk customers ({high_risk['total'].values[0] if len(high_risk) > 0 else 0} customers) represent the most immediate revenue threat. Prioritizing retention by both risk level and revenue value maximizes ROI on retention spend.",
    "recommendation": "Build a 2x2 retention priority matrix (Risk × Revenue). High-risk/high-revenue customers get VIP retention treatment. High-risk/low-revenue customers get automated interventions. Low-risk customers get standard engagement programs.",
    "chart_data": {
        "type": "grouped_bar",
        "risk_analysis": {
            "categories": risk_churn['RiskCategory'].tolist(),
            "total_customers": risk_churn['total'].tolist(),
            "churned_customers": risk_churn['churned'].tolist(),
            "churn_rates": risk_churn['churn_rate'].tolist(),
            "avg_health_scores": risk_churn['avg_health'].tolist()
        },
        "revenue_analysis": {
            "segments": rev_churn['RevenueSegment'].tolist(),
            "total_customers": rev_churn['total'].tolist(),
            "churned_customers": rev_churn['churned'].tolist(),
            "churn_rates": rev_churn['churn_rate'].tolist(),
            "total_revenue": rev_churn['total_revenue'].tolist()
        }
    }
})
print(f"[10/10] Segments: High Risk churn = {hr_rate*100:.1f}%")

# ============================================================
# Summary
# ============================================================
summary = {
    "total_customers": total,
    "total_churned": churned,
    "total_active": active,
    "overall_churn_rate": round(churned / total * 100, 2),
    "avg_monthly_charges": round(df['MonthlyCharges'].mean(), 2),
    "avg_tenure": round(df['tenure'].mean(), 2),
    "total_revenue": round(df['TotalCharges'].sum(), 2),
    "revenue_at_risk": round(df[df['Churn'] == 'Yes']['MonthlyCharges'].sum(), 2),
    "key_findings": [
        f"Contract type is the strongest churn predictor — month-to-month customers churn at {highest_churn_contract['churn_rate']*100:.1f}%",
        f"Electronic check payment method correlates with {top_payment['churn_rate']*100:.1f}% churn rate",
        f"Fiber optic customers churn at {top_internet['churn_rate']*100:.1f}% despite higher spend",
        f"Senior citizens churn at {sr_yes_rate*100:.1f}% — nearly {sr_yes_rate/sr_no_rate:.1f}x higher than non-seniors",
        f"First 6 months show {early_churn*100:.1f}% churn — the critical retention window",
        "Gender has negligible impact on churn"
    ],
    "analyses_count": len(analyses)
}

output = {
    "analyses": analyses,
    "summary": summary
}

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, cls=NumpyEncoder, ensure_ascii=False)

print(f"\n{'=' * 60}")
print(f"  EDA Complete! {len(analyses)} analyses exported.")
print(f"  Output: {OUTPUT_PATH}")
print(f"  Key Findings:")
for i, finding in enumerate(summary['key_findings'], 1):
    print(f"    {i}. {finding}")
print(f"{'=' * 60}")

# Cleanup temp columns
df.drop(columns=['MonthlyBin', 'TotalBin', 'Churn_Binary'], inplace=True, errors='ignore')
