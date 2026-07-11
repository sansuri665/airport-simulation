const rawRows = (window.CITY_AIRPORT_QUARTERLY_OPERATIONS_DATA?.rows || []).map((row) => ({ ...row }));
    const rawFinancialRows = (window.CITY_AIRPORT_FINANCIAL_STATE_DATA?.rows || []).map((row) => ({ ...row }));
    let rawValuationRows = (window.CITY_AIRPORT_VALUATION_FORECAST_DATA?.rows || []).map((row) => ({ ...row }));
    let valuationLoaded = !window.AIRPORT_OPERATIONS_VIEWER_LAZY_INDEX || rawValuationRows.length > 0;
    let valuationLoadPromise = null;
    const el = {
      statusText: document.getElementById("statusText"),
      seedSelect: document.getElementById("seedSelect"),
      chartModeSwitch: document.getElementById("chartModeSwitch"),
      financeSideTools: document.getElementById("financeSideTools"),
      financeSideSwitch: document.getElementById("financeSideSwitch"),
      trajectoryLegend: document.getElementById("trajectoryLegend"),
      financeScopeSelect: document.getElementById("financeScopeSelect"),
      financeYearRange: document.getElementById("financeYearRange"),
      summaryGrid: document.getElementById("summaryGrid"),
      financeChart: document.getElementById("financeChart"),
      financeMetrics: document.getElementById("financeMetrics"),
      assetDetailPanel: document.getElementById("assetDetailPanel"),
      assetDetailNote: document.getElementById("assetDetailNote"),
      assetSlotTable: document.getElementById("assetSlotTable"),
    };

    const SLOT_ASSETS = [
      {
        airportName: "北京首都",
        slotName: "首都T3航站楼",
        facilitySize: "extra_large",
        inServiceYear: 2008,
        assetOriginalMillionCny: 51000,
        usefulLifeYears: 40,
        residualValuePct: 10,
      },
      {
        airportName: "北京首都",
        slotName: "首都T2航站楼",
        facilitySize: "large",
        inServiceYear: 2000,
        assetOriginalMillionCny: 28500,
        usefulLifeYears: 35,
        residualValuePct: 10,
      },
      {
        airportName: "北京首都",
        slotName: "首都玩家扩建槽位 1",
        facilitySize: "empty",
        inServiceYear: null,
        assetOriginalMillionCny: 0,
        usefulLifeYears: 0,
        residualValuePct: 0,
      },
      {
        airportName: "北京首都",
        slotName: "首都玩家扩建槽位 2",
        facilitySize: "empty",
        inServiceYear: null,
        assetOriginalMillionCny: 0,
        usefulLifeYears: 0,
        residualValuePct: 0,
      },
      {
        airportName: "北京首都",
        slotName: "首都玩家扩建槽位 3",
        facilitySize: "empty",
        inServiceYear: null,
        assetOriginalMillionCny: 0,
        usefulLifeYears: 0,
        residualValuePct: 0,
      },
      {
        airportName: "北京大兴",
        slotName: "大兴T1航站楼",
        facilitySize: "giant",
        inServiceYear: 2019,
        assetOriginalMillionCny: 78750,
        usefulLifeYears: 45,
        residualValuePct: 10,
      },
      {
        airportName: "北京大兴",
        slotName: "大兴T2航站楼",
        facilitySize: "empty",
        inServiceYear: null,
        assetOriginalMillionCny: 0,
        usefulLifeYears: 0,
        residualValuePct: 0,
      },
      {
        airportName: "北京大兴",
        slotName: "大兴玩家扩建槽位 1",
        facilitySize: "empty",
        inServiceYear: null,
        assetOriginalMillionCny: 0,
        usefulLifeYears: 0,
        residualValuePct: 0,
      },
      {
        airportName: "北京大兴",
        slotName: "大兴玩家扩建槽位 2",
        facilitySize: "empty",
        inServiceYear: null,
        assetOriginalMillionCny: 0,
        usefulLifeYears: 0,
        residualValuePct: 0,
      },
      {
        airportName: "北京大兴",
        slotName: "大兴玩家扩建槽位 3",
        facilitySize: "empty",
        inServiceYear: null,
        assetOriginalMillionCny: 0,
        usefulLifeYears: 0,
        residualValuePct: 0,
      },
    ];

    const configuredInitialAssets = (window.CITY_AIRPORT_FINANCIAL_STATE_DATA?.initial_assets || []).map((asset) => ({
      airportName: asset.airport_name || asset.airport_id || "-",
      slotName: asset.slot_name || asset.slot_id || asset.asset_id || "-",
      facilitySize: asset.facility_size || "-",
      inServiceYear: num(asset.in_service_year, null),
      assetOriginalMillionCny: num(asset.asset_original_million_cny),
      usefulLifeYears: num(asset.useful_life_years),
      residualValuePct: num(asset.residual_value_pct),
    }));
    if (configuredInitialAssets.length) {
      SLOT_ASSETS.splice(0, SLOT_ASSETS.length, ...configuredInitialAssets);
    }
    const configuredGeneralLoans = (window.CITY_AIRPORT_FINANCIAL_STATE_DATA?.general_loans || []).map((loan) => ({
      id: loan.loan_id || "",
      name: loan.loan_name || loan.loan_id || "",
      style: loan.repayment_style || "",
    }));
    const loanNameMap = new Map(configuredGeneralLoans.map((loan) => [loan.id, loan.name]));

    const state = window.AirportOperationsViewerState;

    function valuationDatasetEntry() {
      const datasets = Array.isArray(window.AIRPORT_OPERATIONS_VIEWER_LAZY_INDEX?.datasets)
        ? window.AIRPORT_OPERATIONS_VIEWER_LAZY_INDEX.datasets
        : [];
      return datasets.find((dataset) => dataset.datasetId === "valuation") || null;
    }

    async function ensureValuationLoaded() {
      if (valuationLoaded) return;
      if (valuationLoadPromise) return valuationLoadPromise;
      const index = window.AIRPORT_OPERATIONS_VIEWER_LAZY_INDEX;
      const dataset = valuationDatasetEntry();
      if (!index || !dataset) {
        valuationLoaded = true;
        return;
      }
      valuationLoadPromise = (async () => {
        el.statusText.textContent = "loading: 估值数据";
        const response = await fetch(new URL(dataset.file, index.baseUrl).href, { cache: "no-store" });
        if (!response.ok) throw new Error("无法加载估值数据");
        const chunk = await response.json();
        if (
          chunk?.schemaVersion !== index.chunkSchemaVersion
          || chunk?.datasetId !== "valuation"
          || chunk?.marketId !== index.marketId
          || !Array.isArray(chunk.rows)
          || chunk.rows.length !== dataset.rowCount
        ) {
          throw new Error("估值数据格式不兼容");
        }
        rawValuationRows = chunk.rows.map((row) => ({ ...row }));
        valuationLoaded = true;
      })();
      try {
        await valuationLoadPromise;
      } finally {
        valuationLoadPromise = null;
      }
    }

    const PASSENGER_COMPONENTS = [
      { key: "business", label: "商务" },
      { key: "leisure", label: "休闲" },
      { key: "vfr", label: "探亲访友" },
      { key: "long_haul", label: "长途" },
      { key: "transfer", label: "中转" },
    ];

    function num(value, fallback = 0) {
      const parsed = Number(value);
      return Number.isFinite(parsed) ? parsed : fallback;
    }

    function fmtBillion(millionCny) {
      return `${(num(millionCny) / 100).toFixed(1)} 亿元`;
    }

    function fmtPassenger(million) {
      const value = num(million);
      if (value >= 100) return `${(value / 100).toFixed(3)} 亿`;
      return `${(value * 100).toFixed(0)} 万`;
    }

    function fmtPassengerShort(million) {
      const value = num(million);
      if (value >= 100) return `${(value / 100).toFixed(3)}亿`;
      return `${(value * 100).toFixed(0)}万`;
    }

    function fmtPct(value) {
      return `${num(value).toFixed(1)}%`;
    }

    function fmtBps(value) {
      return `${num(value).toFixed(0)} bps`;
    }

    function uniqueSemiList(value) {
      const parts = String(value || "").split(";").map((part) => part.trim()).filter(Boolean);
      return [...new Set(parts)];
    }

    function loanIdsLabel(value) {
      const ids = uniqueSemiList(value);
      if (!ids.length) return "无";
      return ids.map((id) => loanNameMap.get(id) || id).join(" / ");
    }

    function fmtMultiplier(value) {
      return `${num(value, 1).toFixed(3)}x`;
    }

    function fmtValuationMultiple(value) {
      const parsed = Number(value);
      if (!Number.isFinite(parsed) || Math.abs(parsed) <= 1e-9) return "-";
      return `${parsed.toFixed(2)}x`;
    }

    function fmtCny(value) {
      return `${num(value).toFixed(1)} 元/客`;
    }

    function fmtYears(value) {
      return `${num(value).toFixed(1)} 年`;
    }

    function contractBasisLabel(value) {
      if (value === "minimum_guarantee") return "保底生效";
      if (value === "revenue_share") return "分成生效";
      if (value === "mixed") return "混合生效";
      return value || "-";
    }

    function contractStatusLabel(value) {
      if (value === "startup_history_fixed") return "开局历史合同";
      if (value === "auto_forecast_renewal") return "自动预测重签";
      if (value === "fixed_contract") return "固定合同";
      return value || "-";
    }

    function gamePhaseLabel(value) {
      if (value === "startup_operating_history") return "开局历史";
      if (value === "player_operation") return "玩家经营";
      return value || "-";
    }

    function toneClass(value, warningAt, dangerAt) {
      const v = num(value);
      if (v >= dangerAt) return "danger";
      if (v >= warningAt) return "warning";
      return "positive";
    }

    function groupAnnual(rows) {
      const grouped = new Map();
      rows.forEach((row) => {
        const year = num(row.year);
        if (!grouped.has(year)) grouped.set(year, []);
        grouped.get(year).push(row);
      });

      return [...grouped.entries()].sort((a, b) => a[0] - b[0]).map(([year, items]) => {
        items.sort((a, b) => num(String(a.quarter).replace("Q", ""), 1) - num(String(b.quarter).replace("Q", ""), 1));
        const first = items[0];
        const quarters = Object.fromEntries(items.map((row) => [row.quarter, row]));
        const revenue = items.reduce((sum, row) => sum + num(row.total_operating_revenue_million_cny), 0);
        const cost = items.reduce((sum, row) => sum + num(row.total_operating_cost_million_cny), 0);
        const profit = items.reduce((sum, row) => sum + num(row.quarter_operating_profit_million_cny), 0);
        const commercial = items.reduce((sum, row) => sum + num(row.commercial_revenue_million_cny), 0);
        const foodRetail = items.reduce((sum, row) => sum + num(row.food_retail_revenue_million_cny), 0);
        const dutyFreeContract = items.reduce((sum, row) => sum + num(row.duty_free_revenue_million_cny), 0);
        const luxuryContract = items.reduce((sum, row) => sum + num(row.luxury_retail_revenue_million_cny), 0);
        const contractCommercial = items.reduce(
          (sum, row) => sum + num(
            row.contract_commercial_revenue_million_cny,
            num(row.duty_free_revenue_million_cny) + num(row.luxury_retail_revenue_million_cny)
          ),
          0
        );
        const foodRetailFixedCost = items.reduce(
          (sum, row) => sum + num(row.food_retail_fixed_operating_cost_million_cny),
          0
        );
        const foodRetailPassengerCost = items.reduce(
          (sum, row) => sum + num(row.food_retail_passenger_service_cost_million_cny),
          0
        );
        const foodRetailSalesCost = items.reduce(
          (sum, row) => sum + num(row.food_retail_sales_cost_million_cny),
          0
        );
        const foodRetailOperatingCost = items.reduce(
          (sum, row) => sum + num(
            row.food_retail_operating_cost_million_cny,
            num(row.food_retail_sales_cost_million_cny) +
            num(row.food_retail_fixed_operating_cost_million_cny) +
              num(row.food_retail_passenger_service_cost_million_cny)
          ),
          0
        );
        const foodRetailProfit = items.reduce(
          (sum, row) => sum + num(
            row.food_retail_operating_profit_million_cny,
            num(row.food_retail_revenue_million_cny) -
              num(row.food_retail_operating_cost_million_cny)
          ),
          0
        );
        const dutyFreeWeightedPassengers = items.reduce(
          (sum, row) => sum + num(row.duty_free_weighted_passengers_million),
          0
        );
        const dutyFreeSales = items.reduce((sum, row) => sum + num(row.duty_free_sales_million_cny), 0);
        const dutyFreeGuarantee = items.reduce(
          (sum, row) => sum + num(row.duty_free_contract_minimum_guarantee_million_cny),
          0
        );
        const dutyFreeShareRevenue = items.reduce(
          (sum, row) => sum + num(row.duty_free_contract_share_revenue_million_cny),
          0
        );
        const dutyFreeForecastSales = num(first.duty_free_contract_forecast_annual_sales_million_cny);
        const dutyFreeBasisSet = new Set(items.map((row) => row.duty_free_contract_revenue_basis || ""));
        const luxuryWeightedPassengers = items.reduce(
          (sum, row) => sum + num(row.luxury_weighted_passengers_million),
          0
        );
        const luxurySales = items.reduce((sum, row) => sum + num(row.luxury_sales_million_cny), 0);
        const luxuryGuarantee = items.reduce(
          (sum, row) => sum + num(row.luxury_contract_minimum_guarantee_million_cny),
          0
        );
        const luxuryShareRevenue = items.reduce(
          (sum, row) => sum + num(row.luxury_contract_share_revenue_million_cny),
          0
        );
        const luxuryForecastSales = num(first.luxury_contract_forecast_annual_sales_million_cny);
        const luxuryBasisSet = new Set(items.map((row) => row.luxury_contract_revenue_basis || ""));
        const commercialDirectCost = items.reduce(
          (sum, row) => sum + num(row.commercial_direct_cost_million_cny),
          0
        );
        const commercialProfit = items.reduce(
          (sum, row) => sum + num(
            row.commercial_operating_profit_million_cny,
            num(row.commercial_revenue_million_cny) - num(row.commercial_direct_cost_million_cny)
          ),
          0
        );
        const aero = items.reduce((sum, row) => sum + num(row.aeronautical_revenue_million_cny), 0);
        const fixedCost = items.reduce((sum, row) => sum + num(row.quarter_slot_fixed_operating_cost_million_cny), 0);
        const passengerCost = items.reduce(
          (sum, row) => sum + num(row.quarter_passenger_variable_cost_million_cny),
          0
        );
        const congestion = items.reduce((sum, row) => sum + num(row.quarter_congestion_cost_million_cny), 0);
        const potentialPassengers = items.reduce(
          (sum, row) => sum + num(row.quarter_city_potential_passengers_million),
          0
        );
        const airlineSupply = items.reduce(
          (sum, row) => sum + num(row.quarter_airline_supply_passengers_million),
          0
        );
        const passengers = items.reduce((sum, row) => sum + num(row.quarter_served_passengers_million), 0);
        const designCapacity = items.reduce((sum, row) => sum + num(row.quarter_design_capacity_million), 0);
        const maxCapacity = items.reduce((sum, row) => sum + num(row.quarter_max_capacity_million), 0);
        const airlineSupplyFulfillment = potentialPassengers ? Math.min(100, airlineSupply / potentialPassengers * 100) : 100;
        const airlineSupplyGap = Math.max(0, potentialPassengers - airlineSupply);
        const passengerComponents = PASSENGER_COMPONENTS.map((component) => {
          const potential = items.reduce(
            (sum, row) => sum + num(
              row[`${component.key}_quarter_potential_passengers_million`],
              num(row[`${component.key}_quarter_served_passengers_million`])
            ),
            0
          );
          const supplyFallback = potentialPassengers ? airlineSupply * potential / potentialPassengers : potential;
          const supply = items.reduce(
            (sum, row) => sum + num(
              row[`${component.key}_quarter_airline_supply_passengers_million`],
              supplyFallback / items.length
            ),
            0
          );
          const served = items.reduce(
            (sum, row) => sum + num(row[`${component.key}_quarter_served_passengers_million`]),
            0
          );
          return { ...component, potential, airlineSupply: supply, passengers: served };
        });
        const renovationPeriodDepreciation = items.reduce(
          (sum, row) => sum + num(row.renovation_asset_period_depreciation_million_cny),
          0
        );
        const latestRenovationAsset = items[items.length - 1] || first;
        const constructionPeriodDepreciation = items.reduce(
          (sum, row) => sum + num(row.construction_asset_period_depreciation_million_cny),
          0
        );
        const latestConstructionAsset = items[items.length - 1] || first;
        const rebuildPeriodDepreciation = items.reduce(
          (sum, row) => sum + num(row.rebuild_asset_period_depreciation_million_cny),
          0
        );
        const latestRebuildAsset = items[items.length - 1] || first;
        const qualityWeight = items.reduce((sum, row) => sum + num(row.quarter_served_passengers_million), 0);
        const weightedQuarterAverage = (field, fallback = 0) => {
          if (!qualityWeight) return fallback;
          return items.reduce(
            (sum, row) => sum + num(row[field], fallback) * num(row.quarter_served_passengers_million),
            0
          ) / qualityWeight;
        };
        const qualityIndex = weightedQuarterAverage("city_airport_perceived_quality_index", 100);
        const qualitySizeScore = weightedQuarterAverage("perceived_quality_size_score", 0);
        const qualityAgeScore = weightedQuarterAverage("perceived_quality_age_score", 0);
        const qualityCapacityScore = weightedQuarterAverage("perceived_quality_capacity_score", 0);
        const qualityDisruptionScore = weightedQuarterAverage("perceived_quality_construction_disruption_score", 0);
        const foodRetailQualityMultiplier = weightedQuarterAverage(
          "food_retail_perceived_quality_revenue_multiplier",
          1
        );
        const dutyFreeQualityMultiplier = weightedQuarterAverage(
          "duty_free_perceived_quality_sales_multiplier",
          1
        );
        const luxuryQualityMultiplier = weightedQuarterAverage(
          "luxury_perceived_quality_sales_multiplier",
          1
        );
        return {
          year,
          seed: num(first.seed),
          potentialPassengers: potentialPassengers || num(first.annual_city_potential_passengers_million, num(first.annual_served_passengers_million)),
          airlineSupply: airlineSupply || num(first.annual_city_airline_supply_passengers_million, num(first.annual_city_potential_passengers_million, num(first.annual_served_passengers_million))),
          airlineSupplyIndex: num(first.annual_city_airline_supply_index, 100),
          airlineSupplyFulfillment,
          airlineSupplyGap,
          airlineSupplyVolatilityRegime: first.annual_city_airline_supply_volatility_regime || "normal_airline_supply_cycle",
          passengerComponents,
          passengers,
          designCapacity,
          maxCapacity,
          revenue,
          cost,
          profit,
          commercial,
          foodRetail,
          dutyFreeContract,
          luxuryContract,
          contractCommercial,
          foodRetailFixedCost,
          foodRetailPassengerCost,
          foodRetailSalesCost,
          foodRetailOperatingCost,
          foodRetailProfit,
          dutyFreeWeightedPassengers,
          dutyFreeSales,
          dutyFreeGuarantee,
          dutyFreeShareRevenue,
          dutyFreeForecastSales,
          dutyFreeContractBasis: dutyFreeBasisSet.size === 1 ? [...dutyFreeBasisSet][0] : "mixed",
          dutyFreeContractCycle: first.duty_free_contract_cycle_id || "-",
          dutyFreeContractStatus: first.duty_free_contract_status || "-",
          gamePhase: first.game_phase || "-",
          playerDecisionEnabled: num(first.player_decision_enabled),
          luxuryWeightedPassengers,
          luxurySales,
          luxuryGuarantee,
          luxuryShareRevenue,
          luxuryForecastSales,
          luxuryContractBasis: luxuryBasisSet.size === 1 ? [...luxuryBasisSet][0] : "mixed",
          luxuryContractCycle: first.luxury_contract_cycle_id || "-",
          luxuryContractStatus: first.luxury_contract_status || "-",
          commercialDirectCost,
          commercialProfit,
          aero,
          fixedCost,
          passengerCost,
          congestion,
          renovationActiveEventIds: [...new Set(items.map((row) => row.renovation_active_event_ids || "").filter(Boolean))].join(";"),
          renovationCompletedEventIds: [...new Set(items.map((row) => row.renovation_completed_event_ids || "").filter(Boolean))].join(";"),
          renovationAssetInServicePeriods: latestRenovationAsset.renovation_asset_in_service_periods || "",
          renovationCapexOutlay: items.reduce((sum, row) => sum + num(row.renovation_quarter_capex_outlay_million_cny), 0),
          renovationConstructionInProgress: Math.max(...items.map((row) => num(row.renovation_construction_in_progress_million_cny))),
          renovationAssetOriginal: num(latestRenovationAsset.renovation_asset_original_million_cny),
          renovationAssetResidualFloor: num(latestRenovationAsset.renovation_asset_residual_floor_million_cny),
          renovationAssetAccumulatedDepreciation: num(latestRenovationAsset.renovation_asset_accumulated_depreciation_million_cny),
          renovationAssetBookValue: num(latestRenovationAsset.renovation_asset_book_value_million_cny),
          renovationAssetPeriodDepreciation: renovationPeriodDepreciation,
          constructionActiveEventIds: [...new Set(items.map((row) => row.construction_active_event_ids || "").filter(Boolean))].join(";"),
          constructionCompletedEventIds: [...new Set(items.map((row) => row.construction_completed_event_ids || "").filter(Boolean))].join(";"),
          constructionAssetInServicePeriods: latestConstructionAsset.construction_asset_in_service_periods || "",
          constructionCapexOutlay: items.reduce((sum, row) => sum + num(row.construction_quarter_capex_outlay_million_cny), 0),
          constructionInProgress: Math.max(...items.map((row) => num(row.construction_in_progress_million_cny))),
          constructionAssetOriginal: num(latestConstructionAsset.construction_asset_original_million_cny),
          constructionAssetResidualFloor: num(latestConstructionAsset.construction_asset_residual_floor_million_cny),
          constructionAssetAccumulatedDepreciation: num(latestConstructionAsset.construction_asset_accumulated_depreciation_million_cny),
          constructionAssetBookValue: num(latestConstructionAsset.construction_asset_book_value_million_cny),
          constructionAssetPeriodDepreciation: constructionPeriodDepreciation,
          rebuildActiveEventIds: [...new Set(items.map((row) => row.rebuild_active_event_ids || "").filter(Boolean))].join(";"),
          rebuildStartedEventIds: [...new Set(items.map((row) => row.rebuild_started_event_ids || "").filter(Boolean))].join(";"),
          rebuildStartedSlotIds: [...new Set(items.map((row) => row.rebuild_started_slot_ids || "").filter(Boolean))].join(";"),
          rebuildCompletedEventIds: [...new Set(items.map((row) => row.rebuild_completed_event_ids || "").filter(Boolean))].join(";"),
          rebuildAssetInServicePeriods: latestRebuildAsset.rebuild_asset_in_service_periods || "",
          rebuildCapexOutlay: items.reduce((sum, row) => sum + num(row.rebuild_quarter_capex_outlay_million_cny), 0),
          rebuildDemolitionExpense: items.reduce((sum, row) => sum + num(row.rebuild_quarter_demolition_expense_million_cny), 0),
          rebuildOldRenovationAssetWriteoff: items.reduce((sum, row) => sum + num(row.rebuild_old_renovation_asset_writeoff_million_cny), 0),
          rebuildConstructionInProgress: Math.max(...items.map((row) => num(row.rebuild_construction_in_progress_million_cny))),
          rebuildAssetOriginal: num(latestRebuildAsset.rebuild_asset_original_million_cny),
          rebuildAssetResidualFloor: num(latestRebuildAsset.rebuild_asset_residual_floor_million_cny),
          rebuildAssetAccumulatedDepreciation: num(latestRebuildAsset.rebuild_asset_accumulated_depreciation_million_cny),
          rebuildAssetBookValue: num(latestRebuildAsset.rebuild_asset_book_value_million_cny),
          rebuildAssetPeriodDepreciation: rebuildPeriodDepreciation,
          qualityIndex,
          qualitySizeScore,
          qualityAgeScore,
          qualityCapacityScore,
          qualityDisruptionScore,
          foodRetailQualityMultiplier,
          dutyFreeQualityMultiplier,
          luxuryQualityMultiplier,
          quarters,
          margin: revenue ? profit / revenue * 100 : 0,
          maxQuarterDesignUtilization: Math.max(...items.map((row) => num(row.quarter_design_utilization_pct))),
          maxQuarterMaxUtilization: Math.max(...items.map((row) => num(row.quarter_max_utilization_pct))),
          maxQuarterCrowding: Math.max(...items.map((row) => num(row.quarter_crowding_index))),
          bottleneck: first.annual_city_binding_bottleneck || "-",
          branch: first.branch_scenario_id || "none",
          branchState: first.branch_scenario_state || "baseline",
        };
      });
    }

    function rowsForSeed() {
      return rawRows.filter((row) => num(row.seed) === state.seed);
    }

    function financialRowsForSeed() {
      return rawFinancialRows.filter((row) => num(row.seed) === state.seed);
    }

    function valuationRowsForSeed() {
      return rawValuationRows.filter((row) => num(row.seed) === state.seed);
    }

    function valuationScopeQuarter() {
      return state.financeScope === "annual" ? "Q4" : state.financeScope;
    }

    function valuationRowsForYear(year) {
      return valuationRowsForSeed()
        .filter((row) => num(row.as_of_year) === num(year))
        .sort((a, b) => (
          num(String(a.as_of_quarter).replace("Q", ""), 1) -
          num(String(b.as_of_quarter).replace("Q", ""), 1)
        ));
    }

    function valuationRowForYear(year) {
      const rows = valuationRowsForYear(year);
      if (!rows.length) return null;
      const quarter = valuationScopeQuarter();
      const exact = rows.find((row) => row.as_of_quarter === quarter);
      if (exact) return exact;
      return state.financeScope === "annual" ? rows[rows.length - 1] : null;
    }

    function valuationValues(row) {
      const valuation = valuationRowForYear(row.year);
      return {
        row: valuation,
        asOfYear: valuation ? num(valuation.as_of_year) : row.year,
        asOfQuarter: valuation?.as_of_quarter || valuationScopeQuarter(),
        valuationPrimaryMethod: valuation?.valuation_primary_method || "net_asset_value",
        netAssetEquityValue: num(
          valuation?.net_asset_equity_value_million_cny,
          num(valuation?.primary_equity_value_million_cny, num(valuation?.equity_value_million_cny))
        ),
        netAssetEnterpriseValue: num(
          valuation?.net_asset_enterprise_value_million_cny,
          num(valuation?.primary_enterprise_value_million_cny, num(valuation?.enterprise_value_million_cny))
        ),
        operatingEnterpriseValue: num(
          valuation?.experimental_operating_enterprise_value_million_cny,
          num(
            valuation?.operating_enterprise_value_million_cny,
            num(valuation?.enterprise_value_million_cny)
          )
        ),
        marketEnterpriseValue: num(
          valuation?.experimental_market_enterprise_value_million_cny,
          num(
            valuation?.market_enterprise_value_million_cny,
            num(valuation?.enterprise_value_million_cny)
          )
        ),
        experimentalEquityValue: num(
          valuation?.experimental_equity_value_million_cny,
          num(valuation?.enterprise_value_million_cny)
        ),
        equityValue: num(
          valuation?.primary_equity_value_million_cny,
          num(valuation?.net_asset_equity_value_million_cny, num(valuation?.equity_value_million_cny))
        ),
        enterpriseValue: num(
          valuation?.primary_enterprise_value_million_cny,
          num(
            valuation?.net_asset_enterprise_value_million_cny,
            num(valuation?.enterprise_value_million_cny)
          )
        ),
        conservativeEquityValue: num(valuation?.equity_value_conservative_million_cny),
        optimisticEquityValue: num(valuation?.equity_value_optimistic_million_cny),
        netDebt: num(valuation?.net_debt_million_cny),
        recognizedCash: num(valuation?.recognized_cash_million_cny),
        totalDebt: num(valuation?.current_total_debt_million_cny),
        currentOperatingProfit: num(valuation?.current_annual_operating_profit_million_cny),
        currentAccountingProfit: num(valuation?.current_annual_accounting_profit_million_cny),
        operatingDiscountRatePct: num(valuation?.operating_discount_rate_pct, num(valuation?.discount_rate_pct)),
        operatingTerminalGrowthPct: num(valuation?.operating_terminal_growth_pct, num(valuation?.terminal_growth_pct)),
        marketMultiplier: num(valuation?.market_valuation_multiplier, 1),
        marketAdjustmentPct: num(valuation?.market_valuation_adjustment_pct),
        marketAdjustment: num(valuation?.market_valuation_adjustment_million_cny),
        marketRateAdjustmentPct: num(valuation?.market_rate_adjustment_pct),
        marketCreditAdjustmentPct: num(valuation?.market_credit_adjustment_pct),
        marketEquityValuationPe: num(
          valuation?.market_equity_valuation_pe,
          num(valuation?.input_equity_valuation_pe, 17)
        ),
        marketEquityValuationAdjustmentPct: num(valuation?.market_equity_valuation_adjustment_pct),
        marketEquitySentimentAdjustmentPct: num(valuation?.market_equity_sentiment_adjustment_pct),
        marketBranchAdjustmentPct: num(valuation?.market_branch_adjustment_pct),
        forecastFcffSum: num(valuation?.forecast_5y_fcff_sum_million_cny),
        operatingNormalizedFcffSum: num(
          valuation?.operating_5y_normalized_fcff_sum_million_cny,
          num(valuation?.forecast_5y_fcff_sum_million_cny)
        ),
        normalizedTerminalFcff: num(valuation?.normalized_terminal_fcff_million_cny),
        forecastYear1Fcff: num(valuation?.forecast_year_1_fcff_million_cny),
        operatingEvToOperatingProfit: num(valuation?.operating_ev_to_current_operating_profit_multiple),
        marketEvToOperatingProfit: num(
          valuation?.market_ev_to_current_operating_profit_multiple,
          num(valuation?.ev_to_current_operating_profit_multiple)
        ),
        priceToOperatingProfit: num(valuation?.price_to_current_operating_profit_multiple),
        priceToAccountingProfit: num(valuation?.price_to_current_accounting_profit_multiple),
        priceToBook: num(
          valuation?.price_to_book_equity_multiple,
          num(valuation?.equity_to_book_equity_multiple)
        ),
        equityToBook: num(valuation?.equity_to_book_equity_multiple),
        uncertaintyRangePct: num(valuation?.valuation_uncertainty_range_pct),
        riskTags: valuation?.valuation_risk_tags || "normal",
      };
    }

    function valuationRiskLabel(value) {
      const labels = {
        normal: "正常",
        capacity_pressure: "容量压力",
        loan_stress_active: "贷款压力",
        branch_event_active: "分岔事件",
        market_discount: "市场折价",
        market_premium: "市场溢价",
        elevated_leverage: "杠杆偏高",
        high_leverage: "高杠杆",
        negative_equity_value: "股权价值为负",
        negative_terminal_fcff: "终值现金流为负",
      };
      const tags = uniqueSemiList(value);
      if (!tags.length) return labels.normal;
      return tags.map((tag) => labels[tag] || tag.replaceAll("_", " ")).join(" / ");
    }

    function bottleneckLabel(value) {
      const labels = {
        demand_limited: "需求不足",
        airline_bottleneck: "航司供给",
        airport_bottleneck: "机场容量",
        dual_airline_airport_bottleneck: "航司 + 机场",
      };
      return labels[value] || value || "-";
    }

    function airlineSupplyVolatilityLabel(value) {
      const labels = {
        normal_airline_supply_cycle: "正常周期",
        volatile_airline_supply: "波动偏强",
        highly_volatile_airline_supply: "剧烈波动",
      };
      return labels[value] || value || "-";
    }

    function annualRows() {
      return groupAnnual(rowsForSeed());
    }

    function chartRowsForMode(data) {
      if (state.chartMode !== "valuation") return data;
      return data.filter((row) => valuationRowForYear(row.year));
    }

    function financialAnnualRows() {
      const grouped = new Map();
      financialRowsForSeed().forEach((row) => {
        const year = num(row.year);
        if (!grouped.has(year)) grouped.set(year, []);
        grouped.get(year).push(row);
      });

      return [...grouped.entries()].sort((a, b) => a[0] - b[0]).map(([year, items]) => {
        items.sort((a, b) => num(String(a.quarter).replace("Q", ""), 1) - num(String(b.quarter).replace("Q", ""), 1));
        const first = items[0];
        const latest = items[items.length - 1];
        const quarters = Object.fromEntries(items.map((row) => [row.quarter, row]));
        const operatingProfit = items.reduce((sum, row) => sum + num(row.period_operating_profit_million_cny), 0);
        const depreciation = items.reduce((sum, row) => sum + num(row.period_accounting_depreciation_million_cny), 0);
        const pretaxAccountingProfit = items.reduce((sum, row) => sum + num(row.period_pretax_accounting_profit_million_cny), 0);
        const taxableIncomeBeforeLoss = items.reduce((sum, row) => sum + num(row.period_taxable_income_million_cny), 0);
        const taxableIncomeAfterLoss = items.reduce((sum, row) => sum + num(row.period_annual_taxable_income_after_loss_million_cny), 0);
        const hasAnnualTaxSettlement = items.some((row) => row.period_annual_income_tax_payable_million_cny !== undefined && row.period_annual_income_tax_payable_million_cny !== "");
        const taxPrepayment = items.reduce((sum, row) => sum + num(row.period_income_tax_prepayment_million_cny), 0);
        const taxSettlement = items.reduce((sum, row) => sum + num(row.period_income_tax_settlement_million_cny), 0);
        const cashTaxPaid = items.reduce((sum, row) => sum + num(row.period_cash_tax_paid_million_cny), 0);
        const taxLossUsed = items.reduce((sum, row) => sum + num(row.period_tax_loss_used_million_cny), 0);
        const taxLossGenerated = items.reduce((sum, row) => sum + num(row.period_tax_loss_generated_million_cny), 0);
        const taxLossExpired = items.reduce((sum, row) => sum + num(row.period_tax_loss_expired_million_cny), 0);
        const taxLossCarryforwardEnding = num(latest.period_tax_loss_carryforward_ending_million_cny);
        const taxableIncome = hasAnnualTaxSettlement ? taxableIncomeAfterLoss : taxableIncomeBeforeLoss;
        const incomeTax = items.reduce((sum, row) => sum + num(row.period_income_tax_expense_million_cny), 0);
        const accountingProfit = items.reduce((sum, row) => sum + num(row.period_accounting_profit_million_cny), 0);
        const capex = items.reduce((sum, row) => sum + num(row.period_total_capex_outlay_million_cny), 0);
        const rebuildCapex = items.reduce((sum, row) => sum + num(row.period_rebuild_capex_outlay_million_cny), 0);
        const rebuildDemolitionExpense = items.reduce(
          (sum, row) => sum + num(row.period_rebuild_demolition_expense_million_cny),
          0
        );
        const rebuildInitialWriteoff = items.reduce(
          (sum, row) => sum + num(row.period_rebuild_old_initial_asset_writeoff_million_cny),
          0
        );
        const rebuildRenovationWriteoff = items.reduce(
          (sum, row) => sum + num(row.period_rebuild_old_renovation_asset_writeoff_million_cny),
          0
        );
        const rebuildOldAssetWriteoff = items.reduce(
          (sum, row) => sum + num(row.period_rebuild_old_asset_writeoff_million_cny),
          0
        );
        const freeCashFlow = items.reduce((sum, row) => sum + num(row.period_free_cash_flow_before_financing_million_cny), 0);
        const interestExpense = items.reduce((sum, row) => sum + num(row.period_interest_expense_million_cny), 0);
        const loanDrawdown = items.reduce((sum, row) => sum + num(row.period_loan_drawdown_million_cny), 0);
        const interestPayment = items.reduce((sum, row) => sum + num(row.period_interest_payment_million_cny), 0);
        const principalRepayment = items.reduce((sum, row) => sum + num(row.period_principal_repayment_million_cny), 0);
        const debtService = items.reduce((sum, row) => sum + num(row.period_debt_service_million_cny), 0);
        const financingCashFlow = items.reduce((sum, row) => sum + num(row.period_financing_cash_flow_million_cny), 0);
        const debtRateWeight = items.reduce(
          (sum, row) => sum + (num(row.short_term_debt_million_cny) + num(row.long_term_debt_million_cny)) * num(row.loan_weighted_interest_rate_pct),
          0
        );
        const debtRateBase = items.reduce(
          (sum, row) => sum + num(row.short_term_debt_million_cny) + num(row.long_term_debt_million_cny),
          0
        );
        const drawdownLeverageBefore = Math.max(...items.map((row) => num(row.loan_drawdown_leverage_before_pct)));
        const drawdownLeverageAfter = Math.max(...items.map((row) => num(row.loan_drawdown_leverage_after_pct)));
        const drawdownLeverageSpreadWeight = items.reduce(
          (sum, row) => sum + num(row.period_loan_drawdown_million_cny) * num(row.loan_drawdown_leverage_spread_bps),
          0
        );
        const drawdownRateWeight = items.reduce(
          (sum, row) => sum + num(row.period_loan_drawdown_million_cny) * num(row.loan_drawdown_weighted_interest_rate_pct),
          0
        );
        const loanActiveIds = uniqueSemiList(items.map((row) => row.loan_active_ids || "").join(";")).join(";");
        const loanDrawdownIds = uniqueSemiList(items.map((row) => row.loan_drawdown_ids || "").join(";")).join(";");
        const loanPrincipalRepaymentIds = uniqueSemiList(
          items.map((row) => row.loan_principal_repayment_ids || "").join(";")
        ).join(";");
        const loanBlockedIds = uniqueSemiList(items.map((row) => row.loan_blocked_ids || "").join(";")).join(";");
        const loanBlockedReasons = uniqueSemiList(items.map((row) => row.loan_blocked_reasons || "").join(";")).join(";");
        return {
          year,
          seed: num(first.seed),
          quarters,
          beginCash: num(first.period_begin_cash_million_cny),
          endCash: num(latest.period_end_cash_million_cny),
          operatingProfit,
          depreciation,
          pretaxAccountingProfit,
          taxableIncomeBeforeLoss,
          taxableIncome,
          taxPrepayment,
          taxSettlement,
          cashTaxPaid,
          taxLossUsed,
          taxLossGenerated,
          taxLossExpired,
          taxLossCarryforwardEnding,
          incomeTax,
          effectiveTaxRatePct: pretaxAccountingProfit > 0 ? incomeTax / pretaxAccountingProfit * 100 : 0,
          accountingProfit,
          capex,
          rebuildCapex,
          rebuildDemolitionExpense,
          rebuildInitialWriteoff,
          rebuildRenovationWriteoff,
          rebuildOldAssetWriteoff,
          freeCashFlow,
          interestExpense,
          loanDrawdown,
          interestPayment,
          principalRepayment,
          debtService,
          financingCashFlow,
          loanActiveIds,
          loanDrawdownIds,
          loanPrincipalRepaymentIds,
          loanWeightedInterestRatePct: debtRateBase ? debtRateWeight / debtRateBase : 0,
          loanDrawdownWeightedInterestRatePct: loanDrawdown ? drawdownRateWeight / loanDrawdown : 0,
          loanDrawdownLeverageBeforePct: drawdownLeverageBefore,
          loanDrawdownLeverageAfterPct: drawdownLeverageAfter,
          loanDrawdownLeverageSpreadBps: loanDrawdown ? drawdownLeverageSpreadWeight / loanDrawdown : 0,
          loanBlockedIds,
          loanBlockedReasons,
          fixedAssetOriginal: num(latest.fixed_asset_original_million_cny),
          fixedAssetResidualFloor: num(latest.fixed_asset_residual_floor_million_cny),
          fixedAssetAccumulatedDepreciation: num(latest.fixed_asset_accumulated_depreciation_million_cny),
          fixedAssetBook: num(latest.fixed_asset_book_value_million_cny),
          constructionInProgress: num(latest.construction_in_progress_million_cny),
          totalNoncurrentAssets: num(latest.total_noncurrent_assets_million_cny),
          totalAssets: num(latest.total_assets_million_cny),
          shortTermDebt: num(latest.short_term_debt_million_cny),
          longTermDebt: num(latest.long_term_debt_million_cny),
          totalLiabilities: num(latest.total_liabilities_million_cny),
          contributedCapital: num(latest.contributed_capital_million_cny),
          retainedEarnings: num(latest.retained_earnings_million_cny),
          totalEquity: num(latest.total_equity_million_cny),
          balanceCheck: num(latest.balance_check_million_cny),
          gamePhase: latest.game_phase || "-",
        };
      });
    }

    function financialAnnualMap() {
      return new Map(financialAnnualRows().map((row) => [row.year, row]));
    }

