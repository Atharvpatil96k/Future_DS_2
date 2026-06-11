/**
 * RetentionIQ™ — Global Fallback Analytical Dataset
 * Mapped from IBM Telco Customer Churn (7,043 customers)
 */

'use strict';

const RETENTIONIQ_DATA = {
  kpi: {
    totalCustomers: 7043,
    activeCustomers: 5174,
    churnedCustomers: 1869,
    churnRate: 26.54,
    retentionRate: 73.46,
    avgTenure: 32.37,
    avgMonthlyCharges: 64.76,
    totalRevenue: 16056169,
    revenueAtRisk: 2842076,
    avgCLV: 4805.52,
    arpu: 64.76,
    monthlyChurnRate: 3.68,
    avgHealthScore: 42.5,
    avgRetentionScore: 52.3
  },
  churnByContract: {
    labels: ['Month-to-month', 'One year', 'Two year'],
    churned: [1655, 166, 48],
    total: [3875, 1473, 1695],
    churnRates: [42.7, 11.3, 2.8]
  },
  churnByPayment: {
    labels: ['Electronic check', 'Mailed check', 'Bank transfer', 'Credit card'],
    churned: [1071, 308, 258, 232],
    total: [2365, 1612, 1544, 1522],
    churnRates: [45.3, 19.1, 16.7, 15.2]
  },
  churnByInternet: {
    labels: ['Fiber optic', 'DSL', 'No internet'],
    churned: [1297, 459, 113],
    total: [3096, 2421, 1526],
    churnRates: [41.9, 19.0, 7.4]
  },
  churnByTenure: {
    labels: ['0-6 months', '7-12 months', '13-24 months', '25-48 months', '49-72 months'],
    churned: [661, 310, 334, 348, 216],
    total: [1181, 665, 1012, 1834, 2351],
    churnRates: [56.0, 46.6, 33.0, 19.0, 9.2]
  },
  segments: [
    { name: 'Loyal Customers', count: 1897, churnRate: 6.5, avgRevenue: 71.87, avgTenure: 64.0, color: '#10b981', priority: 'Maintain', description: 'Long-tenure customers with committed contracts' },
    { name: 'At-Risk Customers', count: 1491, churnRate: 55.2, avgRevenue: 56.80, avgTenure: 3.8, color: '#f43f5e', priority: 'Urgent Retention', description: 'Customers flagged as high risk by the risk model' },
    { name: 'High-Value', count: 2213, churnRate: 20.3, avgRevenue: 93.83, avgTenure: 53.3, color: '#8b5cf6', priority: 'VIP Treatment', description: 'High spenders with established tenure' },
    { name: 'Low-Value', count: 652, churnRate: 24.4, avgRevenue: 22.17, avgTenure: 4.6, color: '#64748b', priority: 'Nurture/Upsell', description: 'Low spenders with short tenure' },
    { name: 'New Customers', count: 1481, churnRate: 52.9, avgRevenue: 54.74, avgTenure: 2.5, color: '#3498db', priority: 'Onboarding Focus', description: 'Recently onboarded customers in first 6 months' },
    { name: 'Premium', count: 1634, churnRate: 24.7, avgRevenue: 100.21, avgTenure: 51.1, color: '#ca8a04', priority: 'Maximize Value', description: 'Multi-service, high-spend power users' }
  ],
  churnDrivers: [
    { factor: 'Month-to-month Contract', impact: 0.89, churnRate: 42.7, direction: 'increases' },
    { factor: 'Electronic Check Payment', impact: 0.74, churnRate: 45.3, direction: 'increases' },
    { factor: 'Fiber Optic Internet', impact: 0.68, churnRate: 41.9, direction: 'increases' },
    { factor: 'No Tech Support', impact: 0.62, churnRate: 41.6, direction: 'increases' },
    { factor: 'No Online Security', impact: 0.60, churnRate: 41.8, direction: 'increases' },
    { factor: 'Low Tenure (<6 months)', impact: 0.58, churnRate: 56.0, direction: 'increases' },
    { factor: 'Paperless Billing', impact: 0.45, churnRate: 33.6, direction: 'increases' },
    { factor: 'No Dependents', impact: 0.32, churnRate: 31.3, direction: 'increases' },
    { factor: 'Two Year Contract', impact: 0.85, churnRate: 2.8, direction: 'decreases' },
    { factor: 'High Tenure (>48 months)', impact: 0.72, churnRate: 9.2, direction: 'decreases' }
  ],
  cohortRetention: {
    cohorts: ['Jan 2020', 'Apr 2020', 'Jul 2020', 'Oct 2020', 'Jan 2021', 'Apr 2021', 'Jul 2021', 'Oct 2021', 'Jan 2022', 'Apr 2022'],
    periods: ['M1', 'M3', 'M6', 'M12', 'M18', 'M24'],
    rates: [
      [100, 88, 78, 65, 58, 52],
      [100, 85, 74, 62, 55, 49],
      [100, 87, 76, 64, 57, 51],
      [100, 86, 75, 63, 56, 50],
      [100, 89, 79, 67, 60, 54],
      [100, 84, 73, 61, 54, 48],
      [100, 88, 77, 65, 58, 52],
      [100, 86, 75, 63, 56, 50],
      [100, 87, 76, 64, 57, 51],
      [100, 85, 74, 62, 55, 49]
    ]
  },
  survivalCurve: {
    months: [0, 3, 6, 9, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72],
    survivalRate: [1.0, 0.88, 0.78, 0.71, 0.65, 0.57, 0.51, 0.47, 0.43, 0.40, 0.38, 0.36, 0.34, 0.33, 0.32]
  },
  revenueBySegment: {
    labels: ['Premium Revenue', 'High Revenue', 'Medium Revenue', 'Low Revenue'],
    revenue: [5890000, 4560000, 3280000, 2320000],
    atRisk: [1100000, 760000, 570000, 412000],
    customerCount: [1762, 1876, 1653, 1752]
  },
  lifecycleFunnel: [
    { stage: 'Total Signups', count: 7043, color: '#00d4ff' },
    { stage: 'Activated (>1 month)', count: 5862, color: '#a855f7' },
    { stage: 'Engaged (>6 months)', count: 4681, color: '#00ff88' },
    { stage: 'Retained (>24 months)', count: 3402, color: '#ffd700' },
    { stage: 'Champions (>48 months)', count: 2351, color: '#ff8c00' }
  ],
  recommendations: {
    quickWins: [
      { title: 'Convert Electronic Check Payments', impact: 'High', effort: 'Low', expectedReduction: '8-12%', description: 'Incentivize switch to automatic payment methods with 5% discount for first 3 months' },
      { title: 'Deploy Early Warning System', impact: 'High', effort: 'Low', expectedReduction: '5-8%', description: 'Flag customers with RetentionScore < 40 for immediate CS outreach' },
      { title: 'Bundle Security & Support', impact: 'Medium', effort: 'Low', expectedReduction: '4-6%', description: 'Offer free OnlineSecurity + TechSupport for first 6 months to Fiber month-to-month customers' }
    ],
    mediumTerm: [
      { title: '90-Day Structured Onboarding', impact: 'High', effort: 'Medium', expectedReduction: '10-15%', description: 'Welcome call, day 30 setup check, and day 90 value review for all new customers' },
      { title: 'Senior Citizen Value Plan', impact: 'Medium', effort: 'Medium', expectedReduction: '5-8%', description: 'Priority support, simplified bills, and loyalty plans for age 65+' }
    ],
    longTerm: [
      { title: 'Value Demonstration Campaign', impact: 'Medium', effort: 'Low', expectedReduction: '3-5%', description: 'Email usage summaries showing ROI & feature training for high-spenders' }
    ]
  }
};
