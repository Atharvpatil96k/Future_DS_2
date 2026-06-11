import pandas as pd
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE, "data", "processed", "telco_churn_featured.csv")
OUTPUT_PATH = os.path.join(BASE, "dashboard", "js", "customers_db.js")

# Load engineered dataset
df = pd.read_csv(DATA_PATH)

# Impute and clean
df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce').fillna(0)
df['SeniorCitizen'] = df['SeniorCitizen'].map({'Yes': 1, 'No': 0, '1': 1, '0': 0, 1: 1, 0: 0}).fillna(0).astype(int)

# Extract and map columns to short keys for compression
# Key maps:
# g: gender (Female/Male)
# s: senior citizen (0/1)
# t: tenure (months)
# i: internet service (Fiber optic/DSL/No)
# c: contract type (Month-to-month/One year/Two year)
# p: payment method (Electronic check/Mailed check/Bank transfer (automatic)/Credit card (automatic))
# m: monthly charges (float)
# tc: total charges (float)
# ch: churn status (Yes/No)
# h: health index (0-100)
# r: retention score (0-100)
# clv: CLV estimate (float)

records = []
for _, row in df.iterrows():
    records.append({
        "g": str(row['gender']),
        "s": int(row['SeniorCitizen']),
        "t": int(row['tenure']),
        "i": str(row['InternetService']),
        "c": str(row['Contract']),
        "p": str(row['PaymentMethod']),
        "m": float(row['MonthlyCharges']),
        "tc": float(row['TotalCharges']),
        "ch": str(row['Churn']),
        "h": float(row['CustomerHealthIndex']),
        "r": float(row['RetentionScore']),
        "clv": float(row['CLV_Estimate'])
    })

# Write as JavaScript file
with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write("// RetentionIQ™ — Compressed Customer Database\n")
    f.write("// Used for real-time dashboard filtering and metrics calculation\n\n")
    f.write("const CUSTOMERS_DB = ")
    json.dump(records, f, indent=None)  # output compact
    f.write(";\n")

print(f"Exported {len(records)} customer records to {OUTPUT_PATH}")
