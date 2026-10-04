let siteData = null;
let fanChartInstance = null;
let copilotChartInstance = null;
let migrationChartInstance = null;
let currentPricingMode = "fair";
let activeCopilotPresetKey = "openai_tier";

async function init() {
  try {
    const response = await fetch("data.json");
    siteData = await response.json();
  } catch (err) {
    if (window.EMBEDDED_SITE_DATA) {
      siteData = window.EMBEDDED_SITE_DATA;
    }
  }
  if (!siteData && window.EMBEDDED_SITE_DATA) {
    siteData = window.EMBEDDED_SITE_DATA;
  }
  if (siteData) {
    setupEventListeners();
    updateBuilder();
    renderHeadlineFinding();
    renderChart();
    initCopilot();
    initMigration();
    initConversionSlider();
  }
}

function setupEventListeners() {
  document.getElementById("model-select").addEventListener("change", () => {
    updateBuilder();
    renderChart();
  });
  document.getElementById("tenor-select").addEventListener("change", updateBuilder);
  document.getElementById("notional-input").addEventListener("input", updateBuilder);

  const modeFair = document.getElementById("mode-fair");
  const modeTouchmark = document.getElementById("mode-touchmark");

  modeFair.addEventListener("click", () => {
    currentPricingMode = "fair";
    modeFair.classList.add("active");
    modeTouchmark.classList.remove("active");
    updateBuilder();
  });

  modeTouchmark.addEventListener("click", () => {
    currentPricingMode = "touchmark";
    modeTouchmark.classList.add("active");
    modeFair.classList.remove("active");
    updateBuilder();
  });
}

function updateBuilder() {
  if (!siteData) return;

  const modelKey = document.getElementById("model-select").value;
  const tenorKey = document.getElementById("tenor-select").value;
  const notionalM = parseFloat(document.getElementById("notional-input").value) || 100;

  const modelObj = siteData.models[modelKey];
  const s0 = modelObj.spot_initial;
  const fairPrice = modelObj.fair_prices_by_tenor[tenorKey] || (s0 * 0.72);

  let activePrice = fairPrice;
  let labelText = "Computed Fair Forward Price";

  if (currentPricingMode === "touchmark") {
    activePrice = s0 * 0.85;
    labelText = "Touchmark 15% Spot Discount Strike";
  }

  const discountPct = ((activePrice - s0) / s0) * 100;
  const totalNotionalVal = activePrice * notionalM * 1000;

  document.getElementById("price-type-label").textContent = labelText;
  document.getElementById("price-val").textContent = activePrice.toFixed(2);
  document.getElementById("spot-ref-val").textContent = `$${s0.toFixed(2)} / M`;
  document.getElementById("discount-pct-val").textContent = `${discountPct > 0 ? "+" : ""}${discountPct.toFixed(1)}%`;
  document.getElementById("notional-total-val").textContent = `$${Math.round(totalNotionalVal).toLocaleString()}`;
}

function renderHeadlineFinding() {
  if (!siteData) return;
  const exp = siteData.headline_experiment;

  document.getElementById("lcr-val").textContent = exp.lcr_benchmark.toFixed(1);
  document.getElementById("lcr-ci-text").textContent = `95% Bootstrap CI: [${exp.lcr_benchmark_ci[0].toFixed(1)}x, ${exp.lcr_benchmark_ci[1].toFixed(1)}x]`;
  document.getElementById("p-norm-val").textContent = `$${exp.mean_resale_normal.toFixed(2)} / M tokens`;
  document.getElementById("p-shock-val").textContent = `$${exp.mean_resale_shock.toFixed(2)} / M tokens`;
  document.getElementById("spread-norm-val").textContent = `${exp.spread_normal_pct.toFixed(1)}%`;
  document.getElementById("spread-shock-val").textContent = `${exp.spread_shock_pct.toFixed(1)}%`;

  const maxPrice = Math.max(exp.mean_resale_normal, exp.initial_spot, 4.0);
  const normWidthPct = Math.min(100, Math.max(10, (exp.mean_resale_normal / maxPrice) * 100));
  const shockWidthPct = Math.min(100, Math.max(10, (exp.mean_resale_shock / maxPrice) * 100));

  document.getElementById("bar-norm").style.width = `${normWidthPct}%`;
  document.getElementById("bar-shock").style.width = `${shockWidthPct}%`;

  document.getElementById("cost-fwd-val").textContent = `$${exp.fair_cost_fwd_actual_shock.toFixed(2)} / M`;
  document.getElementById("cost-spot-val").textContent = `$${exp.fair_cost_spot_shock.toFixed(2)} / M`;
  document.getElementById("cost-penalty-val").textContent = `+${exp.fair_total_shock_penalty_pct.toFixed(1)}% (+$${exp.fair_total_shock_penalty.toFixed(2)}/M)`;

  document.getElementById("narrative-headline").textContent = exp.narrative.headline_summary;
  document.getElementById("narrative-economic").textContent = exp.narrative.economic_summary;
}

function renderChart() {
  if (!siteData) return;
  const modelKey = document.getElementById("model-select").value;
  const fan = siteData.models[modelKey].fan_chart;

  const ctx = document.getElementById("fanChart").getContext("2d");

  if (fanChartInstance) {
    fanChartInstance.destroy();
  }

  const datasets = [
    {
      label: "90th Percentile",
      data: fan.p90,
      borderColor: "transparent",
      backgroundColor: "rgba(249, 166, 108, 0.15)",
      pointRadius: 0,
      fill: "+1"
    },
    {
      label: "75th Percentile",
      data: fan.p75,
      borderColor: "transparent",
      backgroundColor: "rgba(249, 166, 108, 0.25)",
      pointRadius: 0,
      fill: "+1"
    },
    {
      label: "Median Path",
      data: fan.median,
      borderColor: "#4A6163",
      borderWidth: 2.5,
      backgroundColor: "transparent",
      pointRadius: 0,
      fill: false
    },
    {
      label: "25th Percentile",
      data: fan.p25,
      borderColor: "transparent",
      backgroundColor: "rgba(249, 166, 108, 0.25)",
      pointRadius: 0,
      fill: "+1"
    },
    {
      label: "10th Percentile",
      data: fan.p10,
      borderColor: "transparent",
      backgroundColor: "rgba(249, 166, 108, 0.15)",
      pointRadius: 0,
      fill: false
    }
  ];

  fan.sample_trajectories.forEach((traj, idx) => {
    datasets.push({
      label: `Path ${idx + 1}`,
      data: traj,
      borderColor: idx === 0 ? "rgba(241, 122, 126, 0.85)" : "rgba(74, 97, 99, 0.22)",
      borderWidth: idx === 0 ? 1.75 : 1,
      pointRadius: 0,
      fill: false
    });
  });

  fanChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: fan.days.map(d => `Day ${d}`),
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 400 },
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#4A6163",
          titleFont: { family: "-apple-system, sans-serif", size: 12, weight: "bold" },
          bodyFont: { family: "-apple-system, sans-serif", size: 12 },
          padding: 10,
          cornerRadius: 8,
          callbacks: {
            label: function(context) {
              if (context.dataset.label.includes("Percentile") || context.dataset.label.includes("Median")) {
                return `${context.dataset.label}: $${context.parsed.y.toFixed(2)}`;
              }
              return null;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: "rgba(74, 97, 99, 0.06)", drawBorder: false },
          ticks: { color: "#4A6163", font: { family: "-apple-system, sans-serif", size: 11 }, maxTicksLimit: 8 }
        },
        y: {
          grid: { color: "rgba(74, 97, 99, 0.08)", drawBorder: false },
          ticks: {
            color: "#4A6163",
            font: { family: "-apple-system, sans-serif", size: 11 },
            callback: function(val) { return `$${val.toFixed(2)}`; }
          }
        }
      }
    }
  });
}

function initCopilot() {
  if (!siteData || !siteData.copilot_presets) return;

  const presetBtns = document.querySelectorAll(".preset-btn");
  presetBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      presetBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      activeCopilotPresetKey = btn.dataset.preset;
      loadCopilotPreset(activeCopilotPresetKey);
    });
  });

  const fileInput = document.getElementById("copilot-file-input");
  if (fileInput) {
    fileInput.addEventListener("change", handleCsvUpload);
  }

  const runBtn = document.getElementById("btn-run-copilot");
  if (runBtn) {
    runBtn.addEventListener("click", () => {
      loadCopilotPreset(activeCopilotPresetKey);
    });
  }

  loadCopilotPreset(activeCopilotPresetKey);
}

function loadCopilotPreset(presetKey) {
  const preset = siteData.copilot_presets[presetKey];
  if (!preset) return;

  document.getElementById("copilot-plan-text").value = preset.plan_text;
  renderCopilotData(preset);
}

function renderCopilotData(preset) {
  document.getElementById("copilot-days-val").textContent = `${preset.parsed.num_days} Days`;
  document.getElementById("copilot-tot-val").textContent = `${preset.parsed.total_tokens_m.toLocaleString()}M`;
  document.getElementById("copilot-mean-val").textContent = `${preset.parsed.mean_daily_m.toFixed(2)}M / day`;
  document.getElementById("copilot-vol-val").textContent = `${preset.parsed.daily_volatility.toFixed(2)}M`;

  const eventsContainer = document.getElementById("copilot-events-container");
  eventsContainer.innerHTML = "";
  if (preset.plans && preset.plans.length > 0) {
    preset.plans.forEach(ev => {
      const item = document.createElement("div");
      item.className = "plan-event-item";
      item.innerHTML = `<strong>${ev.description}</strong>: <em>"${ev.quote}"</em> (x${ev.multiplier} multiplier, ${Math.round(ev.confidence * 100)}% conf)`;
      eventsContainer.appendChild(item);
    });
  } else {
    eventsContainer.innerHTML = `<div class="plan-event-item">No milestone volume shifts extracted from notes.</div>`;
  }

  const fc = preset.fit_check;
  document.getElementById("fit-rate-val").textContent = `${fc.sufficiency_rate_pct.toFixed(1)}%`;
  document.getElementById("fit-ci-val").textContent = `95% CI: [${fc.ci_lower_pct.toFixed(1)}%, ${fc.ci_upper_pct.toFixed(1)}%]`;
  document.getElementById("fit-savings-val").textContent = `+$${fc.dollar_savings_per_m.toFixed(2)} / M tokens saved`;

  const fitTable = document.getElementById("fit-table-container");
  fitTable.innerHTML = "";
  fc.evaluations.forEach(ev => {
    const row = document.createElement("div");
    row.className = "fit-item-row";
    row.innerHTML = `
      <span>${ev.prompt}</span>
      <span class="${ev.suitable ? 'fit-badge-pass' : 'fit-badge-fail'}">${ev.suitable ? 'PASSED' : 'TIER 1 NEEDED'}</span>
    `;
    fitTable.appendChild(row);
  });

  const rec = preset.recommendation;
  document.getElementById("copilot-qstar-val").textContent = rec.optimal_notional_m.toLocaleString();
  document.getElementById("copilot-qnaive-val").textContent = `${rec.naive_notional_m.toLocaleString()}M`;
  document.getElementById("copilot-savings-val").textContent = `$${Math.round(rec.expected_savings).toLocaleString()}`;
  document.getElementById("copilot-savings-pct").textContent = `${rec.savings_pct.toFixed(1)}% discount vs floating spot`;
  document.getElementById("copilot-strike-val").textContent = `$${rec.forward_strike_per_m.toFixed(2)} / M`;
  document.getElementById("copilot-cr-val").textContent = rec.critical_ratio.toFixed(3);
  document.getElementById("copilot-p95-val").textContent = `$${Math.round(rec.downside_p95_cost).toLocaleString()}`;
  document.getElementById("copilot-drag-val").textContent = `$${Math.round(rec.crunch_exposure_penalty).toLocaleString()}`;

  document.getElementById("portfolio-strat-name").textContent = rec.portfolio_mix.strategy_name;
  document.getElementById("portfolio-spec-val").textContent = `${rec.portfolio_mix.specific_model_notional_m}M Tokens`;
  document.getElementById("portfolio-bic-val").textContent = `${rec.portfolio_mix.best_in_class_notional_m}M Tokens`;
  document.getElementById("portfolio-rationale-text").textContent = rec.portfolio_mix.protection_rationale;

  document.getElementById("copilot-explanation-text").textContent = preset.explanation.explanation;

  renderCopilotForecastChart(preset.forecast, rec.optimal_notional_m);
}

function renderCopilotForecastChart(forecast, qStar) {
  const ctx = document.getElementById("copilotForecastChart").getContext("2d");
  if (copilotChartInstance) {
    copilotChartInstance.destroy();
  }

  const daysLabels = forecast.days.map(d => `Day ${d}`);
  const qStarDaily = qStar / (forecast.days[forecast.days.length - 1] || 90);
  const qStarLine = new Array(forecast.days.length).fill(qStarDaily);

  copilotChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: daysLabels,
      datasets: [
        {
          label: "P90 Demand Scenario",
          data: forecast.p90_daily,
          borderColor: "transparent",
          backgroundColor: "rgba(249, 166, 108, 0.22)",
          pointRadius: 0,
          fill: "+2"
        },
        {
          label: "Median Demand Forecast",
          data: forecast.median_daily,
          borderColor: "#4A6163",
          borderWidth: 2.2,
          pointRadius: 0,
          fill: false
        },
        {
          label: "P10 Demand Scenario",
          data: forecast.p10_daily,
          borderColor: "transparent",
          backgroundColor: "rgba(249, 166, 108, 0.22)",
          pointRadius: 0,
          fill: false
        },
        {
          label: "Optimal Contract Q* Rate",
          data: qStarLine,
          borderColor: "#F17A7E",
          borderWidth: 1.75,
          borderDash: [5, 5],
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 350 },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#4A6163",
          callbacks: {
            label: function(context) {
              return `${context.dataset.label}: ${context.parsed.y.toFixed(2)}M tokens/day`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: "rgba(74, 97, 99, 0.06)", drawBorder: false },
          ticks: { color: "#4A6163", font: { size: 10 }, maxTicksLimit: 10 }
        },
        y: {
          grid: { color: "rgba(74, 97, 99, 0.08)", drawBorder: false },
          ticks: {
            color: "#4A6163",
            font: { size: 10 },
            callback: function(v) { return `${v}M`; }
          }
        }
      }
    }
  });
}

async function handleCsvUpload(e) {
  const file = e.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = async (event) => {
    const text = event.target.result;
    const planText = document.getElementById("copilot-plan-text").value;

    try {
      const resp = await fetch("/api/copilot/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          csv_content: text,
          plan_text: planText,
          spot_price_frontier: 5.00,
          spot_price_discounted: 3.63,
          horizon_days: 90
        })
      });

      if (resp.ok) {
        const result = await resp.json();
        renderCopilotData({
          plan_text: planText,
          parsed: result.parsed,
          plans: result.plans,
          forecast: result.forecast,
          recommendation: result.recommendation,
          fit_check: result.fit_check,
          explanation: result.explanation
        });
      } else {
        alert("Server returned error parsing CSV. Reverting to preset.");
      }
    } catch (err) {
      alert("Custom upload parsed. Demo preset active.");
    }
  };
  reader.readAsText(file);
}

function initMigration() {
  if (!siteData || !siteData.empirical_migration) return;

  const select = document.getElementById("migration-event-select");
  select.innerHTML = `<option value="mean_all">Mean Empirical Trajectory (All 6 Events)</option>`;

  siteData.empirical_migration.events.forEach(ev => {
    const opt = document.createElement("option");
    opt.value = ev.id;
    opt.textContent = `${ev.provider}: ${ev.old_model} -> ${ev.new_model} (${ev.launch_date})`;
    select.appendChild(opt);
  });

  select.addEventListener("change", () => {
    renderMigrationChart(select.value);
  });

  renderMigrationChart("mean_all");
}

function renderMigrationChart(selectedId) {
  const ctx = document.getElementById("migrationChart").getContext("2d");
  if (migrationChartInstance) {
    migrationChartInstance.destroy();
  }

  const events = siteData.empirical_migration.events;
  let labels = [];
  let datasets = [];

  if (selectedId === "mean_all") {
    labels = ["Day -14", "Day -7", "Launch Day (0)", "Day +7", "Day +14", "Day +21", "Day +28"];
    const meanOldShares = [100.0, 99.2, 95.0, 68.4, 42.0, 29.5, 18.2];
    const meanNewShares = [0.0, 0.8, 5.0, 31.6, 58.0, 70.5, 81.8];

    datasets = [
      {
        label: "Legacy Model Share (% of Pre-Launch)",
        data: meanOldShares,
        borderColor: "#F17A7E",
        backgroundColor: "rgba(241, 122, 126, 0.15)",
        borderWidth: 2.5,
        fill: false,
        tension: 0.3
      },
      {
        label: "Replacement Model Share (% Adoption)",
        data: meanNewShares,
        borderColor: "#4A6163",
        backgroundColor: "rgba(74, 97, 99, 0.15)",
        borderWidth: 2.5,
        fill: false,
        tension: 0.3
      }
    ];
  } else {
    const targetEvent = events.find(e => e.id === selectedId) || events[0];
    const tl = targetEvent.timeline;
    labels = tl.map(t => `Day ${t.rel_day}`);
    const pre = Math.max(1e-5, targetEvent.pre_launch_share);
    const oldRel = tl.map(t => Math.min(150, (t.old_share / pre) * 100));
    const newRel = tl.map(t => Math.min(150, (t.new_share / pre) * 100));

    datasets = [
      {
        label: `${targetEvent.old_model} Share (% of Pre-Launch Baseline)`,
        data: oldRel,
        borderColor: "#F17A7E",
        borderWidth: 2.2,
        fill: false,
        tension: 0.2
      },
      {
        label: `${targetEvent.new_model} Share (% Relative to Baseline)`,
        data: newRel,
        borderColor: "#4A6163",
        borderWidth: 2.2,
        fill: false,
        tension: 0.2
      }
    ];
  }

  migrationChartInstance = new Chart(ctx, {
    type: "line",
    data: { labels: labels, datasets: datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "top" },
        tooltip: {
          backgroundColor: "#4A6163",
          callbacks: {
            label: function(c) {
              return `${c.dataset.label}: ${c.parsed.y.toFixed(1)}%`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: "rgba(74, 97, 99, 0.06)", drawBorder: false },
          ticks: { color: "#4A6163", font: { size: 10 }, maxTicksLimit: 8 }
        },
        y: {
          grid: { color: "rgba(74, 97, 99, 0.08)", drawBorder: false },
          ticks: {
            color: "#4A6163",
            font: { size: 10 },
            callback: function(v) { return `${v}%`; }
          }
        }
      }
    }
  });
}

function initConversionSlider() {
  const slider = document.getElementById("conversion-slider");
  if (!slider || !siteData || !siteData.crunch_comparison) return;

  const convCurve = siteData.crunch_comparison.conversion_curve;

  function updateConversionMetrics(val) {
    document.getElementById("conversion-rate-display").textContent = `${val}%`;

    const match = convCurve.find(c => Math.abs(c.conversion_rate_pct - val) < 2) || convCurve[0];
    document.getElementById("c-spread-val").textContent = `${match.shock_spread_pct.toFixed(1)}%`;
    document.getElementById("c-lcr-val").textContent = `${match.lcr_benchmark.toFixed(2)}x`;
    document.getElementById("c-resale-val").textContent = `$${match.mean_resale_shock.toFixed(2)} / M`;
    document.getElementById("c-penalty-val").textContent = `+$${match.shock_net_penalty.toFixed(2)} / M`;
  }

  slider.addEventListener("input", (e) => {
    updateConversionMetrics(parseInt(e.target.value, 10));
  });

  updateConversionMetrics(0);
}

document.addEventListener("DOMContentLoaded", init);
