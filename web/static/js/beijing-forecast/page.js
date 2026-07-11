(async () => {
    try {
      await window.AIRPORT_FORECAST_DATA_READY;
    } catch (error) {
      document.getElementById("statusText").textContent = "预测数据加载失败";
      document.querySelector("main").innerHTML = `<div class="empty">${String(error?.message || error)}</div>`;
      return;
    }
    const lazyIndex = window.AIRPORT_FORECAST_LAZY_INDEX || null;
    const payload = window.CITY_AIRPORT_POTENTIAL_PASSENGER_FORECAST_DATA || { config: {}, rows: [] };
    if (lazyIndex?.config) payload.config = lazyIndex.config;
    const rawRows = (payload.rows || []).map((row) => ({ ...row }));

    const el = {
      statusText: document.getElementById("statusText"),
      seedSelect: document.getElementById("seedSelect"),
      asOfRange: document.getElementById("asOfRange"),
      reportSelect: document.getElementById("reportSelect"),
      asOfLabel: document.getElementById("asOfLabel"),
      summaryGrid: document.getElementById("summaryGrid"),
      forecastLegend: document.getElementById("forecastLegend"),
      forecastChart: document.getElementById("forecastChart"),
      componentCaption: document.getElementById("componentCaption"),
      componentYearSelect: document.getElementById("componentYearSelect"),
      componentGrid: document.getElementById("componentGrid"),
      forecastTable: document.getElementById("forecastTable"),
      tableCaption: document.getElementById("tableCaption"),
    };

    const REPORT_META = {
      public_consensus: { label: "初级预测", color: "#facc15" },
      basic_research: { label: "中级预测", color: "#fb7185" },
      professional_consulting: { label: "高级预测", color: "#22d3ee" },
      top_institution: { label: "专业级预测", color: "#34d399" },
      god_future_peek: { label: "神级预测", color: "#a78bfa" },
    };
    const CONFIG_REPORT_META = new Map((payload.config.forecast_reports || []).map((item) => [item.forecast_report_id, item]));
    const COMPONENTS = [
      { key: "business", label: "商务", weight: 1.3 },
      { key: "leisure", label: "休闲", weight: 1.0 },
      { key: "vfr", label: "探亲访友", weight: 0.75 },
      { key: "long_haul", label: "长途", weight: 1.35 },
      { key: "transfer", label: "中转", weight: 1.15 },
    ];

    const state = window.AirportForecastViewerState;

    function num(value, fallback = 0) {
      const parsed = Number(value);
      return Number.isFinite(parsed) ? parsed : fallback;
    }

    function uniq(values) {
      return Array.from(new Set(values));
    }

    function fmt(value, digits = 1) {
      if (!Number.isFinite(value)) return "n/a";
      return value.toLocaleString("zh-CN", { maximumFractionDigits: digits, minimumFractionDigits: digits });
    }

    function fmtPassenger(value) {
      return `${fmt(value, 1)} 百万人`;
    }

    function fmtPct(value, digits = 1) {
      return `${fmt(value, digits)}%`;
    }

    function escapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }

    function reportLabel(reportId) {
      return CONFIG_REPORT_META.get(reportId)?.forecast_report_display_name || REPORT_META[reportId]?.label || reportId;
    }

    function reportColor(reportId) {
      const tier = CONFIG_REPORT_META.get(reportId)?.forecast_report_tier;
      const tierColor = {
        initial: "#facc15",
        middle: "#fb7185",
        high: "#22d3ee",
        professional: "#34d399",
        god: "#a78bfa",
      }[tier];
      return CONFIG_REPORT_META.get(reportId)?.forecast_report_color || REPORT_META[reportId]?.color || tierColor || "#94a3b8";
    }

    function bottleneckLabel(value) {
      const labels = {
        demand_limited: "潜在需求",
        airline_supply_limited: "航司供给",
        unknown: "未知",
      };
      return labels[value] || value || "-";
    }

    function isGodRow(row) {
      return row.future_peek_mode === "true" || row.forecast_report_id === "god_future_peek";
    }

    function normalizeRows(rows) {
      return rows.map((row) => {
        const item = {
          ...row,
          seed: num(row.seed),
          as_of_year: num(row.as_of_year),
          forecast_year: num(row.forecast_year),
          forecast_horizon_years: num(row.forecast_horizon_years),
          configured_forecast_quality_score: num(row.configured_forecast_quality_score),
          forecast_quality_score: num(row.forecast_quality_score),
          current_effective_passengers_million: num(row.current_effective_passengers_million, num(row.current_potential_passengers_million)),
          current_potential_passengers_million: num(row.current_potential_passengers_million),
          current_airline_supply_passengers_million: num(row.current_airline_supply_passengers_million, num(row.current_potential_passengers_million)),
          forecast_effective_passengers_mid_million: num(row.forecast_effective_passengers_mid_million, num(row.forecast_potential_passengers_mid_million)),
          forecast_effective_passengers_low_million: num(row.forecast_effective_passengers_low_million, num(row.forecast_potential_passengers_low_million)),
          forecast_effective_passengers_high_million: num(row.forecast_effective_passengers_high_million, num(row.forecast_potential_passengers_high_million)),
          forecast_potential_passengers_mid_million: num(row.forecast_potential_passengers_mid_million),
          forecast_airline_supply_passengers_mid_million: num(row.forecast_airline_supply_passengers_mid_million, num(row.forecast_potential_passengers_mid_million)),
          realized_report_quality_score: num(row.realized_report_quality_score),
          realized_point_quality_score: num(row.realized_point_quality_score),
          realized_midpoint_accuracy_score: num(row.realized_midpoint_accuracy_score),
          realized_trend_accuracy_score: num(row.realized_trend_accuracy_score),
          realized_shape_accuracy_score: num(row.realized_shape_accuracy_score),
          realized_component_structure_score: num(row.realized_component_structure_score),
          realized_bottleneck_accuracy_score: num(row.realized_bottleneck_accuracy_score),
          realized_interval_calibration_score: num(row.realized_interval_calibration_score),
          realized_report_weighted_abs_error_pct: num(row.realized_report_weighted_abs_error_pct),
          realized_report_interval_hit_rate_pct: num(row.realized_report_interval_hit_rate_pct),
          realized_report_bias_pct: num(row.realized_report_bias_pct),
          debug_hidden_true_effective_passengers_million: num(row.debug_hidden_true_effective_passengers_million, num(row.debug_hidden_true_potential_passengers_million)),
          debug_hidden_true_potential_passengers_million: num(row.debug_hidden_true_potential_passengers_million),
          debug_hidden_true_airline_supply_passengers_million: num(row.debug_hidden_true_airline_supply_passengers_million, num(row.debug_hidden_true_potential_passengers_million)),
          debug_model_gap_to_true_pct: num(row.debug_model_gap_to_true_pct),
          forecast_confidence_pct: num(row.forecast_confidence_pct),
        };
        COMPONENTS.forEach((component) => {
          item[`${component.key}_forecast_effective_passengers_mid_million`] = num(row[`${component.key}_forecast_effective_passengers_mid_million`]);
          item[`${component.key}_forecast_effective_share_pct`] = num(row[`${component.key}_forecast_effective_share_pct`]);
          item[`${component.key}_debug_hidden_true_effective_passengers_million`] = num(row[`${component.key}_debug_hidden_true_effective_passengers_million`]);
          item[`${component.key}_debug_hidden_true_effective_share_pct`] = num(row[`${component.key}_debug_hidden_true_effective_share_pct`]);
          item[`${component.key}_debug_hidden_true_potential_passengers_million`] = num(row[`${component.key}_debug_hidden_true_potential_passengers_million`]);
          item[`${component.key}_debug_hidden_true_airline_supply_passengers_million`] = num(row[`${component.key}_debug_hidden_true_airline_supply_passengers_million`]);
        });
        return item;
      });
    }

    let rows = normalizeRows(rawRows);
    let loadedReportId = lazyIndex ? null : "__legacy_all__";
    let reportLoadGeneration = 0;
    const configuredReportOrder = (payload.config.forecast_reports || []).map((item) => item.forecast_report_id);

    async function ensureReportLoaded(reportId) {
      if (!lazyIndex || loadedReportId === reportId) return;
      const report = (lazyIndex.reports || []).find((item) => item.reportId === reportId);
      if (!report) throw new Error(`预测目录中不存在报告 ${reportId}`);
      const response = await fetch(new URL(report.file, lazyIndex.baseUrl), { cache: "force-cache" });
      if (!response.ok) throw new Error(`报告 ${reportId} 加载失败：HTTP ${response.status}`);
      const chunk = await response.json();
      if (chunk.schemaVersion !== lazyIndex.chunkSchemaVersion || chunk.reportId !== reportId) {
        throw new Error(`报告 ${reportId} 的数据协议不匹配`);
      }
      if (!Array.isArray(chunk.rows) || chunk.rows.length !== report.rowCount) {
        throw new Error(`报告 ${reportId} 的数据行数不匹配`);
      }
      rows = normalizeRows(chunk.rows);
      loadedReportId = reportId;
    }

    function reportOrder() {
      const ids = lazyIndex
        ? (lazyIndex.reports || []).map((report) => report.reportId)
        : uniq(rows.map((row) => row.forecast_report_id));
      return [
        ...configuredReportOrder.filter((id) => ids.includes(id)),
        ...ids.filter((id) => !configuredReportOrder.includes(id)).sort(),
      ];
    }

    function displayReportOrder() {
      return reportOrder().includes(state.reportId) ? [state.reportId] : [];
    }

    function rowsForSeed() {
      return rows.filter((row) => row.seed === state.seed);
    }

    function asOfYears() {
      return uniq(rowsForSeed()
        .filter((row) => row.forecast_report_id === state.reportId)
        .map((row) => row.as_of_year)
      ).sort((a, b) => a - b);
    }

    function selectedAsOfYear() {
      const years = asOfYears();
      return years[Math.min(state.asOfIndex, Math.max(0, years.length - 1))] || 0;
    }

    function selectedAsOfRows() {
      const asOf = selectedAsOfYear();
      return rowsForSeed()
        .filter((row) => row.as_of_year === asOf)
        .filter((row) => row.forecast_report_id === state.reportId)
        .sort((left, right) => {
          const reportDelta = reportOrder().indexOf(left.forecast_report_id) - reportOrder().indexOf(right.forecast_report_id);
          return reportDelta || left.forecast_year - right.forecast_year;
        });
    }

    function mean(values) {
      const clean = values.filter(Number.isFinite);
      if (!clean.length) return 0;
      return clean.reduce((sum, value) => sum + value, 0) / clean.length;
    }

    function formatHorizonList(values) {
      const sorted = uniq(values).sort((a, b) => a - b);
      if (!sorted.length) return "-";
      const continuous = sorted.every((value, index) => index === 0 || value === sorted[index - 1] + 1);
      if (continuous) return `${sorted[0]}-${sorted.at(-1)}`;
      if (sorted.length > 8) return `${sorted[0]}-${sorted.at(-1)} / ${sorted.length} 个年份`;
      return sorted.join(" / ");
    }

    function statCard(label, value, note, tone = "") {
      return `<article class="stat"><span>${escapeHtml(label)}</span><strong class="${tone}">${escapeHtml(value)}</strong><small>${escapeHtml(note)}</small></article>`;
    }

    function renderSummary() {
      const seedRows = rowsForSeed();
      const selectedRows = selectedAsOfRows();
      const reportRows = seedRows.filter((row) => row.forecast_report_id === state.reportId);
      const selectedReportRows = selectedRows.filter((row) => !isGodRow(row));
      const scoringRows = selectedReportRows.length ? selectedReportRows : selectedRows;
      const targetYears = uniq(selectedRows.map((row) => row.forecast_year)).sort((a, b) => a - b);
      const first = selectedRows[0] || reportRows[0] || {};
      const generationScores = scoringRows.map((row) => row.forecast_quality_score);
      const generationScoreLabel = generationScores.length
        ? `${fmt(Math.min(...generationScores), 1)} - ${fmt(Math.max(...generationScores), 1)}`
        : "n/a";
      const auditScore = num(first.realized_report_quality_score, NaN);
      const componentScore = num(first.realized_component_structure_score, NaN);
      const bottleneckScore = num(first.realized_bottleneck_accuracy_score, NaN);
      const hitRate = num(first.realized_report_interval_hit_rate_pct, NaN);
      const weightedError = num(first.realized_report_weighted_abs_error_pct, NaN);
      el.summaryGrid.innerHTML = [
        statCard("城市", payload.config.city_name || "北京", `${payload.config.city_airport_market_id || "beijing_airport_system"}`),
        statCard("报告", reportLabel(state.reportId), first.forecast_report_source || state.reportId),
        statCard("发布年份", String(selectedAsOfYear()), `${targetYears[0] || "-"} 到 ${targetYears.at(-1) || "-"}`),
        statCard("审计分", fmt(auditScore, 1), first.realized_report_bias_label || "输出后评分", auditScore >= 80 ? "positive" : auditScore >= 55 ? "warning" : "danger"),
        statCard("分项分", fmt(componentScore, 1), `瓶颈分 ${fmt(bottleneckScore, 1)}`, componentScore >= 80 ? "positive" : componentScore >= 55 ? "warning" : "danger"),
        statCard("生成分", generationScoreLabel, isGodRow(first) ? "神级未来透视" : "生成时使用的能力分"),
        statCard("加权误差", fmtPct(weightedError), `区间命中 ${fmtPct(hitRate)}`),
      ].join("");
    }

    function renderLegend() {
      const items = state.reportId === "god_future_peek"
        ? [`<span><i class="swatch" style="background:${reportColor(state.reportId)}"></i>神级预测 / 真实有效客流</span>`]
        : [
          `<span><i class="swatch" style="background:#f5f7fb"></i>隐藏真实有效客流</span>`,
          ...displayReportOrder().map((id) => `<span><i class="swatch" style="background:${reportColor(id)}"></i>${escapeHtml(reportLabel(id))}</span>`),
        ];
      el.forecastLegend.innerHTML = items.join("");
    }

    function emptyChart(node, message) {
      node.innerHTML = `<div class="empty">${escapeHtml(message)}</div>`;
    }

    function makeScale(domainMin, domainMax, rangeMin, rangeMax) {
      const span = domainMax - domainMin || 1;
      return (value) => rangeMin + (value - domainMin) / span * (rangeMax - rangeMin);
    }

    function svgText(x, y, content, options = {}) {
      const fill = options.fill || "#94a3b8";
      const anchor = options.anchor || "middle";
      const size = options.size || 11;
      return `<text x="${x}" y="${y}" fill="${fill}" font-size="${size}" text-anchor="${anchor}">${escapeHtml(content)}</text>`;
    }

    function svgLine(x1, y1, x2, y2, options = {}) {
      return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${options.stroke || "#273244"}" stroke-width="${options.width || 1}" stroke-dasharray="${options.dash || ""}" opacity="${options.opacity ?? 1}" />`;
    }

    function renderForecastChart() {
      const chartRows = selectedAsOfRows();
      if (!chartRows.length) {
        emptyChart(el.forecastChart, "没有预测数据");
        return;
      }

      const width = 1120;
      const height = 430;
      const margin = { top: 26, right: 28, bottom: 42, left: 62 };
      const innerW = width - margin.left - margin.right;
      const innerH = height - margin.top - margin.bottom;
      const asOf = selectedAsOfYear();
      const current = chartRows[0].current_effective_passengers_million;
      const targetYears = uniq(chartRows.map((row) => row.forecast_year)).sort((a, b) => a - b);
      const xMin = Math.min(asOf, ...targetYears);
      const xMax = Math.max(...targetYears);
      const values = [current];
      chartRows.forEach((row) => {
        values.push(
          row.forecast_effective_passengers_low_million,
          row.forecast_effective_passengers_mid_million,
          row.forecast_effective_passengers_high_million,
          row.debug_hidden_true_effective_passengers_million
        );
      });
      const yMin = Math.max(0, Math.min(...values) * 0.88);
      const yMax = Math.max(...values) * 1.08;
      const x = makeScale(xMin, xMax, margin.left, margin.left + innerW);
      const y = makeScale(yMin, yMax, margin.top + innerH, margin.top);
      const parts = [];

      for (let i = 0; i <= 5; i += 1) {
        const value = yMin + (yMax - yMin) * i / 5;
        const yy = y(value);
        parts.push(svgLine(margin.left, yy, margin.left + innerW, yy, { stroke: "#1f2937" }));
        parts.push(svgText(margin.left - 10, yy + 4, fmt(value, 0), { anchor: "end" }));
      }

      const span = xMax - xMin;
      const tickStep = span > 25 ? 5 : span > 14 ? 2 : 1;
      const xTicks = [];
      for (let year = Math.ceil(xMin / tickStep) * tickStep; year <= xMax; year += tickStep) {
        xTicks.push(year);
      }
      if (!xTicks.includes(xMin)) xTicks.unshift(xMin);
      if (!xTicks.includes(xMax)) xTicks.push(xMax);
      xTicks.forEach((year) => {
        const xx = x(year);
        parts.push(svgLine(xx, margin.top, xx, margin.top + innerH, { stroke: "#111827" }));
        parts.push(svgText(xx, margin.top + innerH + 24, String(year)));
      });

      parts.push(svgLine(margin.left, margin.top + innerH, margin.left + innerW, margin.top + innerH, { stroke: "#43536c" }));
      parts.push(svgLine(margin.left, margin.top, margin.left, margin.top + innerH, { stroke: "#43536c" }));
      parts.push(svgText(18, margin.top + 12, "百万人", { anchor: "start", size: 12 }));

      const trueMap = new Map();
      chartRows.forEach((row) => trueMap.set(row.forecast_year, row.debug_hidden_true_effective_passengers_million));
      const truePoints = [{ year: asOf, value: current }, ...targetYears.map((year) => ({ year, value: trueMap.get(year) }))];
      const truePolyline = truePoints.map((point) => `${x(point.year)},${y(point.value)}`).join(" ");
      const trueColor = state.reportId === "god_future_peek" ? reportColor(state.reportId) : "#f5f7fb";
      parts.push(`<polyline points="${truePolyline}" fill="none" stroke="${trueColor}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />`);
      truePoints.forEach((point) => {
        parts.push(`<circle cx="${x(point.year)}" cy="${y(point.value)}" r="4" fill="${trueColor}"><title>真实值 ${point.year}: ${fmtPassenger(point.value)}</title></circle>`);
      });

      if (state.reportId === "god_future_peek") {
        el.forecastChart.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="真实 seed 有效客流曲线">${parts.join("")}</svg>`;
        return;
      }

      const ids = displayReportOrder();
      const offsetStep = Math.min(8, innerW / Math.max(1, targetYears.length) / Math.max(6, ids.length + 2));
      ids.forEach((reportId, index) => {
        const reportRows = chartRows.filter((row) => row.forecast_report_id === reportId).sort((a, b) => a.forecast_year - b.forecast_year);
        if (!reportRows.length) return;
        const color = reportColor(reportId);
        const offset = (index - (ids.length - 1) / 2) * offsetStep;
        const points = [{ year: asOf, value: current }, ...reportRows.map((row) => ({ year: row.forecast_year, value: row.forecast_effective_passengers_mid_million }))];
        const polyline = points.map((point) => `${x(point.year)},${y(point.value)}`).join(" ");
        parts.push(`<polyline points="${polyline}" fill="none" stroke="${color}" stroke-width="${reportId === "god_future_peek" ? 1.8 : 2.4}" stroke-linecap="round" stroke-linejoin="round" opacity="${reportId === "god_future_peek" ? 0.75 : 0.95}" />`);
        reportRows.forEach((row) => {
          const xx = x(row.forecast_year) + offset;
          const yyLow = y(row.forecast_effective_passengers_low_million);
          const yyMid = y(row.forecast_effective_passengers_mid_million);
          const yyHigh = y(row.forecast_effective_passengers_high_million);
          const inside = row.debug_hidden_true_inside_forecast_range === "true";
          parts.push(svgLine(xx, yyLow, xx, yyHigh, { stroke: color, width: inside ? 1.4 : 2.2, opacity: inside ? 0.45 : 0.9 }));
          parts.push(svgLine(xx - 4, yyLow, xx + 4, yyLow, { stroke: color, width: 1, opacity: 0.65 }));
          parts.push(svgLine(xx - 4, yyHigh, xx + 4, yyHigh, { stroke: color, width: 1, opacity: 0.65 }));
          parts.push(`<circle cx="${xx}" cy="${yyMid}" r="${inside ? 3 : 4.6}" fill="${color}" stroke="${inside ? "#070a0f" : "#f5f7fb"}" stroke-width="${inside ? 1 : 1.5}"><title>${escapeHtml(reportLabel(reportId))} ${row.forecast_year}: 审计分 ${fmt(row.realized_point_quality_score, 1)}, 有效中值 ${fmtPassenger(row.forecast_effective_passengers_mid_million)}, 真实有效 ${fmtPassenger(row.debug_hidden_true_effective_passengers_million)}, 偏差 ${fmtPct(row.debug_model_gap_to_true_pct)}</title></circle>`);
        });
      });

      el.forecastChart.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="有效客流预测曲线">${parts.join("")}</svg>`;
    }

    function filteredContinuityRows() {
      return rowsForSeed().filter((row) => {
        if (state.continuityReport !== "all" && row.forecast_report_id !== state.continuityReport) return false;
        return Number.isFinite(row.forecast_quality_score) && row.future_peek_mode !== "true";
      });
    }

    function renderQualityChart() {
      const sample = filteredContinuityRows();
      if (!sample.length) {
        emptyChart(el.qualityChart, "没有连续性样本");
        return;
      }
      const width = 820;
      const height = 310;
      const margin = { top: 22, right: 22, bottom: 42, left: 54 };
      const innerW = width - margin.left - margin.right;
      const innerH = height - margin.top - margin.bottom;
      const yMax = Math.max(10, Math.min(60, Math.ceil(Math.max(...sample.map((row) => Math.abs(row.debug_model_gap_to_true_pct))) / 5) * 5));
      const x = makeScale(0, 70, margin.left, margin.left + innerW);
      const y = makeScale(0, yMax, margin.top + innerH, margin.top);
      const parts = [];

      for (let i = 0; i <= 7; i += 1) {
        const score = i * 10;
        const xx = x(score);
        parts.push(svgLine(xx, margin.top, xx, margin.top + innerH, { stroke: "#111827" }));
        parts.push(svgText(xx, margin.top + innerH + 24, String(score)));
      }
      for (let i = 0; i <= 5; i += 1) {
        const value = yMax * i / 5;
        const yy = y(value);
        parts.push(svgLine(margin.left, yy, margin.left + innerW, yy, { stroke: "#1f2937" }));
        parts.push(svgText(margin.left - 10, yy + 4, fmt(value, 0), { anchor: "end" }));
      }

      parts.push(svgText(margin.left + innerW / 2, height - 8, "forecast_quality_score", { size: 12 }));
      parts.push(svgText(12, margin.top + 12, "误差%", { anchor: "start", size: 12 }));

      sample.forEach((row) => {
        const xx = x(row.forecast_quality_score);
        const yy = y(Math.min(yMax, Math.abs(row.debug_model_gap_to_true_pct)));
        const color = reportColor(row.forecast_report_id);
        const outside = row.debug_hidden_true_inside_forecast_range !== "true";
        parts.push(`<circle cx="${xx}" cy="${yy}" r="${outside ? 4.2 : 3.1}" fill="${color}" fill-opacity="${outside ? 0.95 : 0.62}" stroke="${outside ? "#f5f7fb" : "#070a0f"}" stroke-width="${outside ? 1.2 : 0.8}"><title>${escapeHtml(reportLabel(row.forecast_report_id))} ${row.as_of_year}->${row.forecast_year}: 分数 ${fmt(row.forecast_quality_score, 1)}, 绝对误差 ${fmtPct(Math.abs(row.debug_model_gap_to_true_pct))}, 区间${outside ? "外" : "内"}</title></circle>`);
      });

      const buckets = qualityBuckets(sample);
      const bucketPoints = buckets
        .filter((bucket) => bucket.count > 0)
        .map((bucket) => `${x((bucket.low + bucket.high) / 2)},${y(Math.min(yMax, bucket.avgGap))}`)
        .join(" ");
      if (bucketPoints) {
        parts.push(`<polyline points="${bucketPoints}" fill="none" stroke="#f5f7fb" stroke-width="2" stroke-dasharray="5 5" opacity="0.65" />`);
      }

      el.qualityChart.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="质量分数和真实误差连续性">${parts.join("")}</svg>`;
    }

    function qualityBuckets(sample) {
      const definitions = [
        { label: "0-20", low: 0, high: 20 },
        { label: "20-35", low: 20, high: 35 },
        { label: "35-50", low: 35, high: 50 },
        { label: "50-60", low: 50, high: 60 },
        { label: "60-70", low: 60, high: 70.0001 },
      ];
      return definitions.map((definition) => {
        const bucketRows = sample.filter((row) => row.forecast_quality_score >= definition.low && row.forecast_quality_score < definition.high);
        const outsidePct = bucketRows.length
          ? bucketRows.filter((row) => row.debug_hidden_true_inside_forecast_range !== "true").length / bucketRows.length * 100
          : 0;
        return {
          ...definition,
          count: bucketRows.length,
          avgGap: mean(bucketRows.map((row) => Math.abs(row.debug_model_gap_to_true_pct))),
          outsidePct,
        };
      });
    }

    function renderBuckets() {
      const sample = filteredContinuityRows();
      const buckets = qualityBuckets(sample);
      el.bucketCaption.textContent = state.continuityReport === "all" ? "全部普通预测" : reportLabel(state.continuityReport);
      el.scoreBuckets.innerHTML = buckets.map((bucket) => {
        const width = Math.min(100, bucket.avgGap * 3.2);
        return `<article class="score-card">
          <span>评分 ${escapeHtml(bucket.label)}</span>
          <strong>${fmtPct(bucket.avgGap)}</strong>
          <small>${bucket.count} 条，区间外 ${fmtPct(bucket.outsidePct)}</small>
          <div class="score-bar"><i style="width:${width}%"></i></div>
        </article>`;
      }).join("");
    }

    function renderReportCards() {
      const seedRows = rowsForSeed();
      const cards = reportOrder().map((reportId) => {
        const reportRows = seedRows.filter((row) => row.forecast_report_id === reportId);
        if (!reportRows.length) return "";
        const ordinary = reportRows.filter((row) => row.future_peek_mode !== "true");
        const scoreValues = reportRows.map((row) => row.forecast_quality_score);
        const sample = ordinary.length ? ordinary : reportRows;
        const avgGap = mean(sample.map((row) => Math.abs(row.debug_model_gap_to_true_pct)));
        const outsidePct = sample.length
          ? sample.filter((row) => row.debug_hidden_true_inside_forecast_range !== "true").length / sample.length * 100
          : 0;
        const first = reportRows[0];
        const scoreRange = `${fmt(Math.min(...scoreValues), 1)} - ${fmt(Math.max(...scoreValues), 1)}`;
        return `<article class="score-card">
          <span><i class="swatch" style="background:${reportColor(reportId)}"></i> ${escapeHtml(reportLabel(reportId))}</span>
          <strong>${scoreRange}</strong>
          <small>${escapeHtml(first.forecast_bias_direction || "mixed")} / 平均误差 ${fmtPct(avgGap)} / 区间外 ${fmtPct(outsidePct)}</small>
          <div class="score-bar"><i style="width:${Math.min(100, Math.max(...scoreValues))}%"></i></div>
        </article>`;
      });
      el.reportCards.innerHTML = cards.join("");
    }

    function scoreTone(score) {
      if (score >= 80) return "positive";
      if (score >= 55) return "warning";
      return "danger";
    }

    function selectedComponentRow() {
      const rowsForAsOf = selectedAsOfRows();
      if (!rowsForAsOf.length) return null;
      const years = rowsForAsOf.map((row) => row.forecast_year);
      if (!years.includes(state.componentYear)) {
        state.componentYear = years.at(-1);
      }
      return rowsForAsOf.find((row) => row.forecast_year === state.componentYear) || rowsForAsOf.at(-1);
    }

    function renderComponentBreakdown() {
      const row = selectedComponentRow();
      if (!row) {
        el.componentGrid.innerHTML = `<div class="empty">没有分项数据</div>`;
        return;
      }
      el.componentCaption.textContent = `${selectedAsOfYear()} 年发布，目标 ${row.forecast_year}，${bottleneckLabel(row.forecast_market_bottleneck)}瓶颈`;
      el.componentGrid.innerHTML = COMPONENTS.map((component) => {
        const forecast = row[`${component.key}_forecast_effective_passengers_mid_million`];
        const trueValue = row[`${component.key}_debug_hidden_true_effective_passengers_million`];
        const forecastShare = row[`${component.key}_forecast_effective_share_pct`];
        const trueShare = row[`${component.key}_debug_hidden_true_effective_share_pct`];
        const potential = row[`${component.key}_debug_hidden_true_potential_passengers_million`];
        const supply = row[`${component.key}_debug_hidden_true_airline_supply_passengers_million`];
        const gapPct = trueValue ? (forecast - trueValue) / trueValue * 100 : 0;
        const tone = Math.abs(gapPct) >= 15 ? "danger" : Math.abs(gapPct) >= 8 ? "warning" : "positive";
        return `<article class="score-card">
          <span>${escapeHtml(component.label)}有效客流</span>
          <strong class="${tone}">${fmtPassenger(forecast)}</strong>
          <small>真实 ${fmtPassenger(trueValue)} / 偏差 ${fmtPct(gapPct)}</small>
          <small>占比 ${fmtPct(forecastShare)} / 真实 ${fmtPct(trueShare)}</small>
          <small>真实潜在 ${fmtPassenger(potential)} / 真实供给 ${fmtPassenger(supply)}</small>
        </article>`;
      }).join("");
    }

    function renderTable() {
      const tableRows = selectedAsOfRows();
      el.tableCaption.textContent = `${selectedAsOfYear()} 年发布，${reportLabel(state.reportId)}，${tableRows.length} 条预测`;
      el.forecastTable.innerHTML = tableRows.map((row) => {
        const inside = row.debug_hidden_true_inside_forecast_range === "true";
        const gap = row.debug_model_gap_to_true_pct;
        return `<tr>
          <td>${row.forecast_year}</td>
          <td class="${scoreTone(row.realized_point_quality_score)}">${fmt(row.realized_point_quality_score, 1)}</td>
          <td class="muted">${fmt(row.forecast_quality_score, 1)}</td>
          <td>${escapeHtml(row.forecast_bias_direction)}</td>
          <td>${fmtPct(row.forecast_confidence_pct)}</td>
          <td>${fmt(row.forecast_effective_passengers_mid_million, 1)}</td>
          <td>${fmt(row.forecast_potential_passengers_mid_million, 1)} / ${fmt(row.forecast_airline_supply_passengers_mid_million, 1)}</td>
          <td>${fmt(row.forecast_effective_passengers_low_million, 1)} - ${fmt(row.forecast_effective_passengers_high_million, 1)}</td>
          <td>${fmt(row.debug_hidden_true_effective_passengers_million, 1)}</td>
          <td>${fmt(row.debug_hidden_true_potential_passengers_million, 1)} / ${fmt(row.debug_hidden_true_airline_supply_passengers_million, 1)}</td>
          <td>${bottleneckLabel(row.forecast_market_bottleneck)} / ${bottleneckLabel(row.debug_hidden_true_market_bottleneck)}</td>
          <td class="${Math.abs(gap) >= 15 ? "danger" : Math.abs(gap) >= 8 ? "warning" : "positive"}">${fmtPct(gap)}</td>
          <td class="${inside ? "positive" : "danger"}">${inside ? "是" : "否"}</td>
        </tr>`;
      }).join("");
    }

    function syncControls() {
      const seeds = lazyIndex?.seeds?.length
        ? [...lazyIndex.seeds]
        : uniq(rows.map((row) => row.seed)).sort((a, b) => a - b);
      if (state.seed === null) state.seed = seeds[0] || null;
      el.seedSelect.innerHTML = seeds.map((seed) => `<option value="${seed}">${seed}</option>`).join("");
      el.seedSelect.value = String(state.seed);

      const reports = reportOrder();
      if (!reports.includes(state.reportId)) state.reportId = reports[0] || "";
      el.reportSelect.innerHTML = reports.map((id) => {
        return `<option value="${escapeHtml(id)}">${escapeHtml(reportLabel(id))}</option>`;
      }).join("");
      el.reportSelect.value = state.reportId;

      const years = asOfYears();
      el.asOfRange.min = "0";
      el.asOfRange.max = String(Math.max(0, years.length - 1));
      el.asOfRange.value = String(Math.min(state.asOfIndex, Math.max(0, years.length - 1)));
      el.asOfLabel.textContent = `${selectedAsOfYear()} 年发布，显示未来 ${formatHorizonList(selectedAsOfRows().map((row) => row.forecast_horizon_years))} 年窗口`;

      const componentRows = selectedAsOfRows();
      const componentYears = componentRows.map((row) => row.forecast_year);
      if (!componentYears.includes(state.componentYear)) state.componentYear = componentYears.at(-1) || null;
      el.componentYearSelect.innerHTML = componentYears
        .map((year) => `<option value="${year}">${year}</option>`)
        .join("");
      el.componentYearSelect.value = String(state.componentYear || "");
    }

    function render() {
      if (!rows.length) {
        document.querySelector("main").innerHTML = `<div class="empty">No forecast data found</div>`;
        return;
      }
      syncControls();
      renderSummary();
      renderLegend();
      renderForecastChart();
      renderComponentBreakdown();
      renderTable();
      const totalRows = lazyIndex?.totalRows ?? rows.length;
      el.statusText.textContent = `${totalRows} rows / ${reportOrder().length} reports`;
    }

    function bindEvents() {
      el.seedSelect.addEventListener("change", () => {
        state.seed = Number(el.seedSelect.value);
        state.asOfIndex = 0;
        render();
      });
      el.asOfRange.addEventListener("input", () => {
        state.asOfIndex = Number(el.asOfRange.value);
        state.componentYear = null;
        render();
      });
      el.reportSelect.addEventListener("change", async () => {
        const generation = ++reportLoadGeneration;
        state.reportId = el.reportSelect.value;
        state.asOfIndex = 0;
        state.componentYear = null;
        el.reportSelect.disabled = true;
        el.statusText.textContent = `正在加载 ${reportLabel(state.reportId)}…`;
        try {
          await ensureReportLoaded(state.reportId);
          if (generation === reportLoadGeneration) render();
        } catch (error) {
          if (generation === reportLoadGeneration) {
            el.statusText.textContent = "报告加载失败";
            emptyChart(el.forecastChart, String(error?.message || error));
          }
        } finally {
          if (generation === reportLoadGeneration) el.reportSelect.disabled = false;
        }
      });
      el.componentYearSelect.addEventListener("change", () => {
        state.componentYear = Number(el.componentYearSelect.value);
        render();
      });
    }

    bindEvents();
    if (lazyIndex) {
      state.reportId = lazyIndex.defaultReportId || reportOrder()[0] || "";
      state.seed = lazyIndex.seeds?.[0] ?? null;
      el.statusText.textContent = `正在加载 ${reportLabel(state.reportId)}…`;
      try {
        await ensureReportLoaded(state.reportId);
      } catch (error) {
        el.statusText.textContent = "预测数据加载失败";
        document.querySelector("main").innerHTML = `<div class="empty">${String(error?.message || error)}</div>`;
        return;
      }
    }
    render();
  })();
