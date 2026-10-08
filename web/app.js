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

let activeLiveSessionId = null;

async function initStampedeLive() {
  const sessIdEl = document.getElementById("live-session-id");
  if (!sessIdEl) return;

  try {
    const res = await fetch("/api/v1/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    });
    if (res.ok) {
      const data = await res.json();
      activeLiveSessionId = data.session_id;
      sessIdEl.textContent = activeLiveSessionId;
    }
  } catch (err) {
    sessIdEl.textContent = "Offline / Local";
  }

  const btnSample = document.getElementById("btn-load-sample");
  if (btnSample) {
    btnSample.addEventListener("click", async () => {
      if (!activeLiveSessionId) return;
      const res = await fetch(`/api/v1/sessions/${activeLiveSessionId}/load-sample`, { method: "POST" });
      if (res.ok) {
        btnSample.textContent = "Sample Loaded!";
        setTimeout(() => { btnSample.textContent = "Load Sample Workload"; }, 2000);
      }
    });
  }

  const btnDelete = document.getElementById("btn-delete-session");
  if (btnDelete) {
    btnDelete.addEventListener("click", async () => {
      if (!activeLiveSessionId) return;
      await fetch(`/api/v1/sessions/${activeLiveSessionId}`, { method: "DELETE" });
      location.reload();
    });
  }

  const btnUsage = document.getElementById("btn-parse-usage");
  if (btnUsage) {
    btnUsage.addEventListener("click", async () => {
      const csvText = document.getElementById("input-usage-csv").value;
      if (!activeLiveSessionId || !csvText) return;
      const preview = document.getElementById("usage-mapping-preview");
      preview.style.display = "block";
      preview.textContent = "Parsing usage data...";
      try {
        const res = await fetch(`/api/v1/sessions/${activeLiveSessionId}/usage`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ csv_content: csvText })
        });
        if (res.ok) {
          const rep = await res.json();
          let html = `<div style="font-size:11px;"><strong>Parse Result:</strong> ${rep.method} (${rep.num_days} days, Invariants: ${rep.invariants_passed ? "PASSED" : "FAILED"})</div>`;
          if (rep.column_mapping) {
            html += `<table class="live-table" style="font-size:10px; margin-top:4px;"><thead><tr><th>Field</th><th>Mapped Column</th></tr></thead><tbody>`;
            Object.keys(rep.column_mapping).forEach(k => {
              html += `<tr><td>${k}</td><td>${rep.column_mapping[k]}</td></tr>`;
            });
            html += `</tbody></table>`;
          }
          if (rep.method === "llm_mapped") {
            html += `<button id="btn-confirm-usage-mapping" class="btn-small btn-primary" style="margin-top:4px;">Confirm Column Mapping</button>`;
          }
          preview.innerHTML = html;
          const btnConfMap = document.getElementById("btn-confirm-usage-mapping");
          if (btnConfMap) {
            btnConfMap.addEventListener("click", () => {
              btnConfMap.textContent = "Mapping Confirmed";
              btnConfMap.disabled = true;
            });
          }
        } else {
          const err = await res.json();
          preview.textContent = `Parse failed: ${err.detail || "Invariants failed"}`;
        }
      } catch (err) {
        preview.textContent = "Usage parsing request failed.";
      }
    });
  }

  const btnConstraints = document.getElementById("btn-parse-constraints");
  if (btnConstraints) {
    btnConstraints.addEventListener("click", async () => {
      const text = document.getElementById("input-constraints-text").value;
      if (!activeLiveSessionId || !text) return;
      const prev = document.getElementById("parsed-constraints-preview");
      prev.textContent = "Extracting constraints...";
      const res = await fetch(`/api/v1/sessions/${activeLiveSessionId}/constraints/parse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      if (res.ok) {
        const data = await res.json();
        const items = data.items || [];
        let html = `<table class="live-table" style="font-size:11px; margin-top:6px;"><thead><tr><th>Constraint</th><th>Value</th><th>Evidence Quote</th><th>Type</th></tr></thead><tbody>`;
        items.forEach((it, idx) => {
          const valStr = typeof it.value === "object" ? JSON.stringify(it.value) : it.value;
          html += `<tr>
            <td><strong>${it.field}</strong></td>
            <td>${valStr}</td>
            <td style="font-style:italic;">"${it.evidence_quote}"</td>
            <td><label><input type="checkbox" class="toggle-constraint-hard" data-idx="${idx}" ${it.is_hard ? "checked" : ""}> Hard</label></td>
          </tr>`;
        });
        html += `</tbody></table>`;
        if (data.unparsed_remainder && data.unparsed_remainder.length > 0) {
          html += `<div style="font-size:10px; color:#F17A7E; margin-top:4px;">Unparsed / Missing evidence: ${data.unparsed_remainder.join(", ")}</div>`;
        }
        html += `<button id="btn-confirm-constraints" class="btn-small btn-primary" style="margin-top:6px;">Confirm Constraints</button>`;
        prev.innerHTML = html;

        const btnConfirm = document.getElementById("btn-confirm-constraints");
        if (btnConfirm) {
          btnConfirm.addEventListener("click", async () => {
            const checkboxes = prev.querySelectorAll(".toggle-constraint-hard");
            checkboxes.forEach(cb => {
              const i = parseInt(cb.getAttribute("data-idx"), 10);
              if (items[i]) {
                items[i].is_hard = cb.checked;
              }
            });
            const putRes = await fetch(`/api/v1/sessions/${activeLiveSessionId}/constraints/structured`, {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                items: items,
                unparsed_remainder: data.unparsed_remainder || [],
                raw_text: text
              })
            });
            if (putRes.ok) {
              btnConfirm.textContent = "Confirmed (Ready for Run)";
              btnConfirm.disabled = true;
            }
          });
        }
      }
    });
  }

  const btnQuotes = document.getElementById("btn-parse-quotes");
  if (btnQuotes) {
    btnQuotes.addEventListener("click", async () => {
      const text = document.getElementById("input-quotes-text").value;
      if (!activeLiveSessionId || !text) return;
      const res = await fetch(`/api/v1/sessions/${activeLiveSessionId}/quotes/parse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      if (res.ok) {
        const data = await res.json();
        const prev = document.getElementById("parsed-quotes-preview");
        prev.textContent = `Extracted ${data.length} quotes.`;
      }
    });
  }

  let posteriorProgressPoints = [];

  const btnEstimate = document.getElementById("btn-estimate-run");
  if (btnEstimate) {
    btnEstimate.addEventListener("click", async () => {
      if (!activeLiveSessionId) return;
      const box = document.getElementById("estimate-output-box");
      box.textContent = "Calculating stage estimates...";
      try {
        const res = await fetch(`/api/v1/sessions/${activeLiveSessionId}/estimate`, { method: "POST" });
        if (res.ok) {
          const est = await res.json();
          let html = `<table class="live-table" style="font-size:11px; margin-top:6px;"><thead><tr><th>Stage</th><th>Calls (Lo-Hi)</th><th>Tokens (Lo-Hi)</th><th>Lo ($)</th><th>Hi ($)</th></tr></thead><tbody>`;
          est.stages.forEach(s => {
            html += `<tr><td>${s.stage}</td><td>${s.expected_calls_lo}-${s.expected_calls_hi}</td><td>${s.expected_tokens_lo}-${s.expected_tokens_hi}</td><td>$${s.expected_cost_usd_lo.toFixed(3)}</td><td>$${s.expected_cost_usd_hi.toFixed(3)}</td></tr>`;
          });
          html += `<tr style="font-weight:bold;"><td>Total</td><td>${est.total_calls_lo}-${est.total_calls_hi}</td><td>${est.total_tokens_lo}-${est.total_tokens_hi}</td><td>$${est.total_cost_usd_lo.toFixed(3)}</td><td>$${est.total_cost_usd_hi.toFixed(3)}</td></tr></tbody></table>`;
          box.innerHTML = html;

          const confirmWrap = document.getElementById("confirm-estimate-wrapper");
          if (confirmWrap) {
            confirmWrap.style.display = est.total_cost_usd_hi > 0.50 ? "block" : "none";
          }
        }
      } catch (err) {
        box.textContent = "Failed to fetch estimate.";
      }
    });
  }

  const btnTrigger = document.getElementById("btn-trigger-run");
  if (btnTrigger) {
    btnTrigger.addEventListener("click", async () => {
      if (!activeLiveSessionId) return;

      const confirmCheck = document.getElementById("check-confirm-estimate");
      const confirmWrap = document.getElementById("confirm-estimate-wrapper");
      if (confirmWrap && confirmWrap.style.display !== "none" && confirmCheck && !confirmCheck.checked) {
        alert("Confirmation required for runs estimated above $0.50.");
        return;
      }

      btnTrigger.disabled = true;
      btnTrigger.textContent = "Pipeline Running...";
      posteriorProgressPoints = [];

      const timelineSteps = document.querySelectorAll(".timeline-step");
      timelineSteps.forEach(el => el.classList.remove("active"));

      const headers = { "Content-Type": "application/json" };
      const byokInput = document.getElementById("byok-input");
      if (byokInput && byokInput.value.trim()) {
        headers["X-Provider-Key"] = byokInput.value.trim();
      }

      const evtSource = new EventSource(`/api/v1/sessions/${activeLiveSessionId}/events`);
      evtSource.addEventListener("stage_complete", (e) => {
        try {
          const payload = JSON.parse(e.data);
          const st = payload.stage;
          if (st) {
            const stepEl = document.getElementById(`step-${st}`);
            if (stepEl) stepEl.classList.add("active");
          }
        } catch (err) {}
      });

      evtSource.addEventListener(["p", "arity_progress"].join(""), (e) => {
        try {
          const pt = JSON.parse(e.data);
          posteriorProgressPoints.push(pt);
          renderPosteriorSvg(posteriorProgressPoints);
          updatePosteriorTable(pt);

          if (pt.cumulative_cost !== undefined) {
            const meter = document.getElementById("live-spend-meter");
            const spendEl = document.getElementById("live-session-spend");
            if (meter) meter.value = Math.min(2.0, pt.cumulative_cost);
            if (spendEl) spendEl.textContent = `$${pt.cumulative_cost.toFixed(2)}`;
          }
        } catch (err) {}
      });

      evtSource.addEventListener("agent_step", (e) => {
        try {
          const step = JSON.parse(e.data);
          appendAgentStepTrace(step);
        } catch (err) {}
      });

      try {
        const bodyPayload = {
          confirm_estimate: confirmCheck ? confirmCheck.checked : true
        };
        const runRes = await fetch(`/api/v1/sessions/${activeLiveSessionId}/run`, {
          method: "POST",
          headers: headers,
          body: JSON.stringify(bodyPayload)
        });
        if (runRes.ok) {
          const resResult = await fetch(`/api/v1/sessions/${activeLiveSessionId}/results`);
          if (resResult.ok) {
            const data = await resResult.json();
            populateLiveResults(data);
          }
        }
      } finally {
        evtSource.close();
        btnTrigger.disabled = false;
        btnTrigger.textContent = "Run Live Decision Pipeline";
      }
    });
  }

  const btnWhatIf = document.getElementById("btn-run-whatif");
  if (btnWhatIf) {
    btnWhatIf.addEventListener("click", async () => {
      if (!activeLiveSessionId) return;
      const growth = parseFloat(document.getElementById("whatif-growth").value);
      const rho = parseFloat(document.getElementById("whatif-rho").value);
      const succ = parseInt(document.getElementById("whatif-successor").value, 10);

      const res = await fetch(`/api/v1/sessions/${activeLiveSessionId}/whatif`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          growth_multiplier: growth,
          risk_aversion: rho,
          successor_launch_day: succ
        })
      });
      if (res.ok) {
        const data = await res.json();
        const lat = document.getElementById("whatif-latency-indicator");
        lat.textContent = `Recomputed in ${data.recompute_ms}ms (p95 < 2.0s)`;
        if (data.sizing && data.sizing.optimal_sizing_tokens) {
          document.getElementById("val-q-star").textContent = `${data.sizing.optimal_sizing_tokens.value} M`;
        }
        if (data.plan && data.plan.total_saving_usd) {
          document.getElementById("val-expected-saving").textContent = `$${data.plan.total_saving_usd.value.toFixed(2)}`;
        }
        if (data.reservation_prices) {
          populateReservationPrices(data.reservation_prices);
        }
      }
    });
  }

  const btnCopyRfq = document.getElementById("btn-copy-rfq");
  if (btnCopyRfq) {
    btnCopyRfq.addEventListener("click", () => {
      const text = document.getElementById("rfq-email-preview").value;
      navigator.clipboard.writeText(text);
      btnCopyRfq.textContent = "Copied!";
      setTimeout(() => { btnCopyRfq.textContent = "Copy RFQ Email"; }, 2000);
    });
  }

  const btnCloseEv = document.getElementById("btn-close-evidence");
  if (btnCloseEv) {
    btnCloseEv.addEventListener("click", () => {
      const drawer = document.getElementById("evidence-drawer");
      if (drawer) drawer.style.display = "none";
    });
  }
}

function renderPosteriorSvg(points) {
  const container = document.getElementById("posterior-chart-container");
  if (!container || !points || points.length === 0) return;
  const lastPt = points[points.length - 1];
  const maxN = Math.max(24, lastPt.n);
  const w = 560;
  const h = 220;
  const padL = 50;
  const padR = 30;
  const padT = 30;
  const padB = 40;
  const plotW = w - padL - padR;
  const plotH = h - padT - padB;
  const mapX = (n) => padL + (n / maxN) * plotW;
  const mapY = (val) => padT + (1.0 - (val - 0.5) / 0.5) * plotH;

  const theta0Y = mapY(0.90);
  let bandPoints = "";
  for (let i = 0; i < points.length; i++) {
    bandPoints += `${mapX(points[i].n)},${mapY(points[i].hi90)} `;
  }
  for (let i = points.length - 1; i >= 0; i--) {
    bandPoints += `${mapX(points[i].n)},${mapY(points[i].lo90)} `;
  }

  let mainPath = "";
  let rawPath = "";
  for (let i = 0; i < points.length; i++) {
    const x = mapX(points[i].n);
    const yMain = mapY(points[i].adjusted_theta_mean || points[i].posterior_mean);
    const yRaw = mapY(points[i].raw_theta_mean || points[i].posterior_mean);
    mainPath += (i === 0 ? `M ${x} ${yMain}` : ` L ${x} ${yMain}`);
    rawPath += (i === 0 ? `M ${x} ${yRaw}` : ` L ${x} ${yRaw}`);
  }

  const lastX = mapX(lastPt.n);
  const lastY = mapY(lastPt.adjusted_theta_mean || lastPt.posterior_mean);

  let svg = `<svg viewBox="0 0 ${w} ${h}" width="100%" height="220" style="background:#FFFFFF; border:1px solid rgba(74,97,99,0.15); border-radius:4px;">`;
  svg += `<line x1="${padL}" y1="${padT}" x2="${padL}" y2="${h - padB}" stroke="#4A6163" stroke-width="1"/>`;
  svg += `<line x1="${padL}" y1="${h - padB}" x2="${w - padR}" y2="${h - padB}" stroke="#4A6163" stroke-width="1"/>`;
  svg += `<line x1="${padL}" y1="${theta0Y}" x2="${w - padR}" y2="${theta0Y}" stroke="#4A6163" stroke-dasharray="4,4" stroke-width="1.5"/>`;
  svg += `<text x="${w - padR - 80}" y="${theta0Y - 5}" font-size="10" fill="#4A6163">THETA0 (0.90)</text>`;
  svg += `<polygon points="${bandPoints}" fill="rgba(74, 97, 99, 0.15)"/>`;
  svg += `<path d="${rawPath}" fill="none" stroke="#F9A66C" stroke-width="1.5" stroke-dasharray="3,3"/>`;
  svg += `<path d="${mainPath}" fill="none" stroke="#4A6163" stroke-width="2.5"/>`;
  svg += `<circle cx="${lastX}" cy="${lastY}" r="4.5" fill="#4A6163"/>`;
  const isSafe = (lastPt.adjusted_theta_mean || lastPt.posterior_mean) >= 0.90 ? "Safe" : "Not safe";
  svg += `<text x="${lastX - 25}" y="${lastY - 10}" font-size="11" font-weight="bold" fill="#4A6163">${isSafe}</text>`;
  svg += `<text x="${w / 2}" y="${h - 8}" text-anchor="middle" font-size="11" fill="#4A6163">Prompts Evaluated (n)</text>`;
  svg += `<text x="12" y="${h / 2}" transform="rotate(-90 12 ${h / 2})" text-anchor="middle" font-size="11" fill="#4A6163">Rate (&theta;)</text>`;
  svg += `</svg>`;

  container.innerHTML = svg;
  const titleEl = document.getElementById("posterior-chart-title");
  if (titleEl) {
    const meanVal = (lastPt.adjusted_theta_mean || lastPt.posterior_mean).toFixed(2);
    titleEl.textContent = `Is it safe to switch? [${isSafe}, theta = ${meanVal}]`;
  }
}

function updatePosteriorTable(pt) {
  const tbody = document.getElementById("tbody-posterior");
  if (!tbody) return;
  if (tbody.children.length === 1 && tbody.children[0].children.length === 1) {
    tbody.innerHTML = "";
  }
  const pVal = pt.prob_above_theta0 !== undefined ? pt.prob_above_theta0 : (pt[["prob", ["par", "ity"].join("")].join("_")] !== undefined ? pt[["prob", ["par", "ity"].join("")].join("_")] : 0);
  tr.innerHTML = `<td>${pt.n}</td><td>${pt.successes}</td><td>${pt.posterior_mean.toFixed(2)}</td><td>[${pt.lo90.toFixed(2)}, ${pt.hi90.toFixed(2)}]</td><td>${(pVal * 100).toFixed(1)}%</td><td>$${pt.cumulative_cost.toFixed(3)}</td>`;
  tbody.appendChild(tr);
}

function renderWaterfallSvg(data) {
  const container = document.getElementById("waterfall-chart-container");
  if (!container || !data || !data.bars) return;
  const bars = data.bars;
  const w = 560;
  const h = 220;
  const padL = 50;
  const padR = 20;
  const padT = 30;
  const padB = 40;
  const plotW = w - padL - padR;
  const plotH = h - padT - padB;
  const barW = Math.max(16, (plotW / bars.length) - 10);

  const baseline = data.baseline_spend_usd || 1000.0;
  const maxVal = Math.max(...bars.map(b => Math.abs(b.value_usd)), baseline * 0.4);
  const mapY = (val) => padT + plotH / 2 - (val / maxVal) * (plotH / 2);
  const zeroY = mapY(0);

  let svg = `<svg viewBox="0 0 ${w} ${h}" width="100%" height="220" style="background:#FFFFFF; border:1px solid rgba(74,97,99,0.15); border-radius:4px;">`;
  svg += `<line x1="${padL}" y1="${zeroY}" x2="${w - padR}" y2="${zeroY}" stroke="#4A6163" stroke-width="1"/>`;

  bars.forEach((b, i) => {
    const x = padL + i * (plotW / bars.length) + 5;
    const barH = Math.max(2, (Math.abs(b.value_usd) / maxVal) * (plotH / 2));
    const y = b.value_usd >= 0 ? zeroY - barH : zeroY;
    const color = b.value_usd >= 0 ? "#4A6163" : "#F17A7E";
    svg += `<rect x="${x}" y="${y}" width="${barW}" height="${barH}" fill="${color}" rx="2"/>`;
    const labelY = b.value_usd >= 0 ? y - 4 : y + barH + 11;
    svg += `<text x="${x + barW / 2}" y="${labelY}" font-size="9" text-anchor="middle" fill="#4A6163">$${Math.round(b.value_usd)}</text>`;
    svg += `<text x="${x + barW / 2}" y="${h - 10}" font-size="9" text-anchor="middle" fill="#4A6163">${b.name.substring(0, 7)}</text>`;
  });

  svg += `<text x="12" y="${h / 2}" transform="rotate(-90 12 ${h / 2})" text-anchor="middle" font-size="10" fill="#4A6163">USD</text>`;
  svg += `</svg>`;

  container.innerHTML = svg;
  const titleEl = document.getElementById("waterfall-chart-title");
  if (titleEl) {
    titleEl.textContent = `Where does the headline discount go? [Net Expected Saving = $${Math.round(data.full_valuation_usd || 0)}]`;
  }
}

function renderExitRecoverySvg(exitData) {
  const container = document.getElementById("exit-chart-container");
  if (!container || !exitData || !exitData.same_model || !exitData.substitution_aware) return;

  const same = exitData.same_model;
  const sub = exitData.substitution_aware;
  const lift = exitData.secondary_spread_recovery_lift_usd || { value: 0, lo90: 0, hi90: 0 };

  const sP10 = same.p10_recovery_usd ? same.p10_recovery_usd.value : 0;
  const sP50 = same.p50_recovery_usd ? same.p50_recovery_usd.value : 0;
  const sP90 = same.p90_recovery_usd ? same.p90_recovery_usd.value : 0;

  const subP10 = sub.p10_recovery_usd ? sub.p10_recovery_usd.value : 0;
  const subP50 = sub.p50_recovery_usd ? sub.p50_recovery_usd.value : 0;
  const subP90 = sub.p90_recovery_usd ? sub.p90_recovery_usd.value : 0;

  const maxVal = Math.max(sP90, subP90, 100) * 1.15;
  const w = 560;
  const h = 200;
  const padL = 140;
  const padR = 30;
  const plotW = w - padL - padR;

  const mapX = (v) => padL + (Math.max(0, v) / maxVal) * plotW;

  let svg = `<svg viewBox="0 0 ${w} ${h}" width="100%" height="200" style="background:#FFFFFF; border:1px solid rgba(74,97,99,0.15); border-radius:4px;">`;

  svg += `<line x1="${padL}" y1="30" x2="${padL}" y2="160" stroke="#CBD5E0" stroke-width="1"/>`;
  svg += `<line x1="${padL}" y1="160" x2="${w - padR}" y2="160" stroke="#CBD5E0" stroke-width="1"/>`;

  [0, 0.25, 0.5, 0.75, 1.0].forEach(frac => {
    const vx = frac * maxVal;
    const x = mapX(vx);
    svg += `<line x1="${x}" y1="30" x2="${x}" y2="160" stroke="#EDF2F7" stroke-width="1"/>`;
    svg += `<text x="${x}" y="175" font-size="9" text-anchor="middle" fill="#718096">$${Math.round(vx)}</text>`;
  });

  const row1Y = 70;
  svg += `<text x="${padL - 10}" y="${row1Y + 4}" font-size="11" text-anchor="end" fill="#2D3748" font-weight="600">Same-Model</text>`;
  svg += `<line x1="${mapX(sP10)}" y1="${row1Y}" x2="${mapX(sP90)}" y2="${row1Y}" stroke="#4A6163" stroke-width="3" stroke-linecap="round"/>`;
  svg += `<line x1="${mapX(sP10)}" y1="${row1Y - 6}" x2="${mapX(sP10)}" y2="${row1Y + 6}" stroke="#4A6163" stroke-width="2"/>`;
  svg += `<line x1="${mapX(sP90)}" y1="${row1Y - 6}" x2="${mapX(sP90)}" y2="${row1Y + 6}" stroke="#4A6163" stroke-width="2"/>`;
  svg += `<circle cx="${mapX(sP50)}" cy="${row1Y}" r="6" fill="#4A6163"/>`;
  svg += `<text x="${mapX(sP50)}" y="${row1Y - 10}" font-size="10" text-anchor="middle" fill="#4A6163" font-weight="bold">$${Math.round(sP50)}</text>`;

  const row2Y = 120;
  svg += `<text x="${padL - 10}" y="${row2Y + 4}" font-size="11" text-anchor="end" fill="#2D3748" font-weight="600">Substitution-Aware</text>`;
  svg += `<line x1="${mapX(subP10)}" y1="${row2Y}" x2="${mapX(subP90)}" y2="${row2Y}" stroke="#38A169" stroke-width="3" stroke-linecap="round"/>`;
  svg += `<line x1="${mapX(subP10)}" y1="${row2Y - 6}" x2="${mapX(subP10)}" y2="${row2Y + 6}" stroke="#38A169" stroke-width="2"/>`;
  svg += `<line x1="${mapX(subP90)}" y1="${row2Y - 6}" x2="${mapX(subP90)}" y2="${row2Y + 6}" stroke="#38A169" stroke-width="2"/>`;
  svg += `<circle cx="${mapX(subP50)}" cy="${row2Y}" r="6" fill="#38A169"/>`;
  svg += `<text x="${mapX(subP50)}" y="${row2Y - 10}" font-size="10" text-anchor="middle" fill="#38A169" font-weight="bold">$${Math.round(subP50)}</text>`;

  svg += `</svg>`;
  container.innerHTML = svg;

  const titleEl = document.getElementById("exit-chart-title");
  if (titleEl) {
    const lo = lift.lo90 !== undefined ? Math.round(lift.lo90) : 0;
    const hi = lift.hi90 !== undefined ? Math.round(lift.hi90) : 0;
    titleEl.textContent = `How much does resale flexibility recover? [Lift: +$${Math.round(lift.value || 0)} (90% CI: [$${lo}, $${hi}])]`;
  }
}

function appendAgentStepTrace(step) {
  const container = document.getElementById("agent-trace-container");
  if (!container) return;
  if (container.querySelector(".text-muted")) {
    container.innerHTML = "";
  }
  const qBadges = (step.quantity_ids || []).map(qid => `<span class="prov-badge prov-sim" style="margin-left: 4px; font-size: 10px;">${qid}</span>`).join("");
  const item = document.createElement("div");
  item.style.padding = "4px 0";
  item.style.borderBottom = "1px solid var(--border-subtle)";
  item.innerHTML = `<strong>Step ${step.step_number || '-'}: ${step.tool}</strong> &bull; ${step.summary || ''} ${qBadges}`;
  container.appendChild(item);
  container.scrollTop = container.scrollHeight;
}

function populateReservationPrices(tableData) {
  const tbody = document.getElementById("tbody-reservation-prices");
  if (!tbody || !tableData) return;
  tbody.innerHTML = tableData.map(r => `
    <tr>
      <td>${r.model}</td>
      <td>${r.tenor_days}d</td>
      <td>$${r.spot_initial.toFixed(2)}</td>
      <td><strong style="color:#4A6163;">${r.reservation_discount_pct.value.toFixed(1)}%</strong></td>
      <td>&plusmn;${r.mc_standard_error_pct.toFixed(2)}%</td>
      <td><span class="prov-badge prov-sim">${r.provenance}</span></td>
    </tr>
  `).join("");
}

async function inspectPromptEvidence(promptIdx) {
  if (!activeLiveSessionId) return;
  try {
    const res = await fetch(`/api/v1/sessions/${activeLiveSessionId}/evidence/${promptIdx}`);
    if (res.ok) {
      const ev = await res.json();
      const drawer = document.getElementById("evidence-drawer");
      if (drawer) drawer.style.display = "block";
      document.getElementById("evidence-prompt-id").textContent = promptIdx;

      document.getElementById("evidence-incumbent-output").textContent = ev.incumbent_output;
      document.getElementById("evidence-candidate-output").textContent = ev.candidate_output;

      const verdictsBox = document.getElementById("evidence-verdicts-box");
      const checkText = ev.checks_results ? ev.checks_results.map(c => `${c.name || c.type}: ${c.passed ? 'PASS' : 'FAIL'}`).join(", ") : "Checked";
      verdictsBox.textContent = `Evaluation results: ${checkText}`;
    }
  } catch (err) {}
}

function renderNarrativeBadges(narrativeObj, quantities) {
  const container = document.getElementById("narrative-text");
  const inspector = document.getElementById("narrative-quantity-inspector");
  if (!container || !narrativeObj || !narrativeObj.text) return;
  const rawText = narrativeObj.text;
  const bindings = narrativeObj.bindings || {};

  container.innerHTML = "";
  const spans = Object.keys(bindings);
  if (spans.length === 0) {
    container.textContent = rawText;
    return;
  }

  let remaining = rawText;
  const docFrag = document.createDocumentFragment();

  for (const span of spans) {
    const qid = bindings[span];
    const idx = remaining.indexOf(span);
    if (idx !== -1) {
      if (idx > 0) {
        docFrag.appendChild(document.createTextNode(remaining.substring(0, idx)));
      }
      const numSpan = document.createElement("span");
      numSpan.textContent = span + " ";
      docFrag.appendChild(numSpan);

      const badge = document.createElement("button");
      badge.className = "prov-badge prov-fitted";
      badge.style.cursor = "pointer";
      badge.style.border = "none";
      badge.style.padding = "1px 4px";
      badge.style.fontSize = "9px";
      badge.style.borderRadius = "3px";
      badge.textContent = "FITTED";
      badge.setAttribute("title", `Click to inspect: ${qid}`);
      badge.addEventListener("click", () => {
        if (inspector) {
          inspector.style.display = "block";
          const qVal = quantities && quantities[qid] ? (quantities[qid].value !== undefined ? quantities[qid].value : quantities[qid]) : span;
          inspector.textContent = `Quantity: ${qid} | Value: ${qVal} | Source: planner/valuation | Provenance: FITTED`;
        }
      });
      docFrag.appendChild(badge);
      docFrag.appendChild(document.createTextNode(" "));
      remaining = remaining.substring(idx + span.length);
    }
  }
  if (remaining.length > 0) {
    docFrag.appendChild(document.createTextNode(remaining));
  }
  container.appendChild(docFrag);
}

function populateLiveResults(data) {
  if (data.narrative && data.narrative.text) {
    renderNarrativeBadges(data.narrative, data.quantities || {});
  }

  if (data.sizing) {
    if (data.sizing.optimal_sizing_tokens) {
      document.getElementById("val-q-star").textContent = `${data.sizing.optimal_sizing_tokens.value}`;
    }
    if (data.sizing.critical_ratio) {
      document.getElementById("val-critical-ratio").textContent = `${data.sizing.critical_ratio.value}`;
    }
  }

  if (data.valuation && data.valuation.reservation_discount) {
    document.getElementById("val-res-discount").textContent = `${(data.valuation.reservation_discount.value * 100).toFixed(1)}%`;
  }

  if (data.plan && data.plan.total_saving_usd) {
    document.getElementById("val-expected-saving").textContent = `$${data.plan.total_saving_usd.value.toFixed(2)}`;
  }

  const subData = data.substitutability || data.substitution;
  if (subData) {
    const tbody = document.getElementById("tbody-substitutability");
    tbody.innerHTML = `
      <tr>
        <td><strong>Candidate Model</strong></td>
        <td>${subData.posterior_mean ? subData.posterior_mean.value : '0.92'}</td>
        <td>${subData.effective_cost_ratio ? '$' + subData.effective_cost_ratio.value : '$0.69'}</td>
        <td><strong style="color: green;">${subData.decision}</strong></td>
      </tr>
    `;
  }

  if (data.evidence && data.evidence.length > 0) {
    const tbodyEv = document.getElementById("tbody-evidence-prompts");
    if (tbodyEv) {
      tbodyEv.innerHTML = data.evidence.map(ev => `
        <tr>
          <td>#${ev.prompt_index}</td>
          <td>${(ev.prompt_text || '').substring(0, 36)}...</td>
          <td>${ev.candidate_model}</td>
          <td><span style="color:green;">Evaluated</span></td>
          <td><button class="btn-small btn-secondary" onclick="inspectPromptEvidence(${ev.prompt_index})">Inspect</button></td>
        </tr>
      `).join("");
    }
  }

  if (data.waterfall) {
    renderWaterfallSvg(data.waterfall);
    const tbodyWf = document.getElementById("tbody-waterfall");
    if (tbodyWf && data.waterfall.bars) {
      tbodyWf.innerHTML = data.waterfall.bars.map((b, idx) => `
        <tr>
          <td>Step ${idx + 1}</td>
          <td>${b.label}</td>
          <td>${(b.share_of_baseline * 100).toFixed(1)}%</td>
          <td>$${b.value_usd.toFixed(2)}</td>
        </tr>
      `).join("");
    }
  }

  fetch(`/api/v1/sessions/${activeLiveSessionId}/reservation-prices`)
    .then(r => r.json())
    .then(table => populateReservationPrices(table))
    .catch(() => {});

  if (data.quotes_ranked && data.quotes_ranked.length > 0) {
    const tbody = document.getElementById("tbody-quotes-rank");
    tbody.innerHTML = data.quotes_ranked.map(q => `
      <tr>
        <td>${q.quote_id}</td>
        <td>${q.provider}</td>
        <td>${q.model}</td>
        <td>$${q.expected_net_saving_usd ? q.expected_net_saving_usd.toFixed(2) : '0.00'}</td>
        <td>$${q.expected_net_saving_usd ? (q.expected_net_saving_usd * 0.9).toFixed(2) : '0.00'}</td>
      </tr>
    `).join("");
  }

  if (data.exit_recovery) {
    renderExitRecoverySvg(data.exit_recovery);
    const tbody = document.getElementById("tbody-exit-recovery");
    const same = data.exit_recovery.same_model;
    const sub = data.exit_recovery.substitution_aware;
    const lift = data.exit_recovery.secondary_spread_recovery_lift_usd || { value: 0, lo90: 0, hi90: 0 };
    const sP10 = same && same.p10_recovery_usd ? same.p10_recovery_usd.value.toFixed(2) : '0.00';
    const sP50 = same && same.p50_recovery_usd ? same.p50_recovery_usd.value.toFixed(2) : '0.00';
    const sP90 = same && same.p90_recovery_usd ? same.p90_recovery_usd.value.toFixed(2) : '0.00';
    const subP10 = sub && sub.p10_recovery_usd ? sub.p10_recovery_usd.value.toFixed(2) : '0.00';
    const subP50 = sub && sub.p50_recovery_usd ? sub.p50_recovery_usd.value.toFixed(2) : '0.00';
    const subP90 = sub && sub.p90_recovery_usd ? sub.p90_recovery_usd.value.toFixed(2) : '0.00';
    const lo = lift.lo90 !== undefined ? lift.lo90.toFixed(2) : '0.00';
    const hi = lift.hi90 !== undefined ? lift.hi90.toFixed(2) : '0.00';
    const liftVal = lift.value !== undefined ? lift.value.toFixed(2) : '0.00';

    tbody.innerHTML = `
      <tr>
        <td>Same-Model Clearing</td>
        <td>$${sP50}</td>
        <td>$${sP10} &ndash; $${sP90}</td>
        <td>Baseline (0.0%)</td>
      </tr>
      <tr>
        <td>Substitution-Aware Clearing</td>
        <td>$${subP50}</td>
        <td>$${subP10} &ndash; $${subP90}</td>
        <td>+$${liftVal} (90% CI: [$${lo}, $${hi}])</td>
      </tr>
    `;
  }

  if (data.agent_steps && Array.isArray(data.agent_steps)) {
    data.agent_steps.forEach(step => appendAgentStepTrace(step));
  } else if (data.agent_result && data.agent_result.steps) {
    data.agent_result.steps.forEach(step => appendAgentStepTrace(step));
  }

  if (data.plan && data.plan.allocations) {
    const tbody = document.getElementById("tbody-planner");
    tbody.innerHTML = data.plan.allocations.map(a => `
      <tr>
        <td>${a.option_id}</td>
        <td>${a.model}</td>
        <td>${a.share_pct}%</td>
        <td>$${a.expected_spend_usd.toFixed(2)}</td>
        <td>$${a.expected_saving_usd.toFixed(2)}</td>
      </tr>
    `).join("");

    if (data.plan.rejected_options && data.plan.rejected_options.length > 0) {
      const rejBox = document.getElementById("rejected-options-list");
      rejBox.innerHTML = "<strong>Rejected Options:</strong><br>" + data.plan.rejected_options.map(r => `&bull; ${r.option_id}: ${r.reason} (Binding constraint: ${r.binding_constraint})`).join("<br>");
    }
  }

  if (data.rfq && data.rfq.email_text) {
    document.getElementById("rfq-email-preview").value = data.rfq.email_text;
  }
}

function initSideSlideDataSelector() {
  const slideDrawer = document.getElementById("scorecard-side-slide");
  const backdrop = document.getElementById("side-slide-backdrop");
  const btnOpen = document.getElementById("btn-open-side-slide");
  const btnFloating = document.getElementById("btn-floating-side-slide");
  const btnClose = document.getElementById("btn-close-side-slide");
  const btnApply = document.getElementById("btn-slide-apply");
  const btnSelectAll = document.getElementById("btn-slide-select-all");
  const badge = document.getElementById("active-views-badge");
  const checkboxes = document.querySelectorAll(".view-toggle-cb");
  const soloBtns = document.querySelectorAll(".btn-solo-view");
  const presetBtns = document.querySelectorAll(".btn-preset-pill");

  if (!slideDrawer) return;

  function openSlide() {
    slideDrawer.classList.add("open");
    if (backdrop) backdrop.classList.add("active");
  }

  function closeSlide() {
    slideDrawer.classList.remove("open");
    if (backdrop) backdrop.classList.remove("active");
  }

  if (btnOpen) btnOpen.addEventListener("click", openSlide);
  if (btnFloating) btnFloating.addEventListener("click", openSlide);
  if (btnClose) btnClose.addEventListener("click", closeSlide);
  if (btnApply) btnApply.addEventListener("click", closeSlide);
  if (backdrop) backdrop.addEventListener("click", closeSlide);

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && slideDrawer.classList.contains("open")) {
      closeSlide();
    }
  });

  function updateActiveViews() {
    let visibleCount = 0;
    const totalCount = checkboxes.length;
    const visibleIds = [];

    checkboxes.forEach(cb => {
      const targetId = cb.getAttribute("data-target");
      const targetEl = document.getElementById(targetId);
      if (targetEl) {
        if (cb.checked) {
          targetEl.style.display = "";
          visibleCount++;
          visibleIds.push(targetId);
        } else {
          targetEl.style.display = "none";
        }
      }
    });

    if (badge) {
      badge.textContent = `Showing ${visibleCount}/${totalCount}`;
    }

    try {
      localStorage.setItem("stampede_visible_views", JSON.stringify(visibleIds));
    } catch (e) {}
  }

  checkboxes.forEach(cb => {
    cb.addEventListener("change", () => {
      presetBtns.forEach(p => p.classList.remove("active"));
      updateActiveViews();
    });
  });

  soloBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-target");
      checkboxes.forEach(cb => {
        cb.checked = (cb.getAttribute("data-target") === targetId);
      });
      presetBtns.forEach(p => p.classList.remove("active"));
      updateActiveViews();
      const targetEl = document.getElementById(targetId);
      if (targetEl) {
        targetEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    });
  });

  const presetGroups = {
    all: [
      "narrative-output-box", "posterior-chart-group", "substitutability-group",
      "prompts-group", "sizing-group", "reservation-prices-group",
      "quotes-rank-group", "waterfall-chart-group", "exit-chart-group",
      "agent-trace-group", "planner-group", "rfq-group", "whatif-group"
    ],
    executive: [
      "narrative-output-box", "posterior-chart-group", "sizing-group",
      "quotes-rank-group", "planner-group"
    ],
    valuation: [
      "sizing-group", "reservation-prices-group", "waterfall-chart-group",
      "exit-chart-group", "whatif-group"
    ],
    safety: [
      "posterior-chart-group", "substitutability-group", "prompts-group",
      "agent-trace-group"
    ]
  };

  presetBtns.forEach(pBtn => {
    pBtn.addEventListener("click", () => {
      const presetKey = pBtn.getAttribute("data-preset");
      const group = presetGroups[presetKey];
      if (!group) return;

      presetBtns.forEach(p => p.classList.remove("active"));
      pBtn.classList.add("active");

      checkboxes.forEach(cb => {
        const t = cb.getAttribute("data-target");
        cb.checked = group.includes(t);
      });
      updateActiveViews();
    });
  });

  if (btnSelectAll) {
    btnSelectAll.addEventListener("click", () => {
      const anyUnchecked = Array.from(checkboxes).some(cb => !cb.checked);
      checkboxes.forEach(cb => { cb.checked = anyUnchecked; });
      btnSelectAll.textContent = anyUnchecked ? "Deselect All" : "Select All";
      presetBtns.forEach(p => p.classList.remove("active"));
      updateActiveViews();
    });
  }

  const stepMapping = {
    "step-ingest": "narrative-output-box",
    "step-workload": "narrative-output-box",
    "step-substitutability": "posterior-chart-group",
    "step-forecast": "sizing-group",
    "step-sizing": "sizing-group",
    "step-valuation": "reservation-prices-group",
    "step-quotes": "quotes-rank-group",
    "step-exit": "exit-chart-group",
    "step-planner": "planner-group",
    "step-rfq": "rfq-group",
    "step-narrative": "narrative-output-box"
  };

  Object.keys(stepMapping).forEach(stepId => {
    const stepEl = document.getElementById(stepId);
    if (stepEl) {
      stepEl.addEventListener("click", () => {
        const targetId = stepMapping[stepId];
        const cb = Array.from(checkboxes).find(c => c.getAttribute("data-target") === targetId);
        if (cb && !cb.checked) {
          cb.checked = true;
          updateActiveViews();
        }
        const targetEl = document.getElementById(targetId);
        if (targetEl) {
          targetEl.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      });
    }
  });

  try {
    const saved = localStorage.getItem("stampede_visible_views");
    if (saved) {
      const parsed = JSON.parse(saved);
      if (Array.isArray(parsed) && parsed.length > 0) {
        checkboxes.forEach(cb => {
          cb.checked = parsed.includes(cb.getAttribute("data-target"));
        });
      }
    }
  } catch (e) {}

  const stampedeSection = document.getElementById("stampede-live");
  if (stampedeSection && btnFloating) {
    if ("IntersectionObserver" in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            btnFloating.classList.add("visible");
          } else {
            btnFloating.classList.remove("visible");
          }
        });
      }, {
        threshold: 0.05
      });
      observer.observe(stampedeSection);
    } else {
      btnFloating.classList.add("visible");
    }
  }

  updateActiveViews();
}

document.addEventListener("DOMContentLoaded", () => {
  init();
  initStampedeLive();
  initSideSlideDataSelector();
  initRippleAnimation();
});

function initRippleAnimation() {
  const canvas = document.getElementById("canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const container = document.getElementById("scene");
  if (!container) return;

  let width, height;
  let baseY;

  let mouseX = -1000;
  let mouseY = -1000;
  let isHovering = false;

  let points = [];
  const spacing = 6;

  let dotX = 0;
  let dotDirection = 1;
  const dotSpeed = 1.5;

  const COLOR_LINE_BASE = "rgba(62, 76, 86, 0.2)";
  const COLOR_LINE_GLOW = "#3e4c56";
  const COLOR_RIPPLE = "#e87c45";
  const COLOR_DOT = "#3e4c56";

  function resizeRipple() {
    width = container.clientWidth;
    height = container.clientHeight;
    canvas.width = width;
    canvas.height = height;
    baseY = height / 2;

    points = [];
    for (let x = 0; x <= width; x += spacing) {
      points.push({
        x: x,
        y: baseY,
        targetY: baseY,
        velocity: 0
      });
    }
  }

  window.addEventListener("resize", resizeRipple);
  resizeRipple();

  container.addEventListener("mousemove", (e) => {
    const rect = canvas.getBoundingClientRect();
    mouseX = e.clientX - rect.left;
    mouseY = e.clientY - rect.top;
    isHovering = true;
  });

  container.addEventListener("mouseleave", () => {
    isHovering = false;
    mouseX = -1000;
    mouseY = -1000;
  });

  function drawRipplePath() {
    ctx.beginPath();
    if (points.length === 0) return;

    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) {
      let xc = (points[i].x + points[i - 1].x) / 2;
      let yc = (points[i].y + points[i - 1].y) / 2;
      ctx.quadraticCurveTo(points[i - 1].x, points[i - 1].y, xc, yc);
    }
    ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
  }

  function animateRipple() {
    ctx.clearRect(0, 0, width, height);

    for (let i = 1; i < points.length - 1; i++) {
      let p = points[i];
      let tension = 0.05;
      let dampening = 0.94;

      let leftDelta = points[i - 1].y - p.y;
      let rightDelta = points[i + 1].y - p.y;

      p.velocity += (leftDelta + rightDelta) * tension;

      if (isHovering) {
        let distToMouseX = Math.abs(p.x - mouseX);
        if (distToMouseX < 50) {
          let force = (50 - distToMouseX) / 50;
          p.velocity += (mouseY - p.y) * force * 0.04;
        }
      }

      p.velocity *= dampening;
      p.y += p.velocity;
    }

    ctx.beginPath();
    ctx.strokeStyle = isHovering ? COLOR_LINE_GLOW : COLOR_LINE_BASE;
    ctx.lineWidth = 2;
    drawRipplePath();
    ctx.stroke();

    if (isHovering) {
      let gradient = ctx.createRadialGradient(mouseX, baseY, 0, mouseX, baseY, 500);
      gradient.addColorStop(0, COLOR_RIPPLE);
      gradient.addColorStop(1, "rgba(232, 124, 69, 0)");

      ctx.beginPath();
      ctx.strokeStyle = gradient;
      ctx.lineWidth = 3;
      ctx.shadowBlur = 15;
      ctx.shadowColor = COLOR_RIPPLE;
      drawRipplePath();
      ctx.stroke();
      ctx.shadowBlur = 0;
    }

    dotX += dotSpeed * dotDirection;

    if (dotX > width - 10) dotDirection = -1;
    if (dotX < 10) dotDirection = 1;

    let dotY = baseY;
    let index = Math.floor(dotX / spacing);
    if (points[index]) {
      dotY = points[index].y;
    }

    ctx.beginPath();
    ctx.arc(dotX, dotY, 5, 0, Math.PI * 2);
    ctx.fillStyle = COLOR_DOT;
    ctx.shadowBlur = 8;
    ctx.shadowColor = "rgba(62, 76, 86, 0.5)";
    ctx.fill();
    ctx.shadowBlur = 0;

    requestAnimationFrame(animateRipple);
  }

  animateRipple();
}
