/* ═══════════════════════════════════════════════════════════════════
   RetentionIQ — charts.js
   All Chart.js 4.x chart configurations
   Premium light theme: minimal gridlines, custom tooltips, clean axes
   Future Interns Task 2: Customer Retention & Churn Analysis
   ═══════════════════════════════════════════════════════════════════ */

'use strict';

// ── Global Chart Defaults ─────────────────────────────────────────
Chart.defaults.font.family = "'Inter', -apple-system, sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = '#94a3b8';
Chart.defaults.plugins.legend.display = false;
Chart.defaults.plugins.tooltip.backgroundColor = '#ffffff';
Chart.defaults.plugins.tooltip.titleColor = '#0f172a';
Chart.defaults.plugins.tooltip.bodyColor = '#475569';
Chart.defaults.plugins.tooltip.borderColor = '#e2e8f0';
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.padding = 10;
Chart.defaults.plugins.tooltip.cornerRadius = 8;
Chart.defaults.plugins.tooltip.titleFont = { weight: '600', size: 12 };
Chart.defaults.plugins.tooltip.bodyFont = { size: 11 };
Chart.defaults.plugins.tooltip.boxShadow = '0 4px 12px rgba(0,0,0,0.08)';
Chart.defaults.animation.duration = 900;
Chart.defaults.animation.easing = 'easeOutQuart';

// Shared axis config
const AXIS_GRID = { color: 'rgba(0,0,0,0.04)', drawBorder: false };
const AXIS_GRID_NONE = { display: false };
const AXIS_TICK = { color: '#94a3b8', font: { size: 11 } };

// Color palette
const C = {
  rose:    '#f43f5e',
  emerald: '#10b981',
  indigo:  '#6366f1',
  amber:   '#f59e0b',
  sky:     '#0ea5e9',
  violet:  '#8b5cf6',
  slate:   '#64748b',
  roseAlpha:    (a) => `rgba(244,63,94,${a})`,
  emeraldAlpha: (a) => `rgba(16,185,129,${a})`,
  indigoAlpha:  (a) => `rgba(99,102,241,${a})`,
  amberAlpha:   (a) => `rgba(245,158,11,${a})`,
  skyAlpha:     (a) => `rgba(14,165,233,${a})`,
};

// Track chart instances to destroy before re-init
const chartInstances = {};

function getCtx(id) {
  const canvas = document.getElementById(id);
  if (!canvas) return null;
  if (chartInstances[id]) {
    chartInstances[id].destroy();
    delete chartInstances[id];
  }
  return canvas.getContext('2d');
}

function registerChart(id, instance) {
  if (instance) chartInstances[id] = instance;
}

// ── PAGE 1: OVERVIEW CHARTS ───────────────────────────────────────

function initChurnDonut(kpis) {
  const ctx = getCtx('chart-churn-donut');
  if (!ctx) return;

  const churned = kpis?.churn_rate || 26.54;
  const retained = 100 - churned;

  const chart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Churned', 'Retained'],
      datasets: [{
        data: [churned, retained],
        backgroundColor: [C.rose, C.emerald],
        borderColor: ['#fff', '#fff'],
        borderWidth: 3,
        hoverOffset: 4
      }]
    },
    options: {
      responsive: false,
      cutout: '72%',
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.label}: ${ctx.parsed.toFixed(2)}%`
          }
        }
      }
    }
  });
  registerChart('chart-churn-donut', chart);

  // Legend
  const legendEl = document.getElementById('donut-legend');
  if (legendEl) {
    legendEl.innerHTML = `
      <div class="legend-item">
        <div class="legend-dot" style="background:${C.rose}"></div>
        <span class="legend-label">Churned Customers</span>
        <span class="legend-value">${churned.toFixed(2)}%</span>
      </div>
      <div class="legend-item">
        <div class="legend-dot" style="background:${C.emerald}"></div>
        <span class="legend-label">Active Customers</span>
        <span class="legend-value">${retained.toFixed(2)}%</span>
      </div>
      <div class="legend-item">
        <div class="legend-dot" style="background:var(--border)"></div>
        <span class="legend-label">Total Dataset</span>
        <span class="legend-value">7,043</span>
      </div>
      <div class="legend-item">
        <div class="legend-dot" style="background:${C.rose}"></div>
        <span class="legend-label">Churned Count</span>
        <span class="legend-value">1,869</span>
      </div>
      <div class="legend-item">
        <div class="legend-dot" style="background:${C.emerald}"></div>
        <span class="legend-label">Active Count</span>
        <span class="legend-value">5,174</span>
      </div>`;
  }
}

function initContractBar(data) {
  const ctx = getCtx('chart-contract-bar');
  if (!ctx || !data) return;

  const chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.labels || [],
      datasets: [{
        label: 'Churn Rate (%)',
        data: data.churn_rates || [],
        backgroundColor: (data.churn_rates || []).map(v =>
          v > 35 ? C.roseAlpha(0.8) : v > 15 ? C.amberAlpha(0.8) : C.emeraldAlpha(0.8)
        ),
        borderColor: (data.churn_rates || []).map(v =>
          v > 35 ? C.rose : v > 15 ? C.amber : C.emerald
        ),
        borderWidth: 1.5,
        borderRadius: 6,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` Churn Rate: ${ctx.parsed.x.toFixed(2)}%`,
            afterLabel: (ctx) => {
              const i = ctx.dataIndex;
              const c = (data.churned||[])[i];
              const t = (data.total||[])[i];
              return c && t ? ` ${c.toLocaleString()} churned of ${t.toLocaleString()}` : '';
            }
          }
        }
      },
      scales: {
        x: {
          grid: AXIS_GRID,
          ticks: { ...AXIS_TICK, callback: v => v + '%' },
          max: 55
        },
        y: { grid: AXIS_GRID_NONE, ticks: AXIS_TICK }
      }
    }
  });
  registerChart('chart-contract-bar', chart);
}

function initArpuCompare(kpis) {
  const ctx = getCtx('chart-arpu-compare');
  if (!ctx) return;

  const chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Active Customers', 'Churned Customers'],
      datasets: [{
        label: 'ARPU ($/month)',
        data: [kpis?.arpu_active || 61.27, kpis?.arpu_churned || 74.44],
        backgroundColor: [C.emeraldAlpha(0.75), C.roseAlpha(0.75)],
        borderColor: [C.emerald, C.rose],
        borderWidth: 1.5,
        borderRadius: 8,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: { label: ctx => ` ARPU: $${ctx.parsed.y.toFixed(2)}/month` }
        }
      },
      scales: {
        x: { grid: AXIS_GRID_NONE, ticks: AXIS_TICK },
        y: {
          grid: AXIS_GRID,
          ticks: { ...AXIS_TICK, callback: v => '$' + v },
          min: 50, max: 85
        }
      }
    }
  });
  registerChart('chart-arpu-compare', chart);
}

// ── PAGE 2: WHY CHURN CHARTS ──────────────────────────────────────

function initDriversBar(drivers) {
  const ctx = getCtx('chart-drivers');
  if (!ctx || !drivers || !drivers.length) return;

  const top = drivers.slice(0, 10);
  const chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: top.map(d => d.factor),
      datasets: [{
        label: 'Impact Score',
        data: top.map(d => d.impact_score || d.correlation || 0),
        backgroundColor: top.map(d => (d.impact_score || 0) > 0.3 ? C.indigoAlpha(0.75) : C.skyAlpha(0.65)),
        borderColor: top.map(d => (d.impact_score || 0) > 0.3 ? C.indigo : C.sky),
        borderWidth: 1.5,
        borderRadius: 5,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` Impact Score: ${ctx.parsed.x.toFixed(3)}`,
            afterLabel: ctx => {
              const d = top[ctx.dataIndex];
              return ` Churn Rate: ${(d.churn_rate||0).toFixed(1)}%`;
            }
          }
        }
      },
      scales: {
        x: { grid: AXIS_GRID, ticks: AXIS_TICK },
        y: { grid: AXIS_GRID_NONE, ticks: { ...AXIS_TICK, font: { size: 10 } } }
      }
    }
  });
  registerChart('chart-drivers', chart);
}

function initPaymentBar(data) {
  const ctx = getCtx('chart-payment');
  if (!ctx || !data) return;

  const chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.labels || [],
      datasets: [{
        label: 'Churn Rate (%)',
        data: data.churn_rates || [],
        backgroundColor: (data.churn_rates||[]).map(v => v > 30 ? C.roseAlpha(0.75) : v > 20 ? C.amberAlpha(0.7) : C.skyAlpha(0.7)),
        borderColor: (data.churn_rates||[]).map(v => v > 30 ? C.rose : v > 20 ? C.amber : C.sky),
        borderWidth: 1.5,
        borderRadius: 6,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => ` Churn Rate: ${ctx.parsed.x.toFixed(2)}%`,
            afterLabel: ctx => {
              const i = ctx.dataIndex;
              const c = (data.churned||[])[i];
              return c ? ` ${c.toLocaleString()} churned` : '';
            }
          }
        }
      },
      scales: {
        x: { grid: AXIS_GRID, ticks: { ...AXIS_TICK, callback: v => v + '%' }, max: 55 },
        y: { grid: AXIS_GRID_NONE, ticks: { ...AXIS_TICK, font: { size: 10 } } }
      }
    }
  });
  registerChart('chart-payment', chart);
}

function initInternetBar(data) {
  const ctx = getCtx('chart-internet');
  if (!ctx || !data) return;

  const chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.labels || [],
      datasets: [{
        label: 'Churn Rate (%)',
        data: data.churn_rates || [],
        backgroundColor: [C.roseAlpha(0.75), C.amberAlpha(0.7), C.emeraldAlpha(0.7)],
        borderColor: [C.rose, C.amber, C.emerald],
        borderWidth: 1.5,
        borderRadius: 6,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.y.toFixed(2)}% churn rate` } }
      },
      scales: {
        x: { grid: AXIS_GRID_NONE, ticks: { ...AXIS_TICK, font: {size:10} } },
        y: { grid: AXIS_GRID, ticks: { ...AXIS_TICK, callback: v => v+'%' }, max: 55 }
      }
    }
  });
  registerChart('chart-internet', chart);
}

function initSeniorDonut(data) {
  const ctx = getCtx('chart-senior');
  if (!ctx || !data) return;

  const chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.labels || [],
      datasets: [{
        label: 'Churn Rate (%)',
        data: data.churn_rates || [],
        backgroundColor: [C.skyAlpha(0.7), C.roseAlpha(0.75)],
        borderColor: [C.sky, C.rose],
        borderWidth: 1.5,
        borderRadius: 6,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: {display:false}, tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.y.toFixed(2)}% churn` } } },
      scales: {
        x: { grid: AXIS_GRID_NONE, ticks: AXIS_TICK },
        y: { grid: AXIS_GRID, ticks: { ...AXIS_TICK, callback: v => v+'%' }, max: 55 }
      }
    }
  });
  registerChart('chart-senior', chart);
}

function initGenderDonut(data) {
  const ctx = getCtx('chart-gender');
  if (!ctx || !data) return;

  const chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.labels || [],
      datasets: [{
        label: 'Churn Rate (%)',
        data: data.churn_rates || [26.16, 26.92],
        backgroundColor: [C.skyAlpha(0.6), C.violetAlpha ? C.violetAlpha(0.6) : 'rgba(139,92,246,0.6)'],
        borderColor: [C.sky, C.violet],
        borderWidth: 1.5,
        borderRadius: 6,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: {display:false}, tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.y.toFixed(2)}% churn` } } },
      scales: {
        x: { grid: AXIS_GRID_NONE, ticks: AXIS_TICK },
        y: { grid: AXIS_GRID, ticks: { ...AXIS_TICK, callback: v => v+'%' }, min: 24, max: 30 }
      }
    }
  });
  registerChart('chart-gender', chart);
}

function initTenureLine(data) {
  const ctx = getCtx('chart-tenure-line');
  if (!ctx || !data) return;

  const chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.labels || [],
      datasets: [{
        label: 'Churn Rate (%)',
        data: data.churn_rates || [],
        borderColor: C.rose,
        backgroundColor: C.roseAlpha(0.08),
        borderWidth: 2.5,
        pointBackgroundColor: C.rose,
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 6,
        pointHoverRadius: 8,
        tension: 0.35,
        fill: true
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => ` Churn Rate: ${ctx.parsed.y.toFixed(2)}%` } }
      },
      scales: {
        x: { grid: AXIS_GRID_NONE, ticks: AXIS_TICK },
        y: {
          grid: AXIS_GRID,
          ticks: { ...AXIS_TICK, callback: v => v+'%' },
          min: 0, max: 65
        }
      }
    }
  });
  registerChart('chart-tenure-line', chart);
}

function initChargesBar(data) {
  const ctx = getCtx('chart-charges');
  if (!ctx || !data) return;

  const chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.ranges || [],
      datasets: [
        {
          label: 'Churned',
          data: data.churned || [],
          backgroundColor: C.roseAlpha(0.7),
          borderColor: C.rose,
          borderWidth: 1,
          borderRadius: 4,
          borderSkipped: false,
        },
        {
          label: 'Active',
          data: data.active || [],
          backgroundColor: C.emeraldAlpha(0.55),
          borderColor: C.emerald,
          borderWidth: 1,
          borderRadius: 4,
          borderSkipped: false,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top',
          align: 'end',
          labels: { boxWidth: 10, boxHeight: 10, padding: 16, font: { size: 11 }, color: '#475569' }
        }
      },
      scales: {
        x: { grid: AXIS_GRID_NONE, ticks: AXIS_TICK },
        y: { grid: AXIS_GRID, ticks: AXIS_TICK }
      }
    }
  });
  registerChart('chart-charges', chart);
}

// ── PAGE 3: WHO CHURNS CHARTS ─────────────────────────────────────

function initSegmentBubble(segments) {
  const ctx = getCtx('chart-segment-bubble');
  if (!ctx || !segments || !segments.length) return;

  const chart = new Chart(ctx, {
    type: 'bubble',
    data: {
      datasets: segments.slice(0, 8).map(seg => ({
        label: seg.name,
        data: [{
          x: seg.avg_monthly_charges || 0,
          y: seg.churn_rate || 0,
          r: Math.sqrt(seg.size || 100) / 4
        }],
        backgroundColor: seg.color ? seg.color + 'bb' : C.indigoAlpha(0.7),
        borderColor: seg.color || C.indigo,
        borderWidth: 1.5,
      }))
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'bottom',
          labels: { boxWidth: 8, boxHeight: 8, padding: 10, font: { size: 10 }, color: '#475569' }
        },
        tooltip: {
          callbacks: {
            label: ctx => {
              const d = ctx.raw;
              return [
                ` ${ctx.dataset.label}`,
                ` Avg Revenue: $${d.x.toFixed(2)}/mo`,
                ` Churn Rate: ${d.y.toFixed(1)}%`
              ];
            }
          }
        }
      },
      scales: {
        x: {
          grid: AXIS_GRID,
          ticks: { ...AXIS_TICK, callback: v => '$' + v },
          title: { display: true, text: 'Avg Monthly Revenue ($)', color: '#94a3b8', font: { size: 11 } }
        },
        y: {
          grid: AXIS_GRID,
          ticks: { ...AXIS_TICK, callback: v => v + '%' },
          title: { display: true, text: 'Churn Rate (%)', color: '#94a3b8', font: { size: 11 } }
        }
      }
    }
  });
  registerChart('chart-segment-bubble', chart);
}

function initRocCurve(rocData) {
  const ctx = getCtx('chart-roc');
  if (!ctx) return;

  const points = (rocData || []).filter(p => p.fpr !== undefined && p.tpr !== undefined);
  points.sort((a, b) => a.fpr - b.fpr);

  const chart = new Chart(ctx, {
    type: 'line',
    data: {
      datasets: [
        {
          label: 'ROC Curve (Random Forest)',
          data: points.map(p => ({ x: p.fpr, y: p.tpr })),
          borderColor: C.indigo,
          backgroundColor: C.indigoAlpha(0.06),
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.3,
          fill: true
        },
        {
          label: 'Random Classifier',
          data: [{ x: 0, y: 0 }, { x: 1, y: 1 }],
          borderColor: '#e2e8f0',
          borderWidth: 1.5,
          borderDash: [5, 5],
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'bottom',
          labels: { boxWidth: 10, boxHeight: 10, padding: 12, font: { size: 11 }, color: '#475569' }
        },
        tooltip: { callbacks: { label: ctx => ` TPR: ${ctx.parsed.y.toFixed(3)}, FPR: ${ctx.parsed.x.toFixed(3)}` } }
      },
      scales: {
        x: {
          type: 'linear', min: 0, max: 1,
          grid: AXIS_GRID, ticks: AXIS_TICK,
          title: { display: true, text: 'False Positive Rate', color: '#94a3b8', font: { size: 11 } }
        },
        y: {
          type: 'linear', min: 0, max: 1,
          grid: AXIS_GRID, ticks: AXIS_TICK,
          title: { display: true, text: 'True Positive Rate', color: '#94a3b8', font: { size: 11 } }
        }
      }
    }
  });
  registerChart('chart-roc', chart);
}

// ── PAGE 4: LIFETIME & COHORTS CHARTS ────────────────────────────

function initSurvivalChart(surv) {
  const ctx = getCtx('chart-survival');
  if (!ctx || !surv) return;

  const byContract = surv.by_contract || {};
  const contractColors = {
    'Month-to-month': { line: C.rose, bg: C.roseAlpha(0.05) },
    'One year':       { line: C.amber, bg: C.amberAlpha(0.05) },
    'Two year':       { line: C.emerald, bg: C.emeraldAlpha(0.05) }
  };

  const datasets = [];

  // Overall survival with CI
  const overall = surv.overall || {};
  if (overall.timeline && overall.survival_pct) {
    const tl = overall.timeline;
    const sf = overall.survival_pct;
    const cl = overall.ci_lower || [];
    const cu = overall.ci_upper || [];

    if (cl.length && cu.length) {
      datasets.push({
        label: 'CI Upper',
        data: tl.map((t, i) => ({ x: t, y: cu[i] || null })),
        borderColor: 'transparent',
        backgroundColor: C.indigoAlpha(0.06),
        borderWidth: 0,
        pointRadius: 0,
        fill: '+1',
        tension: 0.3
      });
      datasets.push({
        label: 'CI Lower',
        data: tl.map((t, i) => ({ x: t, y: cl[i] || null })),
        borderColor: 'transparent',
        backgroundColor: 'transparent',
        borderWidth: 0,
        pointRadius: 0,
        fill: false,
        tension: 0.3
      });
    }
  }

  // Per-contract curves
  Object.entries(byContract).forEach(([contract, cdata]) => {
    if (!cdata.timeline || !cdata.survival) return;
    const colors = contractColors[contract] || { line: C.slate, bg: 'transparent' };
    datasets.push({
      label: contract,
      data: cdata.timeline.map((t, i) => ({ x: t, y: cdata.survival[i] })),
      borderColor: colors.line,
      backgroundColor: colors.bg,
      borderWidth: 2,
      pointRadius: 0,
      tension: 0.3,
      fill: false
    });
  });

  // If no by-contract data, use overall
  if (datasets.length === 0 && overall.timeline) {
    datasets.push({
      label: 'Overall Survival',
      data: overall.timeline.map((t, i) => ({ x: t, y: overall.survival_pct[i] })),
      borderColor: C.indigo,
      backgroundColor: C.indigoAlpha(0.06),
      borderWidth: 2.5,
      pointRadius: 0,
      tension: 0.3,
      fill: true
    });
  }

  const chart = new Chart(ctx, {
    type: 'line',
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      parsing: false,
      plugins: {
        legend: {
          display: true,
          position: 'bottom',
          labels: {
            filter: item => !['CI Upper','CI Lower'].includes(item.text),
            boxWidth: 12, boxHeight: 2, padding: 14, font: { size: 11 }, color: '#475569'
          }
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          filter: item => !['CI Upper','CI Lower'].includes(item.dataset.label),
          callbacks: {
            title: items => `Month ${items[0]?.parsed.x}`,
            label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y?.toFixed(1)}%`
          }
        }
      },
      scales: {
        x: {
          type: 'linear',
          grid: AXIS_GRID,
          ticks: { ...AXIS_TICK, callback: v => `M${v}` },
          title: { display: true, text: 'Months since joining', color: '#94a3b8', font: { size: 11 } }
        },
        y: {
          grid: AXIS_GRID,
          ticks: { ...AXIS_TICK, callback: v => v + '%' },
          min: 0, max: 100,
          title: { display: true, text: 'Survival Probability (%)', color: '#94a3b8', font: { size: 11 } }
        }
      }
    }
  });
  registerChart('chart-survival', chart);
}

function initCohortTrends(cohortData) {
  const ctx = getCtx('chart-cohort-trends');
  if (!ctx) return;

  const yearly = (cohortData.yearly || []).filter(y => y.customers > 10);

  const chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: yearly.map(y => y.year),
      datasets: [
        {
          label: 'Retention Rate (%)',
          data: yearly.map(y => 100 - (y.churn_rate || 0)),
          backgroundColor: C.emeraldAlpha(0.7),
          borderColor: C.emerald,
          borderWidth: 1.5,
          borderRadius: 5,
          borderSkipped: false,
          yAxisID: 'y'
        },
        {
          label: 'Churn Rate (%)',
          data: yearly.map(y => y.churn_rate || 0),
          backgroundColor: C.roseAlpha(0.65),
          borderColor: C.rose,
          borderWidth: 1.5,
          borderRadius: 5,
          borderSkipped: false,
          yAxisID: 'y'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top',
          align: 'end',
          labels: { boxWidth: 10, boxHeight: 10, padding: 12, font: { size: 11 }, color: '#475569' }
        }
      },
      scales: {
        x: { grid: AXIS_GRID_NONE, ticks: AXIS_TICK },
        y: { grid: AXIS_GRID, ticks: { ...AXIS_TICK, callback: v => v + '%' }, max: 100 }
      }
    }
  });
  registerChart('chart-cohort-trends', chart);
}

function initTenureBySegment(segments) {
  const ctx = getCtx('chart-tenure-segment');
  if (!ctx || !segments) return;

  const sorted = [...segments].sort((a, b) => (b.avg_tenure || 0) - (a.avg_tenure || 0)).slice(0, 7);

  const chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: sorted.map(s => s.name),
      datasets: [{
        label: 'Avg Tenure (months)',
        data: sorted.map(s => s.avg_tenure || 0),
        backgroundColor: sorted.map(s => s.color ? s.color + 'bb' : C.indigoAlpha(0.7)),
        borderColor: sorted.map(s => s.color || C.indigo),
        borderWidth: 1.5,
        borderRadius: 5,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: { legend: {display:false}, tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.x.toFixed(1)} months` } } },
      scales: {
        x: { grid: AXIS_GRID, ticks: { ...AXIS_TICK, callback: v => v + 'mo' } },
        y: { grid: AXIS_GRID_NONE, ticks: { ...AXIS_TICK, font: { size: 10 } } }
      }
    }
  });
  registerChart('chart-tenure-segment', chart);
}

// ── PAGE 5: RECOMMENDATIONS CHARTS ───────────────────────────────

function initRecImpactChart(recs) {
  const ctx = getCtx('chart-rec-impact');
  if (!ctx || !recs) return;

  const chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: recs.map(r => r.title.length > 25 ? r.title.slice(0, 22) + '...' : r.title),
      datasets: [{
        label: 'Expected Churn Reduction (%)',
        data: recs.map(r => r.expected_churn_reduction_pct || 0),
        backgroundColor: C.indigoAlpha(0.75),
        borderColor: C.indigo,
        borderWidth: 1.5,
        borderRadius: 5,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: { legend: {display:false}, tooltip: { callbacks: { label: ctx => ` -${ctx.parsed.x.toFixed(1)}% churn` } } },
      scales: {
        x: { grid: AXIS_GRID, ticks: { ...AXIS_TICK, callback: v => '-' + v + '%' } },
        y: { grid: AXIS_GRID_NONE, ticks: { ...AXIS_TICK, font: { size: 10 } } }
      }
    }
  });
  registerChart('chart-rec-impact', chart);
}

function initRecRevenueChart(recs) {
  const ctx = getCtx('chart-rec-revenue');
  if (!ctx || !recs) return;

  const chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: recs.map(r => r.title.length > 25 ? r.title.slice(0, 22) + '...' : r.title),
      datasets: [{
        label: 'Revenue Saved ($/mo)',
        data: recs.map(r => r.expected_revenue_saved_monthly || 0),
        backgroundColor: C.emeraldAlpha(0.75),
        borderColor: C.emerald,
        borderWidth: 1.5,
        borderRadius: 5,
        borderSkipped: false,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: { legend: {display:false}, tooltip: { callbacks: { label: ctx => ` $${ctx.parsed.x.toLocaleString()}/month` } } },
      scales: {
        x: { grid: AXIS_GRID, ticks: { ...AXIS_TICK, callback: v => '$' + (v/1000).toFixed(0) + 'K' } },
        y: { grid: AXIS_GRID_NONE, ticks: { ...AXIS_TICK, font: { size: 10 } } }
      }
    }
  });
  registerChart('chart-rec-revenue', chart);
}
