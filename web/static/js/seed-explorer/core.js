const apiClient = window.AirportApiClient;
const PLAYER_SIMULATION_MIN_YEARS = 60;
const el = {
      seedInput: document.getElementById("seedInput"),
      yearsInput: document.getElementById("yearsInput"),
      cachedRunSelect: document.getElementById("cachedRunSelect"),
      forceInput: document.getElementById("forceInput"),
      runButton: document.getElementById("runButton"),
      randomButton: document.getElementById("randomButton"),
      status: document.getElementById("status"),
      sortSelect: document.getElementById("sortSelect"),
      searchInput: document.getElementById("searchInput"),
      cityList: document.getElementById("cityList"),
      cityTitle: document.getElementById("cityTitle"),
      runCaption: document.getElementById("runCaption"),
      summaryGrid: document.getElementById("summaryGrid"),
      chart: document.getElementById("chart"),
      chartCaption: document.getElementById("chartCaption"),
      detailRows: document.getElementById("detailRows"),
      cityTools: document.getElementById("cityTools"),
      cityView: document.getElementById("cityView"),
      operationsView: document.getElementById("operationsView"),
      tabButtons: document.querySelectorAll("[data-view]"),
      operationModeOptionButtons: document.querySelectorAll("[data-operation-mode-option]"),
      operationModePickerHint: document.getElementById("operationModePickerHint"),
      runOpsButton: document.getElementById("runOpsButton"),
      prevQuarterButton: document.getElementById("prevQuarterButton"),
      nextQuarterButton: document.getElementById("nextQuarterButton"),
      opsModeBanner: document.getElementById("opsModeBanner"),
      opsModeLabel: document.getElementById("opsModeLabel"),
      opsModeDescription: document.getElementById("opsModeDescription"),
      simSaveSummary: document.getElementById("simSaveSummary"),
      saveSimSlotButton: document.getElementById("saveSimSlotButton"),
      loadSimSlotButton: document.getElementById("loadSimSlotButton"),
      simSaveSlotHint: document.getElementById("simSaveSlotHint"),
      opsModuleButtons: document.querySelectorAll("[data-ops-module]"),
      opsModulePanels: document.querySelectorAll("[data-ops-panel]"),
      financingAffairsCaption: document.getElementById("financingAffairsCaption"),
      financingAffairsStatus: document.getElementById("financingAffairsStatus"),
      financingAffairsRules: document.getElementById("financingAffairsRules"),
      financingAffairsProducts: document.getElementById("financingAffairsProducts"),
      financingAffairsLoans: document.getElementById("financingAffairsLoans"),
      contractAffairsCaption: document.getElementById("contractAffairsCaption"),
      contractAffairsModeBadge: document.getElementById("contractAffairsModeBadge"),
      contractAffairsAlerts: document.getElementById("contractAffairsAlerts"),
      contractAffairsContractButtons: document.querySelectorAll("[data-contract-affairs-contract]"),
      contractAffairsDecisionList: document.getElementById("contractAffairsDecisionList"),
      projectAffairsCaption: document.getElementById("projectAffairsCaption"),
      projectAffairsSlotList: document.getElementById("projectAffairsSlotList"),
      projectAffairsSlotTitle: document.getElementById("projectAffairsSlotTitle"),
      projectAffairsSlotCaption: document.getElementById("projectAffairsSlotCaption"),
      projectAffairsSlotActions: document.getElementById("projectAffairsSlotActions"),
      projectAffairsSlotOverview: document.getElementById("projectAffairsSlotOverview"),
      projectAffairsPlanList: document.getElementById("projectAffairsPlanList"),
      projectAffairsStartedTitle: document.getElementById("projectAffairsStartedTitle"),
      projectAffairsStartedCaption: document.getElementById("projectAffairsStartedCaption"),
      projectAffairsStartedRows: document.getElementById("projectAffairsStartedRows"),
      opsReportButtons: document.querySelectorAll("[data-ops-report-section]"),
      opsReportPanels: document.querySelectorAll("[data-ops-report-panel]"),
      opsBreakdownButtons: document.querySelectorAll("[data-ops-breakdown-section]"),
      trafficCapacityMetricTitle: document.getElementById("trafficCapacityMetricTitle"),
      trafficCapacityMetricCaption: document.getElementById("trafficCapacityMetricCaption"),
      trafficCapacityValueHeader: document.getElementById("trafficCapacityValueHeader"),
      trafficCapacityGrowthHeader: document.getElementById("trafficCapacityGrowthHeader"),
      trafficCapacityMetricChart: document.getElementById("trafficCapacityMetricChart"),
      trafficCapacityNavigator: document.getElementById("trafficCapacityNavigator"),
      trafficCapacityRangeInput: document.getElementById("trafficCapacityRangeInput"),
      trafficCapacityTicks: document.getElementById("trafficCapacityTicks"),
      trafficCapacityWindowHint: document.getElementById("trafficCapacityWindowHint"),
      trafficCapacityWindowLabel: document.getElementById("trafficCapacityWindowLabel"),
      trafficCapacityMetricRows: document.getElementById("trafficCapacityMetricRows"),
      trafficCapacityScopeSelect: document.getElementById("trafficCapacityScopeSelect"),
      serviceQualityMetricButtons: document.querySelectorAll("[data-service-quality-metric]"),
      serviceQualityMetricTitle: document.getElementById("serviceQualityMetricTitle"),
      serviceQualityMetricCaption: document.getElementById("serviceQualityMetricCaption"),
      serviceQualityValueHeader: document.getElementById("serviceQualityValueHeader"),
      serviceQualityGrowthHeader: document.getElementById("serviceQualityGrowthHeader"),
      serviceQualityChartPanel: document.getElementById("serviceQualityChartPanel"),
      serviceQualityMetricChart: document.getElementById("serviceQualityMetricChart"),
      serviceQualityRangeInput: document.getElementById("serviceQualityRangeInput"),
      serviceQualityTicks: document.getElementById("serviceQualityTicks"),
      serviceQualityWindowHint: document.getElementById("serviceQualityWindowHint"),
      serviceQualityWindowLabel: document.getElementById("serviceQualityWindowLabel"),
      serviceQualityMetricTable: document.getElementById("serviceQualityMetricTable"),
      serviceQualityMetricRows: document.getElementById("serviceQualityMetricRows"),
      serviceQualityMaintenanceTable: document.getElementById("serviceQualityMaintenanceTable"),
      serviceQualityMaintenanceCaption: document.getElementById("serviceQualityMaintenanceCaption"),
      serviceQualityMaintenanceRows: document.getElementById("serviceQualityMaintenanceRows"),
      serviceQualityScopeSelect: document.getElementById("serviceQualityScopeSelect"),
      facilitiesProjectMetricButtons: document.querySelectorAll("[data-facilities-project-metric]"),
      facilitiesProjectMetricTitle: document.getElementById("facilitiesProjectMetricTitle"),
      facilitiesProjectMetricCaption: document.getElementById("facilitiesProjectMetricCaption"),
      facilitiesProjectMetricTable: document.getElementById("facilitiesProjectMetricTable"),
      facilitiesProjectHeaderRow: document.getElementById("facilitiesProjectHeaderRow"),
      facilitiesProjectValueHeader: document.getElementById("facilitiesProjectValueHeader"),
      facilitiesProjectGrowthHeader: document.getElementById("facilitiesProjectGrowthHeader"),
      facilitiesProjectMetricChart: document.getElementById("facilitiesProjectMetricChart"),
      facilitiesProjectRangeInput: document.getElementById("facilitiesProjectRangeInput"),
      facilitiesProjectTicks: document.getElementById("facilitiesProjectTicks"),
      facilitiesProjectWindowHint: document.getElementById("facilitiesProjectWindowHint"),
      facilitiesProjectWindowLabel: document.getElementById("facilitiesProjectWindowLabel"),
      facilitiesProjectMetricRows: document.getElementById("facilitiesProjectMetricRows"),
      facilitiesProjectScopeControl: document.getElementById("facilitiesProjectScopeControl"),
      facilitiesProjectScopeSelect: document.getElementById("facilitiesProjectScopeSelect"),
      facilitiesProjectLedgerYearControl: document.getElementById("facilitiesProjectLedgerYearControl"),
      facilitiesProjectLedgerYearSelect: document.getElementById("facilitiesProjectLedgerYearSelect"),
      facilitiesProjectLedgerQuarterControl: document.getElementById("facilitiesProjectLedgerQuarterControl"),
      facilitiesProjectLedgerQuarterSelect: document.getElementById("facilitiesProjectLedgerQuarterSelect"),
      facilitiesProjectLedgerTables: document.getElementById("facilitiesProjectLedgerTables"),
      facilitiesProjectAssetLedgerCaption: document.getElementById("facilitiesProjectAssetLedgerCaption"),
      facilitiesProjectAssetLedgerRows: document.getElementById("facilitiesProjectAssetLedgerRows"),
      facilitiesProjectProjectLedgerCaption: document.getElementById("facilitiesProjectProjectLedgerCaption"),
      facilitiesProjectProjectLedgerRows: document.getElementById("facilitiesProjectProjectLedgerRows"),
      debtFinancingMetricButtons: document.querySelectorAll("[data-debt-financing-metric]"),
      debtFinancingScopeControl: document.getElementById("debtFinancingScopeControl"),
      debtFinancingScopeSelect: document.getElementById("debtFinancingScopeSelect"),
      debtFinancingLedgerYearControl: document.getElementById("debtFinancingLedgerYearControl"),
      debtFinancingLedgerYearSelect: document.getElementById("debtFinancingLedgerYearSelect"),
      debtFinancingLedgerQuarterControl: document.getElementById("debtFinancingLedgerQuarterControl"),
      debtFinancingLedgerQuarterSelect: document.getElementById("debtFinancingLedgerQuarterSelect"),
      debtFinancingEventStartYearControl: document.getElementById("debtFinancingEventStartYearControl"),
      debtFinancingEventStartYearSelect: document.getElementById("debtFinancingEventStartYearSelect"),
      debtFinancingEventStartQuarterControl: document.getElementById("debtFinancingEventStartQuarterControl"),
      debtFinancingEventStartQuarterSelect: document.getElementById("debtFinancingEventStartQuarterSelect"),
      debtFinancingEventEndYearControl: document.getElementById("debtFinancingEventEndYearControl"),
      debtFinancingEventEndYearSelect: document.getElementById("debtFinancingEventEndYearSelect"),
      debtFinancingEventEndQuarterControl: document.getElementById("debtFinancingEventEndQuarterControl"),
      debtFinancingEventEndQuarterSelect: document.getElementById("debtFinancingEventEndQuarterSelect"),
      debtFinancingChartPanel: document.getElementById("debtFinancingChartPanel"),
      debtFinancingMetricTitle: document.getElementById("debtFinancingMetricTitle"),
      debtFinancingMetricCaption: document.getElementById("debtFinancingMetricCaption"),
      debtFinancingMetricChart: document.getElementById("debtFinancingMetricChart"),
      debtFinancingRangeInput: document.getElementById("debtFinancingRangeInput"),
      debtFinancingTicks: document.getElementById("debtFinancingTicks"),
      debtFinancingWindowHint: document.getElementById("debtFinancingWindowHint"),
      debtFinancingWindowLabel: document.getElementById("debtFinancingWindowLabel"),
      debtFinancingHeaderRow: document.getElementById("debtFinancingHeaderRow"),
      debtFinancingMetricRows: document.getElementById("debtFinancingMetricRows"),
      aviationMetricButtons: document.querySelectorAll("[data-aviation-metric]"),
      aviationMetricTitle: document.getElementById("aviationMetricTitle"),
      aviationMetricCaption: document.getElementById("aviationMetricCaption"),
      aviationValueHeader: document.getElementById("aviationValueHeader"),
      aviationGrowthHeader: document.getElementById("aviationGrowthHeader"),
      aviationMetricChart: document.getElementById("aviationMetricChart"),
      aviationRangeInput: document.getElementById("aviationRangeInput"),
      aviationTicks: document.getElementById("aviationTicks"),
      aviationWindowHint: document.getElementById("aviationWindowHint"),
      aviationWindowLabel: document.getElementById("aviationWindowLabel"),
      aviationMetricRows: document.getElementById("aviationMetricRows"),
      aviationScopeSelect: document.getElementById("aviationScopeSelect"),
      foodRetailMetricButtons: document.querySelectorAll("[data-food-retail-metric]"),
      foodRetailMetricTitle: document.getElementById("foodRetailMetricTitle"),
      foodRetailMetricCaption: document.getElementById("foodRetailMetricCaption"),
      foodRetailValueHeader: document.getElementById("foodRetailValueHeader"),
      foodRetailGrowthHeader: document.getElementById("foodRetailGrowthHeader"),
      foodRetailMetricChart: document.getElementById("foodRetailMetricChart"),
      foodRetailRangeInput: document.getElementById("foodRetailRangeInput"),
      foodRetailTicks: document.getElementById("foodRetailTicks"),
      foodRetailWindowHint: document.getElementById("foodRetailWindowHint"),
      foodRetailWindowLabel: document.getElementById("foodRetailWindowLabel"),
      foodRetailMetricRows: document.getElementById("foodRetailMetricRows"),
      foodRetailScopeSelect: document.getElementById("foodRetailScopeSelect"),
      dutyFreeMetricButtons: document.querySelectorAll("[data-duty-free-metric]"),
      dutyFreeMetricTitle: document.getElementById("dutyFreeMetricTitle"),
      dutyFreeMetricCaption: document.getElementById("dutyFreeMetricCaption"),
      dutyFreeValueHeader: document.getElementById("dutyFreeValueHeader"),
      dutyFreeGrowthHeader: document.getElementById("dutyFreeGrowthHeader"),
      dutyFreeMetricChart: document.getElementById("dutyFreeMetricChart"),
      dutyFreeRangeInput: document.getElementById("dutyFreeRangeInput"),
      dutyFreeTicks: document.getElementById("dutyFreeTicks"),
      dutyFreeWindowHint: document.getElementById("dutyFreeWindowHint"),
      dutyFreeWindowLabel: document.getElementById("dutyFreeWindowLabel"),
      dutyFreeMetricRows: document.getElementById("dutyFreeMetricRows"),
      dutyFreeScopeSelect: document.getElementById("dutyFreeScopeSelect"),
      luxuryMetricButtons: document.querySelectorAll("[data-luxury-metric]"),
      luxuryMetricTitle: document.getElementById("luxuryMetricTitle"),
      luxuryMetricCaption: document.getElementById("luxuryMetricCaption"),
      luxuryValueHeader: document.getElementById("luxuryValueHeader"),
      luxuryGrowthHeader: document.getElementById("luxuryGrowthHeader"),
      luxuryMetricChart: document.getElementById("luxuryMetricChart"),
      luxuryRangeInput: document.getElementById("luxuryRangeInput"),
      luxuryTicks: document.getElementById("luxuryTicks"),
      luxuryWindowHint: document.getElementById("luxuryWindowHint"),
      luxuryWindowLabel: document.getElementById("luxuryWindowLabel"),
      luxuryMetricRows: document.getElementById("luxuryMetricRows"),
      luxuryScopeSelect: document.getElementById("luxuryScopeSelect"),
      contractPartnershipMetricButtons: document.querySelectorAll("[data-contract-partnership-metric]"),
      contractPartnershipScopeControl: document.getElementById("contractPartnershipScopeControl"),
      contractPartnershipScopeSelect: document.getElementById("contractPartnershipScopeSelect"),
      contractPartnershipLedgerYearControl: document.getElementById("contractPartnershipLedgerYearControl"),
      contractPartnershipLedgerYearSelect: document.getElementById("contractPartnershipLedgerYearSelect"),
      contractPartnershipLedgerQuarterControl: document.getElementById("contractPartnershipLedgerQuarterControl"),
      contractPartnershipLedgerQuarterSelect: document.getElementById("contractPartnershipLedgerQuarterSelect"),
      contractPartnershipEventStartYearControl: document.getElementById("contractPartnershipEventStartYearControl"),
      contractPartnershipEventStartYearSelect: document.getElementById("contractPartnershipEventStartYearSelect"),
      contractPartnershipEventStartQuarterControl: document.getElementById("contractPartnershipEventStartQuarterControl"),
      contractPartnershipEventStartQuarterSelect: document.getElementById("contractPartnershipEventStartQuarterSelect"),
      contractPartnershipEventEndYearControl: document.getElementById("contractPartnershipEventEndYearControl"),
      contractPartnershipEventEndYearSelect: document.getElementById("contractPartnershipEventEndYearSelect"),
      contractPartnershipEventEndQuarterControl: document.getElementById("contractPartnershipEventEndQuarterControl"),
      contractPartnershipEventEndQuarterSelect: document.getElementById("contractPartnershipEventEndQuarterSelect"),
      contractPartnershipChartPanel: document.getElementById("contractPartnershipChartPanel"),
      contractPartnershipMetricTitle: document.getElementById("contractPartnershipMetricTitle"),
      contractPartnershipMetricCaption: document.getElementById("contractPartnershipMetricCaption"),
      contractPartnershipMetricChart: document.getElementById("contractPartnershipMetricChart"),
      contractPartnershipRangeInput: document.getElementById("contractPartnershipRangeInput"),
      contractPartnershipTicks: document.getElementById("contractPartnershipTicks"),
      contractPartnershipWindowHint: document.getElementById("contractPartnershipWindowHint"),
      contractPartnershipWindowLabel: document.getElementById("contractPartnershipWindowLabel"),
      contractPartnershipHeaderRow: document.getElementById("contractPartnershipHeaderRow"),
      contractPartnershipMetricRows: document.getElementById("contractPartnershipMetricRows"),
      financialMetricButtons: document.querySelectorAll("[data-financial-metric]"),
      opsTitle: document.getElementById("opsTitle"),
      opsCaption: document.getElementById("opsCaption"),
      financialMetricTitle: document.getElementById("financialMetricTitle"),
      financialCashFlowSummary: document.getElementById("financialCashFlowSummary"),
      financialHeaderRow: document.getElementById("financialHeaderRow"),
      netProfitCaption: document.getElementById("netProfitCaption"),
      netProfitChart: document.getElementById("netProfitChart"),
      netProfitNavigator: document.getElementById("netProfitNavigator"),
      netProfitRangeInput: document.getElementById("netProfitRangeInput"),
      netProfitTicks: document.getElementById("netProfitTicks"),
      netProfitWindowHint: document.getElementById("netProfitWindowHint"),
      netProfitWindowLabel: document.getElementById("netProfitWindowLabel"),
      netProfitRows: document.getElementById("netProfitRows"),
      financialScopeSelect: document.getElementById("financialScopeSelect"),
      opsSummaryGrid: document.getElementById("opsSummaryGrid"),
      opsTrafficChart: document.getElementById("opsTrafficChart"),
      opsProfitChart: document.getElementById("opsProfitChart"),
      opsCashChart: document.getElementById("opsCashChart"),
      opsQuarterCaption: document.getElementById("opsQuarterCaption"),
      opsReportGrid: document.getElementById("opsReportGrid"),
      opsRiskCaption: document.getElementById("opsRiskCaption"),
      opsRiskBody: document.getElementById("opsRiskBody"),
      opsComponentRows: document.getElementById("opsComponentRows"),
    };

    const state = window.AirportSeedExplorerState;

    const NET_PROFIT_WINDOW_SIZE = 6;
    const TRAFFIC_CAPACITY_WINDOW_SIZE = 6;
    const SERVICE_QUALITY_WINDOW_SIZE = 6;
    const FACILITIES_PROJECT_WINDOW_SIZE = 6;
    const DEBT_FINANCING_WINDOW_SIZE = 6;
    const AVIATION_WINDOW_SIZE = 6;
    const FOOD_RETAIL_WINDOW_SIZE = 6;
    const DUTY_FREE_WINDOW_SIZE = 6;
    const LUXURY_WINDOW_SIZE = 6;
    const CONTRACT_PARTNERSHIP_WINDOW_SIZE = 6;
    const FACILITY_SIZE_DESIGN_CAPACITY = {
      empty: 0,
      small: 8,
      medium: 16,
      large: 32,
      extra_large: 50,
      giant: 72,
    };
    const FACILITY_SIZE_MAX_CAPACITY = {
      empty: 0,
      small: 12,
      medium: 24,
      large: 45,
      extra_large: 65,
      giant: 90,
    };
    const SERVICE_QUALITY_MAINTENANCE_MODEL = {
      renovationRetentionRatio: 0.55,
      renovationMinimumAgeYears: 5,
      ageScore: {
        maxScore: 6,
        scoreSpan: 18,
        midpointYears: 24,
        softnessYears: 8,
      },
    };
    const CONTRACT_DEFINITIONS = [
      {
        id: "DUTY_FREE_MAIN",
        name: "免税经营合同",
        segment: "免税",
        revenueKey: "dutyFreeRevenue",
        salesKey: "dutyFreeSales",
        guaranteeKey: "dutyFreeMinimumGuarantee",
        shareRevenueKey: "dutyFreeShareRevenue",
        revenueSharePctKey: "dutyFreeRevenueSharePct",
        coveragePctKey: "dutyFreeMinimumGuaranteeCoveragePct",
        basisKey: "dutyFreeRevenueBasis",
        typeKey: "dutyFreeContractType",
        statusKey: "dutyFreeContractStatus",
        cycleKey: "dutyFreeContractCycle",
        cycleStartYearKey: "dutyFreeContractCycleStartYear",
        cycleEndYearKey: "dutyFreeContractCycleEndYear",
        forecastQuarterSalesKey: "dutyFreeContractForecastQuarterSales",
        forecastAnnualSalesKey: "dutyFreeContractForecastAnnualSales",
        historyYearsUsedKey: "dutyFreeContractHistoryYearsUsed",
        trendMultiplierKey: "dutyFreeContractTrendMultiplier",
        macroRiskDiscountMultiplierKey: "dutyFreeContractMacroRiskDiscountMultiplier",
        bargainingPowerMultiplierKey: "dutyFreeContractBargainingPowerMultiplier",
        weightedPassengersKey: "dutyFreeWeightedPassengers",
      },
      {
        id: "LUXURY_RETAIL_MAIN",
        name: "奢侈品零售合同",
        segment: "奢侈品",
        revenueKey: "luxuryRevenue",
        salesKey: "luxurySales",
        guaranteeKey: "luxuryMinimumGuarantee",
        shareRevenueKey: "luxuryShareRevenue",
        revenueSharePctKey: "luxuryRevenueSharePct",
        coveragePctKey: "luxuryMinimumGuaranteeCoveragePct",
        basisKey: "luxuryRevenueBasis",
        typeKey: "luxuryContractType",
        statusKey: "luxuryContractStatus",
        cycleKey: "luxuryContractCycle",
        cycleStartYearKey: "luxuryContractCycleStartYear",
        cycleEndYearKey: "luxuryContractCycleEndYear",
        forecastQuarterSalesKey: "luxuryContractForecastQuarterSales",
        forecastAnnualSalesKey: "luxuryContractForecastAnnualSales",
        historyYearsUsedKey: "luxuryContractHistoryYearsUsed",
        trendMultiplierKey: "luxuryContractTrendMultiplier",
        macroRiskDiscountMultiplierKey: "luxuryContractMacroRiskDiscountMultiplier",
        bargainingPowerMultiplierKey: "luxuryContractBargainingPowerMultiplier",
        weightedPassengersKey: "luxuryWeightedPassengers",
      },
    ];
    const CONTRACT_OVERRIDE_SCHEMA_VERSION = "contract-operation-overrides-v0.1";
    const CONTRACT_OVERRIDE_TAX_RATE_PCT = 25;
    const FACILITIES_PROJECT_DEFAULT_SCOPE_OPTIONS = [
      { value: "latest", label: "最新" },
      { value: "annual", label: "年报" },
      { value: "half", label: "半年报" },
      { value: "q1", label: "一季报" },
      { value: "q3", label: "三季报" },
    ];
    const FACILITY_ASSET_LEDGER_PROJECTS = [
      {
        id: "PEK_SLOT_1_RENOVATION_STANDARD",
        name: "首都T3航站楼翻新工程",
        airport: "北京首都",
        slotId: "PEK_SLOT_1",
        slotRole: "main_slot",
        facilitySize: "extra_large",
        type: "翻新",
        activeIdsKey: "renovationActiveIds",
        completedIdsKey: "renovationCompletedIds",
        capexKey: "renovationCapex",
        cipKey: "renovationConstructionInProgress",
        originalKey: "renovationAssetOriginal",
        accumulatedDepreciationKey: "renovationAssetAccumulatedDepreciation",
        bookKey: "renovationAssetBookValue",
        depreciationKey: "renovationAssetPeriodDepreciation",
        designLossKey: "renovationDesignCapacityLoss",
        maxLossKey: "renovationMaxCapacityLoss",
      },
      {
        id: "PEK_SLOT_2_RENOVATION_2032Q1",
        name: "首都T2航站楼翻新工程",
        airport: "北京首都",
        slotId: "PEK_SLOT_2",
        slotRole: "secondary_slot",
        facilitySize: "large",
        type: "翻新",
        activeIdsKey: "renovationActiveIds",
        completedIdsKey: "renovationCompletedIds",
        capexKey: "renovationCapex",
        cipKey: "renovationConstructionInProgress",
        originalKey: "renovationAssetOriginal",
        accumulatedDepreciationKey: "renovationAssetAccumulatedDepreciation",
        bookKey: "renovationAssetBookValue",
        depreciationKey: "renovationAssetPeriodDepreciation",
        designLossKey: "renovationDesignCapacityLoss",
        maxLossKey: "renovationMaxCapacityLoss",
      },
      {
        id: "PKX_SLOT_1_RENOVATION_STANDARD",
        name: "大兴T1航站楼翻新工程",
        airport: "北京大兴",
        slotId: "PKX_SLOT_1",
        slotRole: "main_slot",
        facilitySize: "giant",
        type: "翻新",
        activeIdsKey: "renovationActiveIds",
        completedIdsKey: "renovationCompletedIds",
        capexKey: "renovationCapex",
        cipKey: "renovationConstructionInProgress",
        originalKey: "renovationAssetOriginal",
        accumulatedDepreciationKey: "renovationAssetAccumulatedDepreciation",
        bookKey: "renovationAssetBookValue",
        depreciationKey: "renovationAssetPeriodDepreciation",
        designLossKey: "renovationDesignCapacityLoss",
        maxLossKey: "renovationMaxCapacityLoss",
      },
      {
        id: "PEK_SLOT_2_REBUILD_2056Q1",
        name: "首都T2航站楼拆除重建工程",
        airport: "北京首都",
        slotId: "PEK_SLOT_2",
        slotRole: "secondary_slot",
        facilitySize: "extra_large",
        type: "拆除重建",
        activeIdsKey: "rebuildActiveIds",
        startedIdsKey: "rebuildStartedIds",
        completedIdsKey: "rebuildCompletedIds",
        capexKey: "rebuildCapex",
        demolitionKey: "rebuildDemolitionExpense",
        writeoffKey: "rebuildOldAssetWriteoff",
        cipKey: "rebuildConstructionInProgress",
        originalKey: "rebuildAssetOriginal",
        accumulatedDepreciationKey: "rebuildAssetAccumulatedDepreciation",
        bookKey: "rebuildAssetBookValue",
        depreciationKey: "rebuildAssetPeriodDepreciation",
        designLossKey: "rebuildDesignCapacityLoss",
        maxLossKey: "rebuildMaxCapacityLoss",
        designDeltaKey: "rebuildCompletedDesignCapacityDelta",
        maxDeltaKey: "rebuildCompletedMaxCapacityDelta",
      },
      {
        id: "PKX_SLOT_2_CONSTRUCTION_2065Q3",
        name: "大兴T2航站楼新建工程",
        airport: "北京大兴",
        slotId: "PKX_SLOT_2",
        slotRole: "secondary_slot",
        facilitySize: "large",
        type: "新建",
        activeIdsKey: "constructionActiveIds",
        completedIdsKey: "constructionCompletedIds",
        capexKey: "constructionCapex",
        cipKey: "constructionInProgress",
        originalKey: "constructionAssetOriginal",
        accumulatedDepreciationKey: "constructionAssetAccumulatedDepreciation",
        bookKey: "constructionAssetBookValue",
        depreciationKey: "constructionAssetPeriodDepreciation",
      },
    ];
    const FACILITY_LEDGER_INITIAL_ASSETS = [
      {
        assetId: "PEK_SLOT_1_T3_INITIAL_ASSET",
        name: "首都T3航站楼",
        airport: "北京首都",
        slotId: "PEK_SLOT_1",
        slotRole: "main_slot",
        facilitySize: "extra_large",
        original: 51000,
        inServiceYear: 2008,
        usefulLifeYears: 40,
        residualValuePct: 10,
      },
      {
        assetId: "PEK_SLOT_2_T2_INITIAL_ASSET",
        name: "首都T2航站楼",
        airport: "北京首都",
        slotId: "PEK_SLOT_2",
        slotRole: "secondary_slot",
        facilitySize: "large",
        original: 28500,
        inServiceYear: 2000,
        usefulLifeYears: 35,
        residualValuePct: 10,
      },
      {
        assetId: "PKX_SLOT_1_T1_INITIAL_ASSET",
        name: "大兴T1航站楼",
        airport: "北京大兴",
        slotId: "PKX_SLOT_1",
        slotRole: "main_slot",
        facilitySize: "giant",
        original: 78750,
        inServiceYear: 2019,
        usefulLifeYears: 45,
        residualValuePct: 10,
      },
    ];
    const PROJECT_AFFAIRS_SLOTS = [
      {
        slotId: "PEK_SLOT_1",
        name: "首都T3航站楼",
        airport: "北京首都",
        slotRole: "main_slot",
        facilitySize: "extra_large",
        kind: "operating",
      },
      {
        slotId: "PEK_SLOT_2",
        name: "首都T2航站楼",
        airport: "北京首都",
        slotRole: "secondary_slot",
        facilitySize: "large",
        kind: "operating",
      },
      {
        slotId: "PEK_SLOT_3",
        name: "空白槽位",
        airport: "北京首都",
        slotRole: "auxiliary_slot",
        facilitySize: "empty",
        kind: "empty",
      },
      {
        slotId: "PEK_SLOT_4",
        name: "空白槽位",
        airport: "北京首都",
        slotRole: "auxiliary_slot",
        facilitySize: "empty",
        kind: "empty",
      },
      {
        slotId: "PEK_SLOT_5",
        name: "空白槽位",
        airport: "北京首都",
        slotRole: "auxiliary_slot",
        facilitySize: "empty",
        kind: "empty",
      },
      {
        slotId: "PKX_SLOT_1",
        name: "大兴T1航站楼",
        airport: "北京大兴",
        slotRole: "main_slot",
        facilitySize: "giant",
        kind: "operating",
      },
      {
        slotId: "PKX_SLOT_2",
        name: "空白槽位",
        airport: "北京大兴",
        slotRole: "secondary_slot",
        facilitySize: "empty",
        kind: "empty",
      },
      {
        slotId: "PKX_SLOT_3",
        name: "空白槽位",
        airport: "北京大兴",
        slotRole: "auxiliary_slot",
        facilitySize: "empty",
        kind: "empty",
      },
      {
        slotId: "PKX_SLOT_4",
        name: "空白槽位",
        airport: "北京大兴",
        slotRole: "auxiliary_slot",
        facilitySize: "empty",
        kind: "empty",
      },
      {
        slotId: "PKX_SLOT_5",
        name: "空白槽位",
        airport: "北京大兴",
        slotRole: "auxiliary_slot",
        facilitySize: "empty",
        kind: "empty",
      },
    ];
    const DEBT_FINANCING_LOANS = [
      {
        id: "BJ_SHORT_BULLET_2030Q1",
        name: "北京短期周转贷款测试",
        type: "short_term",
        startYear: 2030,
        startQuarter: "Q1",
        principal: 5000,
        tenorQuarters: 8,
        repaymentStyle: "bullet_principal",
        graceQuarters: 0,
      },
      {
        id: "BJ_LONG_EQUAL_2056Q1",
        name: "首都机场重建期长期贷款测试",
        type: "long_term",
        startYear: 2056,
        startQuarter: "Q1",
        principal: 30000,
        tenorQuarters: 80,
        repaymentStyle: "equal_principal",
        graceQuarters: 0,
      },
      {
        id: "BJ_LONG_GRACE_EQUAL_2065Q3",
        name: "大兴扩建宽限期长期贷款测试",
        type: "long_term",
        startYear: 2065,
        startQuarter: "Q3",
        principal: 24000,
        tenorQuarters: 60,
        repaymentStyle: "grace_then_equal_principal",
        graceQuarters: 16,
      },
    ];

    function fmt(value, digits = 1) {
      const number = Number(value);
      if (!Number.isFinite(number)) return "-";
      return number.toLocaleString("zh-CN", { maximumFractionDigits: digits, minimumFractionDigits: digits });
    }

    function finiteNumber(value, fallback = 0) {
      const number = Number(value);
      return Number.isFinite(number) ? number : fallback;
    }

    function round4(value) {
      return Math.round(finiteNumber(value) * 10000) / 10000;
    }

    function fmtPassenger(value) {
      return `${fmt(value, 1)} 百万人`;
    }

    function fmtMoney(value) {
      return `${fmt(Number(value) / 100, 1)} 亿元`;
    }

    function fmtPct(value) {
      return `${fmt(value, 1)}%`;
    }

    function fmtPctPoint(value) {
      return `${fmt(value, 1)} 个百分点`;
    }

    function fmtCny(value) {
      return `${fmt(value, 0)} 元`;
    }

    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      }[char]));
    }

    function status(text, kind = "") {
      el.status.className = `status ${kind}`.trim();
      el.status.textContent = text;
    }

    function setLoading(value) {
      state.loading = value;
      el.runButton.disabled = value;
      el.randomButton.disabled = value;
      el.runButton.textContent = value ? "运行中..." : "运行全链路";
    }

    function startTaskProgressPolling(seed, years) {
      let stopped = false;
      let timer = null;
      const poll = async () => {
        try {
          const payload = await apiClient.requestJson(`/api/task-status?seed=${encodeURIComponent(seed)}&years=${encodeURIComponent(years)}`);
          if (!stopped && payload.ok && payload.status === "running") {
            status(`${payload.message}（${payload.progressPct}%）`);
          }
        } catch {
          // Progress is optional; the original synchronous request remains authoritative.
        }
      };
      poll();
      timer = window.setInterval(poll, 500);
      return () => {
        stopped = true;
        if (timer !== null) window.clearInterval(timer);
      };
    }

    function bottleneckLabel(value) {
      if (value === "airline_bottleneck") return "航司供给";
      if (value === "airline_supply_limited") return "航司供给";
      if (value === "airport_bottleneck") return "机场容量";
      if (value === "airport_capacity_limited") return "机场容量";
      if (value === "dual_airline_airport_bottleneck") return "航司 + 机场";
      if (value === "demand_limited") return "潜在需求";
      return value || "-";
    }

    function phaseLabel(value) {
      if (value === "startup_operating_history") return "自动历史期";
      if (value === "player_operation") return "玩家运营期";
      return value || "-";
    }

    function operationModeLabel(mode) {
      if (mode === "simulate_default") return "模拟运营";
      if (mode === "replay") return "加载历史";
      return "尚未选择模式";
    }

    function operationModeDescription(mode) {
      if (mode === "simulate_default") {
        return "以当前 seed 的外部世界和默认初始配置进入服务端季度沙盘；合同动作写入本局行动日志。";
      }
      if (mode === "replay") {
        return "读取已经跑好的历史结果，包含测试贷款、测试项目和自动合同续期。";
      }
      return "左侧选择加载历史或模拟运营，然后点击运营。";
    }

    function operationCacheLabel(operations) {
      const mode = operations?.mode || "replay";
      if (mode === "simulate_default") {
        return "服务端行动日志";
      }
      return operations?.cached ? "读取回放结果" : "新运行回放";
    }

    function setOperationModeVisual(mode) {
      const cleanMode = mode || "";
      el.operationsView.setAttribute("data-ops-mode", cleanMode || "none");
      el.opsModeBanner.className = `ops-mode-banner ${cleanMode === "simulate_default" ? "simulation" : cleanMode === "replay" ? "replay" : ""}`.trim();
      el.opsModeLabel.textContent = operationModeLabel(cleanMode);
      el.opsModeDescription.textContent = operationModeDescription(cleanMode);
      el.runOpsButton.className = `${cleanMode || state.selectedOperationMode || "replay"} ${cleanMode ? "active" : ""}`.trim();
      el.runOpsButton.textContent = "运营";
    }

    function setSelectedOperationMode(mode) {
      const cleanMode = mode === "simulate_default" ? "simulate_default" : "replay";
      state.selectedOperationMode = cleanMode;
      el.operationModeOptionButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-operation-mode-option") === cleanMode));
      });
      el.operationModePickerHint.textContent = operationModeDescription(cleanMode);
      if (!state.operations) {
        setOperationModeVisual(cleanMode);
      } else if (state.operationMode !== cleanMode) {
        el.runOpsButton.className = cleanMode;
      }
    }

    function renderSimSaveSlots() {
      const summary = state.simSaveSummary;
      const canSave = Boolean(state.operations && state.operations.mode === "simulate_default");
      const canLoad = Boolean(summary?.occupied);
      el.saveSimSlotButton.disabled = !canSave;
      el.loadSimSlotButton.disabled = !canLoad;
      el.simSaveSummary.textContent = summary?.occupied
        ? `当前 seed 存档：${summary.currentLabel || "-"} / ${summary.savedAt || "-"}`
        : "当前 seed 存档：空";
      el.simSaveSlotHint.textContent = summary?.occupied
        ? `绑定 seed ${summary.seed} / ${summary.years} 年，${summary.playerActionCount || 0} 个玩家动作；报表由服务端重算。`
        : "存档绑定当前 seed；模拟运营加载后可保存当前季度。";
    }

    async function refreshSimSaveSlots(silent = true) {
      try {
        const payload = await apiClient.requestJson("/api/sim-save", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            action: "status",
            seed: Number(el.seedInput.value),
            years: Number(el.yearsInput.value || 60),
          }),
        });
        if (!payload.ok) throw new Error(payload.error || "save status failed");
        state.simSaveSummary = payload.summary || null;
        renderSimSaveSlots();
      } catch (error) {
        state.simSaveSummary = null;
        renderSimSaveSlots();
        const message = String(error.message || error);
        if (!silent) status(message === "not found" ? "当前动态测试服务没有存档接口，请重启服务。" : message, "error");
      }
    }

    function setOpsLoading(value, mode = "") {
      el.runOpsButton.disabled = value;
      el.saveSimSlotButton.disabled = true;
      el.loadSimSlotButton.disabled = true;
      el.runOpsButton.textContent = value
        ? (mode === "simulate_default" ? "模拟中..." : "加载中...")
        : "运营";
      if (value) {
        el.prevQuarterButton.disabled = true;
        el.nextQuarterButton.disabled = true;
      } else {
        el.runOpsButton.disabled = false;
        renderOperations();
        renderSimSaveSlots();
      }
    }

    function resetLoadedData() {
      state.data = null;
      state.operations = null;
      state.operationMode = null;
      state.operationsQuarterIndex = null;
      state.contractSignatures = {};
      state.playerActions = [];
      state.operationOverrides = {};
      state.projectAffairsSlotId = "PEK_SLOT_1";
      state.projectAffairsRenamingSlotId = null;
      state.projectRebuildTargetByTemplate = {};
      state.projectConstructionTargetByTemplate = {};
      state.simSaveSummary = null;
      state.netProfitWindowStart = null;
      state.netProfitWindowPinnedToLatest = true;
      state.trafficCapacityWindowStart = null;
      state.trafficCapacityWindowPinnedToLatest = true;
      state.serviceQualityWindowStart = null;
      state.serviceQualityWindowPinnedToLatest = true;
      state.facilitiesProjectLedgerYear = "latest";
      state.facilitiesProjectLedgerQuarter = "latest";
      state.facilitiesProjectWindowStart = null;
      state.facilitiesProjectWindowPinnedToLatest = true;
      state.debtFinancingWindowStart = null;
      state.debtFinancingWindowPinnedToLatest = true;
      state.debtFinancingLedgerYear = "latest";
      state.debtFinancingLedgerQuarter = "latest";
      state.debtFinancingEventStartYear = "earliest";
      state.debtFinancingEventStartQuarter = "q1";
      state.debtFinancingEventEndYear = "latest";
      state.debtFinancingEventEndQuarter = "latest";
      state.aviationWindowStart = null;
      state.aviationWindowPinnedToLatest = true;
      state.foodRetailWindowStart = null;
      state.foodRetailWindowPinnedToLatest = true;
      state.dutyFreeWindowStart = null;
      state.dutyFreeWindowPinnedToLatest = true;
      state.luxuryWindowStart = null;
      state.luxuryWindowPinnedToLatest = true;
      state.contractPartnershipWindowStart = null;
      state.contractPartnershipWindowPinnedToLatest = true;
      state.contractPartnershipLedgerYear = "latest";
      state.contractPartnershipLedgerQuarter = "latest";
      state.contractPartnershipEventStartYear = "earliest";
      state.contractPartnershipEventStartQuarter = "q1";
      state.contractPartnershipEventEndYear = "latest";
      state.contractPartnershipEventEndQuarter = "latest";
      state.selectedCityId = null;
      render();
      renderOperations();
      refreshSimSaveSlots();
    }

    function cacheOptionLabel(run) {
      const cityPart = run.cityCount ? ` / ${run.cityCount}城` : "";
      const timePart = run.lastWriteTime ? ` / ${run.lastWriteTime}` : "";
      const operationsPart = Number(run.years) < PLAYER_SIMULATION_MIN_YEARS
        ? ` / 运营自动扩至${PLAYER_SIMULATION_MIN_YEARS}年`
        : "";
      return `seed ${run.seed} / ${run.years}年${cityPart}${operationsPart}${timePart}`;
    }

    function renderCachedRuns() {
      if (!state.cachedRuns.length) {
        el.cachedRunSelect.innerHTML = `<option value="">暂无缓存</option>`;
        return;
      }
      const currentRunId = state.data?.runId || state.operations?.runId || "";
      el.cachedRunSelect.innerHTML = [
        `<option value="">选择已有缓存...</option>`,
        ...state.cachedRuns.map((run) => {
          const selected = run.runId === currentRunId ? " selected" : "";
          return `<option value="${escapeHtml(run.runId)}"${selected}>${escapeHtml(cacheOptionLabel(run))}</option>`;
        }),
      ].join("");
    }

    async function refreshCachedRuns(silent = true) {
      try {
        const payload = await apiClient.requestJson("/api/cached-runs");
        if (!payload.ok) throw new Error(payload.error || "cached run list failed");
        state.cachedRuns = payload.runs || [];
        renderCachedRuns();
      } catch (error) {
        el.cachedRunSelect.innerHTML = `<option value="">缓存列表读取失败</option>`;
        if (!silent) status(String(error.message || error), "error");
      }
    }

    function applyCachedRun(runId) {
      const run = state.cachedRuns.find((item) => item.runId === runId);
      if (!run) return;
      el.seedInput.value = String(run.seed);
      el.yearsInput.value = String(run.years || 60);
      el.forceInput.checked = false;
      resetLoadedData();
      const shortRunNote = Number(run.years) < PLAYER_SIMULATION_MIN_YEARS
        ? `这是短期分析缓存；进入模拟运营时会自动扩展为 ${PLAYER_SIMULATION_MIN_YEARS} 年完整世界线。`
        : "点击运行或运营读取结果。";
      status(`已选择缓存：seed ${run.seed} / ${run.years || 60} 年。${shortRunNote}`, "ok");
    }

    function setOpsModule(module) {
      state.opsModule = module;
      el.opsModuleButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-ops-module") === module));
      });
      el.opsModulePanels.forEach((panel) => {
        panel.classList.toggle("active", panel.getAttribute("data-ops-panel") === module);
      });
      if (module === "contractAffairs") {
        renderContractAffairs();
      } else if (module === "projectAffairs") {
        renderProjectAffairs();
      } else if (module === "financingAffairs") {
        renderFinancingAffairs();
      }
    }

    function setContractAffairsContract(contractId) {
      const fallbackId = CONTRACT_DEFINITIONS[0]?.id || "";
      state.contractAffairsContractId = contractById(contractId) ? contractId : fallbackId;
      el.contractAffairsContractButtons.forEach((button) => {
        button.setAttribute(
          "aria-selected",
          String(button.getAttribute("data-contract-affairs-contract") === state.contractAffairsContractId),
        );
      });
      renderContractAffairs();
    }

    function setOpsReportSection(section) {
      state.opsReportSection = section;
      el.opsReportButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-ops-report-section") === section));
      });
      el.opsReportPanels.forEach((panel) => {
        panel.classList.toggle("active", panel.getAttribute("data-ops-report-panel") === section);
      });
      if (section === "trafficCapacity") {
        setOpsBreakdownSection(state.opsBreakdownSection);
      }
      if (section === "serviceQuality") {
        setServiceQualityMetric(state.serviceQualityMetric);
      }
      if (section === "facilitiesProject") {
        setFacilitiesProjectMetric(state.facilitiesProjectMetric);
      }
      if (section === "debtFinancing") {
        setDebtFinancingMetric(state.debtFinancingMetric);
      }
      if (section === "aviationBusiness") {
        setAviationMetric(state.aviationMetric);
      }
      if (section === "foodRetailBusiness") {
        setFoodRetailMetric(state.foodRetailMetric);
      }
      if (section === "dutyFreeBusiness") {
        setDutyFreeMetric(state.dutyFreeMetric);
      }
      if (section === "luxuryBusiness") {
        setLuxuryMetric(state.luxuryMetric);
      }
      if (section === "contractPartnership") {
        setContractPartnershipMetric(state.contractPartnershipMetric);
      }
    }

    function setOpsBreakdownSection(section) {
      state.opsBreakdownSection = section || "potentialTraffic";
      state.trafficCapacityWindowStart = null;
      state.trafficCapacityWindowPinnedToLatest = true;
      el.opsBreakdownButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-ops-breakdown-section") === state.opsBreakdownSection));
      });
      renderTrafficCapacityAnalysis();
    }

    function setServiceQualityMetric(metric) {
      state.serviceQualityMetric = metric || "qualityIndex";
      state.serviceQualityWindowStart = null;
      state.serviceQualityWindowPinnedToLatest = true;
      el.serviceQualityMetricButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-service-quality-metric") === state.serviceQualityMetric));
      });
      renderServiceQualityAnalysis();
    }

    function setFacilitiesProjectMetric(metric) {
      state.facilitiesProjectMetric = metric || "designCapacityChange";
      const config = facilitiesProjectMetricConfig(state.facilitiesProjectMetric);
      const ledgerScopeSelected = ["current", "year"].includes(state.facilitiesProjectReportScope);
      if (!config.ledgerOnly && ledgerScopeSelected) {
        state.facilitiesProjectReportScope = "latest";
      }
      state.facilitiesProjectWindowStart = null;
      state.facilitiesProjectWindowPinnedToLatest = true;
      el.facilitiesProjectMetricButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-facilities-project-metric") === state.facilitiesProjectMetric));
      });
      renderFacilitiesProjectAnalysis();
    }

    function setDebtFinancingMetric(metric) {
      state.debtFinancingMetric = metric || "loanLedger";
      state.debtFinancingWindowStart = null;
      state.debtFinancingWindowPinnedToLatest = true;
      el.debtFinancingMetricButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-debt-financing-metric") === state.debtFinancingMetric));
      });
      renderDebtFinancingAnalysis();
    }

    function setAviationMetric(metric) {
      state.aviationMetric = metric || "aviationRevenue";
      state.aviationWindowStart = null;
      state.aviationWindowPinnedToLatest = true;
      el.aviationMetricButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-aviation-metric") === state.aviationMetric));
      });
      renderAviationBusinessAnalysis();
    }

    function setFoodRetailMetric(metric) {
      state.foodRetailMetric = metric || "foodRetailRevenue";
      state.foodRetailWindowStart = null;
      state.foodRetailWindowPinnedToLatest = true;
      el.foodRetailMetricButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-food-retail-metric") === state.foodRetailMetric));
      });
      renderFoodRetailBusinessAnalysis();
    }

    function setDutyFreeMetric(metric) {
      state.dutyFreeMetric = metric || "dutyFreeRevenue";
      state.dutyFreeWindowStart = null;
      state.dutyFreeWindowPinnedToLatest = true;
      el.dutyFreeMetricButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-duty-free-metric") === state.dutyFreeMetric));
      });
      renderDutyFreeBusinessAnalysis();
    }

    function setLuxuryMetric(metric) {
      state.luxuryMetric = metric || "luxuryRevenue";
      state.luxuryWindowStart = null;
      state.luxuryWindowPinnedToLatest = true;
      el.luxuryMetricButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-luxury-metric") === state.luxuryMetric));
      });
      renderLuxuryBusinessAnalysis();
    }

    function setContractPartnershipMetric(metric) {
      state.contractPartnershipMetric = metric || "contractLedger";
      state.contractPartnershipWindowStart = null;
      state.contractPartnershipWindowPinnedToLatest = true;
      el.contractPartnershipMetricButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-contract-partnership-metric") === state.contractPartnershipMetric));
      });
      renderContractPartnershipAnalysis();
    }

    function setView(view) {
      state.view = view;
      el.cityView.classList.toggle("active", view === "city");
      el.operationsView.classList.toggle("active", view === "operations");
      el.cityTools.hidden = view !== "city";
      el.tabButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-view") === view));
      });
      if (view === "operations") {
        setOpsModule(state.opsModule);
        setOpsReportSection(state.opsReportSection);
        renderOperations();
      } else {
        render();
      }
    }

    function currentOperationQuarter() {
      if (!state.operations || !state.operations.quarters.length) return null;
      const minIndex = state.operations.playerStartIndex ?? 0;
      const index = Math.min(
        Math.max(minIndex, state.operationsQuarterIndex ?? minIndex),
        state.operations.quarters.length - 1,
      );
      state.operationsQuarterIndex = index;
      return state.operations.quarters[index];
    }
