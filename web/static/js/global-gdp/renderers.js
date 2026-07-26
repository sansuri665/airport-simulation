    const {
      branchRisksForRow,
      activeScenarioRows,
      simulateBranchRisk,
      clearScenario,
      scenarioDeltaSummary,
    } = window.AirportGlobalScenarioModel;

    function render() {
      const rows = rowsForSeed();
      if (!rows.length) {
        renderEmptyView();
        return;
      }
      state.selectedIndex = Math.max(0, Math.min(state.selectedIndex, rows.length - 1));
      el.yearRange.max = String(rows.length - 1);
      el.yearRange.value = String(state.selectedIndex);
      el.yearLabel.textContent = state.selectedIndex === 0
        ? `${selectedRow(rows).year} · 起点`
        : String(selectedRow(rows).year);
      if (state.view === "aviation") {
        renderAviationStats(rows);
        renderAviationDetail(rows);
        renderAviationChart(rows);
        renderAviationNarrative(rows);
        renderAviationTable(rows);
      } else {
        renderStats(rows);
        renderDetail(rows);
        renderChart(rows);
        renderNarrative(rows);
        renderTable(rows);
      }
    }

    function renderActiveChart() {
      const rows = rowsForSeed();
      if (!rows.length) return;
      if (state.view === "aviation") renderAviationChart(rows);
      else renderChart(rows);
    }

    function escapeHtml(value) {
      return String(value ?? "-").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      }[char]));
    }

    function makeStat(label, value, sub = "-", tone = "") {
      return { label, value, sub, tone };
    }

    function boundarySummary(row, field, formatter = fmtIndex) {
      const rawField = `unclamped_${field}_target`;
      const stateField = `${field}_boundary_state`;
      const runField = `${field}_consecutive_boundary_years`;
      const stateValue = row[stateField] || "none";
      const runValue = Number(row[runField] || 0);
      return `target ${formatter(row[rawField])} · ${stateValue}${runValue ? ` ${runValue}y` : ""}`;
    }

    const DETAIL_IDS = [
      "detailGdp",
      "detailGrowth",
      "detailRegionalShare",
      "detailRegionalRank",
      "detailInflation",
      "detailCoreInflation",
      "detailPolicyRate",
      "detailPolicyTarget",
      "detailRealPolicyRate",
      "detailTenYearYield",
      "detailTermSpread",
      "detailDollar",
      "detailLiquidity",
      "detailFinancialConditions",
      "detailHySpread",
      "detailIgSpread",
      "detailCreditAvailability",
      "detailEquity",
      "detailEquityReturn",
      "detailEquityPe",
      "detailBond",
      "detailOil",
      "detailOilReturn",
      "detailCommodity",
      "detailEnergyPressure",
      "detailFeedbackIntensity",
      "detailFeedbackGrowth",
      "detailPotentialGrowth",
      "detailGap",
      "detailStress",
      "detailShock",
    ];

    const MACRO_DETAIL_LABELS = {
      detailGdp: "GDP / 指数",
      detailGrowth: "GDP 增长率",
      detailRegionalShare: "全球占比",
      detailRegionalRank: "GDP 排名 / 贡献",
      detailInflation: "Headline 通胀",
      detailCoreInflation: "核心通胀",
      detailPolicyRate: "政策利率",
      detailPolicyTarget: "政策目标",
      detailRealPolicyRate: "实际政策利率",
      detailTenYearYield: "10Y 利率",
      detailTermSpread: "期限利差",
      detailDollar: "美元 / 货币",
      detailLiquidity: "流动性",
      detailFinancialConditions: "金融条件",
      detailHySpread: "HY 利差",
      detailIgSpread: "IG 利差",
      detailCreditAvailability: "信贷可得性",
      detailEquity: "股票价格指数",
      detailEquityReturn: "股票年度总回报",
      detailEquityPe: "PE",
      detailBond: "主权债总回报指数",
      detailOil: "油价 / 能源",
      detailOilReturn: "油价年变动",
      detailCommodity: "商品指数",
      detailEnergyPressure: "能源成本压力",
      detailFeedbackIntensity: "反馈强度",
      detailFeedbackGrowth: "GDP 反馈",
      detailPotentialGrowth: "潜在增长率",
      detailGap: "模型估计周期缺口",
      detailStress: "金融压力",
      detailShock: "冲击项",
    };

    const AVIATION_DETAIL_LABELS = {
      detailGdp: "航空需求指数",
      detailGrowth: "航空需求增长",
      detailRegionalShare: "商务需求 / 占比",
      detailRegionalRank: "休闲需求 / 占比",
      detailInflation: "VFR 需求 / 占比",
      detailCoreInflation: "长途需求 / 占比",
      detailPolicyRate: "中转需求 / 占比",
      detailPolicyTarget: "票价敏感度",
      detailRealPolicyRate: "票价压力",
      detailTenYearYield: "商务票价弹性",
      detailTermSpread: "休闲票价弹性",
      detailDollar: "VFR 票价弹性",
      detailLiquidity: "长途票价弹性",
      detailFinancialConditions: "中转票价弹性",
      detailHySpread: "高端票价弹性",
      detailIgSpread: "高端客倾向",
      detailCreditAvailability: "高端客占比",
      detailEquity: "免税倾向",
      detailEquityReturn: "奢侈品倾向",
      detailEquityPe: "电子产品倾向",
      detailBond: "餐饮倾向",
      detailOil: "普通零售倾向",
      detailOilReturn: "机场事件提示",
      detailCommodity: "事件压力",
      detailEnergyPressure: "事件冲击",
      detailFeedbackIntensity: "输入 GDP 增长",
      detailFeedbackGrowth: "输入收入增长",
      detailPotentialGrowth: "输入消费者信心",
      detailGap: "输入宏观压力",
      detailStress: "输入能源压力",
      detailShock: "分岔阶段 / 强度",
    };

    const MACRO_TABLE_HEADERS = [
      "年份",
      "GDP",
      "增长率",
      "通胀",
      "核心",
      "利率",
      "10Y",
      "期限利差",
      "美元/货币",
      "流动性",
      "HY",
      "IG",
      "股票总回报",
      "主权债总回报",
      "PE",
      "油价/能源",
      "Oil YoY",
      "商品",
      "潜在增长",
      "模型估计缺口",
      "严格水平缺口",
      "测量残差",
      "压力",
      "央行",
      "曲线",
      "美元环境",
      "信用",
      "资产",
      "石油",
      "状态",
    ];

    const AVIATION_TABLE_HEADERS = [
      "年份",
      "总需求",
      "增长",
      "商务",
      "休闲",
      "VFR",
      "长途",
      "中转",
      "商务满足",
      "休闲满足",
      "VFR 满足",
      "长途满足",
      "中转满足",
      "票价敏感",
      "票价压力",
      "商务弹性",
      "休闲弹性",
      "高端倾向",
      "高端占比",
      "免税",
      "奢侈品",
      "电子",
      "餐饮",
      "普通零售",
      "事件",
      "事件压力",
      "宏观压力",
      "能源压力",
      "信心",
      "GDP 输入",
      "收入输入",
      "分岔阶段",
      "状态",
    ];

    function macroLegendHtml(row = null) {
      const portfolioLabel = row?.macro_scope === "regional" ? "居民实际金融财富" : "60/40 总回报";
      return `
      <span><i class="swatch" style="background: var(--blue)"></i>GDP</span>
      <span><i class="swatch" style="background: var(--green)"></i>正增长</span>
      <span><i class="swatch" style="background: var(--red)"></i>负增长</span>
      <span><i class="swatch" style="background: var(--yellow)"></i>通胀</span>
      <span><i class="swatch" style="background: #a78bfa"></i>利率</span>
      <span><i class="swatch" style="background: #22d3ee"></i>10Y</span>
      <span><i class="swatch" style="background: #38bdf8"></i>美元/货币</span>
      <span><i class="swatch" style="background: #14b8a6"></i>流动性</span>
      <span><i class="swatch" style="background: #fb923c"></i>HY</span>
      <span><i class="swatch" style="background: #c084fc"></i>IG</span>
      <span><i class="swatch" style="background: #22c55e"></i>股票总回报</span>
      <span><i class="swatch" style="background: #818cf8"></i>主权债总回报</span>
      <span><i class="swatch" style="background: #eab308"></i>${portfolioLabel}</span>
      <span><i class="swatch" style="background: #f97316"></i>油价/能源</span>
      <span><i class="swatch" style="background: #d946ef"></i>商品</span>
      <span><i class="swatch" style="background: rgba(251,113,133,0.38)"></i>危机时代</span>
      `;
    }

    const AVIATION_LEGEND_HTML = `
      <span><i class="swatch" style="background: var(--blue)"></i>航空需求</span>
      <span><i class="swatch" style="background: var(--green)"></i>正增长</span>
      <span><i class="swatch" style="background: var(--red)"></i>负增长</span>
      <span><i class="swatch" style="background: #22d3ee"></i>商务</span>
      <span><i class="swatch" style="background: #facc15"></i>休闲</span>
      <span><i class="swatch" style="background: #a78bfa"></i>VFR</span>
      <span><i class="swatch" style="background: #fb923c"></i>长途/中转</span>
      <span><i class="swatch" style="background: #d946ef"></i>高端/消费</span>
    `;

    function setDetailLabels(labels) {
      for (const id of DETAIL_IDS) {
        const label = labels[id] || "-";
        if (el[id]?.previousElementSibling) el[id].previousElementSibling.textContent = label;
      }
    }

    function clearDetailValues() {
      for (const id of DETAIL_IDS) {
        if (el[id]) {
          el[id].textContent = "-";
          el[id].className = "";
        }
      }
    }

    function setTableHeaders(headers) {
      const row = document.querySelector(".table-panel thead tr");
      if (row) row.innerHTML = headers.map((header) => `<th>${escapeHtml(header)}</th>`).join("");
    }

    function setChartLegend(html) {
      if (el.chartLegend) el.chartLegend.innerHTML = html;
    }

    function unavailableStats(layerName, row) {
      return [
        makeStat(layerName, "-", "当前数据未包含这一层"),
        makeStat(row?.macro_scope === "regional" ? "区域 GDP 指数" : "当前 GDP", fmtGdp(row.global_gdp_trillion_usd, row), String(row.year)),
        makeStat("年增长率", fmtPct(row.realized_growth_pct), `potential ${fmtPct(row.potential_growth_pct)}`, growthClass(row.realized_growth_pct)),
      ];
    }

    function hasRegionalBranch(row) {
      return row?.macro_scope === "regional"
        && row.branch_scenario_id
        && row.branch_scenario_id !== "none"
        && Number(row.regional_branch_strength_index || 0) > 0;
    }

    function regionalBranchStat(row) {
      if (!hasRegionalBranch(row)) return [];
      const stateText = row.regional_branch_transmission_active === "true" ? "已发生" : "观察";
      return [
        makeStat(
          "分岔传导",
          row.branch_scenario_label || row.branch_scenario_id,
          `${stateText} / 暴露 ${fmtIndex(row.regional_branch_exposure_index)} / 强度 ${fmtIndex(row.regional_branch_strength_index)}`
        ),
      ];
    }

    function renderStats(rows) {
      const row = selectedRow(rows);
      setChartLegend(macroLegendHtml(row));
      const first = rows[0];
      const last = rows[rows.length - 1];
      const summary = summarize(rows);
      const cumulativeGrowth = first.global_gdp_trillion_usd ? (row.global_gdp_trillion_usd / first.global_gdp_trillion_usd - 1) * 100 : 0;
      const finalGrowth = first.global_gdp_trillion_usd ? (last.global_gdp_trillion_usd / first.global_gdp_trillion_usd - 1) * 100 : 0;
      const hyIgGap = hasCredit(row) ? row.global_high_yield_spread_bps - row.global_investment_grade_spread_bps : undefined;
      const eventLabel = row.event_phase || row.event_type || "normal";
      const isRegional = row.macro_scope === "regional";
      const hasRegionalSize = isRegional && row.display_gdp_unit === "usd_trillion";
      const gdpLabel = isRegional ? (hasRegionalSize ? "区域 GDP" : "区域 GDP 指数") : "当前 GDP";
      const finalGdpLabel = isRegional ? (hasRegionalSize ? "最终区域 GDP" : "最终 GDP 指数") : "最终 GDP";
      const oilLabel = isRegional ? "能源压力" : "Brent 油价";
      const currencyLabel = isRegional ? "货币指数" : "美元资金条件指数";

      const statsByMode = {
        both: () => [
          makeStat(gdpLabel, fmtGdp(row.global_gdp_trillion_usd, row), `${row.year} / final ${fmtGdp(last.global_gdp_trillion_usd, row)}`),
          ...(hasRegionalSize ? [
            makeStat("全球占比", fmtLevelPct(row.regional_share_of_global_gdp_pct), `#${row.regional_rank_by_gdp} / 贡献 ${fmtPp(row.regional_growth_contribution_pp)}`),
          ] : []),
          ...regionalBranchStat(row),
          makeStat("年增长率", fmtPct(row.realized_growth_pct), `potential ${fmtPct(row.potential_growth_pct)}`, growthClass(row.realized_growth_pct)),
          makeStat("Headline 通胀", hasInflation(row) ? fmtLevelPct(row.headline_inflation_pct) : "-", hasInflation(row) ? `core ${fmtLevelPct(row.core_inflation_pct)}` : "run inflation layer"),
          makeStat("政策利率", hasPolicy(row) ? fmtLevelPct(row.global_policy_rate_pct) : "-", hasPolicy(row) ? `${row.central_bank_reaction_regime || "n/a"} / QE ${fmtIndex(row.qe_liquidity_index)}` : "run policy layer"),
          makeStat("10Y 利率", hasYield(row) ? fmtLevelPct(row.global_10y_yield_pct) : "-", hasYield(row) ? `spread ${fmtPct(row.term_spread_10y_2y_pct)}` : "run yield layer"),
          makeStat(currencyLabel, hasDollar(row) ? fmtIndex(row.global_dollar_index) : "-", hasDollar(row) ? `liquidity ${fmtIndex(row.global_liquidity_index)}` : "run dollar layer"),
          makeStat("HY 利差", hasCredit(row) ? fmtBps(row.global_high_yield_spread_bps) : "-", hasCredit(row) ? `IG ${fmtBps(row.global_investment_grade_spread_bps)}` : "run credit layer"),
          makeStat("股票价格指数", hasAsset(row) ? fmtIndex(row.global_equity_price_index) : "-", hasAsset(row) ? `${fmtPct(row.global_equity_total_return_pct)} 总回报 / ${row.asset_risk_regime || "n/a"}` : "run asset layer"),
          makeStat(oilLabel, hasOil(row) ? fmtOilMetric(row) : "-", hasOil(row) ? `${fmtPct(row.oil_yoy_change_pct)} / ${row.oil_regime || "n/a"}` : "run oil layer"),
          makeStat("反馈强度", hasFeedback(row) ? fmtIndex(row.macro_feedback_intensity_index) : "-", hasFeedback(row) ? `pass delta ${fmtIndex(row.macro_feedback_last_pass_delta_index)}` : "feedback layer"),
        ],
        gdp: () => [
          makeStat(gdpLabel, fmtGdp(row.global_gdp_trillion_usd, row), `${row.year} / base ${fmtGdp(first.global_gdp_trillion_usd, row)}`),
          makeStat(finalGdpLabel, fmtGdp(last.global_gdp_trillion_usd, row), `${rows[0].year}-${last.year}`),
          ...(hasRegionalSize ? [
            makeStat("全球占比", fmtLevelPct(row.regional_share_of_global_gdp_pct), `start ${fmtLevelPct(row.regional_normalized_initial_weight_pct)} / drift ${fmtPp(row.regional_weight_drift_pp)}`),
            makeStat("GDP 排名", `#${row.regional_rank_by_gdp}`, `contribution ${fmtPp(row.regional_growth_contribution_pp)}`),
            makeStat("对账误差", fmtPp(row.regional_weighted_growth_gap_pp), `infl ${fmtPp(row.regional_weighted_inflation_gap_pp)} / HY ${fmtBps(row.regional_weighted_hy_gap_bps)}`),
          ] : []),
          ...regionalBranchStat(row),
          makeStat("累计变化", fmtPct(cumulativeGrowth), `final ${fmtPct(finalGrowth)}`, growthClass(cumulativeGrowth)),
          makeStat("平均增长", fmtPct(summary.avg), `${rows[0].year}-${last.year}`),
          makeStat("最低增长", fmtPct(summary.minRow.realized_growth_pct), String(summary.minRow.year), growthClass(summary.minRow.realized_growth_pct)),
          makeStat("衰退年份", String(summary.recessionYears), row.regime),
          makeStat("潜在增长", fmtPct(row.potential_growth_pct), `trend ${fmtPct(row.trend_growth_pct)}`),
          makeStat("模型估计周期缺口", fmtPct(row.output_gap_pct), `stress ${fmtIndex(row.financial_stress_index)}`, growthClass(row.output_gap_pct)),
          makeStat("严格 GDP 水平缺口", fmtPct(row.gdp_level_gap_pct), `残差 ${fmtPct(row.output_gap_measurement_residual_pct)}`, growthClass(row.gdp_level_gap_pct)),
        ],
        growth: () => [
          makeStat("年增长率", fmtPct(row.realized_growth_pct), `potential ${fmtPct(row.potential_growth_pct)}`, growthClass(row.realized_growth_pct)),
          makeStat("趋势增长", fmtPct(row.trend_growth_pct), `long-run trend`),
          makeStat("周期项", fmtPct(row.cycle_growth_component_pct), "inventory / investment / long wave", growthClass(row.cycle_growth_component_pct)),
          makeStat("冲击项", fmtPct(row.shock_component_pct), eventLabel, growthClass(row.shock_component_pct)),
          makeStat("反馈增长项", hasFeedback(row) ? fmtPct(row.feedback_growth_impulse_pct) : "-", hasFeedback(row) ? `raw ${fmtPct(row.macro_feedback_growth_raw_pct)}` : "feedback layer"),
          makeStat("金融压力", fmtIndex(row.financial_stress_index), `crisis ${fmtIndex(row.crisis_intensity)}`),
          makeStat("模型估计周期缺口", fmtPct(row.output_gap_pct), row.regime, growthClass(row.output_gap_pct)),
          makeStat("严格 GDP 水平缺口", fmtPct(row.gdp_level_gap_pct), `残差 ${fmtPct(row.output_gap_measurement_residual_pct)}`, growthClass(row.gdp_level_gap_pct)),
          makeStat("滞后支撑", fmtPct(row.gdp_lagged_support), `energy impulse ${fmtPct(row.energy_price_impulse)}`, growthClass(row.gdp_lagged_support)),
        ],
        inflation: () => hasInflation(row) ? [
          makeStat("Headline 通胀", fmtLevelPct(row.headline_inflation_pct), row.inflation_regime || "n/a"),
          makeStat("核心通胀", fmtLevelPct(row.core_inflation_pct), `expect ${fmtLevelPct(row.inflation_expectation_pct)}`),
          makeStat("能源通胀", fmtLevelPct(row.energy_inflation_pct), `oil impulse ${fmtPct(row.oil_to_headline_inflation_impulse)}`),
          makeStat("进口通胀", fmtLevelPct(row.import_inflation_pct), `dollar ${fmtPct(row.dollar_to_import_inflation_impulse)}`),
          makeStat("工资压力", fmtLevelPct(row.wage_pressure_pct), `demand ${fmtPct(row.demand_pull_component_pct)}`),
          makeStat("通胀预期", fmtLevelPct(row.inflation_expectation_pct), `feedback ${fmtPct(row.feedback_inflation_impulse_pct)}`),
          makeStat("政策压力", fmtPct(row.inflation_to_policy_rate_impulse), `long rate ${fmtPct(row.inflation_to_long_rate_impulse)}`),
          makeStat("GDP 拖累", fmtPct(row.inflation_to_gdp_drag_placeholder), `stress ${fmtPct(row.stress_disinflation_component_pct)}`, growthClass(row.inflation_to_gdp_drag_placeholder)),
        ] : unavailableStats("通胀层", row),
        policy: () => hasPolicy(row) ? [
          makeStat("政策利率", fmtLevelPct(row.global_policy_rate_pct), row.central_bank_reaction_regime || "n/a"),
          makeStat("反应目标", fmtLevelPct(row.policy_reaction_target_rate_pct), `neutral ${fmtLevelPct(row.neutral_policy_rate_pct)}`),
          makeStat("真实政策利率", fmtLevelPct(row.real_policy_rate_pct), `shadow ${fmtLevelPct(row.shadow_policy_rate_pct)}`),
          makeStat("年变化", fmtPct(row.policy_rate_change_pct), "policy step", growthClass(row.policy_rate_change_pct)),
          makeStat("加息压力", fmtIndex(row.rate_hike_pressure), `inflation ${fmtLevelPct(row.headline_inflation_pct)}`),
          makeStat("降息压力", fmtIndex(row.rate_cut_pressure), `stress ${fmtIndex(row.financial_stress_index)}`),
          makeStat("QE 指数", fmtIndex(row.qe_liquidity_index), `liquidity ${hasDollar(row) ? fmtIndex(row.global_liquidity_index) : "-"}`),
          makeStat("信用冲击", fmtPct(row.policy_to_credit_tightening_impulse), `GDP ${fmtPct(row.policy_to_gdp_drag_placeholder)}`, growthClass(-row.policy_to_credit_tightening_impulse)),
        ] : unavailableStats("政策层", row),
        yield: () => hasYield(row) ? [
          makeStat("10Y 利率", fmtLevelPct(row.global_10y_yield_pct), row.yield_curve_regime || "n/a"),
          makeStat("2Y 利率", fmtLevelPct(row.global_2y_yield_pct), `short ${fmtLevelPct(row.global_short_rate_pct)}`),
          makeStat("实际 10Y", fmtLevelPct(row.global_real_10y_yield_pct), `inflation ${hasInflation(row) ? fmtLevelPct(row.headline_inflation_pct) : "-"}`),
          makeStat("期限利差", fmtPct(row.term_spread_10y_2y_pct), "10Y - 2Y", growthClass(row.term_spread_10y_2y_pct)),
          makeStat("期限溢价", fmtLevelPct(row.term_premium_pct), `target ${fmtLevelPct(row.unclamped_term_premium_target_pct)}`),
          makeStat("可观察短端预期", fmtLevelPct(row.expected_short_rate_10y_pct), `target ${fmtLevelPct(row.unclamped_expected_short_rate_10y_target_pct)}`),
          makeStat("影子短端预期", fmtLevelPct(row.expected_shadow_short_rate_10y_pct), `target ${fmtLevelPct(row.unclamped_expected_shadow_short_rate_10y_target_pct)}`),
          makeStat("美元资金曲线冲击", fmtPct(row.yield_curve_to_dollar_impulse), `credit ${fmtPct(row.yield_curve_to_credit_impulse)}`),
          makeStat("股权估值冲击", fmtPct(row.yield_curve_to_equity_valuation_impulse), "valuation channel", growthClass(row.yield_curve_to_equity_valuation_impulse)),
          makeStat("GDP 拖累", fmtPct(row.yield_curve_to_gdp_drag_placeholder), "curve channel", growthClass(row.yield_curve_to_gdp_drag_placeholder)),
        ] : unavailableStats("收益率曲线", row),
        dollar: () => hasDollar(row) ? [
          makeStat(currencyLabel, fmtIndex(row.global_dollar_index), `target ${fmtIndex(row.unclamped_dollar_target_index)}`),
          makeStat("代理指数 YoY", fmtPct(row.dollar_yoy_change_pct), `momentum ${fmtIndex(row.dollar_momentum_index)}`, growthClass(row.dollar_yoy_change_pct)),
          makeStat("全球流动性", fmtIndex(row.global_liquidity_index), `impulse ${fmtIndex(row.liquidity_impulse_index)}`),
          makeStat("全球 FCI", fmtIndex(row.global_financial_conditions_index), `target ${fmtIndex(row.unclamped_financial_conditions_target_index)} · higher = tighter`),
          makeStat("风险偏好", fmtIndex(row.risk_appetite_index), `EM stress ${fmtIndex(row.em_stress_index)}`),
          makeStat("美元融资压力", fmtIndex(row.dollar_funding_stress_index), `credit ${fmtPct(row.dollar_to_credit_tightening_impulse)}`),
          makeStat("进口通胀冲击", fmtPct(row.dollar_to_import_inflation_impulse), `oil ${fmtPct(row.dollar_to_oil_pressure_impulse)}`),
          makeStat("GDP 拖累", fmtPct(row.dollar_to_gdp_drag_placeholder), "dollar channel", growthClass(row.dollar_to_gdp_drag_placeholder)),
        ] : unavailableStats("美元流动性", row),
        credit: () => hasCredit(row) ? [
          makeStat("HY 利差", fmtBps(row.global_high_yield_spread_bps), row.credit_regime || "n/a"),
          makeStat("IG 利差", fmtBps(row.global_investment_grade_spread_bps), `HY-IG ${fmtBps(hyIgGap)}`),
          makeStat("利差变化", fmtBps(row.credit_spread_change_bps), `index ${fmtIndex(row.global_credit_spread_index)} · ${boundarySummary(row, "global_credit_spread_index")}`),
          makeStat("违约风险", fmtIndex(row.default_risk_index), `bank stress ${fmtIndex(row.bank_credit_stress_index)}`),
          makeStat("信用可得性", fmtIndex(row.credit_availability_index), `${boundarySummary(row, "credit_availability_index")} · standards ${fmtIndex(row.lending_standards_index)}`),
          makeStat("银行放贷意愿", fmtIndex(row.bank_lending_sentiment_index), `balance stress ${fmtIndex(row.bank_balance_sheet_stress_index)}`),
          makeStat("信用疤痕", fmtIndex(row.credit_impairment_stock_index), boundarySummary(row, "credit_impairment_stock_index")),
          makeStat("凸性压力", fmtIndex(row.credit_convexity_pressure_index), `refi ${fmtIndex(row.corporate_refinancing_pressure_index)}`),
          makeStat("GDP 拖累", fmtPct(row.credit_to_gdp_drag_placeholder), `policy easing ${fmtPct(row.credit_to_policy_easing_pressure)}`, growthClass(row.credit_to_gdp_drag_placeholder)),
        ] : unavailableStats("信用利差", row),
        asset: () => hasAsset(row) ? [
          makeStat("股票价格指数", fmtIndex(row.global_equity_price_index), row.asset_risk_regime || "n/a"),
          makeStat("股票总回报指数", fmtIndex(row.global_equity_total_return_index), `本年 ${fmtPct(row.global_equity_total_return_pct)} · 价格 ${fmtPct(row.global_equity_price_return_pct)} · drawdown ${fmtPct(row.global_equity_drawdown_pct)}`, growthClass(row.global_equity_total_return_pct)),
          makeStat("EPS 指数", fmtIndex(row.global_equity_eps_index), `EPS ${fmtPct(row.global_equity_eps_growth_pct)} · ${row.global_equity_eps_boundary_state || "none"}`),
          makeStat("估值 PE", fmtIndex(row.global_equity_valuation_pe), row.global_equity_pe_boundary_state || "none"),
          makeStat("主权债总回报指数", fmtIndex(row.global_sovereign_bond_total_return_index), `return ${fmtPct(row.global_sovereign_bond_total_return_pct)}`, growthClass(row.global_sovereign_bond_total_return_pct)),
          makeStat("企业债总回报指数", Number.isFinite(row.global_corporate_bond_total_return_index) ? fmtIndex(row.global_corporate_bond_total_return_index) : "-", Number.isFinite(row.global_corporate_bond_total_return_pct) ? `return ${fmtPct(row.global_corporate_bond_total_return_pct)}` : "区域视图不提供企业债", growthClass(row.global_corporate_bond_total_return_pct)),
          row.macro_scope === "regional"
            ? makeStat("居民实际金融财富", fmtIndex(row.regional_household_financial_wealth_index), `市场冲量 ${fmtIndex(row.regional_asset_market_impulse_index)}`)
            : makeStat("60/40 总回报指数", fmtIndex(row.global_60_40_total_return_index), `return ${fmtPct(row.global_60_40_total_return_pct)}`, growthClass(row.global_60_40_total_return_pct)),
          makeStat("财富冲击", fmtPct(row.asset_to_gdp_wealth_impulse), `vol ${fmtIndex(row.asset_volatility_index)}`, growthClass(row.asset_to_gdp_wealth_impulse)),
        ] : unavailableStats("资产价格", row),
        oil: () => hasOil(row) ? [
          makeStat(oilLabel, fmtOilMetric(row), `${row.oil_regime || "n/a"} · ${boundarySummary(row, "brent_oil_price_usd", (value) => `$${fmtIndex(value)}`)}`),
          makeStat("油价 YoY", fmtPct(row.oil_yoy_change_pct), `index ${fmtIndex(row.global_oil_price_index)}`, growthClass(row.oil_yoy_change_pct)),
          makeStat("商品指数", fmtIndex(row.broad_commodity_index), `YoY ${fmtPct(row.commodity_yoy_change_pct)}`, growthClass(row.commodity_yoy_change_pct)),
          makeStat("需求压力", fmtIndex(row.oil_demand_pressure_index), `GDP ${fmtPct(row.realized_growth_pct)}`),
          makeStat("供给冲击", fmtIndex(row.oil_supply_shock_index), `inventory ${fmtIndex(row.oil_inventory_pressure_index)}`),
          makeStat("能源成本压力", fmtIndex(row.energy_cost_pressure_index), `${boundarySummary(row, "energy_cost_pressure_index")} · headline ${fmtPct(row.oil_to_headline_inflation_impulse)}`),
          makeStat("金融压力", fmtIndex(row.oil_financial_pressure_index), `credit ${fmtPct(row.oil_to_credit_stress_impulse)}`),
          makeStat("GDP 拖累", fmtPct(row.oil_to_gdp_drag_placeholder), `policy ${fmtPct(row.oil_to_policy_pressure_impulse)}`, growthClass(row.oil_to_gdp_drag_placeholder)),
        ] : unavailableStats("石油商品", row),
      };

      const cards = (statsByMode[state.mode] || statsByMode.both)();
      el.statsGrid.dataset.activeMode = state.mode;
      el.statsGrid.innerHTML = cards.map((card) => `
        <div class="stat">
          <span>${escapeHtml(card.label)}</span>
          <strong class="${escapeHtml(card.tone)}">${escapeHtml(card.value)}</strong>
          <small>${escapeHtml(card.sub)}</small>
        </div>
      `).join("");
    }

    function numericValue(row, key, fallback = 0) {
      const value = row?.[key];
      return typeof value === "number" && !Number.isNaN(value) ? value : fallback;
    }

    function addNarrative(candidates, item) {
      if (item.score >= item.threshold) {
        candidates.push({
          ...item,
          score: Math.min(100, Math.max(0, item.score)),
        });
      }
    }

    function detectNarratives(rows, index) {
      const row = rows[index];
      if (!row || row.year_index === 0) return [];
      const prev = rows[Math.max(0, index - 1)] || row;
      const growth = numericValue(row, "realized_growth_pct");
      const gap = numericValue(row, "output_gap_pct");
      const headline = numericValue(row, "headline_inflation_pct", 2.3);
      const core = numericValue(row, "core_inflation_pct", 2.2);
      const prevHeadline = numericValue(prev, "headline_inflation_pct", headline);
      const prevCore = numericValue(prev, "core_inflation_pct", core);
      const policyRate = numericValue(row, "global_policy_rate_pct");
      const policyChange = numericValue(row, "policy_rate_change_pct");
      const qe = numericValue(row, "qe_liquidity_index");
      const tenYear = numericValue(row, "global_10y_yield_pct");
      const prevTenYear = numericValue(prev, "global_10y_yield_pct", tenYear);
      const termSpread = numericValue(row, "term_spread_10y_2y_pct");
      const dollar = numericValue(row, "global_dollar_index", 100);
      const dollarYoy = numericValue(row, "dollar_yoy_change_pct");
      const fundingStress = numericValue(row, "dollar_funding_stress_index");
      const emStress = numericValue(row, "em_stress_index");
      const liquidity = numericValue(row, "global_liquidity_index", 55);
      const liquidityImpulse = numericValue(row, "liquidity_impulse_index");
      const riskAppetite = numericValue(row, "risk_appetite_index", 50);
      const fci = numericValue(row, "global_financial_conditions_index");
      const hy = numericValue(row, "global_high_yield_spread_bps", 420);
      const spreadChange = numericValue(row, "credit_spread_change_bps");
      const availability = numericValue(row, "credit_availability_index", 58);
      const bankSentiment = numericValue(row, "bank_lending_sentiment_index", 54);
      const bankStress = numericValue(row, "bank_balance_sheet_stress_index", 34);
      const impairment = numericValue(row, "credit_impairment_stock_index");
      const refinancing = numericValue(row, "corporate_refinancing_pressure_index");
      const equityReturn = numericValue(row, "global_equity_total_return_pct");
      const drawdown = numericValue(row, "global_equity_drawdown_pct");
      const pe = numericValue(row, "global_equity_valuation_pe");
      const prevPe = numericValue(prev, "global_equity_valuation_pe", pe);
      const sovereignReturn = numericValue(row, "global_sovereign_bond_total_return_pct");
      const brent = numericValue(row, "brent_oil_price_usd");
      const prevBrent = numericValue(prev, "brent_oil_price_usd", brent);
      const oilYoy = numericValue(row, "oil_yoy_change_pct");
      const energyPressure = numericValue(row, "energy_cost_pressure_index");
      const oilDemand = numericValue(row, "oil_demand_pressure_index", 50);
      const feedback = numericValue(row, "macro_feedback_intensity_index");

      const candidates = [];
      let score = 0;
      score += growth < 0 ? 18 : growth < 1 ? 8 : 0;
      score += gap < -5 ? 18 : gap < -3 ? 10 : 0;
      score += hy > 850 ? 22 : hy > 680 ? 12 : 0;
      score += equityReturn < -10 || drawdown < -22 ? 14 : equityReturn < -6 ? 8 : 0;
      score += bankSentiment < 35 || bankStress > 70 ? 12 : 0;
      score += impairment > 55 ? 12 : impairment > 35 ? 7 : 0;
      score += feedback > 65 ? 8 : 0;
      addNarrative(candidates, {
        id: "financial_crisis",
        label: "金融危机",
        tone: "bad",
        threshold: 62,
        score,
        summary: "增长、信用和风险资产同时失速，金融系统正在去杠杆。即使政策开始托底，实体修复也会被银行资产负债表拖慢。",
        evidence: [`GDP ${fmtPct(growth)}`, `产出缺口 ${fmtPct(gap)}`, `HY ${fmtBps(hy)}`, `股票 ${fmtPct(equityReturn)}`],
      });

      score = 0;
      score += brent > 125 ? 18 : brent > 105 ? 10 : 0;
      score += oilYoy > 28 ? 20 : oilYoy > 15 ? 10 : 0;
      score += energyPressure > 72 ? 18 : energyPressure > 60 ? 9 : 0;
      score += headline - core > 0.75 ? 12 : 0;
      score += numericValue(row, "oil_to_gdp_drag_placeholder") < -0.45 ? 10 : 0;
      score += numericValue(row, "oil_to_policy_pressure_impulse") > 0.45 ? 8 : 0;
      addNarrative(candidates, {
        id: "energy_crisis",
        label: "能源危机",
        tone: "hot",
        threshold: 62,
        score,
        summary: "油价和能源成本推高 headline 通胀，增长和政策空间同时被挤压。这里更像供给冲击，而不是普通需求过热。",
        evidence: [`Brent ${fmtOil(brent)}`, `油价 ${fmtPct(oilYoy)}`, `能源压力 ${fmtIndex(energyPressure)}`, `Headline ${fmtLevelPct(headline)}`],
      });

      score = 0;
      score += growth < 1.2 ? 16 : 0;
      score += gap < -1.5 ? 14 : 0;
      score += headline > 4 ? 20 : headline > 3.4 ? 12 : 0;
      score += core > 3.2 ? 16 : core > 2.8 ? 8 : 0;
      score += policyRate > 3.5 || numericValue(row, "rate_hike_pressure") > numericValue(row, "rate_cut_pressure") ? 10 : 0;
      score += hy > 600 ? 8 : 0;
      addNarrative(candidates, {
        id: "stagflation",
        label: "滞胀",
        tone: "hot",
        threshold: 56,
        score,
        summary: "增长低于潜在水平，但通胀仍然偏高。央行面对的是典型两难：压通胀会伤增长，托增长又可能延长通胀。",
        evidence: [`GDP ${fmtPct(growth)}`, `Headline ${fmtLevelPct(headline)}`, `Core ${fmtLevelPct(core)}`, `政策 ${fmtLevelPct(policyRate)}`],
      });

      score = 0;
      score += growth >= 1.3 && growth <= 3.4 ? 18 : 0;
      score += gap >= -1.8 && gap <= 1.0 ? 16 : 0;
      score += headline >= 1.5 && headline <= 3.2 ? 14 : 0;
      score += prevHeadline - headline > 0.15 ? 12 : 0;
      score += hy < 560 ? 12 : 0;
      score += termSpread > -0.45 ? 8 : 0;
      score += equityReturn > -2 ? 6 : 0;
      addNarrative(candidates, {
        id: "soft_landing",
        label: "软着陆",
        tone: "good",
        threshold: 76,
        score,
        summary: "通胀压力在降温，但增长仍保持正值，信用市场也没有失控。政策从紧张状态进入可控区间，像一次相对温和的减速。",
        evidence: [`GDP ${fmtPct(growth)}`, `Headline ${fmtLevelPct(headline)}`, `HY ${fmtBps(hy)}`, `期限利差 ${fmtPct(termSpread)}`],
      });

      score = 0;
      score += hy > 700 ? 18 : hy > 600 ? 10 : 0;
      score += spreadChange > 80 ? 16 : spreadChange > 35 ? 8 : 0;
      score += availability < 42 ? 16 : availability < 52 ? 8 : 0;
      score += bankSentiment < 42 ? 16 : bankSentiment < 50 ? 8 : 0;
      score += impairment > 45 ? 14 : impairment > 25 ? 7 : 0;
      score += refinancing > 60 ? 10 : 0;
      addNarrative(candidates, {
        id: "credit_tightening",
        label: "信用紧缩",
        tone: "bad",
        threshold: 65,
        score,
        summary: "融资条件正在收紧，信用可得性下降，银行更谨慎。这个局面对 GDP 的影响通常带滞后，不会因为流动性改善立刻消失。",
        evidence: [`HY ${fmtBps(hy)}`, `信用可得性 ${fmtIndex(availability)}`, `银行意愿 ${fmtIndex(bankSentiment)}`, `信用疤痕 ${fmtIndex(impairment)}`],
      });

      score = 0;
      score += policyChange < -0.35 ? 18 : policyChange < -0.15 ? 10 : 0;
      score += qe > 40 ? 16 : qe > 25 ? 8 : 0;
      score += liquidityImpulse > 4 ? 14 : liquidityImpulse > 1 ? 7 : 0;
      score += gap < -1.5 ? 10 : 0;
      score += impairment > 20 ? 10 : 0;
      score += hy < numericValue(prev, "global_high_yield_spread_bps", hy) ? 8 : 0;
      addNarrative(candidates, {
        id: "policy_repair",
        label: "政策宽松修复",
        tone: "good",
        threshold: 64,
        score,
        summary: "政策和流动性开始向修复方向发力，但实体和信用还有旧伤。它更像修复期，而不是已经回到正常扩张。",
        evidence: [`政策变化 ${fmtPct(policyChange)}`, `QE ${fmtIndex(qe)}`, `流动性脉冲 ${fmtIndex(liquidityImpulse)}`, `产出缺口 ${fmtPct(gap)}`],
      });

      score = 0;
      score += dollar > 110 ? 18 : dollar > 105 ? 9 : 0;
      score += dollarYoy > 5 ? 14 : dollarYoy > 2 ? 7 : 0;
      score += fundingStress > 58 ? 18 : fundingStress > 45 ? 9 : 0;
      score += emStress > 58 ? 14 : emStress > 45 ? 7 : 0;
      score += liquidity < 45 ? 12 : 0;
      score += fci > 1 ? 8 : 0;
      addNarrative(candidates, {
        id: "dollar_squeeze",
        label: "美元挤兑",
        tone: "bad",
        threshold: 54,
        score,
        summary: "美元走强叠加融资压力，全球流动性被抽紧。外部部门和高杠杆资产更容易先感到压力。",
        evidence: [`美元 ${fmtIndex(dollar)}`, `美元YoY ${fmtPct(dollarYoy)}`, `融资压力 ${fmtIndex(fundingStress)}`, `EM压力 ${fmtIndex(emStress)}`],
      });

      score = 0;
      score += equityReturn > 9 ? 18 : equityReturn > 6 ? 10 : 0;
      score += riskAppetite > 60 ? 14 : riskAppetite > 55 ? 7 : 0;
      score += liquidity > 64 ? 14 : liquidity > 58 ? 7 : 0;
      score += hy < 450 ? 12 : hy < 520 ? 6 : 0;
      score += pe - prevPe > 0.5 ? 8 : 0;
      score += growth > 1.5 ? 6 : 0;
      addNarrative(candidates, {
        id: "risk_asset_bull",
        label: "风险资产牛市",
        tone: "good",
        threshold: 62,
        score,
        summary: "流动性、风险偏好和股市回报同步走强，信用也在配合。资产端的乐观程度高于普通经济扩张。",
        evidence: [`股票 ${fmtPct(equityReturn)}`, `风险偏好 ${fmtIndex(riskAppetite)}`, `流动性 ${fmtIndex(liquidity)}`, `HY ${fmtBps(hy)}`],
      });

      score = 0;
      score += impairment > 60 ? 22 : impairment > 40 ? 12 : 0;
      score += bankSentiment < 45 ? 14 : 0;
      score += gap < -2 ? 12 : 0;
      score += qe > 30 || policyRate < 2 ? 10 : 0;
      score += availability < 50 ? 10 : 0;
      addNarrative(candidates, {
        id: "balance_sheet_recession",
        label: "资产负债表衰退",
        tone: "bad",
        threshold: 56,
        score,
        summary: "政策宽松已经出现，但银行和企业资产负债表还在修复。流动性不等于信用自动宽松，复苏会更像 U 型磨底。",
        evidence: [`信用疤痕 ${fmtIndex(impairment)}`, `银行意愿 ${fmtIndex(bankSentiment)}`, `QE ${fmtIndex(qe)}`, `产出缺口 ${fmtPct(gap)}`],
      });

      score = 0;
      score += tenYear - prevTenYear > 0.65 ? 18 : tenYear - prevTenYear > 0.35 ? 9 : 0;
      score += sovereignReturn < -5 ? 18 : sovereignReturn < -3 ? 9 : 0;
      score += headline > 3.5 ? 10 : 0;
      score += numericValue(row, "term_premium_pct") > 1.1 ? 10 : 0;
      score += equityReturn < 0 && sovereignReturn < 0 ? 10 : 0;
      addNarrative(candidates, {
        id: "bond_shock",
        label: "债券市场冲击",
        tone: "hot",
        threshold: 56,
        score,
        summary: "长端利率或期限溢价上行压低债券价格，股债可能同时承压。市场不只是担心增长，也在重新定价通胀和期限风险。",
        evidence: [`10Y ${fmtLevelPct(tenYear)}`, `10Y变化 ${fmtPct(tenYear - prevTenYear)}`, `主权债 ${fmtPct(sovereignReturn)}`, `Headline ${fmtLevelPct(headline)}`],
      });

      score = 0;
      score += termSpread < -0.7 ? 18 : termSpread < -0.35 ? 10 : 0;
      score += policyRate > headline ? 12 : 0;
      score += growth < numericValue(prev, "realized_growth_pct", growth) ? 8 : 0;
      score += hy > 520 ? 8 : 0;
      addNarrative(candidates, {
        id: "curve_warning",
        label: "倒挂预警",
        tone: "bad",
        threshold: 52,
        score,
        summary: "短端政策压力高于长端增长预期，收益率曲线给出衰退前置信号。它未必马上爆发，但会压制后续信贷和投资。",
        evidence: [`期限利差 ${fmtPct(termSpread)}`, `政策 ${fmtLevelPct(policyRate)}`, `GDP ${fmtPct(growth)}`, `HY ${fmtBps(hy)}`],
      });

      score = 0;
      score += headline - prevHeadline > 0.7 ? 18 : headline - prevHeadline > 0.35 ? 9 : 0;
      score += core - prevCore > 0.35 ? 14 : core - prevCore > 0.15 ? 7 : 0;
      score += numericValue(row, "inflation_expectation_pct", 2.3) > 3 ? 10 : 0;
      score += energyPressure > 60 || numericValue(row, "import_inflation_pct", 2.3) > 4 ? 10 : 0;
      addNarrative(candidates, {
        id: "inflation_reacceleration",
        label: "通胀再加速",
        tone: "hot",
        threshold: 52,
        score,
        summary: "headline 和 core 同时抬头，通胀预期也更难稳定。政策层可能被迫重新转鹰。",
        evidence: [`Headline ${fmtLevelPct(headline)}`, `Headline变化 ${fmtPct(headline - prevHeadline)}`, `Core变化 ${fmtPct(core - prevCore)}`, `能源压力 ${fmtIndex(energyPressure)}`],
      });

      score = 0;
      score += refinancing > 65 ? 18 : refinancing > 55 ? 9 : 0;
      score += availability < 45 ? 14 : 0;
      score += hy > 650 ? 14 : hy > 560 ? 7 : 0;
      score += impairment > 30 ? 8 : 0;
      addNarrative(candidates, {
        id: "refinancing_wall",
        label: "再融资墙",
        tone: "bad",
        threshold: 52,
        score,
        summary: "企业再融资压力抬升，信用可得性又偏弱。压力不一定立刻体现在 GDP 上，但会拖慢投资和盈利修复。",
        evidence: [`再融资 ${fmtIndex(refinancing)}`, `信用可得性 ${fmtIndex(availability)}`, `HY ${fmtBps(hy)}`, `信用疤痕 ${fmtIndex(impairment)}`],
      });

      score = 0;
      score += prevBrent > 105 ? 10 : 0;
      score += oilYoy < -10 ? 16 : oilYoy < -5 ? 8 : 0;
      score += oilDemand < 45 ? 12 : 0;
      score += gap < -1 ? 8 : 0;
      addNarrative(candidates, {
        id: "oil_demand_destruction",
        label: "需求破坏后的油价回落",
        tone: "neutral",
        threshold: 48,
        score,
        summary: "油价从高位回落并不是纯利好，背后有需求被压制的痕迹。能源通胀降温，但增长动能也偏弱。",
        evidence: [`Brent ${fmtOil(brent)}`, `油价 ${fmtPct(oilYoy)}`, `需求压力 ${fmtIndex(oilDemand)}`, `产出缺口 ${fmtPct(gap)}`],
      });

      score = 0;
      score += growth >= 2 && growth <= 3.5 ? 14 : 0;
      score += headline >= 1.7 && headline <= 2.8 ? 14 : 0;
      score += hy < 470 ? 12 : 0;
      score += equityReturn > 4 ? 10 : 0;
      score += riskAppetite > 55 ? 8 : 0;
      score += liquidity > 56 ? 6 : 0;
      addNarrative(candidates, {
        id: "goldilocks",
        label: "金发姑娘",
        tone: "good",
        threshold: 68,
        score,
        summary: "增长、通胀、信用和资产价格都处在舒适区间。市场喜欢这种组合，因为它既不像衰退，也不像过热。",
        evidence: [`GDP ${fmtPct(growth)}`, `Headline ${fmtLevelPct(headline)}`, `HY ${fmtBps(hy)}`, `股票 ${fmtPct(equityReturn)}`],
      });

      return candidates.sort((a, b) => b.score - a.score).slice(0, 4);
    }

    function topNarrative(rows, index) {
      return detectNarratives(rows, index)[0] || null;
    }

    function narrativePeriod(rows, index, narrativeId) {
      let start = index;
      let end = index;
      while (start > 0 && topNarrative(rows, start - 1)?.id === narrativeId) start -= 1;
      while (end < rows.length - 1 && topNarrative(rows, end + 1)?.id === narrativeId) end += 1;
      return { start, end };
    }

    function renderBranchRiskBlock(risks, row) {
      if (scopeConfig().type !== "global") return "";
      if (!risks.length) return "";
      const strongest = risks[0];
      const horizon = strongest.horizon_years ? `${row.year}-${row.year + strongest.horizon_years}` : String(row.year);
      const items = risks.map((risk) => {
        const evidence = (risk.evidence || []).slice(0, 3).map((item) => `<span>${escapeHtml(item)}</span>`).join("");
        const horizonText = risk.horizon_years ? `观察${risk.horizon_years}年` : "观察";
        const impactText = `${risk.impact_years || risk.horizon_years || 1}+${risk.tail_years || 0}年`;
        const isActive = state.scenario?.seed === state.seed
          && state.scenario?.triggerYear === row.year
          && state.scenario?.risk?.id === risk.id;
        return `
          <div class="branch-risk-item">
            <div class="branch-risk-line">
              <strong>${escapeHtml(risk.label)}</strong>
              <span class="branch-risk-prob">${escapeHtml(risk.probability_pct.toFixed(0))}% / ${escapeHtml(horizonText)}</span>
            </div>
            <p class="branch-risk-summary">${escapeHtml(risk.summary)}</p>
            ${evidence ? `<div class="narrative-evidence">${evidence}</div>` : ""}
            <div class="branch-risk-actions">
              <span>冲击+余波 ${escapeHtml(impactText)}</span>
              <button type="button" data-branch-risk-id="${escapeHtml(risk.id)}">${isActive ? "已模拟" : "模拟发生"}</button>
            </div>
          </div>
        `;
      }).join("");
      return `
        <div class="branch-risk-block">
          <div class="branch-risk-head">
            <strong>分岔观察</strong>
            <span>可能触发窗口 ${escapeHtml(horizon)} · ${escapeHtml(String(risks.length))} 条</span>
          </div>
          <div class="branch-risk-list">${items}</div>
        </div>
      `;
    }

    function renderRegionalBranchBlock(row) {
      if (!hasRegionalBranch(row)) return "";
      const stateText = row.regional_branch_transmission_active === "true" ? "已发生路径" : "观察中的潜在传导";
      const phase = row.branch_effect_phase || "watch";
      const impactText = `${row.branch_impact_years || 0}+${row.branch_tail_years || 0}年`;
      const evidence = [
        `增长 ${fmtPp(row.regional_branch_growth_impulse_pct)}`,
        `通胀 ${fmtPp(row.regional_branch_inflation_impulse_pct)}`,
        `信用 ${fmtBps(row.regional_branch_credit_impulse_bps)}`,
        `资产 ${fmtPct(row.regional_branch_asset_impulse_pct)}`,
      ].map((item) => `<span>${escapeHtml(item)}</span>`).join("");
      return `
        <div class="branch-risk-block">
          <div class="branch-risk-head">
            <strong>全球分岔传导</strong>
            <span>${escapeHtml(stateText)} · ${escapeHtml(phase)} · 冲击+余波 ${escapeHtml(impactText)}</span>
          </div>
          <div class="branch-risk-item">
            <div class="branch-risk-line">
              <strong>${escapeHtml(row.branch_scenario_label || row.branch_scenario_id)}</strong>
              <span class="branch-risk-prob">暴露 ${escapeHtml(fmtIndex(row.regional_branch_exposure_index))} / 强度 ${escapeHtml(fmtIndex(row.regional_branch_strength_index))}</span>
            </div>
            <p class="branch-risk-summary">区域层不重新抽事件，只读取全球分岔信号，并按本区域的能源、美元、信用、政策和资产暴露度形成相对全球平均的额外压力。</p>
            <div class="narrative-evidence">${evidence}</div>
          </div>
        </div>
      `;
    }

    function renderNarrative(rows) {
      if (state.mode !== "both") {
        el.narrativePanel.hidden = true;
        el.narrativePanel.innerHTML = "";
        return;
      }
      const index = Math.max(0, Math.min(state.selectedIndex, rows.length - 1));
      const row = rows[index];
      const narratives = detectNarratives(rows, index);
      const branchRisks = branchRisksForRow(rows, index);
      const regionalBranchHtml = renderRegionalBranchBlock(row);
      if (!narratives.length && !branchRisks.length && !regionalBranchHtml) {
        el.narrativePanel.hidden = true;
        el.narrativePanel.innerHTML = "";
        return;
      }
      const scenarioNote = state.scenario?.seed === state.seed ? `
        <div class="scenario-note">
          <strong>发生情景：${escapeHtml(state.scenario.risk.label)}</strong>
          从 ${escapeHtml(String(state.scenario.triggerYear))} 年后分叉，主冲击 ${escapeHtml(String(state.scenario.impactYears))} 年，余波 ${escapeHtml(String(state.scenario.tailYears))} 年。
          <em>浏览器分叉是非权威情景草图；正式资产会计以服务端 Run 的 v0.16/v6 结果为准。</em>
          <button class="scenario-clear" type="button" data-clear-scenario>清除</button>
          <small>${escapeHtml(scenarioDeltaSummary(rows))}</small>
        </div>
      ` : "";
      const narrativeHtml = narratives.length ? (() => {
        const primary = narratives[0];
        const period = narrativePeriod(rows, index, primary.id);
        const startYear = rows[period.start].year;
        const endYear = rows[period.end].year;
        const periodText = startYear === endYear ? String(startYear) : `${startYear}-${endYear}`;
        const tags = narratives.slice(1).map((item) => `<span class="narrative-tag">${escapeHtml(item.label)} ${item.score.toFixed(0)}</span>`).join("");
        const evidence = primary.evidence.slice(0, 4).map((item) => `<span>${escapeHtml(item)}</span>`).join("");
        return `
          <div class="narrative-head">
            <div class="narrative-title">
              <span>宏观解说</span>
              <strong>${escapeHtml(primary.label)}</strong>
            </div>
            <span class="regime" data-tone="${escapeHtml(primary.tone)}">${escapeHtml(periodText)}</span>
          </div>
          <p>${escapeHtml(primary.summary)}</p>
          ${tags ? `<div class="narrative-tags">${tags}</div>` : ""}
          <div class="narrative-evidence">${evidence}</div>
        `;
      })() : `
        <div class="narrative-head">
          <div class="narrative-title">
            <span>宏观解说</span>
            <strong>没有显著主叙事</strong>
          </div>
          <span class="regime" data-tone="neutral">${escapeHtml(String(row.year))}</span>
        </div>
        <p>当前年份没有强到足以命名的宏观时期，但一些分岔条件已经接近触发线，适合作为观察点。</p>
      `;
      el.narrativePanel.hidden = false;
      el.narrativePanel.innerHTML = `${scenarioNote}${narrativeHtml}${renderBranchRiskBlock(branchRisks, row)}${regionalBranchHtml}`;
      el.narrativePanel.querySelectorAll("[data-branch-risk-id]").forEach((button) => {
        button.addEventListener("click", () => simulateBranchRisk(button.dataset.branchRiskId));
      });
      el.narrativePanel.querySelectorAll("[data-clear-scenario]").forEach((button) => {
        button.addEventListener("click", clearScenario);
      });
    }

    function renderDetail(rows) {
      setDetailLabels(MACRO_DETAIL_LABELS);
      const row = selectedRow(rows);
      el.detailTitle.textContent = `${row.scope_label || "全球"} · ${row.year} 年度明细`;
      el.detailRegime.textContent = row.regime;
      el.detailRegime.dataset.tone = toneForRegime(row.regime);
      el.detailGdp.textContent = fmtGdp(row.global_gdp_trillion_usd, row);
      el.detailGrowth.textContent = fmtPct(row.realized_growth_pct);
      el.detailGrowth.className = growthClass(row.realized_growth_pct);
      if (row.macro_scope === "regional" && row.regional_reconciliation_available) {
        el.detailRegionalShare.textContent = `${fmtLevelPct(row.regional_share_of_global_gdp_pct)} / drift ${fmtPp(row.regional_weight_drift_pp)}`;
        el.detailRegionalRank.textContent = `#${row.regional_rank_by_gdp} / ${fmtPp(row.regional_growth_contribution_pp)}`;
      } else {
        el.detailRegionalShare.textContent = "-";
        el.detailRegionalRank.textContent = "-";
      }
      el.detailInflation.textContent = hasInflation(row) ? fmtLevelPct(row.headline_inflation_pct) : "-";
      el.detailCoreInflation.textContent = hasInflation(row) ? fmtLevelPct(row.core_inflation_pct) : "-";
      el.detailPolicyRate.textContent = hasPolicy(row) ? fmtLevelPct(row.global_policy_rate_pct) : "-";
      el.detailPolicyTarget.textContent = hasPolicy(row) ? fmtLevelPct(row.policy_reaction_target_rate_pct) : "-";
      el.detailRealPolicyRate.textContent = hasPolicy(row) ? fmtLevelPct(row.real_policy_rate_pct) : "-";
      el.detailTenYearYield.textContent = hasYield(row) ? fmtLevelPct(row.global_10y_yield_pct) : "-";
      el.detailTermSpread.textContent = hasYield(row) ? fmtPct(row.term_spread_10y_2y_pct) : "-";
      el.detailDollar.textContent = hasDollar(row) ? fmtIndex(row.global_dollar_index) : "-";
      el.detailLiquidity.textContent = hasDollar(row) ? fmtIndex(row.global_liquidity_index) : "-";
      el.detailFinancialConditions.textContent = hasDollar(row) ? fmtIndex(row.global_financial_conditions_index) : "-";
      el.detailHySpread.textContent = hasCredit(row) ? fmtBps(row.global_high_yield_spread_bps) : "-";
      el.detailIgSpread.textContent = hasCredit(row) ? fmtBps(row.global_investment_grade_spread_bps) : "-";
      el.detailCreditAvailability.textContent = hasCredit(row) ? fmtIndex(row.credit_availability_index) : "-";
      el.detailEquity.textContent = hasAsset(row) ? fmtIndex(row.global_equity_price_index) : "-";
      el.detailEquityReturn.textContent = hasAsset(row) ? fmtPct(row.global_equity_total_return_pct) : "-";
      el.detailEquityPe.textContent = hasAsset(row) ? fmtIndex(row.global_equity_valuation_pe) : "-";
      el.detailBond.textContent = hasAsset(row) ? fmtIndex(row.global_sovereign_bond_total_return_index) : "-";
      el.detailOil.textContent = hasOil(row) ? fmtOilMetric(row) : "-";
      el.detailOilReturn.textContent = hasOil(row) ? fmtPct(row.oil_yoy_change_pct) : "-";
      el.detailCommodity.textContent = hasOil(row) ? fmtIndex(row.broad_commodity_index) : "-";
      el.detailEnergyPressure.textContent = hasOil(row) ? fmtIndex(row.energy_cost_pressure_index) : "-";
      el.detailFeedbackIntensity.textContent = hasFeedback(row) ? fmtIndex(row.macro_feedback_intensity_index) : "-";
      el.detailFeedbackGrowth.textContent = hasFeedback(row) ? fmtPct(row.feedback_growth_impulse_pct) : "-";
      el.detailPotentialGrowth.textContent = fmtPct(row.potential_growth_pct);
      el.detailGap.textContent = fmtPct(row.output_gap_pct);
      el.detailStress.textContent = fmtIndex(row.financial_stress_index);
      el.detailShock.textContent = fmtPct(row.shock_component_pct);
    }

    function renderTable(rows) {
      setTableHeaders(MACRO_TABLE_HEADERS);
      el.tableMeta.textContent = `${scopeConfig().label} · ${rows.length} rows`;
      el.body.innerHTML = rows.map((row, index) => `
        <tr class="${index === state.selectedIndex ? "is-selected" : ""}" data-index="${index}">
          <td>${row.year}</td>
          <td>${fmtGdp(row.global_gdp_trillion_usd, row)}</td>
          <td class="${growthClass(row.realized_growth_pct)}">${fmtPct(row.realized_growth_pct)}</td>
          <td>${hasInflation(row) ? fmtLevelPct(row.headline_inflation_pct) : "-"}</td>
          <td>${hasInflation(row) ? fmtLevelPct(row.core_inflation_pct) : "-"}</td>
          <td>${hasPolicy(row) ? fmtLevelPct(row.global_policy_rate_pct) : "-"}</td>
          <td>${hasYield(row) ? fmtLevelPct(row.global_10y_yield_pct) : "-"}</td>
          <td>${hasYield(row) ? fmtPct(row.term_spread_10y_2y_pct) : "-"}</td>
          <td>${hasDollar(row) ? fmtIndex(row.global_dollar_index) : "-"}</td>
          <td>${hasDollar(row) ? fmtIndex(row.global_liquidity_index) : "-"}</td>
          <td>${hasCredit(row) ? fmtBps(row.global_high_yield_spread_bps) : "-"}</td>
          <td>${hasCredit(row) ? fmtBps(row.global_investment_grade_spread_bps) : "-"}</td>
          <td>${hasAsset(row) ? fmtIndex(row.global_equity_total_return_index) : "-"}</td>
          <td>${hasAsset(row) ? fmtIndex(row.global_sovereign_bond_total_return_index) : "-"}</td>
          <td>${hasAsset(row) ? fmtIndex(row.global_equity_valuation_pe) : "-"}</td>
          <td>${hasOil(row) ? fmtOilMetric(row) : "-"}</td>
          <td>${hasOil(row) ? fmtPct(row.oil_yoy_change_pct) : "-"}</td>
          <td>${hasOil(row) ? fmtIndex(row.broad_commodity_index) : "-"}</td>
          <td>${fmtPct(row.potential_growth_pct)}</td>
          <td>${fmtPct(row.output_gap_pct)}</td>
          <td>${fmtPct(row.gdp_level_gap_pct)}</td>
          <td>${fmtPct(row.output_gap_measurement_residual_pct)}</td>
          <td>${fmtIndex(row.financial_stress_index)}</td>
          <td>${hasPolicy(row) ? row.central_bank_reaction_regime : "-"}</td>
          <td>${hasYield(row) ? row.yield_curve_regime : "-"}</td>
          <td>${hasDollar(row) ? row.dollar_liquidity_regime : "-"}</td>
          <td>${hasCredit(row) ? row.credit_regime : "-"}</td>
          <td>${hasAsset(row) ? row.asset_risk_regime : "-"}</td>
          <td>${hasOil(row) ? row.oil_regime : "-"}</td>
          <td><span class="regime" data-tone="${toneForRegime(row.regime)}">${row.regime}</span></td>
        </tr>
      `).join("");
      el.body.querySelectorAll("tr").forEach((tr) => {
        tr.addEventListener("click", () => {
          state.selectedIndex = Number(tr.dataset.index);
          render();
        });
      });
    }

    function fmtAviationEvent(row) {
      const hint = row?.airport_event_hint || "none";
      return hint && hint !== "none" ? hint : "normal_air_cycle";
    }

    function aviationTone(row) {
      const regime = String(row?.aviation_demand_regime || "");
      const eventHint = String(row?.airport_event_hint || "");
      if (eventHint && eventHint !== "none") return "hot";
      if (regime.includes("drag") || regime.includes("warning")) return "bad";
      if (regime.includes("recovery") || regime.includes("premium") || regime.includes("resilient")) return "good";
      return "neutral";
    }

    function hasAirSupply(row) {
      return row?.air_supply_available === true
        && typeof row.business_fulfillment_pct === "number"
        && !Number.isNaN(row.business_fulfillment_pct);
    }

    function fulfillmentTone(value) {
      if (typeof value !== "number" || Number.isNaN(value)) return "";
      if (value < 86) return "bad";
      if (value < 94) return "hot";
      if (value >= 98) return "good";
      return "neutral";
    }

    function airSupplyStats(row) {
      if (!hasAirSupply(row)) return [];
      const sub = `区域参考满足 ${fmtLevelPct(row.capacity_fulfillment_pct)} / ${row.supply_regime || "supply"}`;
      return [
        makeStat("商务满足率", fmtLevelPct(row.business_fulfillment_pct), sub, fulfillmentTone(row.business_fulfillment_pct)),
        makeStat("休闲满足率", fmtLevelPct(row.leisure_fulfillment_pct), sub, fulfillmentTone(row.leisure_fulfillment_pct)),
        makeStat("VFR 满足率", fmtLevelPct(row.vfr_fulfillment_pct), sub, fulfillmentTone(row.vfr_fulfillment_pct)),
        makeStat("长途满足率", fmtLevelPct(row.long_haul_fulfillment_pct), sub, fulfillmentTone(row.long_haul_fulfillment_pct)),
        makeStat("中转满足率", fmtLevelPct(row.transfer_fulfillment_pct), sub, fulfillmentTone(row.transfer_fulfillment_pct)),
      ];
    }

    function summarizeAviation(rows) {
      const data = rows.filter((row) => row.year_index > 0);
      const growths = data.map((row) => row.regional_air_demand_growth_pct);
      const avg = growths.reduce((acc, value) => acc + value, 0) / Math.max(1, growths.length);
      const minRow = data.reduce((best, row) => row.regional_air_demand_growth_pct < best.regional_air_demand_growth_pct ? row : best, data[0] || rows[0]);
      const eventYears = data.filter((row) => row.airport_event_hint && row.airport_event_hint !== "none").length;
      return { avg, minRow, eventYears };
    }

    function unavailableAviationStats() {
      return [
        makeStat("航空需求", "-", "当前区域还没有航空需求参数"),
        makeStat("可用区域", Object.keys(state.aviationDatasets).length ? Object.keys(state.aviationDatasets).join(", ") : "-", "先开放北美"),
      ];
    }

    function renderAviationStats(rows) {
      setChartLegend(AVIATION_LEGEND_HTML);
      const row = selectedRow(rows);
      if (!row) {
        el.statsGrid.innerHTML = unavailableAviationStats().map((card) => `
          <div class="stat">
            <span>${escapeHtml(card.label)}</span>
            <strong>${escapeHtml(card.value)}</strong>
            <small>${escapeHtml(card.sub)}</small>
          </div>
        `).join("");
        return;
      }
      const first = rows[0];
      const last = rows[rows.length - 1];
      const summary = summarizeAviation(rows);
      const cumulativeDemand = first.regional_air_demand_index
        ? (row.regional_air_demand_index / first.regional_air_demand_index - 1) * 100
        : 0;
      const statsByMode = {
        both: () => [
          makeStat("区域航空需求", fmtIndex(row.regional_air_demand_index), `${row.year} / final ${fmtIndex(last.regional_air_demand_index)}`),
          makeStat("航空需求增长", fmtPct(row.regional_air_demand_growth_pct), `avg ${fmtPct(summary.avg)}`, growthClass(row.regional_air_demand_growth_pct)),
          makeStat("商务需求", fmtIndex(row.business_travel_demand_index), `share ${fmtLevelPct(row.business_travel_share_pct)} / ${fmtPct(row.business_travel_growth_pct)}`),
          makeStat("休闲需求", fmtIndex(row.leisure_travel_demand_index), `share ${fmtLevelPct(row.leisure_travel_share_pct)} / ${fmtPct(row.leisure_travel_growth_pct)}`),
          makeStat("VFR", fmtIndex(row.vfr_travel_demand_index), `share ${fmtLevelPct(row.vfr_travel_share_pct)} / ${fmtPct(row.vfr_travel_growth_pct)}`),
          ...airSupplyStats(row),
          makeStat("票价敏感度", fmtIndex(row.airfare_price_sensitivity_index), `pressure ${fmtIndex(row.airfare_pressure_index)}`),
          makeStat("高端客倾向", fmtIndex(row.premium_passenger_propensity_index), `share ${fmtLevelPct(row.premium_passenger_share_pct)}`),
          makeStat("免税倾向", fmtIndex(row.duty_free_propensity_index), `luxury ${fmtIndex(row.luxury_retail_propensity_index)}`),
          makeStat("事件提示", fmtAviationEvent(row), `${row.branch_effect_phase || "normal"} / pressure ${fmtIndex(row.airport_event_pressure_index)}`, aviationTone(row)),
        ],
        gdp: () => [
          makeStat("总需求指数", fmtIndex(row.regional_air_demand_index), `base ${fmtIndex(first.regional_air_demand_index)} / ${fmtPct(cumulativeDemand)}`),
          makeStat("最终需求指数", fmtIndex(last.regional_air_demand_index), `${first.year}-${last.year}`),
          makeStat("商务需求", fmtIndex(row.business_travel_demand_index), `share ${fmtLevelPct(row.business_travel_share_pct)}`),
          makeStat("休闲需求", fmtIndex(row.leisure_travel_demand_index), `share ${fmtLevelPct(row.leisure_travel_share_pct)}`),
          makeStat("VFR 需求", fmtIndex(row.vfr_travel_demand_index), `share ${fmtLevelPct(row.vfr_travel_share_pct)}`),
          makeStat("长途需求", fmtIndex(row.long_haul_demand_index), `share ${fmtLevelPct(row.long_haul_share_pct)}`),
          makeStat("中转需求", fmtIndex(row.transfer_demand_index), `share ${fmtLevelPct(row.transfer_share_pct)}`),
        ],
        growth: () => [
          makeStat("总需求增长", fmtPct(row.regional_air_demand_growth_pct), `lowest ${fmtPct(summary.minRow.regional_air_demand_growth_pct)} in ${summary.minRow.year}`, growthClass(row.regional_air_demand_growth_pct)),
          makeStat("商务增长", fmtPct(row.business_travel_growth_pct), `input GDP ${fmtPct(row.input_regional_gdp_growth_pct)}`, growthClass(row.business_travel_growth_pct)),
          makeStat("休闲增长", fmtPct(row.leisure_travel_growth_pct), `income ${fmtPct(row.input_real_income_growth_pct)}`, growthClass(row.leisure_travel_growth_pct)),
          makeStat("VFR 增长", fmtPct(row.vfr_travel_growth_pct), "more stable segment", growthClass(row.vfr_travel_growth_pct)),
          makeStat("长途增长", fmtPct(row.long_haul_growth_pct), `currency pressure ${fmtIndex(row.input_currency_pressure_index)}`, growthClass(row.long_haul_growth_pct)),
          makeStat("中转增长", fmtPct(row.transfer_growth_pct), "hub flow", growthClass(row.transfer_growth_pct)),
        ],
        inflation: () => [
          makeStat("商务占比", fmtLevelPct(row.business_travel_share_pct), `index ${fmtIndex(row.business_travel_demand_index)}`),
          makeStat("休闲占比", fmtLevelPct(row.leisure_travel_share_pct), `index ${fmtIndex(row.leisure_travel_demand_index)}`),
          makeStat("VFR 占比", fmtLevelPct(row.vfr_travel_share_pct), `index ${fmtIndex(row.vfr_travel_demand_index)}`),
          makeStat("长途占比", fmtLevelPct(row.long_haul_share_pct), `index ${fmtIndex(row.long_haul_demand_index)}`),
          makeStat("中转占比", fmtLevelPct(row.transfer_share_pct), `index ${fmtIndex(row.transfer_demand_index)}`),
          makeStat("高端客占比", fmtLevelPct(row.premium_passenger_share_pct), `propensity ${fmtIndex(row.premium_passenger_propensity_index)}`),
        ],
        policy: () => [
          makeStat("票价敏感度", fmtIndex(row.airfare_price_sensitivity_index), "higher = demand more price-sensitive"),
          makeStat("票价压力", fmtIndex(row.airfare_pressure_index), `energy ${fmtIndex(row.input_energy_cost_pressure_index)}`),
          makeStat("消费者信心", fmtIndex(row.input_consumer_confidence_index), `stress ${fmtIndex(row.input_macro_stress_index)}`),
          makeStat("能源压力", fmtIndex(row.input_energy_cost_pressure_index), `event ${fmtPct(row.aviation_event_impulse_pct)}`),
        ],
        yield: () => [
          makeStat("商务弹性", fmtIndex(row.business_fare_elasticity), "low elasticity"),
          makeStat("休闲弹性", fmtIndex(row.leisure_fare_elasticity), "high elasticity"),
          makeStat("VFR 弹性", fmtIndex(row.vfr_fare_elasticity), "medium elasticity"),
          makeStat("长途弹性", fmtIndex(row.long_haul_fare_elasticity), "fare and FX sensitive"),
          makeStat("中转弹性", fmtIndex(row.transfer_fare_elasticity), "route-choice sensitive"),
          makeStat("高端弹性", fmtIndex(row.premium_fare_elasticity), "lowest elasticity"),
        ],
        dollar: () => [
          makeStat("高端客倾向", fmtIndex(row.premium_passenger_propensity_index), `share ${fmtLevelPct(row.premium_passenger_share_pct)}`),
          makeStat("商务需求", fmtIndex(row.business_travel_demand_index), `growth ${fmtPct(row.business_travel_growth_pct)}`),
          makeStat("长途需求", fmtIndex(row.long_haul_demand_index), `growth ${fmtPct(row.long_haul_growth_pct)}`),
          makeStat("奢侈品倾向", fmtIndex(row.luxury_retail_propensity_index), `duty free ${fmtIndex(row.duty_free_propensity_index)}`),
        ],
        credit: () => [
          makeStat("机场事件提示", fmtAviationEvent(row), row.aviation_demand_regime || "-", aviationTone(row)),
          makeStat("事件压力", fmtIndex(row.airport_event_pressure_index), `impulse ${fmtPct(row.aviation_event_impulse_pct)}`),
          makeStat("分岔状态", row.branch_scenario_state || "baseline", row.branch_scenario_id || "none"),
          makeStat("分岔阶段", row.branch_effect_phase || "-", `strength ${fmtIndex(row.regional_branch_strength_index)}`),
          makeStat("宏观压力", fmtIndex(row.input_macro_stress_index), `HY ${fmtBps(row.input_hy_spread_bps)}`),
          makeStat("事件年份", String(summary.eventYears), `${first.year}-${last.year}`),
        ],
        asset: () => [
          makeStat("免税倾向", fmtIndex(row.duty_free_propensity_index), `long-haul ${fmtIndex(row.long_haul_demand_index)}`),
          makeStat("奢侈品倾向", fmtIndex(row.luxury_retail_propensity_index), `premium ${fmtIndex(row.premium_passenger_propensity_index)}`),
          makeStat("电子产品倾向", fmtIndex(row.electronics_retail_propensity_index), `currency ${fmtIndex(row.input_currency_pressure_index)}`),
          makeStat("餐饮倾向", fmtIndex(row.food_beverage_propensity_index), `traffic ${fmtIndex(row.regional_air_demand_index)}`),
          makeStat("普通零售", fmtIndex(row.general_retail_propensity_index), `leisure ${fmtIndex(row.leisure_travel_demand_index)}`),
        ],
        oil: () => [
          makeStat("输入 GDP 增长", fmtPct(row.input_regional_gdp_growth_pct), `regional GDP ${fmtUsd(row.regional_reconciled_gdp_trillion_usd)}`, growthClass(row.input_regional_gdp_growth_pct)),
          makeStat("真实收入增长", fmtPct(row.input_real_income_growth_pct), `confidence ${fmtIndex(row.input_consumer_confidence_index)}`, growthClass(row.input_real_income_growth_pct)),
          makeStat("宏观压力", fmtIndex(row.input_macro_stress_index), `HY ${fmtBps(row.input_hy_spread_bps)}`),
          makeStat("能源压力", fmtIndex(row.input_energy_cost_pressure_index), `fare pressure ${fmtIndex(row.airfare_pressure_index)}`),
          makeStat("货币压力", fmtIndex(row.input_currency_pressure_index), `资产市场 ${fmtIndex(row.input_asset_market_impulse_index)}`),
        ],
      };
      const cards = (statsByMode[state.mode] || statsByMode.both)();
      el.statsGrid.dataset.activeMode = `aviation-${state.mode}`;
      el.statsGrid.innerHTML = cards.map((card) => `
        <div class="stat">
          <span>${escapeHtml(card.label)}</span>
          <strong class="${escapeHtml(card.tone)}">${escapeHtml(card.value)}</strong>
          <small>${escapeHtml(card.sub)}</small>
        </div>
      `).join("");
    }

    function renderAviationDetail(rows) {
      setDetailLabels(AVIATION_DETAIL_LABELS);
      const row = selectedRow(rows);
      clearDetailValues();
      if (!row) return;
      el.detailTitle.textContent = `${row.scope_label || "区域"} · ${row.year} 航空需求`;
      el.detailRegime.textContent = row.aviation_demand_regime || "-";
      el.detailRegime.dataset.tone = aviationTone(row);
      el.detailGdp.textContent = fmtIndex(row.regional_air_demand_index);
      el.detailGrowth.textContent = fmtPct(row.regional_air_demand_growth_pct);
      el.detailGrowth.className = growthClass(row.regional_air_demand_growth_pct);
      el.detailRegionalShare.textContent = `${fmtIndex(row.business_travel_demand_index)} / ${fmtLevelPct(row.business_travel_share_pct)}`;
      el.detailRegionalRank.textContent = `${fmtIndex(row.leisure_travel_demand_index)} / ${fmtLevelPct(row.leisure_travel_share_pct)}`;
      el.detailInflation.textContent = `${fmtIndex(row.vfr_travel_demand_index)} / ${fmtLevelPct(row.vfr_travel_share_pct)}`;
      el.detailCoreInflation.textContent = `${fmtIndex(row.long_haul_demand_index)} / ${fmtLevelPct(row.long_haul_share_pct)}`;
      el.detailPolicyRate.textContent = `${fmtIndex(row.transfer_demand_index)} / ${fmtLevelPct(row.transfer_share_pct)}`;
      el.detailPolicyTarget.textContent = fmtIndex(row.airfare_price_sensitivity_index);
      el.detailRealPolicyRate.textContent = fmtIndex(row.airfare_pressure_index);
      el.detailTenYearYield.textContent = fmtIndex(row.business_fare_elasticity);
      el.detailTermSpread.textContent = fmtIndex(row.leisure_fare_elasticity);
      el.detailDollar.textContent = fmtIndex(row.vfr_fare_elasticity);
      el.detailLiquidity.textContent = fmtIndex(row.long_haul_fare_elasticity);
      el.detailFinancialConditions.textContent = fmtIndex(row.transfer_fare_elasticity);
      el.detailHySpread.textContent = fmtIndex(row.premium_fare_elasticity);
      el.detailIgSpread.textContent = fmtIndex(row.premium_passenger_propensity_index);
      el.detailCreditAvailability.textContent = fmtLevelPct(row.premium_passenger_share_pct);
      el.detailEquity.textContent = fmtIndex(row.duty_free_propensity_index);
      el.detailEquityReturn.textContent = fmtIndex(row.luxury_retail_propensity_index);
      el.detailEquityPe.textContent = fmtIndex(row.electronics_retail_propensity_index);
      el.detailBond.textContent = fmtIndex(row.food_beverage_propensity_index);
      el.detailOil.textContent = fmtIndex(row.general_retail_propensity_index);
      el.detailOilReturn.textContent = fmtAviationEvent(row);
      el.detailCommodity.textContent = fmtIndex(row.airport_event_pressure_index);
      el.detailEnergyPressure.textContent = fmtPct(row.aviation_event_impulse_pct);
      el.detailFeedbackIntensity.textContent = fmtPct(row.input_regional_gdp_growth_pct);
      el.detailFeedbackGrowth.textContent = fmtPct(row.input_real_income_growth_pct);
      el.detailPotentialGrowth.textContent = fmtIndex(row.input_consumer_confidence_index);
      el.detailGap.textContent = fmtIndex(row.input_macro_stress_index);
      el.detailStress.textContent = fmtIndex(row.input_energy_cost_pressure_index);
      el.detailShock.textContent = `${row.branch_effect_phase || "-"} / ${fmtIndex(row.regional_branch_strength_index)}`;
    }

    function renderAviationTable(rows) {
      setTableHeaders(AVIATION_TABLE_HEADERS);
      el.tableMeta.textContent = `${scopeConfig().label} · 航空需求 · ${rows.length} rows`;
      el.body.innerHTML = rows.map((row, index) => `
        <tr class="${index === state.selectedIndex ? "is-selected" : ""}" data-index="${index}">
          <td>${row.year}</td>
          <td>${fmtIndex(row.regional_air_demand_index)}</td>
          <td class="${growthClass(row.regional_air_demand_growth_pct)}">${fmtPct(row.regional_air_demand_growth_pct)}</td>
          <td>${fmtIndex(row.business_travel_demand_index)} / ${fmtLevelPct(row.business_travel_share_pct)}</td>
          <td>${fmtIndex(row.leisure_travel_demand_index)} / ${fmtLevelPct(row.leisure_travel_share_pct)}</td>
          <td>${fmtIndex(row.vfr_travel_demand_index)} / ${fmtLevelPct(row.vfr_travel_share_pct)}</td>
          <td>${fmtIndex(row.long_haul_demand_index)} / ${fmtLevelPct(row.long_haul_share_pct)}</td>
          <td>${fmtIndex(row.transfer_demand_index)} / ${fmtLevelPct(row.transfer_share_pct)}</td>
          <td>${hasAirSupply(row) ? fmtLevelPct(row.business_fulfillment_pct) : "-"}</td>
          <td>${hasAirSupply(row) ? fmtLevelPct(row.leisure_fulfillment_pct) : "-"}</td>
          <td>${hasAirSupply(row) ? fmtLevelPct(row.vfr_fulfillment_pct) : "-"}</td>
          <td>${hasAirSupply(row) ? fmtLevelPct(row.long_haul_fulfillment_pct) : "-"}</td>
          <td>${hasAirSupply(row) ? fmtLevelPct(row.transfer_fulfillment_pct) : "-"}</td>
          <td>${fmtIndex(row.airfare_price_sensitivity_index)}</td>
          <td>${fmtIndex(row.airfare_pressure_index)}</td>
          <td>${fmtIndex(row.business_fare_elasticity)}</td>
          <td>${fmtIndex(row.leisure_fare_elasticity)}</td>
          <td>${fmtIndex(row.premium_passenger_propensity_index)}</td>
          <td>${fmtLevelPct(row.premium_passenger_share_pct)}</td>
          <td>${fmtIndex(row.duty_free_propensity_index)}</td>
          <td>${fmtIndex(row.luxury_retail_propensity_index)}</td>
          <td>${fmtIndex(row.electronics_retail_propensity_index)}</td>
          <td>${fmtIndex(row.food_beverage_propensity_index)}</td>
          <td>${fmtIndex(row.general_retail_propensity_index)}</td>
          <td>${fmtAviationEvent(row)}</td>
          <td>${fmtIndex(row.airport_event_pressure_index)}</td>
          <td>${fmtIndex(row.input_macro_stress_index)}</td>
          <td>${fmtIndex(row.input_energy_cost_pressure_index)}</td>
          <td>${fmtIndex(row.input_consumer_confidence_index)}</td>
          <td>${fmtPct(row.input_regional_gdp_growth_pct)}</td>
          <td>${fmtPct(row.input_real_income_growth_pct)}</td>
          <td>${row.branch_effect_phase || "-"}</td>
          <td><span class="regime" data-tone="${aviationTone(row)}">${escapeHtml(row.aviation_demand_regime || "-")}</span></td>
        </tr>
      `).join("");
      el.body.querySelectorAll("tr").forEach((tr) => {
        tr.addEventListener("click", () => {
          state.selectedIndex = Number(tr.dataset.index);
          render();
        });
      });
    }

    function aviationNarrativeText(row) {
      const eventHint = row.airport_event_hint || "none";
      if (eventHint && eventHint !== "none") {
        return {
          title: eventHint,
          summary: `宏观分岔已经传到航空需求层：${eventHint}。当前事件压力 ${fmtIndex(row.airport_event_pressure_index)}，航空冲击 ${fmtPct(row.aviation_event_impulse_pct)}，更适合观察商务、高端和长途需求的分化。`,
          tone: "hot",
        };
      }
      if (row.airfare_price_sensitivity_index >= 70) {
        return {
          title: "票价敏感期",
          summary: `票价敏感度升至 ${fmtIndex(row.airfare_price_sensitivity_index)}，休闲和长途需求更容易被油价、通胀或汇率压力压制。`,
          tone: "bad",
        };
      }
      if (row.premium_passenger_propensity_index >= 145 && row.business_travel_share_pct >= 36) {
        return {
          title: "高端客支撑商业",
          summary: `高端客倾向 ${fmtIndex(row.premium_passenger_propensity_index)}，商务占比 ${fmtLevelPct(row.business_travel_share_pct)}。机场商业层里，免税和精品消费可能比总客流更有韧性。`,
          tone: "good",
        };
      }
      if (row.leisure_travel_growth_pct <= -2.0) {
        return {
          title: "休闲客承压",
          summary: `休闲需求增长 ${fmtPct(row.leisure_travel_growth_pct)}，说明当前价格、收入或信心压力主要打在弹性客群上。`,
          tone: "bad",
        };
      }
      return null;
    }

    function renderAviationNarrative(rows) {
      const row = selectedRow(rows);
      const note = row ? aviationNarrativeText(row) : null;
      if (!note || state.mode === "yield") {
        el.narrativePanel.hidden = true;
        el.narrativePanel.innerHTML = "";
        return;
      }
      el.narrativePanel.hidden = false;
      el.narrativePanel.innerHTML = `
        <div class="narrative-head">
          <div class="narrative-title">
            <span>航空需求解说</span>
            <strong>${escapeHtml(note.title)}</strong>
          </div>
          <span class="regime" data-tone="${escapeHtml(note.tone)}">${escapeHtml(String(row.year))}</span>
        </div>
        <p>${escapeHtml(note.summary)}</p>
        <div class="narrative-evidence">
          <span>总需求 ${fmtIndex(row.regional_air_demand_index)}</span>
          <span>增长 ${fmtPct(row.regional_air_demand_growth_pct)}</span>
          <span>票价压力 ${fmtIndex(row.airfare_pressure_index)}</span>
          <span>宏观压力 ${fmtIndex(row.input_macro_stress_index)}</span>
        </div>
      `;
    }

    function renderEmptyView() {
      const isAviation = state.view === "aviation";
      setChartLegend(isAviation ? AVIATION_LEGEND_HTML : macroLegendHtml());
      setDetailLabels(isAviation ? AVIATION_DETAIL_LABELS : MACRO_DETAIL_LABELS);
      setTableHeaders(isAviation ? AVIATION_TABLE_HEADERS : MACRO_TABLE_HEADERS);
      clearDetailValues();
      el.yearRange.max = "0";
      el.yearRange.value = "0";
      el.yearLabel.textContent = "-";
      el.detailTitle.textContent = isAviation ? "航空需求未开放" : "年度明细";
      el.detailRegime.textContent = "-";
      el.detailRegime.dataset.tone = "neutral";
      el.tableMeta.textContent = "-";
      el.body.innerHTML = "";
      el.narrativePanel.hidden = true;
      el.narrativePanel.innerHTML = "";
      el.statsGrid.innerHTML = (isAviation ? unavailableAviationStats() : [makeStat("数据", "-", "没有可用 rows")]).map((card) => `
        <div class="stat">
          <span>${escapeHtml(card.label)}</span>
          <strong>${escapeHtml(card.value)}</strong>
          <small>${escapeHtml(card.sub)}</small>
        </div>
      `).join("");
      el.chart.innerHTML = `<text x="24" y="44" font-size="14" fill="#94a3b8">没有可用数据</text>`;
    }

    function pathFromPoints(points) {
      return points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`).join(" ");
    }

    function aviationChartSeries(rows) {
      const seriesByMode = {
        both: {
          axisLabel: "demand index",
          percentLabel: "growth %",
          bars: [{ field: "regional_air_demand_growth_pct", label: "总需求增长", color: "auto" }],
          lines: [
            { field: "regional_air_demand_index", label: "总需求", color: "#60a5fa" },
            { field: "business_travel_demand_index", label: "商务", color: "#22d3ee" },
            { field: "leisure_travel_demand_index", label: "休闲", color: "#facc15" },
          ],
        },
        gdp: {
          axisLabel: "demand index",
          lines: [
            { field: "regional_air_demand_index", label: "总需求", color: "#60a5fa" },
            { field: "business_travel_demand_index", label: "商务", color: "#22d3ee" },
            { field: "leisure_travel_demand_index", label: "休闲", color: "#facc15" },
            { field: "vfr_travel_demand_index", label: "VFR", color: "#a78bfa" },
            { field: "long_haul_demand_index", label: "长途", color: "#fb923c" },
            { field: "transfer_demand_index", label: "中转", color: "#14b8a6" },
          ],
        },
        growth: {
          axisLabel: "growth %",
          zero: true,
          bars: [{ field: "regional_air_demand_growth_pct", label: "总需求增长", color: "auto" }],
          lines: [
            { field: "business_travel_growth_pct", label: "商务", color: "#22d3ee" },
            { field: "leisure_travel_growth_pct", label: "休闲", color: "#facc15" },
            { field: "vfr_travel_growth_pct", label: "VFR", color: "#a78bfa" },
            { field: "long_haul_growth_pct", label: "长途", color: "#fb923c" },
            { field: "transfer_growth_pct", label: "中转", color: "#14b8a6" },
          ],
        },
        inflation: {
          axisLabel: "share %",
          lines: [
            { field: "business_travel_share_pct", label: "商务占比", color: "#22d3ee" },
            { field: "leisure_travel_share_pct", label: "休闲占比", color: "#facc15" },
            { field: "vfr_travel_share_pct", label: "VFR 占比", color: "#a78bfa" },
            { field: "long_haul_share_pct", label: "长途占比", color: "#fb923c" },
            { field: "transfer_share_pct", label: "中转占比", color: "#14b8a6" },
            { field: "premium_passenger_share_pct", label: "高端占比", color: "#d946ef" },
          ],
        },
        policy: {
          axisLabel: "price index",
          lines: [
            { field: "airfare_price_sensitivity_index", label: "票价敏感度", color: "#60a5fa" },
            { field: "airfare_pressure_index", label: "票价压力", color: "#fb923c" },
            { field: "input_energy_cost_pressure_index", label: "能源压力", color: "#f97316" },
            { field: "input_consumer_confidence_index", label: "信心", color: "#34d399" },
          ],
        },
        yield: {
          axisLabel: "fare elasticity",
          lines: [
            { field: "business_fare_elasticity", label: "商务", color: "#22d3ee" },
            { field: "leisure_fare_elasticity", label: "休闲", color: "#facc15" },
            { field: "vfr_fare_elasticity", label: "VFR", color: "#a78bfa" },
            { field: "long_haul_fare_elasticity", label: "长途", color: "#fb923c" },
            { field: "transfer_fare_elasticity", label: "中转", color: "#14b8a6" },
            { field: "premium_fare_elasticity", label: "高端", color: "#d946ef" },
          ],
        },
        dollar: {
          axisLabel: "premium / high-value index",
          lines: [
            { field: "premium_passenger_propensity_index", label: "高端客倾向", color: "#d946ef" },
            { field: "business_travel_demand_index", label: "商务需求", color: "#22d3ee" },
            { field: "long_haul_demand_index", label: "长途需求", color: "#fb923c" },
            { field: "luxury_retail_propensity_index", label: "精品倾向", color: "#facc15" },
          ],
        },
        credit: {
          axisLabel: "event / stress index",
          lines: [
            { field: "airport_event_pressure_index", label: "事件压力", color: "#fb7185" },
            { field: "regional_branch_strength_index", label: "分岔强度", color: "#fb923c" },
            { field: "input_macro_stress_index", label: "宏观压力", color: "#a78bfa" },
            { field: "airfare_pressure_index", label: "票价压力", color: "#60a5fa" },
          ],
        },
        asset: {
          axisLabel: "commercial propensity index",
          lines: [
            { field: "duty_free_propensity_index", label: "免税", color: "#60a5fa" },
            { field: "luxury_retail_propensity_index", label: "精品", color: "#d946ef" },
            { field: "electronics_retail_propensity_index", label: "电子", color: "#22d3ee" },
            { field: "food_beverage_propensity_index", label: "餐饮", color: "#facc15" },
            { field: "general_retail_propensity_index", label: "普通零售", color: "#14b8a6" },
          ],
        },
        oil: {
          axisLabel: "macro input index",
          lines: [
            { field: "input_macro_stress_index", label: "宏观压力", color: "#a78bfa" },
            { field: "input_energy_cost_pressure_index", label: "能源压力", color: "#f97316" },
            { field: "input_consumer_confidence_index", label: "信心", color: "#34d399" },
            { field: "airfare_pressure_index", label: "票价压力", color: "#fb923c" },
          ],
        },
      };
      return seriesByMode[state.mode] || seriesByMode.both;
    }

    function renderAviationChart(rows) {
      const svg = el.chart;
      const box = svg.getBoundingClientRect();
      const width = Math.max(320, box.width || 900);
      const height = Math.max(280, box.height || 500);
      const margin = { top: 20, right: 58, bottom: 42, left: 62 };
      const plotW = width - margin.left - margin.right;
      const plotH = height - margin.top - margin.bottom;
      const selected = selectedRow(rows);
      const spec = aviationChartSeries(rows);
      const lineSeries = spec.lines || [];
      const barSeries = spec.bars || [];
      const years = rows.map((row) => row.year);
      const minYear = Math.min(...years);
      const maxYear = Math.max(...years);
      const lineValues = lineSeries.flatMap((series) => rows.map((row) => numericValue(row, series.field, NaN)).filter(Number.isFinite));
      const barValues = barSeries.flatMap((series) => rows.map((row) => numericValue(row, series.field, NaN)).filter(Number.isFinite));
      const axisValues = lineValues.length ? lineValues : barValues;
      const minRaw = Math.min(...axisValues, spec.zero ? 0 : Infinity);
      const maxRaw = Math.max(...axisValues, spec.zero ? 0 : -Infinity);
      const span = Math.max(1e-9, maxRaw - minRaw);
      const minAxis = minRaw - span * 0.10;
      const maxAxis = maxRaw + span * 0.10;
      const maxAbsBar = Math.max(4, ...barValues.map((value) => Math.abs(value))) * 1.15;

      const x = (year) => margin.left + ((year - minYear) / Math.max(1, maxYear - minYear)) * plotW;
      const y = (value) => margin.top + ((maxAxis - value) / Math.max(1e-9, maxAxis - minAxis)) * plotH;
      const yBar = (value) => margin.top + ((maxAbsBar - value) / (maxAbsBar * 2)) * plotH;
      const zeroY = barSeries.length ? yBar(0) : y(0);

      const grid = [];
      for (let i = 0; i <= 5; i += 1) {
        const yy = margin.top + (i / 5) * plotH;
        const tick = maxAxis - (i / 5) * (maxAxis - minAxis);
        grid.push(`<line x1="${margin.left}" y1="${yy}" x2="${margin.left + plotW}" y2="${yy}" stroke="#1f2937" />`);
        grid.push(`<text x="${margin.left - 9}" y="${yy + 4}" text-anchor="end" font-size="11" fill="#94a3b8">${tick.toFixed(tick < 3 ? 2 : 0)}</text>`);
      }
      for (let i = 0; i <= 5; i += 1) {
        const xx = margin.left + (i / 5) * plotW;
        const year = Math.round(minYear + (i / 5) * (maxYear - minYear));
        grid.push(`<line x1="${xx}" y1="${margin.top}" x2="${xx}" y2="${margin.top + plotH}" stroke="#172033" />`);
        grid.push(`<text x="${xx}" y="${height - 13}" text-anchor="middle" font-size="11" fill="#94a3b8">${year}</text>`);
      }

      const bars = barSeries.map((series) => rows.map((row) => {
        const value = numericValue(row, series.field);
        const barW = Math.max(3, plotW / rows.length * 0.62);
        const xx = x(row.year) - barW / 2;
        const yy = Math.min(zeroY, yBar(value));
        const hh = Math.max(1, Math.abs(yBar(value) - zeroY));
        const color = series.color === "auto"
          ? value < 0 ? "rgba(251,113,133,0.74)" : "rgba(52,211,153,0.62)"
          : series.color;
        return `<rect x="${xx.toFixed(2)}" y="${yy.toFixed(2)}" width="${barW.toFixed(2)}" height="${hh.toFixed(2)}" fill="${color}" rx="2" />`;
      }).join("")).join("");

      const lines = lineSeries.map((series) => {
        const points = rows
          .map((row) => ({ x: x(row.year), y: y(numericValue(row, series.field, 0)) }));
        return `<path d="${pathFromPoints(points)}" fill="none" stroke="${series.color}" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round" />`;
      }).join("");

      const eventBands = rows.map((row) => {
        if (!row.airport_event_hint || row.airport_event_hint === "none") return "";
        const bandW = Math.max(8, plotW / rows.length);
        return `<rect x="${(x(row.year) - bandW / 2).toFixed(2)}" y="${margin.top}" width="${bandW.toFixed(2)}" height="${plotH}" fill="rgba(251,146,60,0.13)" />`;
      }).join("");

      const legend = lineSeries.slice(0, 6).map((series, index) => {
        const xx = margin.left + 8 + index * 92;
        return `
          <g pointer-events="none">
            <line x1="${xx}" y1="${margin.top + 14}" x2="${xx + 22}" y2="${margin.top + 14}" stroke="${series.color}" stroke-width="2.3" />
            <text x="${xx + 28}" y="${margin.top + 18}" font-size="11" fill="#94a3b8">${escapeHtml(series.label)}</text>
          </g>
        `;
      }).join("");

      const hitRects = rows.map((row, index) => {
        const w = Math.max(8, plotW / rows.length);
        return `<rect x="${(x(row.year) - w / 2).toFixed(2)}" y="${margin.top}" width="${w.toFixed(2)}" height="${plotH}" fill="transparent" data-index="${index}" class="hit" />`;
      }).join("");

      const selectedX = x(selected.year);
      const selectedMarkers = lineSeries.map((series) => `
        <circle cx="${selectedX}" cy="${y(numericValue(selected, series.field, 0))}" r="4.2" fill="${series.color}" stroke="#0b1120" stroke-width="2" />
      `).join("");

      svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
      svg.innerHTML = `
        <rect x="0" y="0" width="${width}" height="${height}" fill="transparent" />
        ${grid.join("")}
        ${barSeries.length ? `<line x1="${margin.left}" y1="${zeroY}" x2="${margin.left + plotW}" y2="${zeroY}" stroke="#3b4a61" stroke-width="1.1" />` : ""}
        <line x1="${margin.left}" y1="${margin.top}" x2="${margin.left}" y2="${margin.top + plotH}" stroke="#64748b" />
        <line x1="${margin.left}" y1="${margin.top + plotH}" x2="${margin.left + plotW}" y2="${margin.top + plotH}" stroke="#64748b" />
        <text x="18" y="${margin.top + plotH / 2}" transform="rotate(-90 18 ${margin.top + plotH / 2})" text-anchor="middle" font-size="12" fill="#94a3b8">${escapeHtml(spec.axisLabel || "aviation")}</text>
        <text x="${width - 16}" y="${margin.top + plotH / 2}" transform="rotate(90 ${width - 16} ${margin.top + plotH / 2})" text-anchor="middle" font-size="12" fill="#94a3b8">${escapeHtml(spec.percentLabel || spec.axisLabel || "index")}</text>
        ${eventBands}
        ${bars}
        ${lines}
        ${legend}
        <line x1="${selectedX}" y1="${margin.top}" x2="${selectedX}" y2="${margin.top + plotH}" stroke="#e5e7eb" stroke-width="1" stroke-dasharray="4 5" />
        ${selectedMarkers}
        ${hitRects}
      `;
      svg.querySelectorAll(".hit").forEach((rect) => {
        rect.addEventListener("pointermove", () => {
          const next = Number(rect.dataset.index);
          if (next !== state.selectedIndex) {
            state.selectedIndex = next;
            render();
          }
        });
        rect.addEventListener("click", () => {
          state.selectedIndex = Number(rect.dataset.index);
          render();
        });
      });
    }

    function renderChart(rows) {
      const svg = el.chart;
      const box = svg.getBoundingClientRect();
      const width = Math.max(320, box.width || 900);
      const height = Math.max(280, box.height || 500);
      const margin = { top: 20, right: 56, bottom: 42, left: 62 };
      const plotW = width - margin.left - margin.right;
      const plotH = height - margin.top - margin.bottom;
      const scenarioRows = activeScenarioRows(rows);
      const axisRows = scenarioRows ? [...rows, ...scenarioRows] : rows;
      const scenarioSlice = scenarioRows && state.scenario
        ? scenarioRows.filter((row) => row.year_index >= state.scenario.triggerIndex)
        : [];
      const years = rows.map((row) => row.year);
      const gdpValues = axisRows.map((row) => row.global_gdp_trillion_usd);
      const growthValues = axisRows.map((row) => row.realized_growth_pct);
      const inflationValues = axisRows.filter(hasInflation).map((row) => row.headline_inflation_pct);
      const policyValues = axisRows.filter(hasPolicy).map((row) => row.global_policy_rate_pct);
      const yieldValues = axisRows.filter(hasYield).map((row) => row.global_10y_yield_pct);
      const dollarAxisValues = axisRows.filter(hasDollar).flatMap((row) => [row.global_dollar_index, row.global_liquidity_index]);
      const creditAxisValues = axisRows.filter(hasCredit).flatMap((row) => [row.global_high_yield_spread_bps, row.global_investment_grade_spread_bps]);
      const assetAxisValues = axisRows.filter(hasAsset).flatMap((row) => [row.global_equity_total_return_index, row.global_sovereign_bond_total_return_index, row.macro_scope === "regional" ? row.regional_household_financial_wealth_index : row.global_60_40_total_return_index]);
      const oilAxisValues = axisRows.filter(hasOil).flatMap((row) => [row.brent_oil_price_usd, row.broad_commodity_index]);
      const minYear = Math.min(...years);
      const maxYear = Math.max(...years);
      const minGdp = Math.min(...gdpValues) * 0.96;
      const maxGdp = Math.max(...gdpValues) * 1.04;
      const minDollarAxis = dollarAxisValues.length ? Math.min(...dollarAxisValues) - 4 : 0;
      const maxDollarAxis = dollarAxisValues.length ? Math.max(...dollarAxisValues) + 4 : 100;
      const minCreditAxis = creditAxisValues.length ? Math.max(0, Math.min(...creditAxisValues) - 60) : 0;
      const maxCreditAxis = creditAxisValues.length ? Math.max(700, Math.max(...creditAxisValues) + 120) : 1000;
      const minAssetAxis = assetAxisValues.length ? Math.max(0, Math.min(...assetAxisValues) * 0.90) : 0;
      const maxAssetAxis = assetAxisValues.length ? Math.max(140, Math.max(...assetAxisValues) * 1.10) : 200;
      const minOilAxis = oilAxisValues.length ? Math.max(0, Math.min(...oilAxisValues) * 0.86) : 0;
      const maxOilAxis = oilAxisValues.length ? Math.max(120, Math.max(...oilAxisValues) * 1.10) : 160;
      const maxAbsGrowth = Math.max(
        4,
        ...growthValues.map((value) => Math.abs(value)),
        ...inflationValues.map((value) => Math.abs(value)),
        ...policyValues.map((value) => Math.abs(value)),
        ...yieldValues.map((value) => Math.abs(value)),
      ) * 1.15;

      const x = (year) => margin.left + ((year - minYear) / Math.max(1, maxYear - minYear)) * plotW;
      const yGdp = (value) => margin.top + ((maxGdp - value) / Math.max(1e-9, maxGdp - minGdp)) * plotH;
      const yGrowth = (value) => margin.top + ((maxAbsGrowth - value) / (maxAbsGrowth * 2)) * plotH;
      const yDollar = (value) => margin.top + ((maxDollarAxis - value) / Math.max(1e-9, maxDollarAxis - minDollarAxis)) * plotH;
      const yCredit = (value) => margin.top + ((maxCreditAxis - value) / Math.max(1e-9, maxCreditAxis - minCreditAxis)) * plotH;
      const yAsset = (value) => margin.top + ((maxAssetAxis - value) / Math.max(1e-9, maxAssetAxis - minAssetAxis)) * plotH;
      const yOil = (value) => margin.top + ((maxOilAxis - value) / Math.max(1e-9, maxOilAxis - minOilAxis)) * plotH;
      const zeroY = yGrowth(0);
      const selected = selectedRow(rows);
      const showGdp = state.mode === "both" || state.mode === "gdp";
      const showGrowth = state.mode === "both" || state.mode === "growth";
      const showInflation = hasInflation(selected) && (state.mode === "both" || state.mode === "inflation");
      const showPolicy = hasPolicy(selected) && (state.mode === "both" || state.mode === "policy");
      const showYield = hasYield(selected) && (state.mode === "both" || state.mode === "yield");
      const showDollar = hasDollar(selected) && state.mode === "dollar";
      const showCredit = hasCredit(selected) && state.mode === "credit";
      const showAsset = hasAsset(selected) && state.mode === "asset";
      const showOil = hasOil(selected) && state.mode === "oil";
      const isCrisisEra = (row) => ["crisis_onset", "deep_crisis", "crisis_repair", "recession"].includes(row.regime)
        || String(row.regime || "").includes("crisis")
        || String(row.regime || "").includes("recession");

      const grid = [];
      for (let i = 0; i <= 5; i++) {
        const yy = margin.top + (i / 5) * plotH;
        const axisTick = showCredit
          ? maxCreditAxis - (i / 5) * (maxCreditAxis - minCreditAxis)
          : showOil
            ? maxOilAxis - (i / 5) * (maxOilAxis - minOilAxis)
            : showAsset
              ? maxAssetAxis - (i / 5) * (maxAssetAxis - minAssetAxis)
              : showDollar
                ? maxDollarAxis - (i / 5) * (maxDollarAxis - minDollarAxis)
                : maxGdp - (i / 5) * (maxGdp - minGdp);
        grid.push(`<line x1="${margin.left}" y1="${yy}" x2="${margin.left + plotW}" y2="${yy}" stroke="#1f2937" />`);
        grid.push(`<text x="${margin.left - 9}" y="${yy + 4}" text-anchor="end" font-size="11" fill="#94a3b8">${axisTick.toFixed(showDollar ? 1 : 0)}</text>`);
      }
      for (let i = 0; i <= 5; i++) {
        const xx = margin.left + (i / 5) * plotW;
        const year = Math.round(minYear + (i / 5) * (maxYear - minYear));
        grid.push(`<line x1="${xx}" y1="${margin.top}" x2="${xx}" y2="${margin.top + plotH}" stroke="#172033" />`);
        grid.push(`<text x="${xx}" y="${height - 13}" text-anchor="middle" font-size="11" fill="#94a3b8">${year}</text>`);
      }

      const bars = showGrowth ? rows.map((row) => {
        const barW = Math.max(3, plotW / rows.length * 0.62);
        const xx = x(row.year) - barW / 2;
        const yy = Math.min(zeroY, yGrowth(row.realized_growth_pct));
        const hh = Math.max(1, Math.abs(yGrowth(row.realized_growth_pct) - zeroY));
        const color = row.realized_growth_pct < 0 ? "rgba(251,113,133,0.74)" : "rgba(52,211,153,0.62)";
        return `<rect x="${xx.toFixed(2)}" y="${yy.toFixed(2)}" width="${barW.toFixed(2)}" height="${hh.toFixed(2)}" fill="${color}" rx="2" />`;
      }).join("") : "";

      const crisisBands = rows.map((row) => {
        if (!isCrisisEra(row)) return "";
        const bandW = Math.max(8, plotW / rows.length);
        return `<rect x="${(x(row.year) - bandW / 2).toFixed(2)}" y="${margin.top}" width="${bandW.toFixed(2)}" height="${plotH}" fill="rgba(251,113,133,0.10)" />`;
      }).join("");

      const gdpPath = showGdp ? `<path d="${pathFromPoints(rows.map((row) => ({ x: x(row.year), y: yGdp(row.global_gdp_trillion_usd) })))}" fill="none" stroke="#60a5fa" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" />` : "";
      const inflationPath = showInflation ? `<path d="${pathFromPoints(rows.filter(hasInflation).map((row) => ({ x: x(row.year), y: yGrowth(row.headline_inflation_pct) })))}" fill="none" stroke="#facc15" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />` : "";
      const policyPath = showPolicy ? `<path d="${pathFromPoints(rows.filter(hasPolicy).map((row) => ({ x: x(row.year), y: yGrowth(row.global_policy_rate_pct) })))}" fill="none" stroke="#a78bfa" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />` : "";
      const yieldPath = showYield ? `<path d="${pathFromPoints(rows.filter(hasYield).map((row) => ({ x: x(row.year), y: yGrowth(row.global_10y_yield_pct) })))}" fill="none" stroke="#22d3ee" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />` : "";
      const dollarPath = showDollar ? `<path d="${pathFromPoints(rows.filter(hasDollar).map((row) => ({ x: x(row.year), y: yDollar(row.global_dollar_index) })))}" fill="none" stroke="#38bdf8" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />` : "";
      const liquidityPath = showDollar ? `<path d="${pathFromPoints(rows.filter(hasDollar).map((row) => ({ x: x(row.year), y: yDollar(row.global_liquidity_index) })))}" fill="none" stroke="#14b8a6" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />` : "";
      const hyPath = showCredit ? `<path d="${pathFromPoints(rows.filter(hasCredit).map((row) => ({ x: x(row.year), y: yCredit(row.global_high_yield_spread_bps) })))}" fill="none" stroke="#fb923c" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />` : "";
      const igPath = showCredit ? `<path d="${pathFromPoints(rows.filter(hasCredit).map((row) => ({ x: x(row.year), y: yCredit(row.global_investment_grade_spread_bps) })))}" fill="none" stroke="#c084fc" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />` : "";
      const equityPath = showAsset ? `<path d="${pathFromPoints(rows.filter(hasAsset).map((row) => ({ x: x(row.year), y: yAsset(row.global_equity_total_return_index) })))}" fill="none" stroke="#22c55e" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />` : "";
      const sovereignBondPath = showAsset ? `<path d="${pathFromPoints(rows.filter(hasAsset).map((row) => ({ x: x(row.year), y: yAsset(row.global_sovereign_bond_total_return_index) })))}" fill="none" stroke="#818cf8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />` : "";
      const portfolioPath = showAsset ? `<path d="${pathFromPoints(rows.filter(hasAsset).map((row) => ({ x: x(row.year), y: yAsset(row.macro_scope === "regional" ? row.regional_household_financial_wealth_index : row.global_60_40_total_return_index) })))}" fill="none" stroke="#eab308" stroke-width="2.0" stroke-linecap="round" stroke-linejoin="round" />` : "";
      const oilPath = showOil ? `<path d="${pathFromPoints(rows.filter(hasOil).map((row) => ({ x: x(row.year), y: yOil(row.brent_oil_price_usd) })))}" fill="none" stroke="#f97316" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />` : "";
      const commodityPath = showOil ? `<path d="${pathFromPoints(rows.filter(hasOil).map((row) => ({ x: x(row.year), y: yOil(row.broad_commodity_index) })))}" fill="none" stroke="#d946ef" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />` : "";

      const scenarioPath = (field, yFn, color, widthValue = 2.6, filterFn = () => true) => {
        const points = scenarioSlice.filter(filterFn).map((row) => ({ x: x(row.year), y: yFn(row[field]) }));
        if (points.length < 2) return "";
        return `<path d="${pathFromPoints(points)}" fill="none" stroke="${color}" stroke-width="${widthValue}" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="7 5" opacity="0.94" pointer-events="none" />`;
      };
      const scenarioPaths = scenarioSlice.length ? [
        showGdp ? scenarioPath("global_gdp_trillion_usd", yGdp, "#fb923c", 3.0) : "",
        showGrowth ? scenarioPath("realized_growth_pct", yGrowth, "#fb7185", 2.2) : "",
        showInflation ? scenarioPath("headline_inflation_pct", yGrowth, "#f97316", 2.4, hasInflation) : "",
        showPolicy ? scenarioPath("global_policy_rate_pct", yGrowth, "#fb7185", 2.4, hasPolicy) : "",
        showYield ? scenarioPath("global_10y_yield_pct", yGrowth, "#f97316", 2.4, hasYield) : "",
        showDollar ? scenarioPath("global_dollar_index", yDollar, "#fb923c", 2.5, hasDollar) : "",
        showDollar ? scenarioPath("global_liquidity_index", yDollar, "#fbbf24", 2.2, hasDollar) : "",
        showCredit ? scenarioPath("global_high_yield_spread_bps", yCredit, "#fb923c", 2.7, hasCredit) : "",
        showAsset ? scenarioPath("global_equity_total_return_index", yAsset, "#fb923c", 2.7, hasAsset) : "",
        showAsset ? scenarioPath("global_sovereign_bond_total_return_index", yAsset, "#fbbf24", 2.2, hasAsset) : "",
        showOil ? scenarioPath("brent_oil_price_usd", yOil, "#fb923c", 2.7, hasOil) : "",
      ].join("") : "";

      const scenarioBand = scenarioSlice.length && state.scenario ? (() => {
        const bandW = Math.max(8, plotW / rows.length);
        const triggerX = x(state.scenario.triggerYear);
        return `<rect x="${(triggerX - bandW / 2).toFixed(2)}" y="${margin.top}" width="${bandW.toFixed(2)}" height="${plotH}" fill="rgba(251,146,60,0.16)" pointer-events="none" />`;
      })() : "";

      const scenarioLegend = scenarioSlice.length && state.scenario ? `
        <g pointer-events="none">
          <line x1="${margin.left + 8}" y1="${margin.top + 14}" x2="${margin.left + 42}" y2="${margin.top + 14}" stroke="#fb923c" stroke-width="2.6" stroke-dasharray="7 5" />
          <text x="${margin.left + 50}" y="${margin.top + 18}" font-size="12" fill="#fed7aa">发生情景：${escapeHtml(state.scenario.risk.label)}</text>
        </g>
      ` : "";

      const hitRects = rows.map((row, index) => {
        const w = Math.max(8, plotW / rows.length);
        return `<rect x="${(x(row.year) - w / 2).toFixed(2)}" y="${margin.top}" width="${w.toFixed(2)}" height="${plotH}" fill="transparent" data-index="${index}" class="hit" />`;
      }).join("");

      const selectedX = x(selected.year);
      const selectedMarker = `
        <line x1="${selectedX}" y1="${margin.top}" x2="${selectedX}" y2="${margin.top + plotH}" stroke="#e5e7eb" stroke-width="1" stroke-dasharray="4 5" />
        ${showGdp ? `<circle cx="${selectedX}" cy="${yGdp(selected.global_gdp_trillion_usd)}" r="4.5" fill="#60a5fa" stroke="#0b1120" stroke-width="2" />` : ""}
        ${showGrowth ? `<circle cx="${selectedX}" cy="${yGrowth(selected.realized_growth_pct)}" r="4.5" fill="${selected.realized_growth_pct < 0 ? "#fb7185" : "#34d399"}" stroke="#0b1120" stroke-width="2" />` : ""}
        ${showInflation ? `<circle cx="${selectedX}" cy="${yGrowth(selected.headline_inflation_pct)}" r="4.5" fill="#facc15" stroke="#0b1120" stroke-width="2" />` : ""}
        ${showPolicy ? `<circle cx="${selectedX}" cy="${yGrowth(selected.global_policy_rate_pct)}" r="4.5" fill="#a78bfa" stroke="#0b1120" stroke-width="2" />` : ""}
        ${showYield ? `<circle cx="${selectedX}" cy="${yGrowth(selected.global_10y_yield_pct)}" r="4.5" fill="#22d3ee" stroke="#0b1120" stroke-width="2" />` : ""}
        ${showDollar ? `<circle cx="${selectedX}" cy="${yDollar(selected.global_dollar_index)}" r="4.5" fill="#38bdf8" stroke="#0b1120" stroke-width="2" />` : ""}
        ${showDollar ? `<circle cx="${selectedX}" cy="${yDollar(selected.global_liquidity_index)}" r="4.5" fill="#14b8a6" stroke="#0b1120" stroke-width="2" />` : ""}
        ${showCredit ? `<circle cx="${selectedX}" cy="${yCredit(selected.global_high_yield_spread_bps)}" r="4.5" fill="#fb923c" stroke="#0b1120" stroke-width="2" />` : ""}
        ${showCredit ? `<circle cx="${selectedX}" cy="${yCredit(selected.global_investment_grade_spread_bps)}" r="4.5" fill="#c084fc" stroke="#0b1120" stroke-width="2" />` : ""}
        ${showAsset ? `<circle cx="${selectedX}" cy="${yAsset(selected.global_equity_total_return_index)}" r="4.5" fill="#22c55e" stroke="#0b1120" stroke-width="2" />` : ""}
        ${showAsset ? `<circle cx="${selectedX}" cy="${yAsset(selected.global_sovereign_bond_total_return_index)}" r="4.5" fill="#818cf8" stroke="#0b1120" stroke-width="2" />` : ""}
        ${showAsset ? `<circle cx="${selectedX}" cy="${yAsset(selected.macro_scope === "regional" ? selected.regional_household_financial_wealth_index : selected.global_60_40_total_return_index)}" r="4.5" fill="#eab308" stroke="#0b1120" stroke-width="2" />` : ""}
        ${showOil ? `<circle cx="${selectedX}" cy="${yOil(selected.brent_oil_price_usd)}" r="4.5" fill="#f97316" stroke="#0b1120" stroke-width="2" />` : ""}
        ${showOil ? `<circle cx="${selectedX}" cy="${yOil(selected.broad_commodity_index)}" r="4.5" fill="#d946ef" stroke="#0b1120" stroke-width="2" />` : ""}
      `;

      svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
      svg.innerHTML = `
        <rect x="0" y="0" width="${width}" height="${height}" fill="transparent" />
        ${grid.join("")}
        ${showDollar || showCredit || showAsset || showOil ? "" : `<line x1="${margin.left}" y1="${zeroY}" x2="${margin.left + plotW}" y2="${zeroY}" stroke="#3b4a61" stroke-width="1.1" />`}
        <line x1="${margin.left}" y1="${margin.top}" x2="${margin.left}" y2="${margin.top + plotH}" stroke="#64748b" />
        <line x1="${margin.left}" y1="${margin.top + plotH}" x2="${margin.left + plotW}" y2="${margin.top + plotH}" stroke="#64748b" />
        <text x="18" y="${margin.top + plotH / 2}" transform="rotate(-90 18 ${margin.top + plotH / 2})" text-anchor="middle" font-size="12" fill="#94a3b8">${showOil ? (selected.oil_display_unit === "index" ? "energy / commodity pressure" : "oil / commodity index") : showAsset ? "comparable total-return / wealth index" : showCredit ? "credit spread bps" : showDollar ? (selected.macro_scope === "regional" ? "currency / liquidity index" : "dollar funding conditions / liquidity index") : (selected.display_gdp_unit === "index" ? "regional GDP index" : "GDP, trillion USD")}</text>
        <text x="${width - 16}" y="${margin.top + plotH / 2}" transform="rotate(90 ${width - 16} ${margin.top + plotH / 2})" text-anchor="middle" font-size="12" fill="#94a3b8">${showCredit ? "bps" : showOil ? "USD / index" : showAsset || showDollar ? "index" : "growth / rates %"}</text>
        ${crisisBands}
        ${scenarioBand}
        ${bars}
        ${gdpPath}
        ${inflationPath}
        ${policyPath}
        ${yieldPath}
        ${dollarPath}
        ${liquidityPath}
        ${hyPath}
        ${igPath}
        ${equityPath}
        ${sovereignBondPath}
        ${portfolioPath}
        ${oilPath}
        ${commodityPath}
        ${scenarioPaths}
        ${scenarioLegend}
        ${selectedMarker}
        ${hitRects}
      `;
      svg.querySelectorAll(".hit").forEach((rect) => {
        rect.addEventListener("pointermove", () => {
          const next = Number(rect.dataset.index);
          if (next !== state.selectedIndex) {
            state.selectedIndex = next;
            render();
          }
        });
        rect.addEventListener("click", () => {
          state.selectedIndex = Number(rect.dataset.index);
          render();
        });
      });
    }
