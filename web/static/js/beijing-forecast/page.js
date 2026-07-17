(async () => {
  const state = window.AirportForecastViewerState;
  const client = window.AirportForecastDataClient;
  const renderers = window.AirportForecastRenderers;
  const { num, fmt, escapeHtml } = renderers;

  const el = {
    statusText: document.getElementById("statusText"),
    seedSelect: document.getElementById("seedSelect"),
    modeSelect: document.getElementById("modeSelect"),
    summaryGrid: document.getElementById("summaryGrid"),
    candidateLab: document.getElementById("candidateLab"),
    candidateState: document.getElementById("candidateState"),
    candidateTier: document.getElementById("candidateTier"),
    candidateStyle: document.getElementById("candidateStyle"),
    candidateModifierMode: document.getElementById("candidateModifierMode"),
    candidateScoreMin: document.getElementById("candidateScoreMin"),
    candidateScoreMax: document.getElementById("candidateScoreMax"),
    generateCandidate: document.getElementById("generateCandidate"),
    nextCandidate: document.getElementById("nextCandidate"),
    leaveCandidate: document.getElementById("leaveCandidate"),
    candidateModifiers: document.getElementById("candidateModifiers"),
    candidateAvailability: document.getElementById("candidateAvailability"),
    candidateResult: document.getElementById("candidateResult"),
    narrativeTitle: document.getElementById("narrativeTitle"),
    narrativeStyle: document.getElementById("narrativeStyle"),
    narrativeTags: document.getElementById("narrativeTags"),
    narrativeConviction: document.getElementById("narrativeConviction"),
    actualScore: document.getElementById("actualScore"),
    narrativeSummary: document.getElementById("narrativeSummary"),
    asOfRange: document.getElementById("asOfRange"),
    asOfLabel: document.getElementById("asOfLabel"),
    reportSelect: document.getElementById("reportSelect"),
    scopeTabs: document.getElementById("scopeTabs"),
    forecastLegend: document.getElementById("forecastLegend"),
    forecastChart: document.getElementById("forecastChart"),
    componentCaption: document.getElementById("componentCaption"),
    componentGrid: document.getElementById("componentGrid"),
    tableCaption: document.getElementById("tableCaption"),
    forecastTableHead: document.getElementById("forecastTableHead"),
    forecastTable: document.getElementById("forecastTable"),
  };

  try {
    await window.AIRPORT_FORECAST_DATA_READY;
  } catch (error) {
    el.statusText.textContent = "预测数据加载失败";
    document.querySelector("main").innerHTML = `<div class="empty">${escapeHtml(error?.message || error)}</div>`;
    return;
  }

  const playerIndex = window.AIRPORT_FORECAST_LAZY_INDEX;
  const reportCache = new Map();
  let activeIndex = playerIndex;
  let config = playerIndex.config || {};
  let rows = [];
  let loadGeneration = 0;
  let candidateCatalogPayload = null;
  let candidateCatalogError = "";
  let candidateControlsInitialized = false;
  let candidateBusy = false;
  let lastFormalSelection = null;

  const COMPONENTS = {
    business: "商务",
    leisure: "休闲",
    vfr: "探亲访友",
    long_haul: "长途",
    transfer: "中转",
  };
  const SCOPE_LABELS = { total: "总客流", ...COMPONENTS };
  const TIER_COLORS = {
    initial: "#facc15",
    middle: "#fb7185",
    high: "#22d3ee",
    professional: "#34d399",
    god: "#a78bfa",
  };
  const TIER_LABELS = {
    initial: "初级",
    middle: "中级",
    high: "高级",
    professional: "专业级",
    god: "开发审计",
  };
  const MODIFIER_GROUP_LABELS = {
    position: "立场",
    method_focus: "方法侧重",
    revision_behavior: "修订行为",
    uncertainty: "不确定性",
  };
  const DRIVER_LABELS = {
    airline_supply_cycle: "航司供给周期",
    city_demand_growth: "城市需求增长",
    city_demand_slowdown: "城市需求放缓",
    airline_capacity_response: "航司运力响应",
    airline_supply_expansion: "航司扩张",
    city_demand_realization: "需求兑现",
    potential_demand: "潜在需求",
    stable_city_fundamentals: "城市基本面",
    mature_market_trend: "成熟市场趋势",
    long_term_mean_reversion: "长期均值回归",
    hidden_true_path: "隐藏真实路径",
    development_audit: "开发审计",
  };
  const REVISION_LABELS = {
    initial_report: "首次发布",
    routine_inherited_update: "延续上一期观点，按已实现数据例行更新",
    realized_result_above_previous_view: "实际结果高于上一期判断",
    realized_result_below_previous_view: "实际结果低于上一期判断",
    airline_supply_signal_changed: "航司供给信号发生变化",
    city_demand_signal_changed: "城市需求信号发生变化",
    turning_window_shifted: "预期转向窗口发生移动",
    future_truth_refresh: "开发审计真实路径刷新",
  };
  const BOTTLENECK_LABELS = {
    demand_limited: "需求约束",
    airline_supply_limited: "航司供给约束",
    unknown: "未知",
  };
  const SIGNAL_LABELS = {
    strong_decline: "明显收缩",
    decline: "温和收缩",
    stable: "大体稳定",
    moderate_growth: "温和增长",
    strong_growth: "较强增长",
    unclear: "信号不清",
    acceleration: "加速",
    deceleration: "减速",
    none: "暂无明确转向",
  };

  function normalizeRows(source) {
    return source.map((row) => {
      const normalized = { ...row };
      [
        "seed",
        "as_of_year",
        "forecast_year",
        "forecast_horizon_years",
        "current_effective_passengers_million",
        "current_airline_serviceable_supply_million",
        "forecast_effective_passengers_mid_million",
        "forecast_effective_passengers_low_million",
        "forecast_effective_passengers_high_million",
        "forecast_potential_passengers_mid_million",
        "forecast_airline_supply_passengers_mid_million",
        "forecast_airline_serviceable_supply_mid_million",
        "forecast_airline_unused_capacity_mid_million",
        "forecast_confidence_pct",
        "forecast_conviction_pct",
        "forecast_revision_pct",
        "forecast_component_revision_pp",
        "forecast_previous_mid_million",
        "realized_report_quality_score",
        "realized_result_quality_score",
        "realized_report_process_quality_score",
        "realized_total_result_quality_score",
        "realized_component_result_quality_score",
        "realized_component_potential_structure_score",
        "realized_component_supply_structure_score",
        "realized_component_fulfillment_score",
        "realized_component_interval_calibration_score",
        "realized_report_weighted_abs_error_pct",
        "realized_report_interval_hit_rate_pct",
        "realized_turn_timing_score",
        "realized_revision_discipline_score",
        "debug_hidden_true_effective_passengers_million",
        "debug_model_gap_to_true_pct",
      ].forEach((key) => {
        if (row[key] !== undefined && row[key] !== null && row[key] !== "") {
          normalized[key] = num(row[key]);
        }
      });
      Object.keys(COMPONENTS).forEach((component) => {
        [
          `${component}_forecast_effective_passengers_mid_million`,
          `${component}_forecast_effective_passengers_low_million`,
          `${component}_forecast_effective_passengers_high_million`,
          `${component}_forecast_effective_share_pct`,
          `${component}_forecast_potential_passengers_mid_million`,
          `${component}_forecast_potential_share_pct`,
          `${component}_forecast_airline_offered_capacity_million`,
          `${component}_forecast_airline_supply_passengers_mid_million`,
          `${component}_forecast_airline_supply_share_pct`,
          `${component}_forecast_airline_supply_fulfillment_pct`,
          `${component}_forecast_airline_supply_gap_million`,
          `current_${component}_effective_passengers_million`,
          `${component}_debug_hidden_true_effective_passengers_million`,
          `${component}_debug_hidden_true_potential_share_pct`,
          `${component}_debug_hidden_true_airline_supply_share_pct`,
          `${component}_debug_hidden_true_airline_supply_fulfillment_pct`,
        ].forEach((key) => {
          if (row[key] !== undefined) normalized[key] = num(row[key]);
        });
      });
      return normalized;
    });
  }

  function splitMetadata(value) {
    return String(value || "")
      .split(";")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function candidateActive() {
    return Boolean(
      state.candidateResult
      && state.reportId === state.candidateResult.candidate?.candidateId,
    );
  }

  function candidateCatalog() {
    return candidateCatalogPayload?.catalog || null;
  }

  async function ensureCandidateCatalog() {
    if (candidateCatalogPayload || candidateCatalogError) return;
    try {
      candidateCatalogPayload = await client.loadCandidateCatalog();
    } catch (error) {
      candidateCatalogError = error?.message || String(error);
    }
  }

  function selectedCandidateTier() {
    return (candidateCatalog()?.tiers || []).find(
      (tier) => tier.tierProfileId === el.candidateTier.value,
    ) || null;
  }

  function selectedCandidateStyle() {
    return (candidateCatalog()?.styles || []).find(
      (style) => style.narrativeProfileId === el.candidateStyle.value,
    ) || null;
  }

  function candidateModifierMeta(modifierId) {
    return (candidateCatalog()?.modifiers || []).find(
      (modifier) => modifier.modifierId === modifierId,
    ) || {};
  }

  function manualCandidateModifierIds() {
    return Array.from(
      el.candidateModifiers.querySelectorAll('input[type="checkbox"]:checked'),
    ).map((input) => input.value);
  }

  function candidateModifiersCompatible(modifierIds) {
    const selected = new Set(modifierIds);
    return !(candidateCatalog()?.incompatibleModifierPairs || []).some(
      (pair) => pair.every((modifierId) => selected.has(modifierId)),
    );
  }

  function renderCandidateModifierChoices() {
    const style = selectedCandidateStyle();
    const manual = el.candidateModifierMode.value === "manual";
    el.candidateModifiers.hidden = !manual;
    if (!manual || !style) {
      el.candidateModifiers.innerHTML = "";
      return;
    }
    const previous = new Set(manualCandidateModifierIds());
    el.candidateModifiers.innerHTML = style.candidateModifierIds.map((modifierId) => {
      const meta = candidateModifierMeta(modifierId);
      const title = [meta.description, meta.tradeoff ? `代价：${meta.tradeoff}` : ""]
        .filter(Boolean)
        .join(" ");
      return `<label class="candidate-modifier-option" title="${escapeHtml(title)}"><input type="checkbox" value="${escapeHtml(modifierId)}"${previous.has(modifierId) ? " checked" : ""} /><span>${escapeHtml(meta.label || modifierId)}</span></label>`;
    }).join("");
  }

  function initializeCandidateControls() {
    const catalog = candidateCatalog();
    if (!catalog || candidateControlsInitialized) return;
    const currentMeta = reportMeta(state.reportId);
    el.candidateTier.innerHTML = catalog.tiers.map((tier) => (
      `<option value="${escapeHtml(tier.tierProfileId)}">${escapeHtml(tier.label)} · ${tier.naturalHorizonYears}年</option>`
    )).join("");
    el.candidateStyle.innerHTML = catalog.styles.map((style) => (
      `<option value="${escapeHtml(style.narrativeProfileId)}">${escapeHtml(style.label)}</option>`
    )).join("");
    if (catalog.tiers.some((tier) => tier.tierProfileId === currentMeta.forecast_report_tier_profile_id)) {
      el.candidateTier.value = currentMeta.forecast_report_tier_profile_id;
    }
    if (catalog.styles.some((style) => style.narrativeProfileId === currentMeta.forecast_narrative_profile_id)) {
      el.candidateStyle.value = currentMeta.forecast_narrative_profile_id;
    }
    candidateControlsInitialized = true;
    renderCandidateModifierChoices();
  }

  function candidateScoreRange() {
    return {
      minimum: Number(el.candidateScoreMin.value),
      maximum: Number(el.candidateScoreMax.value),
    };
  }

  function candidateRequestIsValid() {
    const catalog = candidateCatalog();
    const tier = selectedCandidateTier();
    const style = selectedCandidateStyle();
    const range = candidateScoreRange();
    const asOfYear = selectedAsOfYear();
    if (!catalog || !tier || !style || !Number.isFinite(asOfYear)) return false;
    if (
      !Number.isFinite(range.minimum)
      || !Number.isFinite(range.maximum)
      || range.minimum < 0
      || range.maximum > 100
      || range.maximum - range.minimum < catalog.minimumScoreBandWidth
    ) return false;
    if (asOfYear > tier.maxFullAsOfYear) return false;
    if (el.candidateModifierMode.value === "manual") {
      const selected = manualCandidateModifierIds();
      if (selected.length > 2 || !candidateModifiersCompatible(selected)) return false;
    }
    return true;
  }

  function renderActualScore(first) {
    if (state.mode !== "audit") {
      el.actualScore.hidden = true;
      el.actualScore.textContent = "";
      el.actualScore.className = "actual-score";
      return;
    }
    el.actualScore.hidden = false;
    const futurePeek = String(first.future_peek_mode || "").toLowerCase() === "true";
    if (futurePeek) {
      el.actualScore.textContent = "审计基准 · 不参与评分";
      el.actualScore.className = "actual-score actual-score-baseline";
      return;
    }
    const score = Number(first.realized_report_process_quality_score);
    const scoreClass = score >= 80
      ? "actual-score-high"
      : score >= 60
        ? "actual-score-mid"
        : "actual-score-low";
    el.actualScore.textContent = Number.isFinite(score)
      ? `实际评分 ${fmt(score)} / 100`
      : "实际评分 -";
    el.actualScore.className = `actual-score ${scoreClass}`;
  }

  function reportMeta(reportId) {
    if (
      state.candidateResult
      && state.candidateResult.candidate?.candidateId === reportId
    ) {
      return state.candidateResult.candidate.reportMeta || {};
    }
    return (config.forecast_reports || []).find(
      (report) => report.forecast_report_id === reportId,
    ) || {};
  }

  function reportLabel(reportId) {
    const meta = reportMeta(reportId);
    const label = [
      TIER_LABELS[meta.forecast_report_tier] || meta.forecast_report_tier,
      meta.forecast_report_display_name || reportId,
    ].filter(Boolean).join(" · ");
    return state.candidateResult?.candidate?.candidateId === reportId
      ? `${label}（临时候选）`
      : label;
  }

  function reportColor(reportId) {
    return TIER_COLORS[reportMeta(reportId).forecast_report_tier] || "#60a5fa";
  }

  function reportIds() {
    const ids = (activeIndex.reports || []).map((report) => report.reportId);
    const candidateId = state.candidateResult?.candidate?.candidateId;
    if (state.mode === "audit" && candidateId && !ids.includes(candidateId)) ids.push(candidateId);
    return ids;
  }

  async function activateMode(mode) {
    state.mode = mode;
    if (mode === "audit") {
      activeIndex = await client.loadAuditIndex(playerIndex);
      await ensureCandidateCatalog();
    } else {
      activeIndex = playerIndex;
      state.candidateResult = null;
      state.candidateNonce = 0;
      lastFormalSelection = null;
    }
    config = activeIndex.config || {};
    const ids = reportIds();
    if (!ids.includes(state.reportId)) {
      state.reportId = activeIndex?.defaultReportId || ids[0] || "";
    }
    state.asOfIndex = 0;
    renderReportOptions();
    await ensureReportLoaded(state.reportId);
  }

  async function ensureReportLoaded(reportId) {
    const generation = ++loadGeneration;
    if (
      state.candidateResult
      && state.candidateResult.candidate?.candidateId === reportId
    ) {
      rows = normalizeRows(state.candidateResult.candidate.rows || []);
      renderAll();
      return;
    }
    const cacheKey = `${activeIndex.dataMode}:${reportId}`;
    el.statusText.textContent = `加载${reportLabel(reportId)}…`;
    let sourceRows = reportCache.get(cacheKey);
    if (!sourceRows) {
      sourceRows = await client.loadReport(activeIndex, reportId);
      reportCache.set(cacheKey, sourceRows);
    }
    if (generation !== loadGeneration) return;
    rows = normalizeRows(sourceRows);
    renderAll();
  }

  function seeds() {
    return activeIndex?.seeds || Array.from(new Set(rows.map((row) => row.seed)));
  }

  function asOfYears() {
    return Array.from(
      new Set(
        rows
          .filter((row) => row.seed === state.seed)
          .map((row) => row.as_of_year),
      ),
    ).sort((left, right) => left - right);
  }

  function selectedAsOfYear() {
    const years = asOfYears();
    return years[Math.min(state.asOfIndex, Math.max(0, years.length - 1))] || 0;
  }

  function selectedRows() {
    const year = selectedAsOfYear();
    return rows
      .filter((row) => row.seed === state.seed && row.as_of_year === year)
      .sort((left, right) => left.forecast_year - right.forecast_year);
  }

  function selectedFirst() {
    return selectedRows()[0] || {};
  }

  function scopePredicted(row) {
    if (state.scope === "total") return row.forecast_effective_passengers_mid_million;
    return row[`${state.scope}_forecast_effective_passengers_mid_million`];
  }

  function scopeTrue(row) {
    if (state.scope === "total") return row.debug_hidden_true_effective_passengers_million;
    return row[`${state.scope}_debug_hidden_true_effective_passengers_million`];
  }

  function scopePotential(row) {
    if (state.scope === "total") return row.forecast_potential_passengers_mid_million;
    return row[`${state.scope}_forecast_potential_passengers_mid_million`];
  }

  function scopeSupply(row) {
    if (state.scope === "total") {
      return row.forecast_airline_supply_passengers_mid_million;
    }
    return row[`${state.scope}_forecast_airline_supply_passengers_mid_million`];
  }

  function scopeCurrent(row) {
    if (state.scope === "total") return row.current_effective_passengers_million;
    return row[`current_${state.scope}_effective_passengers_million`];
  }

  function scopeBand(row, edge) {
    if (state.scope === "total") {
      return row[`forecast_effective_passengers_${edge}_million`];
    }
    return row[`${state.scope}_forecast_effective_passengers_${edge}_million`];
  }

  function scopeInside(row) {
    if (state.scope === "total") {
      return row.debug_hidden_true_inside_forecast_range === "true";
    }
    return row[`${state.scope}_debug_hidden_true_inside_forecast_range`] === "true";
  }

  function scopeGapPct(row) {
    const actual = scopeTrue(row);
    return actual ? (scopePredicted(row) - actual) / actual * 100 : 0;
  }

  function statCard(label, value, note, tone = "") {
    return `<article class="stat"><span>${escapeHtml(label)}</span><strong class="${tone}">${escapeHtml(value)}</strong><small>${escapeHtml(note)}</small></article>`;
  }

  function infoCard(label, value, note = "") {
    return `<article class="score-card"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong><small>${escapeHtml(note)}</small></article>`;
  }

  function renderSeedOptions() {
    const values = seeds();
    if (!values.includes(state.seed)) state.seed = values[0] ?? null;
    el.seedSelect.innerHTML = values
      .map((seed) => `<option value="${seed}"${seed === state.seed ? " selected" : ""}>${seed}</option>`)
      .join("");
  }

  function renderReportOptions() {
    el.reportSelect.innerHTML = reportIds()
      .map((id) => `<option value="${escapeHtml(id)}"${id === state.reportId ? " selected" : ""}>${escapeHtml(reportLabel(id))}</option>`)
      .join("");
  }

  function renderTimeline() {
    const years = asOfYears();
    state.asOfIndex = Math.min(state.asOfIndex, Math.max(0, years.length - 1));
    el.asOfRange.min = "0";
    el.asOfRange.max = String(Math.max(0, years.length - 1));
    el.asOfRange.value = String(state.asOfIndex);
    el.asOfLabel.textContent = candidateActive()
      ? `临时候选发布于 ${selectedAsOfYear()} 年；完整期限评分后仅保留在当前页面`
      : `发布于 ${selectedAsOfYear()} 年；仅使用该时点可见历史与模糊研究信号`;
  }

  function renderSummary() {
    const first = selectedFirst();
    const selected = selectedRows();
    const start = selected[0]?.forecast_year || "-";
    const end = selected.at(-1)?.forecast_year || "-";
    const turnWindow = first.forecast_turn_window_start_year
      ? `${first.forecast_turn_window_start_year}–${first.forecast_turn_window_end_year}`
      : "暂无";
    const cards = [
      statCard(
        "报告",
        reportLabel(state.reportId),
        "研究风格",
      ),
      statCard("发布年份", String(selectedAsOfYear()), `覆盖 ${start}–${end}`),
      statCard("报告信心", `${fmt(first.forecast_conviction_pct)}%`, first.reported_confidence_style || "随期限衰减"),
      statCard("预期转向窗口", turnWindow, SIGNAL_LABELS[first.forecast_signal_turn_direction] || "没有明确转向"),
    ];
    if (state.mode === "audit") {
      cards.push(
        statCard("总量结果分", fmt(first.realized_total_result_quality_score), `加权误差 ${fmt(first.realized_report_weighted_abs_error_pct)}%`),
        statCard("分项结果分", fmt(first.realized_component_result_quality_score), "需求结构、供给分配、满足率与区间"),
      );
    }
    el.summaryGrid.innerHTML = cards.join("");
  }

  function renderNarrative() {
    const first = selectedFirst();
    el.narrativeTitle.textContent = first.forecast_narrative_headline || "暂无报告观点";
    el.narrativeStyle.textContent = [
      TIER_LABELS[first.forecast_report_tier] || first.forecast_report_tier,
      first.forecast_narrative_style_label,
    ].filter(Boolean).join(" · ") || "研究风格";
    const modifierLabels = splitMetadata(first.forecast_narrative_modifier_labels);
    const modifierGroups = splitMetadata(first.forecast_narrative_modifier_groups);
    const modifierDescriptions = splitMetadata(
      first.forecast_narrative_modifier_descriptions,
    );
    const modifierTradeoffs = splitMetadata(
      first.forecast_narrative_modifier_tradeoffs,
    );
    el.narrativeTags.innerHTML = modifierLabels.length
      ? modifierLabels.map((label, index) => {
        const group = modifierGroups[index] || "other";
        const groupLabel = MODIFIER_GROUP_LABELS[group] || "特征";
        const description = modifierDescriptions[index] || "";
        const tradeoff = modifierTradeoffs[index] || "";
        const title = [description, tradeoff ? `代价：${tradeoff}` : ""]
          .filter(Boolean)
          .join(" ");
        return `<span class="modifier-tag" data-group="${escapeHtml(group)}" title="${escapeHtml(title)}">${escapeHtml(groupLabel)} · ${escapeHtml(label)}</span>`;
      }).join("")
      : '<span class="modifier-tag" data-group="audit">无普通修饰标签</span>';
    el.narrativeConviction.textContent = `信心 ${fmt(first.forecast_conviction_pct)}%`;
    renderActualScore(first);
    const turn = first.forecast_turn_window_start_year
      ? `${first.forecast_turn_window_start_year}–${first.forecast_turn_window_end_year}`
      : "没有识别到明确窗口";
    el.narrativeSummary.innerHTML = `
      <div class="narrative-overview">
        <div class="narrative-lead">${escapeHtml(first.forecast_narrative_headline || "-")}</div>
        <p class="narrative-style-summary">${escapeHtml(first.forecast_narrative_style_summary || "该报告尚未提供研究方法说明。")}</p>
      </div>
      <dl class="narrative-facts">
        <div><dt>分析方法</dt><dd>${escapeHtml(first.forecast_narrative_style_method || "-")}</dd></div>
        <div><dt>典型盲点</dt><dd>${escapeHtml(first.forecast_narrative_style_blind_spot || "-")}</dd></div>
        <div><dt>主要驱动</dt><dd>${escapeHtml(DRIVER_LABELS[first.forecast_primary_driver] || first.forecast_primary_driver || "-")}</dd></div>
        <div><dt>次要驱动</dt><dd>${escapeHtml(DRIVER_LABELS[first.forecast_secondary_driver] || first.forecast_secondary_driver || "-")}</dd></div>
        <div><dt>需求信号</dt><dd>${escapeHtml(SIGNAL_LABELS[first.forecast_signal_demand_direction] || first.forecast_signal_demand_direction || "-")}</dd></div>
        <div><dt>供给信号</dt><dd>${escapeHtml(SIGNAL_LABELS[first.forecast_signal_supply_direction] || first.forecast_signal_supply_direction || "-")}</dd></div>
        <div><dt>转向判断</dt><dd>${escapeHtml(turn)}</dd></div>
        <div><dt>本期修订</dt><dd>${escapeHtml(REVISION_LABELS[first.forecast_revision_reason] || first.forecast_revision_reason || "-")}</dd></div>
      </dl>`;
  }

  function renderLegend() {
    const items = [
      `<span><i class="swatch" style="background:${reportColor(state.reportId)}"></i>${escapeHtml(reportLabel(state.reportId))} 中值与区间</span>`,
    ];
    if (state.mode === "audit") {
      items.push('<span><i class="swatch true"></i>隐藏真实路径（圆点可查看预测差异）</span>');
    }
    el.forecastLegend.innerHTML = items.join("");
  }

  function renderChart() {
    const selected = selectedRows();
    const first = selected[0];
    if (!first) {
      el.forecastChart.innerHTML = '<div class="empty">没有预测数据</div>';
      return;
    }
    el.forecastChart.innerHTML = renderers.chart({
      rows: selected,
      asOfYear: selectedAsOfYear(),
      currentValue: scopeCurrent(first),
      scopeLabel: SCOPE_LABELS[state.scope],
      color: reportColor(state.reportId),
      mode: state.mode,
      predictedValue: scopePredicted,
      predictedLow: (row) => scopeBand(row, "low"),
      predictedHigh: (row) => scopeBand(row, "high"),
      trueValue: scopeTrue,
    });
  }

  function renderScopeTabs() {
    el.scopeTabs.querySelectorAll("button").forEach((button) => {
      button.classList.toggle("active", button.dataset.scope === state.scope);
    });
  }

  function renderEvidence() {
    const first = selectedFirst();
    const componentScope = state.scope !== "total";
    const cards = [
      infoCard("当前口径", SCOPE_LABELS[state.scope], componentScope ? "独立需求结构与航司分配路径" : "总量预测路径是分项预测的权威边界"),
      infoCard("预测瓶颈", BOTTLENECK_LABELS[first.forecast_market_bottleneck] || first.forecast_market_bottleneck || "-", "本页不引入机场容量约束"),
      infoCard("相对公开趋势", `${fmt(first.market_consensus_gap_pct)}%`, "报告中值相对朴素公开趋势的偏离"),
      infoCard("修订幅度", componentScope ? `${fmt(first.forecast_component_revision_pp)} 个百分点` : `${fmt(first.forecast_revision_pct)}%`, REVISION_LABELS[first.forecast_revision_reason] || "首次发布"),
    ];
    if (componentScope) {
      cards.push(
        infoCard("供给满足率", `${fmt(first[`${state.scope}_forecast_airline_supply_fulfillment_pct`])}%`, `未满足 ${fmt(first[`${state.scope}_forecast_airline_supply_gap_million`])} 百万人`),
        infoCard("结构占比", `${fmt(first[`${state.scope}_forecast_potential_share_pct`])}% → ${fmt(first[`${state.scope}_forecast_airline_supply_share_pct`])}%`, "潜在需求占比 → 航司有效供给占比"),
      );
    }
    if (state.mode === "audit") {
      cards.push(
        infoCard("潜在需求结构分", fmt(first.realized_component_potential_structure_score), "预测需求占比与真实需求结构的比较"),
        infoCard("航司供给结构分", fmt(first.realized_component_supply_structure_score), "预测供给分配与真实分配的比较"),
        infoCard("供给满足率分", fmt(first.realized_component_fulfillment_score), "五类客群供给保护差异的比较"),
        infoCard("分项区间分", fmt(first.realized_component_interval_calibration_score), "五类真实客流对边际区间的命中情况"),
        infoCard("拐点判断分", fmt(first.realized_turn_timing_score), "预测窗口与真实转向的事后比较"),
        infoCard("修订纪律分", fmt(first.realized_revision_discipline_score), "总量80% + 分项结构20%的修订纪律"),
      );
      el.componentCaption.textContent = "开发审计已加载隐藏真值与 v1.2 总量、分项和过程评分";
    } else {
      el.componentCaption.textContent = componentScope
        ? "分项区间是单客群边际区间，各客群上下限不能直接相加"
        : "报告视图只含叙事、预测路径和修订，不传输隐藏真值";
    }
    el.componentGrid.innerHTML = cards.join("");
  }

  function renderTable() {
    const componentColumns = state.scope === "total"
      ? ""
      : "<th>满足率</th><th>未满足</th>";
    const supplyHeader = state.scope === "total" ? "航司计划投放" : "航司有效供给";
    const auditColumns = state.mode === "audit"
      ? "<th>真实值</th><th>偏差</th><th>区间命中</th>"
      : "";
    el.forecastTableHead.innerHTML = `<tr>
      <th>目标年</th><th>${escapeHtml(SCOPE_LABELS[state.scope])}中值</th><th>预测区间</th>
      <th>潜在需求</th><th>${supplyHeader}</th>${componentColumns}<th>瓶颈</th><th>置信</th><th>较上期</th>${auditColumns}
    </tr>`;
    el.forecastTable.innerHTML = selectedRows().map((row) => {
      const auditCells = state.mode === "audit"
        ? `<td>${fmt(scopeTrue(row))}</td><td>${fmt(scopeGapPct(row))}%</td><td>${scopeInside(row) ? "是" : "否"}</td>`
        : "";
      const low = scopeBand(row, "low");
      const high = scopeBand(row, "high");
      const componentCells = state.scope === "total"
        ? ""
        : `<td>${fmt(row[`${state.scope}_forecast_airline_supply_fulfillment_pct`])}%</td><td>${fmt(row[`${state.scope}_forecast_airline_supply_gap_million`])}</td>`;
      return `<tr>
        <td>${row.forecast_year}</td>
        <td>${fmt(scopePredicted(row))}</td>
        <td>${fmt(low)}–${fmt(high)}</td>
        <td>${fmt(scopePotential(row))}</td>
        <td>${fmt(scopeSupply(row))}</td>
        ${componentCells}
        <td>${escapeHtml(BOTTLENECK_LABELS[row.forecast_market_bottleneck] || row.forecast_market_bottleneck || "-")}</td>
        <td>${fmt(row.forecast_confidence_pct)}%</td>
        <td>${row.forecast_previous_mid_million ? `${fmt(row.forecast_revision_pct)}%` : "首次"}</td>
        ${auditCells}
      </tr>`;
    }).join("");
    el.tableCaption.textContent = `${selectedAsOfYear()} 年发布 · ${SCOPE_LABELS[state.scope]} · ${candidateActive() ? "临时候选" : state.mode === "audit" ? "开发审计" : "玩家报告"}`;
  }

  function renderCandidateResult() {
    const payload = state.candidateResult;
    if (!payload) {
      el.candidateResult.hidden = true;
      el.candidateResult.innerHTML = "";
      el.leaveCandidate.hidden = true;
      el.nextCandidate.disabled = true;
      return;
    }
    const candidate = payload.candidate;
    const target = `${fmt(payload.request.scoreMin)}–${fmt(payload.request.scoreMax)}`;
    const matched = payload.matchStatus === "matched";
    const modifierText = candidate.modifierLabels.length
      ? candidate.modifierLabels.join(" + ")
      : "纯基础风格";
    el.candidateResult.hidden = false;
    el.candidateResult.innerHTML = [
      infoCard("区间状态", matched ? "已命中" : "返回最近候选", `目标 ${target}`),
      infoCard("实际评分", fmt(candidate.actualScore), `结果分 ${fmt(candidate.resultScore)}`),
      infoCard("总量 / 分项", `${fmt(candidate.totalResultScore)} / ${fmt(candidate.componentResultScore)}`, "v1.2 结果评分拆解"),
      infoCard("报告标签", modifierText, `${payload.naturalHorizonYears}年完整预测期`),
      infoCard("首次发布", "修订纪律 92.0", "无历史修订记录，所有独立候选口径一致"),
      infoCard("搜索过程", `${payload.attemptsEvaluated} 个候选`, `候选编号 ${candidate.candidateId.slice(-8)}`),
    ].join("");
    el.leaveCandidate.hidden = !candidateActive();
    el.nextCandidate.disabled = candidateBusy || !candidateRequestIsValid();
  }

  function renderCandidateLab() {
    el.candidateLab.hidden = state.mode !== "audit";
    if (state.mode !== "audit") return;
    if (candidateCatalogError) {
      el.candidateState.textContent = "不可用";
      el.candidateAvailability.textContent = candidateCatalogError;
      el.candidateAvailability.className = "candidate-note warning";
      el.generateCandidate.disabled = true;
      el.nextCandidate.disabled = true;
      return;
    }
    if (!candidateCatalogPayload) {
      el.candidateState.textContent = "加载配置";
      el.candidateAvailability.textContent = "正在加载候选生成配置……";
      el.generateCandidate.disabled = true;
      return;
    }
    initializeCandidateControls();
    const tier = selectedCandidateTier();
    const style = selectedCandidateStyle();
    const asOfYear = selectedAsOfYear();
    const range = candidateScoreRange();
    const minimumWidth = candidateCatalog().minimumScoreBandWidth;
    const issues = [];
    if (!tier || !style) issues.push("请选择等级和基础风格");
    if (
      !Number.isFinite(range.minimum)
      || !Number.isFinite(range.maximum)
      || range.minimum < 0
      || range.maximum > 100
      || range.maximum - range.minimum < minimumWidth
    ) {
      issues.push(`目标分数范围至少需要 ${minimumWidth} 分宽`);
    }
    if (tier && asOfYear > tier.maxFullAsOfYear) {
      issues.push(
        `${tier.label}需要完整${tier.naturalHorizonYears}年未来；当前数据只能支持到${tier.maxFullAsOfYear}年发布`,
      );
    }
    if (el.candidateModifierMode.value === "manual") {
      const selected = manualCandidateModifierIds();
      if (selected.length > 2) issues.push("手动标签最多选择2个");
      if (!candidateModifiersCompatible(selected)) issues.push("当前手动标签组合互相冲突");
    }
    el.candidateAvailability.textContent = issues.length
      ? issues.join("；")
      : `${asOfYear}年首次发布 · ${tier.label}完整预测${tier.naturalHorizonYears}年 · ${style.label} · 目标实际评分${fmt(range.minimum)}–${fmt(range.maximum)}`;
    el.candidateAvailability.className = `candidate-note${issues.length ? " warning" : ""}`;
    el.generateCandidate.disabled = candidateBusy || issues.length > 0;
    el.candidateState.textContent = candidateBusy
      ? "搜索候选中"
      : state.candidateResult
        ? (state.candidateResult.matchStatus === "matched" ? "已命中目标" : "最近候选")
        : "等待生成";
    renderCandidateResult();
  }

  async function generateCandidateReport(next = false) {
    if (!candidateRequestIsValid() || candidateBusy) return;
    if (!candidateActive()) {
      lastFormalSelection = {
        reportId: state.reportId,
        asOfYear: selectedAsOfYear(),
      };
    }
    if (next) state.candidateNonce += 1;
    else state.candidateNonce = 0;
    const range = candidateScoreRange();
    const request = {
      seed: state.seed,
      asOfYear: selectedAsOfYear(),
      tierProfileId: el.candidateTier.value,
      narrativeProfileId: el.candidateStyle.value,
      modifierMode: el.candidateModifierMode.value,
      modifierIds: el.candidateModifierMode.value === "manual"
        ? manualCandidateModifierIds()
        : [],
      scoreMin: range.minimum,
      scoreMax: range.maximum,
      generationNonce: state.candidateNonce,
    };
    candidateBusy = true;
    renderCandidateLab();
    try {
      const payload = await client.generateCandidate(request);
      if (payload.releaseId !== candidateCatalogPayload.release.releaseId) {
        throw new Error("候选生成期间正式 Viewer 发布已经变化，请刷新页面后重试");
      }
      state.candidateResult = payload;
      state.reportId = payload.candidate.candidateId;
      state.asOfIndex = 0;
      rows = normalizeRows(payload.candidate.rows || []);
      renderAll();
    } catch (error) {
      el.candidateState.textContent = "生成失败";
      el.candidateAvailability.textContent = error?.message || String(error);
      el.candidateAvailability.className = "candidate-note warning";
    } finally {
      candidateBusy = false;
      renderCandidateLab();
    }
  }

  async function leaveCandidateReport() {
    if (!state.candidateResult) return;
    const selection = lastFormalSelection || {
      reportId: activeIndex?.defaultReportId || reportIds()[0] || "",
      asOfYear: selectedAsOfYear(),
    };
    state.candidateResult = null;
    state.candidateNonce = 0;
    state.reportId = selection.reportId;
    await ensureReportLoaded(state.reportId);
    const index = asOfYears().indexOf(selection.asOfYear);
    state.asOfIndex = index >= 0 ? index : 0;
    lastFormalSelection = null;
    renderAll();
  }

  function renderAll() {
    renderSeedOptions();
    renderReportOptions();
    renderTimeline();
    renderSummary();
    renderNarrative();
    renderLegend();
    renderScopeTabs();
    renderChart();
    renderEvidence();
    renderTable();
    renderCandidateLab();
    el.modeSelect.value = state.mode;
    el.statusText.textContent = candidateActive()
      ? `开发审计 · 临时候选 · ${rows.length} 行 · 不写入正式发布`
      : `${state.mode === "audit" ? "开发审计" : "报告视图"} · ${rows.length} 行 · 按报告懒加载`;
  }

  el.seedSelect.addEventListener("change", () => {
    state.seed = num(el.seedSelect.value);
    state.asOfIndex = 0;
    renderAll();
  });
  el.modeSelect.addEventListener("change", async () => {
    const previousMode = state.mode;
    try {
      await activateMode(el.modeSelect.value);
    } catch (error) {
      state.mode = previousMode;
      el.modeSelect.value = state.mode;
      el.statusText.textContent = error?.message || String(error);
    }
  });
  el.reportSelect.addEventListener("change", async () => {
    state.reportId = el.reportSelect.value;
    state.asOfIndex = 0;
    await ensureReportLoaded(state.reportId);
  });
  el.asOfRange.addEventListener("input", () => {
    state.asOfIndex = num(el.asOfRange.value);
    renderAll();
  });
  el.scopeTabs.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-scope]");
    if (!button) return;
    state.scope = button.dataset.scope;
    renderAll();
  });
  [el.candidateTier, el.candidateStyle, el.candidateModifierMode].forEach((control) => {
    control.addEventListener("change", () => {
      state.candidateNonce = 0;
      if (control === el.candidateStyle || control === el.candidateModifierMode) {
        renderCandidateModifierChoices();
      }
      renderCandidateLab();
    });
  });
  [el.candidateScoreMin, el.candidateScoreMax].forEach((control) => {
    control.addEventListener("input", () => {
      state.candidateNonce = 0;
      renderCandidateLab();
    });
  });
  el.candidateModifiers.addEventListener("change", () => {
    state.candidateNonce = 0;
    renderCandidateLab();
  });
  el.generateCandidate.addEventListener("click", () => generateCandidateReport(false));
  el.nextCandidate.addEventListener("click", () => generateCandidateReport(true));
  el.leaveCandidate.addEventListener("click", () => leaveCandidateReport());

  try {
    state.reportId = playerIndex.defaultReportId || state.reportId;
    renderReportOptions();
    await ensureReportLoaded(state.reportId);
  } catch (error) {
    el.statusText.textContent = "预测页面初始化失败";
    document.querySelector("main").innerHTML = `<div class="empty">${escapeHtml(error?.message || error)}</div>`;
  }
})();
