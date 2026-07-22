    const SCOPE_OPTIONS = [
      { id: "global", label: "全球", shortLabel: "全球", type: "global" },
      { id: "north_america", label: "北美", shortLabel: "北美", type: "regional" },
      { id: "china_mainland", label: "中国大陆", shortLabel: "中国", type: "regional" },
      { id: "west_north_europe", label: "西欧/北欧", shortLabel: "西欧北欧", type: "regional" },
      { id: "japan_korea", label: "日韩", shortLabel: "日韩", type: "regional" },
      { id: "southeast_asia", label: "东南亚", shortLabel: "东南亚", type: "regional" },
      { id: "south_asia_india", label: "南亚/印度", shortLabel: "南亚印度", type: "regional" },
      { id: "hk_macao_taiwan", label: "港澳台", shortLabel: "港澳台", type: "regional" },
      { id: "middle_east_gulf", label: "中东/海湾", shortLabel: "中东海湾", type: "regional" },
      { id: "oceania", label: "大洋洲", shortLabel: "大洋洲", type: "regional" },
      { id: "south_east_europe_mediterranean", label: "南欧/东欧/地中海", shortLabel: "泛地中海", type: "regional" },
      { id: "central_asia_turkey_eurasia", label: "中亚/土耳其/欧亚桥", shortLabel: "欧亚桥", type: "regional" },
      { id: "north_africa", label: "北非", shortLabel: "北非", type: "regional" },
      { id: "latin_america_caribbean", label: "拉美/加勒比", shortLabel: "拉美加勒比", type: "regional" },
      { id: "sub_saharan_africa", label: "撒哈拉以南非洲", shortLabel: "撒哈拉非洲", type: "regional" },
    ];
    const state = window.AirportGlobalViewerState;
    const EXPECTED_GLOBAL_INDEX = "airport-global-viewer-lazy-index-v2";
    const EXPECTED_GLOBAL_CHUNK = "airport-global-viewer-region-chunk-v2";
    const EXPECTED_CONTEXT_INDEX = "airport-global-viewer-context-index-v1";
    const EXPECTED_CONTEXT_REGION = "airport-global-viewer-context-region-v1";
    const globalApiClient = window.AirportApiClient;
    const sharedSeedContext = window.AirportSeedContext;
    const globalBootstrap = window.AirportGlobalViewerBootstrap;

    const numFields = new Set([
      "year_index",
      "year",
      "seed",
      "global_gdp_trillion_usd",
      "real_gdp_index",
      "potential_gdp_index",
      "realized_growth_pct",
      "potential_growth_pct",
      "trend_growth_pct",
      "cycle_growth_component_pct",
      "long_wave_component_pct",
      "infrastructure_component_pct",
      "investment_component_pct",
      "inventory_component_pct",
      "stochastic_component_pct",
      "shock_component_pct",
      "output_gap_pct",
      "gdp_level_gap_pct",
      "output_gap_measurement_residual_pct",
      "unclamped_output_gap_target_pct",
      "unclamped_target_growth_pct",
      "soft_limited_target_growth_pct",
      "growth_step_limit_pct",
      "growth_step_cap_consecutive_years",
      "global_gdp_level_gap_anchor_pct",
      "global_output_gap_measurement_residual_anchor_pct",
      "financial_stress_index",
      "productivity_wave_index",
      "crisis_intensity",
      "boom_intensity",
      "event_severity",
      "policy_rate_impulse",
      "liquidity_impulse",
      "credit_stress_impulse",
      "dollar_pressure_impulse",
      "energy_price_impulse",
      "gdp_lagged_support",
      "feedback_growth_impulse_pct",
      "feedback_output_gap_impulse_pct",
      "feedback_financial_stress_impulse",
      "feedback_inflation_impulse_pct",
      "feedback_policy_impulse_pct",
      "headline_inflation_pct",
      "core_inflation_pct",
      "energy_inflation_pct",
      "import_inflation_pct",
      "wage_pressure_pct",
      "inflation_expectation_pct",
      "demand_pull_component_pct",
      "energy_component_pct",
      "external_supply_shock_component_pct",
      "import_component_pct",
      "liquidity_component_pct",
      "stress_disinflation_component_pct",
      "inflation_noise_component_pct",
      "monetary_tightening_pressure",
      "monetary_easing_pressure",
      "inflation_to_policy_rate_impulse",
      "inflation_to_long_rate_impulse",
      "inflation_to_gdp_drag_placeholder",
      "global_policy_rate_pct",
      "policy_reaction_target_rate_pct",
      "neutral_policy_rate_pct",
      "real_policy_rate_pct",
      "shadow_policy_rate_pct",
      "policy_rate_change_pct",
      "rate_hike_pressure",
      "rate_cut_pressure",
      "qe_liquidity_index",
      "balance_sheet_impulse",
      "policy_stance_index",
      "policy_to_credit_tightening_impulse",
      "policy_to_dollar_pressure_impulse",
      "policy_to_equity_valuation_impulse",
      "policy_to_gdp_drag_placeholder",
      "policy_to_inflation_lagged_impulse",
      "global_short_rate_pct",
      "global_2y_yield_pct",
      "global_10y_yield_pct",
      "global_real_10y_yield_pct",
      "term_spread_10y_2y_pct",
      "term_premium_pct",
      "expected_short_rate_10y_pct",
      "expected_shadow_short_rate_10y_pct",
      "unclamped_short_rate_target_pct",
      "unclamped_expected_short_rate_10y_target_pct",
      "unclamped_expected_shadow_short_rate_10y_target_pct",
      "unclamped_2y_yield_target_pct",
      "unclamped_10y_yield_target_pct",
      "unclamped_term_premium_target_pct",
      "short_rate_consecutive_boundary_years",
      "expected_short_rate_consecutive_boundary_years",
      "shadow_short_rate_consecutive_boundary_years",
      "yield_2y_consecutive_boundary_years",
      "yield_10y_consecutive_boundary_years",
      "term_premium_consecutive_boundary_years",
      "bond_price_index",
      "bond_total_return_pct",
      "duration_pressure_index",
      "curve_inversion_pressure",
      "yield_curve_to_dollar_impulse",
      "yield_curve_to_equity_valuation_impulse",
      "yield_curve_to_credit_impulse",
      "yield_curve_to_gdp_drag_placeholder",
      "global_dollar_index",
      "unclamped_dollar_target_index",
      "dollar_consecutive_boundary_years",
      "dollar_yoy_change_pct",
      "dollar_momentum_index",
      "global_liquidity_index",
      "liquidity_impulse_index",
      "global_financial_conditions_index",
      "unclamped_financial_conditions_target_index",
      "financial_conditions_consecutive_boundary_years",
      "risk_appetite_index",
      "em_stress_index",
      "dollar_funding_stress_index",
      "dollar_to_import_inflation_impulse",
      "dollar_to_oil_pressure_impulse",
      "dollar_to_gdp_drag_placeholder",
      "dollar_to_credit_tightening_impulse",
      "liquidity_to_equity_impulse",
      "liquidity_to_credit_easing_impulse",
      "global_investment_grade_spread_bps",
      "global_high_yield_spread_bps",
      "global_credit_spread_index",
      "unclamped_global_credit_spread_index_target",
      "global_credit_spread_index_floor_applied",
      "global_credit_spread_index_cap_applied",
      "global_credit_spread_index_boundary_state",
      "global_credit_spread_index_consecutive_boundary_years",
      "credit_spread_change_bps",
      "default_risk_index",
      "lending_standards_index",
      "credit_availability_index",
      "unclamped_credit_availability_index_target",
      "credit_availability_index_floor_applied",
      "credit_availability_index_cap_applied",
      "credit_availability_index_boundary_state",
      "credit_availability_index_consecutive_boundary_years",
      "corporate_refinancing_pressure_index",
      "bank_credit_stress_index",
      "bank_lending_sentiment_index",
      "bank_balance_sheet_stress_index",
      "credit_convexity_pressure_index",
      "credit_impairment_stock_index",
      "unclamped_credit_impairment_stock_index_target",
      "credit_impairment_stock_index_floor_applied",
      "credit_impairment_stock_index_cap_applied",
      "credit_impairment_stock_index_boundary_state",
      "credit_impairment_stock_index_consecutive_boundary_years",
      "credit_to_gdp_drag_placeholder",
      "credit_to_equity_risk_premium_impulse",
      "credit_to_policy_easing_pressure",
      "credit_to_inflation_demand_drag_placeholder",
      "credit_to_oil_demand_impulse",
      "global_equity_index",
      "equity_total_return_pct",
      "equity_earnings_index",
      "unclamped_equity_earnings_index_target",
      "equity_earnings_index_floor_applied",
      "equity_earnings_index_cap_applied",
      "equity_earnings_index_boundary_state",
      "equity_earnings_index_consecutive_boundary_years",
      "equity_eps_growth_pct",
      "equity_valuation_pe",
      "equity_risk_premium_pct",
      "unclamped_equity_risk_premium_pct_target",
      "equity_risk_premium_pct_floor_applied",
      "equity_risk_premium_pct_cap_applied",
      "equity_risk_premium_pct_boundary_state",
      "equity_risk_premium_pct_consecutive_boundary_years",
      "equity_drawdown_pct",
      "global_sovereign_bond_index",
      "sovereign_bond_total_return_pct",
      "global_corporate_bond_index",
      "corporate_bond_total_return_pct",
      "global_60_40_portfolio_index",
      "portfolio_60_40_total_return_pct",
      "asset_volatility_index",
      "asset_to_gdp_wealth_impulse",
      "asset_to_policy_financial_conditions_impulse",
      "asset_to_credit_risk_appetite_impulse",
      "asset_to_inflation_wealth_demand_impulse",
      "brent_oil_price_usd",
      "unclamped_brent_oil_price_usd_target",
      "brent_oil_price_usd_floor_applied",
      "brent_oil_price_usd_cap_applied",
      "brent_oil_price_usd_boundary_state",
      "brent_oil_price_usd_consecutive_boundary_years",
      "global_oil_price_index",
      "oil_yoy_change_pct",
      "broad_commodity_index",
      "commodity_yoy_change_pct",
      "oil_demand_pressure_index",
      "oil_supply_shock_index",
      "oil_inventory_pressure_index",
      "energy_cost_pressure_index",
      "unclamped_energy_cost_pressure_index_target",
      "energy_cost_pressure_index_floor_applied",
      "energy_cost_pressure_index_cap_applied",
      "energy_cost_pressure_index_boundary_state",
      "energy_cost_pressure_index_consecutive_boundary_years",
      "oil_financial_pressure_index",
      "oil_to_headline_inflation_impulse",
      "oil_to_gdp_drag_placeholder",
      "oil_to_credit_stress_impulse",
      "oil_to_policy_pressure_impulse",
      "commodity_to_terms_of_trade_impulse",
      "macro_feedback_iteration",
      "macro_feedback_intensity_index",
      "macro_feedback_growth_raw_pct",
      "macro_feedback_stress_raw",
      "macro_feedback_inflation_raw_pct",
      "macro_feedback_policy_raw_pct",
      "macro_feedback_iterations_requested",
      "macro_feedback_last_pass_delta_index",
      "macro_feedback_max_pass_delta_index",
      "branch_risk_primary_probability_pct",
      "branch_risk_primary_severity_index",
      "branch_risk_primary_horizon_years",
      "branch_risk_primary_impact_years",
      "branch_risk_primary_tail_years",
      "branch_risk_primary_cooldown_years",
      "branch_risk_count",
      "branch_source_year",
      "branch_impact_years",
      "branch_tail_years",
      "branch_year_in_effect",
      "regional_branch_exposure_index",
      "regional_branch_relative_exposure_index",
      "regional_branch_strength_index",
      "regional_branch_growth_impulse_pct",
      "regional_branch_inflation_impulse_pct",
      "regional_branch_policy_impulse_pct",
      "regional_branch_credit_impulse_bps",
      "regional_branch_fx_pressure_impulse",
      "regional_branch_energy_impulse",
      "regional_branch_liquidity_impulse",
      "regional_branch_asset_impulse_pct",
      "regional_branch_confidence_impulse",
      "regional_branch_tail_scarring_index",
      "scenario_impact_years",
      "scenario_tail_years",
      "scenario_event_severity",
      "scenario_policy_rate_impulse",
      "scenario_liquidity_impulse",
      "scenario_credit_stress_impulse",
      "scenario_dollar_pressure_impulse",
      "scenario_energy_price_impulse",
      "scenario_gdp_lagged_support",
      "regional_reconciled_gdp_trillion_usd",
      "regional_air_demand_index",
      "regional_air_demand_growth_pct",
      "business_travel_demand_index",
      "business_travel_growth_pct",
      "business_travel_share_pct",
      "leisure_travel_demand_index",
      "leisure_travel_growth_pct",
      "leisure_travel_share_pct",
      "vfr_travel_demand_index",
      "vfr_travel_growth_pct",
      "vfr_travel_share_pct",
      "long_haul_demand_index",
      "long_haul_growth_pct",
      "long_haul_share_pct",
      "transfer_demand_index",
      "transfer_growth_pct",
      "transfer_share_pct",
      "airfare_price_sensitivity_index",
      "airfare_pressure_index",
      "business_fare_elasticity",
      "leisure_fare_elasticity",
      "vfr_fare_elasticity",
      "long_haul_fare_elasticity",
      "transfer_fare_elasticity",
      "premium_fare_elasticity",
      "premium_passenger_propensity_index",
      "premium_passenger_share_pct",
      "duty_free_propensity_index",
      "luxury_retail_propensity_index",
      "electronics_retail_propensity_index",
      "food_beverage_propensity_index",
      "general_retail_propensity_index",
      "airport_event_pressure_index",
      "aviation_event_impulse_pct",
      "baseline_region_passenger_demand_million",
      "potential_passenger_demand_index",
      "regional_air_capacity_index",
      "regional_air_capacity_growth_pct",
      "available_seat_capacity_index",
      "normalized_capacity_pressure_index",
      "capacity_utilization_pct",
      "target_load_factor_pct",
      "load_factor_pct",
      "capacity_fulfillment_pct",
      "served_passenger_demand_index",
      "unmet_passenger_demand_index",
      "capacity_fare_pressure_index",
      "potential_passengers_million",
      "scheduled_seats_million",
      "operational_availability_pct",
      "available_seats_million",
      "reference_effective_passenger_capacity_million",
      "reference_served_passengers_million",
      "reference_unmet_passengers_million",
      "served_passengers_million",
      "unmet_passengers_million",
      "business_served_index",
      "leisure_served_index",
      "vfr_served_index",
      "long_haul_served_index",
      "transfer_served_index",
      "business_fulfillment_pct",
      "leisure_fulfillment_pct",
      "vfr_fulfillment_pct",
      "long_haul_fulfillment_pct",
      "transfer_fulfillment_pct",
      "airline_capacity_confidence_index",
      "airline_profit_pressure_index",
      "fleet_expansion_appetite_index",
      "route_growth_appetite_index",
      "capacity_cut_risk_index",
      "aircraft_delivery_constraint_index",
      "crew_labor_constraint_index",
      "maintenance_cost_pressure_index",
      "airport_slot_constraint_index",
      "supply_event_impulse_pct",
      "regional_branch_strength_index",
      "input_regional_gdp_growth_pct",
      "input_real_income_growth_pct",
      "input_consumer_confidence_index",
      "input_macro_stress_index",
      "input_energy_cost_pressure_index",
      "input_currency_pressure_index",
      "input_hy_spread_bps",
      "input_equity_return_pct",
    ]);

    const el = {
      status: document.getElementById("dataStatus"),
      viewSelect: document.getElementById("viewSelect"),
      scopeSelect: document.getElementById("scopeSelect"),
      yearRange: document.getElementById("yearRange"),
      yearLabel: document.getElementById("yearLabel"),
      chart: document.getElementById("chart"),
      chartLegend: document.getElementById("chartLegend"),
      narrativePanel: document.getElementById("narrativePanel"),
      body: document.getElementById("dataBody"),
      tableMeta: document.getElementById("tableMeta"),
      statsGrid: document.getElementById("statsGrid"),
      detailTitle: document.getElementById("detailTitle"),
      detailRegime: document.getElementById("detailRegime"),
      detailGdp: document.getElementById("detailGdp"),
      detailGrowth: document.getElementById("detailGrowth"),
      detailRegionalShare: document.getElementById("detailRegionalShare"),
      detailRegionalRank: document.getElementById("detailRegionalRank"),
      detailInflation: document.getElementById("detailInflation"),
      detailCoreInflation: document.getElementById("detailCoreInflation"),
      detailPolicyRate: document.getElementById("detailPolicyRate"),
      detailPolicyTarget: document.getElementById("detailPolicyTarget"),
      detailRealPolicyRate: document.getElementById("detailRealPolicyRate"),
      detailTenYearYield: document.getElementById("detailTenYearYield"),
      detailTermSpread: document.getElementById("detailTermSpread"),
      detailDollar: document.getElementById("detailDollar"),
      detailLiquidity: document.getElementById("detailLiquidity"),
      detailFinancialConditions: document.getElementById("detailFinancialConditions"),
      detailHySpread: document.getElementById("detailHySpread"),
      detailIgSpread: document.getElementById("detailIgSpread"),
      detailCreditAvailability: document.getElementById("detailCreditAvailability"),
      detailEquity: document.getElementById("detailEquity"),
      detailEquityReturn: document.getElementById("detailEquityReturn"),
      detailEquityPe: document.getElementById("detailEquityPe"),
      detailBond: document.getElementById("detailBond"),
      detailOil: document.getElementById("detailOil"),
      detailOilReturn: document.getElementById("detailOilReturn"),
      detailCommodity: document.getElementById("detailCommodity"),
      detailEnergyPressure: document.getElementById("detailEnergyPressure"),
      detailFeedbackIntensity: document.getElementById("detailFeedbackIntensity"),
      detailFeedbackGrowth: document.getElementById("detailFeedbackGrowth"),
      detailPotentialGrowth: document.getElementById("detailPotentialGrowth"),
      detailGap: document.getElementById("detailGap"),
      detailStress: document.getElementById("detailStress"),
      detailShock: document.getElementById("detailShock"),
    };

    function normalizeRows(rows) {
      return rows.map((row) => {
        const next = { ...row };
        for (const key of numFields) {
          if (key in next) next[key] = Number(next[key]);
        }
        return next;
      });
    }

    function toNumber(value, fallback = 0) {
      const next = Number(value);
      return Number.isFinite(next) ? next : fallback;
    }

    function regionalReconciliationKey(regionId, seed, yearIndex) {
      return `${regionId}|${Number(seed)}|${Number(yearIndex)}`;
    }

    function regionalSupplyKey(regionId, seed, yearIndex) {
      return `${regionId}|${Number(seed)}|${Number(yearIndex)}`;
    }

    function buildRegionalReconciliationByKey(rows) {
      return new Map(
        (rows || []).map((row) => [
          regionalReconciliationKey(row.region_id, row.seed, row.year_index),
          row,
        ])
      );
    }

    function buildRegionalReconciliationDiagnosticByKey(rows) {
      return new Map((rows || []).map((row) => [`${Number(row.seed)}|${Number(row.year_index)}`, row]));
    }

    let regionalReconciliationRows = Array.isArray(window.REGIONAL_MACRO_RECONCILED_DATA)
      ? window.REGIONAL_MACRO_RECONCILED_DATA
      : [];
    let regionalReconciliationByKey = buildRegionalReconciliationByKey(regionalReconciliationRows);

    let regionalReconciliationDiagnosticRows = Array.isArray(window.REGIONAL_MACRO_RECONCILIATION_DATA)
      ? window.REGIONAL_MACRO_RECONCILIATION_DATA
      : [];
    let regionalReconciliationDiagnosticByKey = buildRegionalReconciliationDiagnosticByKey(regionalReconciliationDiagnosticRows);

    function setRegionalReconciliationData(reconciledRows = [], diagnosticRows = []) {
      regionalReconciliationRows = reconciledRows || [];
      regionalReconciliationByKey = buildRegionalReconciliationByKey(regionalReconciliationRows);
      regionalReconciliationDiagnosticRows = diagnosticRows || [];
      regionalReconciliationDiagnosticByKey = buildRegionalReconciliationDiagnosticByKey(regionalReconciliationDiagnosticRows);
    }

    function scopeConfig(scope = state.scope) {
      return SCOPE_OPTIONS.find((item) => item.id === scope) || SCOPE_OPTIONS[0];
    }

    function normalizeGlobalRows(rows) {
      return normalizeRows(rows).map((row) => {
        const strictGap = Number.isFinite(row.gdp_level_gap_pct)
          ? row.gdp_level_gap_pct
          : 100 * Math.log(toNumber(row.real_gdp_index) / toNumber(row.potential_gdp_index));
        return {
          ...row,
          gdp_level_gap_pct: strictGap,
          output_gap_measurement_residual_pct: Number.isFinite(row.output_gap_measurement_residual_pct)
            ? row.output_gap_measurement_residual_pct
            : toNumber(row.output_gap_pct) - strictGap,
          macro_scope: "global",
          scope_id: "global",
          scope_label: "全球",
          display_gdp_unit: "usd_trillion",
          oil_display_unit: "usd",
        };
      });
    }

    function normalizeRegionalRows(rows, config) {
      return (rows || []).map((row) => {
        const recon = regionalReconciliationByKey.get(regionalReconciliationKey(config.id, row.seed, row.year_index));
        const diagnostic = regionalReconciliationDiagnosticByKey.get(`${Number(row.seed)}|${Number(row.year_index)}`);
        const hasReconciledSize = Boolean(recon);
        const gdpValue = hasReconciledSize ? toNumber(recon.regional_reconciled_gdp_trillion_usd) : toNumber(row.regional_gdp_index);
        const growthValue = hasReconciledSize ? toNumber(recon.regional_gdp_growth_pct_reconciled) : toNumber(row.regional_gdp_growth_pct);
        const headlineValue = hasReconciledSize ? toNumber(recon.regional_headline_inflation_pct_reconciled) : toNumber(row.regional_headline_inflation_pct);
        const coreValue = hasReconciledSize ? toNumber(recon.regional_core_inflation_pct_reconciled) : toNumber(row.regional_core_inflation_pct);
        const policyValue = hasReconciledSize ? toNumber(recon.regional_policy_rate_pct_reconciled) : toNumber(row.regional_policy_rate_pct);
        const tenYearValue = hasReconciledSize ? toNumber(recon.regional_10y_yield_pct_reconciled) : toNumber(row.regional_10y_yield_pct);
        const hyValue = hasReconciledSize ? toNumber(recon.regional_hy_spread_bps_reconciled) : toNumber(row.regional_hy_spread_bps);
        const igValue = hasReconciledSize ? toNumber(recon.regional_ig_spread_bps_reconciled) : toNumber(row.regional_ig_spread_bps);
        const stressValue = hasReconciledSize ? toNumber(recon.regional_macro_stress_index_reconciled) : toNumber(row.regional_macro_stress_index);
        const energyValue = hasReconciledSize ? toNumber(recon.regional_energy_cost_pressure_index_reconciled) : toNumber(row.regional_energy_cost_pressure_index);
        const equityReturnValue = hasReconciledSize ? toNumber(recon.regional_equity_return_pct_reconciled) : toNumber(row.regional_equity_return_pct);
        return {
          ...row,
          macro_scope: "regional",
          scope_id: config.id,
          scope_label: config.label,
          display_gdp_unit: hasReconciledSize ? "usd_trillion" : "index",
          oil_display_unit: "index",
          param_version: row.regional_macro_param_version,
          global_gdp_trillion_usd: gdpValue,
          real_gdp_index: toNumber(row.regional_gdp_index),
          realized_growth_pct: growthValue,
          potential_growth_pct: toNumber(row.regional_potential_growth_pct),
          trend_growth_pct: toNumber(row.regional_potential_growth_pct),
          output_gap_pct: toNumber(row.regional_output_gap_pct),
          gdp_level_gap_pct: toNumber(row.global_gdp_level_gap_anchor_pct),
          output_gap_measurement_residual_pct: toNumber(
            row.global_output_gap_measurement_residual_anchor_pct
          ),
          output_gap_measurement_version: row.global_output_gap_measurement_version || "",
          financial_stress_index: stressValue,
          regime: row.regional_macro_regime || "regional_macro",
          headline_inflation_pct: headlineValue,
          core_inflation_pct: coreValue,
          energy_inflation_pct: toNumber(row.regional_energy_inflation_pct),
          import_inflation_pct: toNumber(row.regional_import_inflation_pct),
          inflation_expectation_pct: toNumber(row.regional_inflation_expectation_pct),
          inflation_regime: row.regional_inflation_regime || "regional_inflation",
          global_policy_rate_pct: policyValue,
          policy_reaction_target_rate_pct: policyValue,
          neutral_policy_rate_pct: policyValue,
          real_policy_rate_pct: toNumber(row.regional_real_policy_rate_pct),
          shadow_policy_rate_pct: toNumber(row.regional_real_policy_rate_pct),
          global_short_rate_pct: policyValue,
          global_2y_yield_pct: policyValue,
          global_10y_yield_pct: tenYearValue,
          global_real_10y_yield_pct: toNumber(row.regional_real_10y_yield_pct),
          term_spread_10y_2y_pct: toNumber(row.regional_term_spread_pct),
          global_dollar_index: toNumber(row.regional_currency_index),
          dollar_yoy_change_pct: toNumber(row.regional_currency_yoy_pct),
          dollar_momentum_index: toNumber(row.fx_volatility_index),
          global_liquidity_index: toNumber(row.regional_liquidity_index),
          global_financial_conditions_index: toNumber(row.regional_financial_conditions_index),
          risk_appetite_index: toNumber(row.regional_risk_appetite_index),
          dollar_funding_stress_index: toNumber(row.currency_pressure_index),
          dollar_liquidity_regime: "regional_currency_liquidity",
          global_investment_grade_spread_bps: igValue,
          global_high_yield_spread_bps: hyValue,
          default_risk_index: toNumber(row.regional_default_risk_index),
          credit_availability_index: toNumber(row.regional_credit_availability_index),
          bank_credit_stress_index: toNumber(row.regional_credit_stress_index),
          credit_regime: row.regional_growth_regime || "regional_credit",
          global_equity_index: toNumber(row.regional_equity_index),
          equity_total_return_pct: equityReturnValue,
          global_sovereign_bond_index: toNumber(row.regional_bond_index),
          sovereign_bond_total_return_pct: toNumber(row.regional_bond_return_pct),
          global_60_40_portfolio_index: toNumber(row.regional_wealth_effect_index),
          portfolio_60_40_total_return_pct: equityReturnValue * 0.6 + toNumber(row.regional_bond_return_pct) * 0.4,
          asset_risk_regime: row.regional_macro_regime || "regional_asset",
          brent_oil_price_usd: energyValue,
          global_oil_price_index: energyValue,
          oil_yoy_change_pct: toNumber(row.regional_energy_inflation_pct),
          broad_commodity_index: toNumber(row.regional_commodity_pressure_index),
          commodity_yoy_change_pct: toNumber(row.regional_import_inflation_pct),
          energy_cost_pressure_index: energyValue,
          oil_financial_pressure_index: toNumber(row.regional_terms_of_trade_index),
          oil_regime: "regional_energy_pressure",
          central_bank_reaction_regime: "regional_policy",
          yield_curve_regime: "regional_curve",
          event_type: "regional_macro",
          event_phase: row.region_name || config.label,
          crisis_intensity: Math.max(0, stressValue - 55),
          boom_intensity: Math.max(0, growthValue - toNumber(row.regional_potential_growth_pct)),
          shock_component_pct: hasReconciledSize ? toNumber(recon.growth_reconciliation_adjustment_pp) : toNumber(row.growth_reconciliation_adjustment_pct),
          regional_reconciliation_available: hasReconciledSize,
          regional_gdp_index: toNumber(row.regional_gdp_index),
          regional_raw_gdp_trillion_usd: hasReconciledSize ? toNumber(recon.regional_raw_gdp_trillion_usd) : undefined,
          regional_reconciled_gdp_trillion_usd: hasReconciledSize ? toNumber(recon.regional_reconciled_gdp_trillion_usd) : undefined,
          regional_share_of_global_gdp_pct: hasReconciledSize ? toNumber(recon.regional_reconciled_share_of_global_gdp_pct) : undefined,
          regional_share_change_from_start_pct: hasReconciledSize ? toNumber(recon.regional_share_change_from_start_pct) : undefined,
          regional_weight_drift_pp: hasReconciledSize ? toNumber(recon.regional_weight_drift_pp) : undefined,
          regional_normalized_initial_weight_pct: hasReconciledSize ? toNumber(recon.regional_normalized_initial_weight_pct) : undefined,
          regional_rank_by_gdp: hasReconciledSize ? toNumber(recon.regional_rank_by_gdp) : undefined,
          regional_growth_contribution_pp: hasReconciledSize ? toNumber(recon.regional_growth_contribution_pp_reconciled) : undefined,
          regional_growth_raw_pct: hasReconciledSize ? toNumber(recon.regional_gdp_growth_pct_raw) : toNumber(row.regional_gdp_growth_pct),
          regional_growth_adjustment_pp: hasReconciledSize ? toNumber(recon.growth_reconciliation_adjustment_pp) : undefined,
          regional_reconciliation_quality: diagnostic?.reconciliation_quality || "",
          regional_weighted_growth_gap_pp: diagnostic ? toNumber(diagnostic.growth_gap_reconciled_pp) : undefined,
          regional_weighted_inflation_gap_pp: diagnostic ? toNumber(diagnostic.headline_inflation_gap_reconciled_pp) : undefined,
          regional_weighted_hy_gap_bps: diagnostic ? toNumber(diagnostic.hy_gap_reconciled_bps) : undefined,
        };
      });
    }

    function buildDatasets(globalRows, rawDatasets = window.REGIONAL_MACRO_DATASETS || {}) {
      const datasets = { global: normalizeGlobalRows(globalRows) };
      for (const config of SCOPE_OPTIONS.filter((item) => item.type === "regional")) {
        const rawRows = rawDatasets?.[config.id] || [];
        if (rawRows.length) datasets[config.id] = normalizeRegionalRows(rawRows, config);
      }
      return datasets;
    }

    function normalizeAirSupplyRows(rows, config) {
      return normalizeRows(rows || []).map((row) => ({
        ...row,
        region_id: row.region_id || config.id,
        scope_id: config.id,
        scope_label: config.label,
      }));
    }

    function buildSupplyDatasets(rawDatasets = window.REGIONAL_AIR_CAPACITY_SUPPLY_DATASETS || {}) {
      const datasets = {};
      for (const config of SCOPE_OPTIONS.filter((item) => item.type === "regional")) {
        const rawRows = rawDatasets?.[config.id] || [];
        if (rawRows.length) datasets[config.id] = normalizeAirSupplyRows(rawRows, config);
      }
      return datasets;
    }

    function normalizeAviationRows(rows, config, supplyRows = []) {
      const supplyByKey = new Map(
        normalizeAirSupplyRows(supplyRows || [], config).map((row) => [
          regionalSupplyKey(config.id, row.seed, row.year_index),
          row,
        ])
      );
      return normalizeRows(rows || []).map((row) => {
        const supply = supplyByKey.get(regionalSupplyKey(config.id, row.seed, row.year_index));
        return {
          ...row,
          ...(supply ? { ...supply, air_supply_available: true } : { air_supply_available: false }),
          view_scope: "regional_aviation_demand",
          macro_scope: "regional",
          scope_id: config.id,
          scope_label: config.label,
        };
      });
    }

    function buildAviationDatasets(
      rawDatasets = window.REGIONAL_AVIATION_DEMAND_DATASETS || {},
      rawSupplyDatasets = window.REGIONAL_AIR_CAPACITY_SUPPLY_DATASETS || {}
    ) {
      const datasets = {};
      for (const config of SCOPE_OPTIONS.filter((item) => item.type === "regional")) {
        const rawRows = rawDatasets?.[config.id] || [];
        const rawSupplyRows = rawSupplyDatasets?.[config.id] || [];
        if (rawRows.length) datasets[config.id] = normalizeAviationRows(rawRows, config, rawSupplyRows);
      }
      return datasets;
    }

    function cloneRows(rows = []) {
      return rows.map((row) => ({ ...row }));
    }

    function cloneRegionalDatasets(datasets = {}) {
      return Object.fromEntries(
        Object.entries(datasets || {}).map(([key, rows]) => [key, cloneRows(rows || [])])
      );
    }

    function captureViewerData(globalRows, options = {}) {
      return {
        globalRows: cloneRows(globalRows || []),
        regionalDatasets: cloneRegionalDatasets(options.regionalDatasets || {}),
        aviationDatasets: cloneRegionalDatasets(options.aviationDatasets || {}),
        supplyDatasets: cloneRegionalDatasets(options.supplyDatasets || {}),
        reconciledRows: cloneRows(options.reconciledRows || []),
        diagnosticRows: cloneRows(options.diagnosticRows || []),
        lazyIndex: options.lazyIndex || null,
        lazyBaseUrl: options.lazyIndex?.baseUrl || "",
        contextKey: options.contextKey || "",
        contextSource: options.contextSource || "",
        loadedRegionIds: new Set(),
        regionLoadPromises: new Map(),
      };
    }

    function validateRowsContext(rows, context, label) {
      if (!Array.isArray(rows) || !rows.length) throw new Error(`${label}缺少数据。`);
      const seeds = new Set(rows.map((row) => Number(row.seed)));
      const years = rows.map((row) => Number(row.year)).filter(Number.isFinite);
      if (seeds.size !== 1 || !seeds.has(context.seed)) {
        throw new Error(`${label} Seed 与页面上下文不一致。`);
      }
      if (!years.length || Math.max(...years) - Math.min(...years) !== context.years) {
        throw new Error(`${label}年数与页面上下文不一致。`);
      }
    }

    function validateIndex(index) {
      if (
        !index
        || index.schemaVersion !== EXPECTED_GLOBAL_INDEX
        || index.chunkSchemaVersion !== EXPECTED_GLOBAL_CHUNK
        || !Array.isArray(index.regions)
      ) {
        throw new Error("当前 Seed 缺少全球 Viewer 区域索引。");
      }
      return index;
    }

    async function loadViewerData(context) {
      if (context.isCurrentViewerRelease) {
        await globalBootstrap.loadReleaseData();
        const release = window.AIRPORT_VIEWER_RELEASE_INFO || {};
        if (Number(release.seed) !== context.seed || Number(release.years) !== context.years) {
          throw new Error("Viewer Release 与页面 Seed 上下文不一致。");
        }
        const globalRows = normalizeRows(window.GLOBAL_MACRO_FEEDBACK_DATA || []);
        validateRowsContext(globalRows, context, "全球 Viewer 主链");
        return captureViewerData(globalRows, {
          reconciledRows: window.REGIONAL_MACRO_RECONCILED_DATA || [],
          diagnosticRows: window.REGIONAL_MACRO_RECONCILIATION_DATA || [],
          lazyIndex: validateIndex(window.AIRPORT_GLOBAL_VIEWER_LAZY_INDEX),
          contextKey: context.slotId,
          contextSource: "viewer_release",
        });
      }
      if (context.cacheStatus !== "ready") {
        throw new Error("当前 Seed 的全球缓存尚未生成或已经过期，请先返回首页生成当前世界。");
      }
      const query = new URLSearchParams({seed: String(context.seed), years: String(context.years)});
      const payload = await globalApiClient.requestJson(`/api/global-viewer/index?${query.toString()}`, {cache: "no-store"});
      if (!payload?.ok || payload.schemaVersion !== EXPECTED_CONTEXT_INDEX) {
        throw new Error(payload?.error || "全球缓存索引读取失败。");
      }
      sharedSeedContext.assertResponse(payload, "全球缓存索引");
      const globalRows = normalizeRows(payload.core?.globalRows || []);
      validateRowsContext(globalRows, context, "全球缓存主链");
      return captureViewerData(globalRows, {
        reconciledRows: payload.core?.regionalReconciledRows || [],
        diagnosticRows: payload.core?.regionalReconciliationRows || [],
        lazyIndex: validateIndex(payload.index),
        contextKey: context.slotId,
        contextSource: "seed_cache",
      });
    }

    function lazyRegionEntry(data, regionId) {
      const regions = Array.isArray(data?.lazyIndex?.regions) ? data.lazyIndex.regions : [];
      return regions.find((entry) => entry.regionId === regionId) || null;
    }

    function syncLoadedRegion(data, regionId) {
      if (state.activeData !== data) return;
      const config = SCOPE_OPTIONS.find((option) => option.id === regionId && option.type === "regional");
      if (!config) return;
      const regionalRows = data.regionalDatasets?.[regionId] || [];
      const supplyRows = data.supplyDatasets?.[regionId] || [];
      const aviationRows = data.aviationDatasets?.[regionId] || [];
      if (regionalRows.length) state.datasets[regionId] = normalizeRegionalRows(regionalRows, config);
      if (supplyRows.length) state.supplyDatasets[regionId] = normalizeAirSupplyRows(supplyRows, config);
      if (aviationRows.length) state.aviationDatasets[regionId] = normalizeAviationRows(aviationRows, config, supplyRows);
    }

    async function ensureRegionLoaded(data, regionId) {
      if (!data || regionId === "global" || !data.lazyIndex) return;
      if (data.contextKey !== state.seedContext?.slotId) {
        throw new Error("全球 Viewer 内存索引与页面 Seed 上下文不一致。");
      }
      data.loadedRegionIds ||= new Set();
      data.regionLoadPromises ||= new Map();
      const regionKey = `${data.contextKey}:${regionId}`;
      if (data.loadedRegionIds.has(regionKey)) return;
      if (data.regionLoadPromises.has(regionKey)) return data.regionLoadPromises.get(regionKey);
      const entry = lazyRegionEntry(data, regionId);
      if (!entry) throw new Error(`区域目录中没有 ${regionId}`);

      const loadPromise = (async () => {
        let chunk;
        if (data.contextSource === "viewer_release") {
          const baseUrl = data.lazyBaseUrl || data.lazyIndex.baseUrl;
          const response = await fetch(new URL(entry.file, baseUrl).href);
          if (!response.ok) throw new Error(`无法加载区域数据 ${regionId}`);
          chunk = await response.json();
        } else {
          const query = new URLSearchParams({
            seed: String(state.seedContext.seed),
            years: String(state.seedContext.years),
            region: regionId,
          });
          const payload = await globalApiClient.requestJson(`/api/global-viewer/region?${query.toString()}`, {cache: "no-store"});
          if (!payload?.ok || payload.schemaVersion !== EXPECTED_CONTEXT_REGION) {
            throw new Error(payload?.error || `无法加载区域数据 ${regionId}`);
          }
          sharedSeedContext.assertResponse(payload, `全球区域 ${regionId}`);
          chunk = payload.chunk;
        }
        if (
          chunk?.schemaVersion !== data.lazyIndex.chunkSchemaVersion
          || chunk?.regionId !== regionId
          || !Array.isArray(chunk.regionalMacroRows)
          || !Array.isArray(chunk.aviationDemandRows)
          || !Array.isArray(chunk.airCapacitySupplyRows)
        ) {
          throw new Error(`区域数据格式不兼容 ${regionId}`);
        }
        for (const [label, rows] of [
          ["区域宏观", chunk.regionalMacroRows],
          ["航空需求", chunk.aviationDemandRows],
          ["航空供给", chunk.airCapacitySupplyRows],
        ]) validateRowsContext(rows, state.seedContext, `${regionId} ${label}`);
        data.regionalDatasets[regionId] = chunk.regionalMacroRows;
        data.aviationDatasets[regionId] = chunk.aviationDemandRows;
        data.supplyDatasets[regionId] = chunk.airCapacitySupplyRows;
        data.loadedRegionIds.add(regionKey);
        syncLoadedRegion(data, regionId);
      })();
      data.regionLoadPromises.set(regionKey, loadPromise);
      try {
        await loadPromise;
      } finally {
        data.regionLoadPromises.delete(regionKey);
      }
    }

    async function applyViewerData(data, preferredScope = state.scope, preferredSeed = state.seed) {
      data.regionalDatasets ||= {};
      data.aviationDatasets ||= {};
      data.supplyDatasets ||= {};
      data.loadedRegionIds ||= new Set();
      data.regionLoadPromises ||= new Map();
      state.activeData = data;
      window.REGIONAL_MACRO_DATASETS = data.regionalDatasets;
      window.REGIONAL_AVIATION_DEMAND_DATASETS = data.aviationDatasets;
      window.REGIONAL_AIR_CAPACITY_SUPPLY_DATASETS = data.supplyDatasets;
      setRegionalReconciliationData(cloneRows(data.reconciledRows || []), cloneRows(data.diagnosticRows || []));
      state.datasets = buildDatasets(data.globalRows || [], data.regionalDatasets || {});
      state.supplyDatasets = buildSupplyDatasets(data.supplyDatasets || {});
      state.aviationDatasets = buildAviationDatasets(data.aviationDatasets || {}, data.supplyDatasets || {});
      if (!state.datasets.global?.length) throw new Error("当前 Seed 没有全球宏观数据");
      if (preferredScope !== "global") await ensureRegionLoaded(data, preferredScope);
      applyScope(preferredScope, preferredSeed);
    }
