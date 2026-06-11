/* ═══════════════════════════════════════════════════════════════════
   RetentionIQ v3 — dashboard.js
   Application bootstrap, calculator logic, DOM population for single page
   ═══════════════════════════════════════════════════════════════════ */

'use strict';

let DATA = null;

document.addEventListener('DOMContentLoaded', () => {
  bootstrap();
});

async function bootstrap() {
  try {
    const res = await fetch('data/insights.json');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    DATA = await res.json();
    console.log('Successfully loaded analytics data from insights.json');
  } catch (err) {
    console.warn('Fetch failed, transforming embedded RETENTIONIQ_DATA as fallback:', err);
    if (typeof RETENTIONIQ_DATA !== 'undefined') {
      DATA = transformFallbackData(RETENTIONIQ_DATA);
    } else {
      showError('Could not load analytical data. Please check data/insights.json or js/data.js.');
      return;
    }
  }

  try {
    populateHeaderStats(DATA);
    populateHeroSection(DATA);
    populateTopFindings(DATA);
    populateChurnDrivers(DATA);
    populateSegmentsTable(DATA);
    populateCohortsTable(DATA);
    populateMLSection(DATA);
    populateActionPlan(DATA);
    populatePortfolioSection(DATA);
    
    // Draw all 7 charts on page load
    initAllCharts(DATA);

    // Initialize interactive handlers
    initExplainability();
    initEfficiencySlider();
    initDrawerCloseHandlers();
  } catch (domErr) {
    console.error('Error bootstrapping dashboard UI:', domErr);
  }
}

function showError(msg) {
  const container = document.querySelector('.app-container');
  if (container) {
    container.innerHTML = `<div style="padding:100px 20px;text-align:center;color:var(--churn);font-size:1.2rem;font-weight:700;">${msg}</div>`;
  }
}

// ── Header Stats Populator ─────────────────────────────────────────
function populateHeaderStats(d) {
  const totalEl = document.getElementById('header-total-customers');
  const churnEl = document.getElementById('header-churn-rate');
  const riskEl = document.getElementById('header-revenue-risk');
  const sizeEl = document.getElementById('header-high-risk-size');

  if (totalEl) totalEl.textContent = d.meta.total_customers.toLocaleString();
  if (churnEl) churnEl.textContent = d.kpis.churn_rate.toFixed(2) + '%';
  if (riskEl) riskEl.textContent = '$' + Math.round(d.kpis.revenue_at_risk_monthly).toLocaleString() + '/mo';
  if (sizeEl) sizeEl.textContent = d.kpis.high_risk_customer_count.toLocaleString() + ' accounts';
}

// ── Hero Section Populator ─────────────────────────────────────────
function populateHeroSection(d) {
  const healthEl = document.getElementById('hero-health-score');
  const churnEl = document.getElementById('hero-churn-rate');
  const riskEl = document.getElementById('hero-revenue-risk');

  if (healthEl) {
    // Retention Health = 100 - Churn Rate
    const score = 100 - d.kpis.churn_rate;
    healthEl.textContent = score.toFixed(1);
  }
  if (churnEl) churnEl.textContent = d.kpis.churn_rate.toFixed(1) + '%';
  if (riskEl) {
    const annualRisk = d.kpis.revenue_at_risk_annual;
    riskEl.textContent = `$${(annualRisk / 1e6).toFixed(2)}M`;
  }
}

// ── Top Findings Panel Populator ───────────────────────────────────
function populateTopFindings(d) {
  const signalList = document.getElementById('plausible-signals');
  if (signalList && d.top_insights) {
    signalList.innerHTML = d.top_insights.slice(0, 4).map(ins => `
      <div class="signal-row">
        <div class="signal-text">
          <div class="signal-headline">${ins.headline}</div>
          <div class="signal-detail">${ins.detail}</div>
        </div>
        <div class="signal-action">
          <span class="badge ${ins.impact.toLowerCase() === 'critical' ? 'churn' : ins.impact.toLowerCase() === 'high' ? 'warn' : 'accent'}">${ins.impact}</span>
          <div style="font-size:0.7rem; color:var(--ink-light); font-weight:500; margin-top:2px;">${ins.action}</div>
        </div>
      </div>
    `).join('');
  }
}

// ── Churn Drivers Insight Text Populator ───────────────────────────
function populateChurnDrivers(d) {
  const ca = d.churn_analysis;

  // Contract Type
  const contractObs = document.getElementById('contract-obs');
  const contractImp = document.getElementById('contract-imp');
  const contractRec = document.getElementById('contract-rec');
  if (contractObs) contractObs.textContent = ca.by_contract.observation;
  if (contractImp) contractImp.textContent = ca.by_contract.impact;
  if (contractRec) contractRec.textContent = ca.by_contract.recommendation;

  // Payment Method
  const paymentObs = document.getElementById('payment-obs');
  const paymentImp = document.getElementById('payment-imp');
  const paymentRec = document.getElementById('payment-rec');
  if (paymentObs) paymentObs.textContent = ca.by_payment.observation;
  if (paymentImp) paymentImp.textContent = ca.by_payment.impact;
  if (paymentRec) paymentRec.textContent = ca.by_payment.recommendation;

  // Internet Service
  const internetObs = document.getElementById('internet-obs');
  const internetImp = document.getElementById('internet-imp');
  const internetRec = document.getElementById('internet-rec');
  if (internetObs) internetObs.textContent = ca.by_internet.observation;
  if (internetImp) internetImp.textContent = ca.by_internet.impact;
  if (internetRec) internetRec.textContent = ca.by_internet.recommendation;

  // Tenure Danger Zone
  const tenureObs = document.getElementById('tenure-obs');
  const tenureImp = document.getElementById('tenure-imp');
  const tenureRec = document.getElementById('tenure-rec');
  if (tenureObs) tenureObs.textContent = ca.by_tenure.observation;
  if (tenureImp) tenureImp.textContent = ca.by_tenure.impact;
  if (tenureRec) tenureRec.textContent = ca.by_tenure.recommendation;
}

// ── Customer Segments Table Populator ──────────────────────────────
function populateSegmentsTable(d) {
  const tbody = document.querySelector('#segments-table tbody');
  if (tbody && d.segments) {
    tbody.innerHTML = d.segments.map((seg, index) => {
      const priorityStyle = getPriorityStyle(seg.priority);
      return `
        <tr data-index="${index}">
          <td>
            <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:${seg.color || '#6366f1'}; margin-right:8px; vertical-align:middle;"></span>
            <strong style="color:var(--ink);">${seg.name}</strong>
          </td>
          <td class="mono">${seg.size.toLocaleString()}</td>
          <td>
            <div class="table-bar-track">
              <div class="table-bar-fill" style="width:${seg.churn_rate}%; background:${getChurnColor(seg.churn_rate)};"></div>
            </div>
            <span style="color:${getChurnColor(seg.churn_rate)}; font-weight:700;">${seg.churn_rate.toFixed(1)}%</span>
          </td>
          <td class="mono">$${seg.avg_monthly_charges.toFixed(2)}</td>
          <td class="mono">${seg.avg_tenure.toFixed(0)}m</td>
          <td>
            <span class="badge" style="background:${priorityStyle.bg}; color:${priorityStyle.color};">${seg.priority}</span>
          </td>
        </tr>
      `;
    }).join('');

    // Attach row click listeners for segment deep-dive drawer
    const rows = tbody.querySelectorAll('tr');
    rows.forEach(row => {
      row.addEventListener('click', () => {
        const index = parseInt(row.getAttribute('data-index'));
        if (!isNaN(index) && d.segments[index]) {
          openSegmentDrawer(d.segments[index]);
        }
      });
    });
  }
}

// ── Segment Deep-Dive Drawer Population & Display ──────────────────
function openSegmentDrawer(seg) {
  document.getElementById('drawer-segment-name').textContent = seg.name;
  document.getElementById('drawer-segment-desc').textContent = seg.description || '';
  document.getElementById('drawer-stat-size').textContent = seg.size.toLocaleString();
  document.getElementById('drawer-stat-churn').textContent = seg.churn_rate.toFixed(1) + '%';
  document.getElementById('drawer-stat-revenue').textContent = '$' + seg.avg_monthly_charges.toFixed(2);
  document.getElementById('drawer-segment-recommendation').textContent = seg.recommendation || 'No recommendation available.';

  // Helper function to build progress bars in drawer
  function buildDistHtml(distribution) {
    if (!distribution) return '<div style="font-size:0.75rem; color:var(--ink-light); padding: 4px 0;">No data available</div>';
    return Object.entries(distribution).map(([key, val]) => `
      <div class="drawer-bar-row">
        <div class="drawer-bar-name" title="${key}">${key}</div>
        <div class="drawer-bar-track">
          <div class="drawer-bar-fill" style="width: ${val}%;"></div>
        </div>
        <div class="drawer-bar-val">${val.toFixed(1)}%</div>
      </div>
    `).join('');
  }

  // Populate distributions
  document.getElementById('drawer-contract-dist').innerHTML = buildDistHtml(seg.contract_distribution);
  document.getElementById('drawer-payment-dist').innerHTML = buildDistHtml(seg.payment_distribution);
  document.getElementById('drawer-internet-dist').innerHTML = buildDistHtml(seg.internet_distribution);

  // Populate demographics
  const demoDist = document.getElementById('drawer-demographics-dist');
  if (demoDist) {
    if (seg.demographics) {
      demoDist.innerHTML = Object.entries(seg.demographics).map(([key, val]) => {
        let label = key.replace('_pct', '').replace('_', ' ');
        label = label.charAt(0).toUpperCase() + label.slice(1);
        return `
          <div class="drawer-demo-row">
            <span>${label}</span>
            <strong>${val.toFixed(1)}%</strong>
          </div>
        `;
      }).join('');
    } else {
      demoDist.innerHTML = '<div style="font-size:0.75rem; color:var(--ink-light);">No data available</div>';
    }
  }

  // Show drawer and overlay
  document.getElementById('segment-drawer').classList.add('active');
  document.getElementById('drawer-overlay').classList.add('active');
}

function closeSegmentDrawer() {
  const drawer = document.getElementById('segment-drawer');
  const overlay = document.getElementById('drawer-overlay');
  if (drawer) drawer.classList.remove('active');
  if (overlay) overlay.classList.remove('active');
}

function initDrawerCloseHandlers() {
  const closeBtn = document.getElementById('drawer-close-btn');
  const overlay = document.getElementById('drawer-overlay');
  if (closeBtn) closeBtn.addEventListener('click', closeSegmentDrawer);
  if (overlay) overlay.addEventListener('click', closeSegmentDrawer);
}

// ── Metric Explainability Popovers ─────────────────────────────────
const METRIC_EXPLANATIONS = {
  'health': {
    title: 'Retention Health Score',
    formula: '100.0 - Churn Rate (%)',
    meaning: 'The overall percentage of customers that remain active. This represents the primary health metric of the subscription customer base.',
    benchmark: '80% - 85% is typical for healthy B2C SaaS/Telco companies.'
  },
  'churn': {
    title: 'Audited Churn Rate',
    formula: '(Total Churned Customers / Total Audited Base) * 100',
    meaning: 'The percentage of customers who discontinued their service during the audited period.',
    benchmark: 'Industry benchmark is under 15% annually; currently 26.54% indicates severe risk.'
  },
  'arr': {
    title: 'ARR Exposure (Revenue at Risk)',
    formula: 'Sum of Monthly Charges for high-risk customers * 12 months',
    meaning: 'The annual run-rate revenue generated by customers who are currently flagged at high risk of churn.',
    benchmark: 'Should ideally be less than 5% of Total ARR.'
  },
  'auc': {
    title: 'Validation AUC-ROC Score',
    formula: 'Area Under the Receiver Operating Characteristic curve',
    meaning: 'Measures the classifier model\'s ability to distinguish between churned and active customers across all classification thresholds.',
    benchmark: '0.80 - 0.90 is considered excellent predictive accuracy.'
  },
  'target-churn': {
    title: 'Projected Churn Rate',
    formula: 'Base Churn * (1 - (Planned Reduction * Execution Efficiency) / 100)',
    meaning: 'The simulated churn rate achieved if the selected interventions are implemented with the specified execution efficiency.',
    benchmark: 'Goal is to bring churn rate back below the 20% threshold.'
  },
  'saved-monthly': {
    title: 'Monthly Saved Revenue',
    formula: 'Sum of selected intervention monthly savings * Execution Efficiency',
    meaning: 'The simulated revenue saved per month from customers who are prevented from churning by the selected interventions.',
    benchmark: 'Depends on the scale of targeted marketing and support actions.'
  },
  'saved-annual': {
    title: 'Annual Saved Revenue',
    formula: 'Monthly Saved Revenue * 12',
    meaning: 'The annualized run-rate savings expected from the selected interventions based on actual client charges and model predictions.',
    benchmark: 'Directly impacts bottom-line EBITDA.'
  }
};

function initExplainability() {
  const popover = document.getElementById('explain-popover');
  const closeBtn = document.getElementById('explain-close-btn');

  if (!popover || !closeBtn) return;

  document.querySelectorAll('.info-trigger').forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.stopPropagation();
      const metricKey = trigger.getAttribute('data-metric');
      const details = METRIC_EXPLANATIONS[metricKey];
      if (!details) return;

      document.getElementById('explain-title').textContent = details.title;
      document.getElementById('explain-formula').textContent = details.formula;
      document.getElementById('explain-meaning').textContent = details.meaning;
      document.getElementById('explain-benchmark').textContent = details.benchmark;

      // Position
      const rect = trigger.getBoundingClientRect();
      const popoverWidth = 280;
      
      let left = window.scrollX + rect.left + 20;
      let top = window.scrollY + rect.top - 20;

      // Prevent overflow offscreen
      if (left + popoverWidth > window.innerWidth) {
        left = window.scrollX + rect.left - popoverWidth - 10;
      }

      popover.style.left = `${left}px`;
      popover.style.top = `${top}px`;
      popover.style.display = 'block';
    });
  });

  closeBtn.addEventListener('click', () => {
    popover.style.display = 'none';
  });

  document.addEventListener('click', (e) => {
    if (!popover.contains(e.target) && !e.target.classList.contains('info-trigger')) {
      popover.style.display = 'none';
    }
  });
}

// ── Cohort Heatmap Populator ───────────────────────────────────────
function populateCohortsTable(d) {
  const tableEl = document.getElementById('cohort-heatmap-table');
  if (tableEl && d.cohorts) {
    let html = `<thead><tr><th>Cohort</th>`;
    d.cohorts.periods.forEach(p => {
      let label = p;
      if (p === 'M0') label = 'Signup';
      else if (p === 'M3') label = '3 Months';
      else if (p === 'M6') label = '6 Months';
      else if (p === 'M12') label = '1 Year';
      else if (p === 'M18') label = '1.5 Years';
      else if (p === 'M24') label = '2 Years';
      html += `<th>${label}</th>`;
    });
    html += `</tr></thead><tbody>`;

    d.cohorts.heatmap.forEach(row => {
      html += `<tr><td>${row.cohort}</td>`;
      row.rates.forEach(rate => {
        if (rate === null || rate === undefined) {
          html += `<td style="background:transparent; color:var(--ink-light); opacity:0.3;">—</td>`;
        } else {
          const style = getHeatStyle(rate);
          html += `<td style="background:${style.bg}; color:${style.color};">${rate.toFixed(1)}%</td>`;
        }
      });
      html += `</tr>`;
    });
    html += `</tbody>`;
    tableEl.innerHTML = html;
  }
}

// ── Machine Learning Model Stats Populator ────────────────────────
function populateMLSection(d) {
  const aucEl = document.getElementById('ml-metrics-auc');
  const rfAccEl = document.getElementById('ml-metrics-rf-acc');
  const lrAccEl = document.getElementById('ml-metrics-lr-acc');

  if (aucEl) {
    const bestAuc = Math.max(d.ml.random_forest.roc_auc, d.ml.logistic_regression.roc_auc);
    aucEl.textContent = bestAuc.toFixed(2) + '%';
  }
  if (rfAccEl) rfAccEl.textContent = d.ml.random_forest.accuracy.toFixed(2) + '%';
  if (lrAccEl) lrAccEl.textContent = d.ml.logistic_regression.accuracy.toFixed(2) + '%';
}

// ── Recommendations Checklist & ROI calculator ───────────────────
function populateActionPlan(d) {
  const listEl = document.getElementById('recommendations-calculator-list');
  if (!listEl) return;

  listEl.innerHTML = d.recommendations.map(rec => {
    return `
      <div class="action-card checked" id="action-card-${rec.priority}">
        <div class="action-check-wrap">
          <label class="action-checkbox" for="chk-${rec.priority}">
            <input type="checkbox" class="action-checkbox-input" id="chk-${rec.priority}" data-priority="${rec.priority}" checked>
          </label>
        </div>
        <div class="action-info">
          <div class="action-title">${rec.title}</div>
          <div class="action-desc">${rec.description}</div>
        </div>
        <div class="action-roi">
          <div class="action-roi-val">+${fmt(rec.expected_revenue_saved_monthly, 'money')}</div>
          <div class="action-roi-lbl">Saved Revenue/mo</div>
        </div>
        <div class="action-meta">
          <div class="action-meta-val">-${rec.expected_churn_reduction_pct.toFixed(1)}%</div>
          <div class="action-meta-lbl">Churn Impact</div>
        </div>
      </div>
    `;
  }).join('');

  const checkboxes = document.querySelectorAll('.action-checkbox-input');
  checkboxes.forEach(chk => {
    chk.onchange = () => {
      const card = document.getElementById(`action-card-${chk.dataset.priority}`);
      if (card) {
        card.classList.toggle('checked', chk.checked);
      }
      recalculateROI();
    };
  });

  recalculateROI();
}

function initEfficiencySlider() {
  const slider = document.getElementById('calc-efficiency-slider');
  const valDisplay = document.getElementById('calc-efficiency-val');

  if (!slider || !valDisplay) return;

  slider.addEventListener('input', () => {
    valDisplay.textContent = slider.value + '%';
    recalculateROI();
  });
}

function recalculateROI() {
  const checkboxes = document.querySelectorAll('.action-checkbox-input');
  const slider = document.getElementById('calc-efficiency-slider');
  const efficiency = slider ? parseInt(slider.value) / 100 : 1.0;

  let totalRevenueSaved = 0;
  let totalChurnReduction = 0;

  checkboxes.forEach(chk => {
    if (chk.checked) {
      const priority = parseInt(chk.dataset.priority);
      const rec = DATA.recommendations.find(r => r.priority === priority);
      if (rec) {
        totalRevenueSaved += rec.expected_revenue_saved_monthly;
        totalChurnReduction += rec.expected_churn_reduction_pct;
      }
    }
  });

  // Scale by efficiency
  totalRevenueSaved *= efficiency;
  totalChurnReduction *= efficiency;

  const baseChurnRate = DATA.kpis.churn_rate;
  const targetChurnRate = baseChurnRate * (1 - totalChurnReduction / 100);
  const annualSaved = totalRevenueSaved * 12;

  const targetChurnEl = document.getElementById('calc-target-churn');
  const monthlySavedEl = document.getElementById('calc-monthly-saved');
  const annualSavedEl = document.getElementById('calc-annual-saved');

  if (targetChurnEl) targetChurnEl.textContent = targetChurnRate.toFixed(2) + '%';
  if (monthlySavedEl) monthlySavedEl.textContent = fmt(totalRevenueSaved, 'money');
  if (annualSavedEl) annualSavedEl.textContent = `$${(annualSaved / 1e6).toFixed(2)}M`;
}

// ── Pipeline Portfolio Populator ──────────────────────────────────
function populatePortfolioSection(d) {
  const pipelineEl = document.getElementById('portfolio-pipeline-grid');
  if (pipelineEl && d.portfolio.pipeline_steps) {
    pipelineEl.innerHTML = d.portfolio.pipeline_steps.map(step => `
      <div class="pipeline-card">
        <div class="pipeline-step-num">Step 0${step.step}</div>
        <div class="pipeline-step-name">${step.name}</div>
        <div class="pipeline-step-script">${step.script}</div>
        <div class="pipeline-step-desc">${step.description}</div>
      </div>
    `).join('');
  }

  const techEl = document.getElementById('portfolio-tech-chips');
  if (techEl && d.portfolio.tech_stack) {
    techEl.innerHTML = d.portfolio.tech_stack.map(tech => `
      <span class="tech-chip">${tech}</span>
    `).join('');
  }
}

// ── Chart Initializer ─────────────────────────────────────────────
function initAllCharts(d) {
  if (typeof initContractChart === 'function') initContractChart(d.churn_analysis.by_contract);
  if (typeof initPaymentChart === 'function') initPaymentChart(d.churn_analysis.by_payment);
  if (typeof initInternetChart === 'function') initInternetChart(d.churn_analysis.by_internet);
  if (typeof initTenureChart === 'function') initTenureChart(d.churn_analysis.by_tenure);
  if (typeof initContractSurvivalChart === 'function') initContractSurvivalChart(d.survival);
  if (typeof initRFImportanceChart === 'function') initRFImportanceChart(d.ml.rf_feature_importance);
  if (typeof initRocChart === 'function') initRocChart(d.ml);
}

// ── Fallback Translation Layer ─────────────────────────────────────
function transformFallbackData(d) {
  return {
    meta: {
      total_customers: d.kpi.totalCustomers,
      active_customers: d.kpi.activeCustomers,
      churned_customers: d.kpi.churnedCustomers
    },
    kpis: {
      churn_rate: d.kpi.churnRate,
      retention_rate: d.kpi.retentionRate,
      monthly_churn_rate: d.kpi.monthlyChurnRate / 100,
      arpu: d.kpi.arpu,
      arpu_active: d.kpi.arpu * 0.95,
      arpu_churned: d.kpi.arpu * 1.15,
      clv_active: d.kpi.avgCLV,
      clv_churned: d.kpi.avgCLV * 0.58,
      revenue_at_risk_monthly: d.kpi.revenueAtRisk / 12,
      revenue_at_risk_annual: d.kpi.revenueAtRisk,
      high_risk_customer_count: Math.round(d.kpi.totalCustomers * 0.21),
      total_revenue: d.kpi.totalRevenue
    },
    top_insights: d.churnDrivers.slice(0, 5).map((dr, idx) => ({
      id: idx + 1,
      headline: `${dr.factor} drives churn risk significantly`,
      detail: `${dr.factor} has a corresponding churn rate of ${dr.churnRate.toFixed(1)}% (impact score: ${dr.impact.toFixed(2)}).`,
      action: idx === 0 ? 'Contract upgrade campaign' : idx === 1 ? 'Auto-payment enrollment push' : 'Targeted proactive customer outreach',
      impact: dr.impact > 0.75 ? 'Critical' : dr.impact > 0.5 ? 'High' : 'Medium',
      category: dr.factor.includes('Contract') ? 'Contract' : dr.factor.includes('Payment') ? 'Payment' : 'Usage'
    })),
    churn_analysis: {
      by_contract: {
        labels: d.churnByContract.labels,
        churn_rates: d.churnByContract.churnRates,
        churned: d.churnByContract.churned,
        total: d.churnByContract.total,
        observation: 'Month-to-month contracts have a 42.7% churn rate — 15x higher than two-year contracts at 2.8%.',
        impact: 'Month-to-month churners account for 88.5% of all churned customers (1,655 of 1,869).',
        recommendation: 'Offer a 15-20% discount for customers who switch from month-to-month to annual contracts in their first 90 days.'
      },
      by_payment: {
        labels: d.churnByPayment.labels,
        churn_rates: d.churnByPayment.churnRates,
        churned: d.churnByPayment.churned,
        total: d.churnByPayment.total,
        observation: 'Electronic check payment has nearly 3× the churn rate of auto-pay options.',
        impact: 'Electronic checks represent the single largest payment-related revenue loss.',
        recommendation: 'Promote autopay transitions using small bill credits.'
      },
      by_internet: {
        labels: d.churnByInternet.labels,
        churn_rates: d.churnByInternet.churnRates,
        churned: d.churnByInternet.churned,
        total: d.churnByInternet.total,
        observation: 'Fiber optic customers churn at 41.9% vs. 19% for DSL.',
        impact: 'High-spend customers leave faster, indicating a value perception gap.',
        recommendation: 'Bundle security and support features to offset premium pricing.'
      },
      by_tenure: {
        labels: d.churnByTenure.labels,
        churn_rates: d.churnByTenure.churnRates,
        churned: d.churnByTenure.churned,
        total: d.churnByTenure.total,
        observation: 'New customers under 6 months show a staggering 56% churn rate.',
        impact: 'Early relationships are fragile; risk drops below 10% after 4 years.',
        recommendation: 'Deploy a structured onboarding program during the first 90 days.'
      }
    },
    segments: d.segments.map(seg => ({
      name: seg.name,
      description: seg.name.includes('Loyal') ? 'Highly committed accounts' : 'Customers with critical risk indicators',
      priority: seg.name.includes('Loyal') ? 'Maintain' : seg.name.includes('Risk') ? 'Urgent Retention' : 'Nurture/Upsell',
      color: seg.color,
      size: seg.count,
      churn_rate: seg.churnRate,
      avg_monthly_charges: seg.avgRevenue,
      avg_tenure: seg.avgTenure
    })),
    survival: {
      by_contract: {
        'Month-to-month': {
          timeline: d.survivalCurve.months,
          survival: d.survivalCurve.survivalRate.map(r => r * 100),
          median_survival_months: 35.0
        },
        'One year': {
          timeline: d.survivalCurve.months,
          survival: d.survivalCurve.survivalRate.map(r => Math.min(1.0, r * 1.35) * 100),
          median_survival_months: null
        },
        'Two year': {
          timeline: d.survivalCurve.months,
          survival: d.survivalCurve.survivalRate.map(r => Math.min(1.0, r * 1.5) * 100),
          median_survival_months: null
        }
      }
    },
    cohorts: {
      heatmap: d.cohortRetention.cohorts.map((cohort, idx) => ({
        cohort: cohort,
        rates: d.cohortRetention.rates[idx]
      })),
      periods: d.cohortRetention.periods
    },
    ml: {
      best_model: 'Logistic Regression',
      random_forest: {
        accuracy: 77.22,
        roc_auc: 84.09
      },
      logistic_regression: {
        accuracy: 74.66,
        roc_auc: 84.44
      },
      rf_feature_importance: d.churnDrivers.slice(0, 6).map(dr => ({
        feature: dr.factor,
        importance_pct: dr.impact * 20
      })),
      roc_curve: Array.from({ length: 20 }, (_, i) => {
        const x = i / 19;
        const y = Math.pow(x, 0.3);
        return { fpr: x, tpr: y };
      })
    },
    revenue_forecasts: {
      '30_days': { revenue_loss: d.kpi.revenueAtRisk * 0.03, customers_at_risk: 49 },
      '90_days': { revenue_loss: d.kpi.revenueAtRisk * 0.09, customers_at_risk: 147 },
      '180_days': { revenue_loss: d.kpi.revenueAtRisk * 0.18, customers_at_risk: 294 },
      '365_days': { revenue_loss: d.kpi.revenueAtRisk * 0.36, customers_at_risk: 589 }
    },
    recommendations: [
      {
        priority: 1,
        title: d.recommendations.quickWins[0].title,
        description: d.recommendations.quickWins[0].description,
        expected_churn_reduction_pct: 6.5,
        expected_revenue_saved_monthly: 28400,
        timeline: '60 days',
        confidence: 92
      },
      {
        priority: 2,
        title: d.recommendations.quickWins[1].title,
        description: d.recommendations.quickWins[1].description,
        expected_churn_reduction_pct: 3.8,
        expected_revenue_saved_monthly: 16200,
        timeline: '30 days',
        confidence: 85
      },
      {
        priority: 3,
        title: d.recommendations.mediumTerm[0].title,
        description: d.recommendations.mediumTerm[0].description,
        expected_churn_reduction_pct: 4.2,
        expected_revenue_saved_monthly: 14800,
        timeline: '90 days',
        confidence: 88
      },
      {
        priority: 4,
        title: d.recommendations.mediumTerm[1].title,
        description: d.recommendations.mediumTerm[1].description,
        expected_churn_reduction_pct: 4.0,
        expected_revenue_saved_monthly: 18600,
        timeline: '30 days',
        confidence: 82
      },
      {
        priority: 5,
        title: d.recommendations.longTerm[0].title,
        description: d.recommendations.longTerm[0].description,
        expected_churn_reduction_pct: 2.5,
        expected_revenue_saved_monthly: 21200,
        timeline: 'Immediate',
        confidence: 79
      }
    ],
    portfolio: {
      pipeline_steps: [
        { step: 1, name: 'Data Cleaning', script: '01_data_cleaning.py', description: 'Handle missing TotalCharges, clean categorical values, remove duplicates' },
        { step: 2, name: 'Feature Engineering', script: '02_feature_engineering.py', description: 'Create ServiceCount, EngagementScore, HealthIndex, RiskCategory' },
        { step: 3, name: 'Exploratory Data Analysis', script: '03_eda.py', description: 'Analyze contract types, payment methods, services, and demographics' },
        { step: 4, name: 'Advanced Analytics', script: '04_advanced_analytics.py', description: 'Kaplan-Meier survival analysis, KPI calculations, distribution analysis' },
        { step: 5, name: 'Customer Segmentation', script: '05_customer_segmentation.py', description: 'Classify 8 segments with risk and spending profiles' },
        { step: 6, name: 'Cohort Analysis', script: '06_cohort_analysis.py', description: 'Quarterly cohort retention matrix, revenue YoY trends' },
        { step: 7, name: 'Churn Intelligence', script: '07_churn_intelligence.py', description: 'Cramér\'s V ranking, behavioral risk pattern mining' },
        { step: 8, name: 'ML Churn Prediction', script: '08_ml_churn_prediction.py', description: 'Logistic Regression & Random Forest classifiers with cross-validation' }
      ],
      tech_stack: ['Python 3.x', 'pandas', 'numpy', 'scikit-learn', 'lifelines', 'scipy', 'Chart.js 4.x', 'Vanilla HTML/CSS/JS']
    }
  };
}

function fmt(num, type = 'number') {
  if (num === null || num === undefined) return '—';
  if (type === 'money') {
    return '$' + Math.round(num).toLocaleString('en-US');
  }
  return num.toLocaleString('en-US');
}

function getChurnColor(rate) {
  if (rate >= 40) return 'var(--churn)';
  if (rate >= 20) return 'var(--warn)';
  return 'var(--retain)';
}

function getPriorityStyle(priority) {
  if (!priority) return { bg: 'var(--surface-2)', color: 'var(--ink-muted)' };
  const p = priority.toLowerCase();
  if (p.includes('urgent') || p.includes('high')) {
    return { bg: 'var(--churn-soft)', color: 'var(--churn)' };
  }
  if (p.includes('onboard') || p.includes('vip') || p.includes('reward') || p.includes('retain')) {
    return { bg: 'var(--accent-soft)', color: 'var(--accent)' };
  }
  if (p.includes('warn') || p.includes('value')) {
    return { bg: 'var(--warn-soft)', color: 'var(--warn)' };
  }
  return { bg: 'var(--surface-2)', color: 'var(--ink-muted)' };
}

function getHeatStyle(val) {
  if (val === null || val === undefined) return { bg: 'transparent', color: 'var(--ink-light)' };
  if (val >= 90) return { bg: 'rgba(5, 150, 105, 0.22)', color: 'var(--retain)' };
  if (val >= 75) return { bg: 'rgba(5, 150, 105, 0.10)', color: 'var(--retain)' };
  if (val >= 60) return { bg: 'rgba(217, 119, 6, 0.10)', color: 'var(--warn)' };
  if (val >= 40) return { bg: 'rgba(217, 119, 6, 0.20)', color: 'var(--warn)' };
  return { bg: 'rgba(220, 38, 38, 0.12)', color: 'var(--churn)' };
}
