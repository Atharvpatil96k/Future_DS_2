# RetentionIQ Methodology & Technical Specification

This document provides a detailed breakdown of the statistical models, engineering formulas, and data pipeline processes implemented in the RetentionIQ platform.

---

## 1. Data Processing Pipeline Architecture

The pipeline consists of 9 sequential Python scripts executing feature engineering, advanced analytics, and front-end aggregation.

```
data/telco_customer_churn.csv (Raw Dataset)
              │
              ▼
    01_data_cleaning.py ──────────► Outputs data/cleaned/telco_churn_cleaned.csv
              │
              ▼
 02_feature_engineering.py ───────► Outputs data/processed/telco_churn_featured.csv
              │
  ┌───────────┴───────────┬──────────────────────┬──────────────────────┐
  ▼                       ▼                      ▼                      ▼
03_eda.py           04_advanced_analytics.py  05_customer_seg.py   06_cohort_analysis.py
  │                       │                      │                      │
  ▼                       ▼                      ▼                      ▼
eda_results.json    advanced_analytics.json   segmentation.json    cohort_analysis.json
  │                       │                      │                      │
  └───────────┬───────────┴──────────────────────┴───────────┬──────────┘
              ▼                                              ▼
07_churn_intelligence.py                           08_ml_churn_prediction.py
              │                                              │
              ▼                                              ▼
churn_intelligence.json                             ml_results.json
              │                                              │
              └───────────────────────┬──────────────────────┘
                                      ▼
                           09_insights_aggregator.py
                                      │
                                      ▼
                         dashboard/data/insights.json (Frontend Asset)
```

---

## 2. Phase 1: Data Cleaning & Preprocessing

- **Imputation of Missing Values**: The raw dataset has 11 missing values in `TotalCharges` corresponding to customers with `tenure = 0` (who signed up on the date of data extraction). We imputed these using the formula:
  $$\text{TotalCharges} = \text{tenure} \times \text{MonthlyCharges}$$
  resulting in $0.00 for new signups.
- **Categorical Mapping**: `SeniorCitizen` was converted from a binary `0/1` integer to a consistent string `'No'/'Yes'` to match other categorical variables.
- **Duplicate Treatment**: The pipeline performs schema validations, checks for duplicate `customerID` records, and removes duplicate rows if any are present.

---

## 3. Phase 2: Feature Engineering & Scoring Metrics

We engineered several business metrics to translate raw attributes into actionable scores:

### Customer Health Index (CHI)
A score from 0 to 100 indicating a customer's engagement and billing commitment. A higher score represents a healthier, lower-risk customer:
$$\text{CHI} = w_1 \cdot C_{\text{score}} + w_2 \cdot P_{\text{score}} + w_3 \cdot E_{\text{score}} + w_4 \cdot T_{\text{score}}$$
- **Contract Score ($C_{\text{score}}$)**: 100 for Two-year, 50 for One-year, 10 for Month-to-month.
- **Payment Score ($P_{\text{score}}$)**: 100 for credit card/bank transfer auto-pay, 50 for mailed checks, 20 for electronic checks.
- **Engagement Score ($E_{\text{score}}$)**: Based on the count of active services:
  $$\text{ServiceCount} = \sum (\text{OnlineSecurity}, \text{OnlineBackup}, \text{DeviceProtection}, \text{TechSupport}, \text{StreamingTV}, \text{StreamingMovies})$$
  $$\text{EngagementScore} = \text{ServiceCount} \times 16.67$$
- **Tenure Weight ($T_{\text{score}}$)**: Log-normalized tenure to reflect that early tenure months are higher risk:
  $$\text{TenureScore} = \min\left(100, \ln(\text{tenure} + 1) \times 23.3\right)$$
- **Weights**: $w_1 = 0.35$ (Contract), $w_2 = 0.20$ (Payment), $w_3 = 0.25$ (Engagement), $w_4 = 0.20$ (Tenure).

### Customer Lifetime Value (CLV Estimate)
Computes the projected value of a subscriber by incorporating remaining expected tenure:
$$\text{CLV Estimate} = \text{MonthlyCharges} \times (\text{tenure} + \text{ExpectedRemainingTenure})$$
Where the **Expected Remaining Tenure** is estimated using the median survival time calculated via Kaplan-Meier survival curves matching the customer's contract segment:
- **Month-to-month contract**: +18 months expected remaining tenure.
- **One-year contract**: +36 months expected remaining tenure.
- **Two-year contract**: +60 months expected remaining tenure.

---

## 4. Phase 3: Survival Analysis (Kaplan-Meier Fitter)

We performed survival analysis using the `lifelines` Python library, modeling `tenure` as the duration and `Churn` as the event.

- **Overall Median Survival**: The overall base has a high survival rate, but month-to-month contracts have a median survival time of **35.0 months**.
- **Log-Rank Test**: The comparison between contract types yields a p-value of $< 0.0001$, proving statistically significant survival curves.

---

## 5. Phase 4: Machine Learning Churn Prediction

We trained two classification models to evaluate predictive signals:

### Logistic Regression
Used as a baseline and risk probability generator:
- **AUC-ROC**: 84.44%
- **Accuracy**: 74.66%
- **Recall (Sensitivity)**: 60.0%
- **Business Significance**: High AUC-ROC ensures that the generated probability scores are highly calibrated, allowing us to triage customers by risk level.

### Random Forest Classifier
Used for variable importance analysis:
- **AUC-ROC**: 84.09%
- **Accuracy**: 77.22%
- **Precision**: 70.0%
- **Top 5 Feature Importances**:
  1. `RetentionScore` (44.64%)
  2. `ExpectedRemainingTenure` (44.53%)
  3. `Contract` (Month-to-month indicator) (41.01%)
  4. `CustomerHealthIndex` (36.46%)
  5. `tenure` (35.22%)

---

## 6. Phase 5: Segmentation & Churn Drivers

### Cramér's V Correlation for Categorical Variables
Calculated using the Chi-Squared statistic to measure the association strength with Churn:
$$\text{Cramér's V} = \sqrt{\frac{\chi^2}{n(k - 1)}}$$
- **Contract Type**: Cramér's V = 0.4101 (Strongest predictor)
- **Online Security Add-on**: Cramér's V = 0.3474
- **Tech Support Add-on**: Cramér's V = 0.3429
- **Internet Service Type**: Cramér's V = 0.3225
- **Payment Method**: Cramér's V = 0.3034

### Operational Customer Segments
The classification pipeline divides the customer base into 8 profiles:
1. **Loyal Customers**: Tenure > 48 months, non-month-to-month contracts (Avg Churn: 6.54%).
2. **At-Risk Customers**: Flagged in the highest risk threshold by the classifier (Avg Churn: 55.20%).
3. **High-Value Customers**: Spends > $80/mo and tenure > 24 months (Avg Churn: 20.29%).
4. **Low-Value Customers**: Spends < $30/mo and tenure ≤ 12 months (Avg Churn: 24.39%).
5. **New Customers**: Tenure ≤ 6 months (Avg Churn: 52.94%).
6. **Dormant Customers**: Less than 2 active services and engagement score < 30 (Avg Churn: 31.72%).
7. **Long-Term Subscribers**: Tenure > 36 months (Avg Churn: 11.93%).
8. **Premium Customers**: More than 6 active services and MonthlyCharges > $80 (Avg Churn: 24.72%).
