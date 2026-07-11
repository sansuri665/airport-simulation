    function makeStat(label, value, sub = "", className = "") {
      return `<article class="stat"><span>${label}</span><strong class="${className}">${value}</strong>${sub ? `<small>${sub}</small>` : ""}</article>`;
    }

    function renderSummary(data) {
      const first = data[0];
      const latest = data[data.length - 1];
      const selected = data.find((row) => row.year === state.selectedYear) || first;
      const latestBalance = balanceValues(latest);
      el.summaryGrid.innerHTML = [
        makeStat("当前 seed", String(state.seed), `${data.length} 年，${rowsForSeed().length} 个季度`),
        makeStat("当前阶段", gamePhaseLabel(selected.gamePhase), `${selected.year} / ${selected.dutyFreeContractCycle}`),
        makeStat("首年客流", fmtPassenger(first.passengers), `${first.year}`),
        makeStat("末年客流", fmtPassenger(latest.passengers), `${latest.year}`),
        makeStat(
          "末年航司供给",
          fmtPassenger(latest.airlineSupply),
          `满足率 ${fmtPct(latest.airlineSupplyFulfillment)} / 缺口 ${fmtPassengerShort(latest.airlineSupplyGap)}`
        ),
        makeStat("首年经营结果", fmtBillion(first.profit), `经营利润率 ${fmtPct(first.margin)}`, first.profit >= 0 ? "positive" : "danger"),
        makeStat("末年经营结果", fmtBillion(latest.profit), `经营利润率 ${fmtPct(latest.margin)}`, latest.profit >= 0 ? "positive" : "danger"),
        makeStat(
          "末年最大客流使用率",
          fmtPct(latest.maxQuarterMaxUtilization),
          `设计 ${fmtPct(latest.maxQuarterDesignUtilization)} / ${bottleneckLabel(latest.bottleneck)}`,
          toneClass(latest.maxQuarterMaxUtilization, 90, 100)
        ),
        makeStat(
          "末年感知品质",
          latest.qualityIndex.toFixed(1),
          `商业乘数 自营 ${latest.foodRetailQualityMultiplier.toFixed(3)} / 免税 ${latest.dutyFreeQualityMultiplier.toFixed(3)} / 奢侈品 ${latest.luxuryQualityMultiplier.toFixed(3)}`,
          latest.qualityIndex >= 100 ? "positive" : "warning"
        ),
        makeStat(
          "末年总资产",
          fmtBillion(latestBalance.totalAssets),
          `现金 ${fmtBillion(latestBalance.endCash)} / 负债 ${fmtBillion(latestBalance.totalLiabilities)}`,
          Math.abs(latestBalance.balanceCheck) < 0.01 ? "positive" : "warning"
        ),
      ].join("");
    }

    function q(row, quarter) {
      return row.quarters[quarter] || {};
    }

    function profitClass(value) {
      return num(value) >= 0 ? "positive" : "danger";
    }

    function aeronauticalValues(row) {
      if (state.financeScope === "annual") {
        const totalCost = row.fixedCost + row.passengerCost + row.congestion;
        return {
          revenue: row.aero,
          fixedCost: row.fixedCost,
          passengerCost: row.passengerCost,
          congestionCost: row.congestion,
          totalCost,
          result: row.aero - totalCost,
        };
      }
      const quarter = q(row, state.financeScope);
      const revenue = num(quarter.aeronautical_revenue_million_cny);
      const fixedCost = num(quarter.quarter_slot_fixed_operating_cost_million_cny);
      const passengerCost = num(quarter.quarter_passenger_variable_cost_million_cny);
      const congestionCost = num(quarter.quarter_congestion_cost_million_cny);
      const totalCost = fixedCost + passengerCost + congestionCost;
      return {
        revenue,
        fixedCost,
        passengerCost,
        congestionCost,
        totalCost,
        result: revenue - totalCost,
      };
    }

    function commercialValues(row) {
      if (state.financeScope === "annual") {
        return {
          selfRevenue: row.foodRetail,
          dutyFreeRevenue: row.dutyFreeContract,
          luxuryRevenue: row.luxuryContract,
          contractRevenue: row.contractCommercial,
          fixedCost: row.foodRetailFixedCost,
          passengerServiceCost: row.foodRetailPassengerCost,
          salesCost: row.foodRetailSalesCost,
          foodRetailOperatingCost: row.foodRetailOperatingCost,
          foodRetailResult: row.foodRetailProfit,
          dutyFreeWeightedPassengers: row.dutyFreeWeightedPassengers,
          dutyFreeSales: row.dutyFreeSales,
          dutyFreeGuarantee: row.dutyFreeGuarantee,
          dutyFreeShareRevenue: row.dutyFreeShareRevenue,
          dutyFreeForecastSales: row.dutyFreeForecastSales,
          dutyFreeContractBasis: row.dutyFreeContractBasis,
          dutyFreeContractCycle: row.dutyFreeContractCycle,
          dutyFreeContractStatus: row.dutyFreeContractStatus,
          luxuryWeightedPassengers: row.luxuryWeightedPassengers,
          luxurySales: row.luxurySales,
          luxuryGuarantee: row.luxuryGuarantee,
          luxuryShareRevenue: row.luxuryShareRevenue,
          luxuryForecastSales: row.luxuryForecastSales,
          luxuryContractBasis: row.luxuryContractBasis,
          luxuryContractCycle: row.luxuryContractCycle,
          luxuryContractStatus: row.luxuryContractStatus,
          qualityIndex: row.qualityIndex,
          qualitySizeScore: row.qualitySizeScore,
          qualityAgeScore: row.qualityAgeScore,
          qualityCapacityScore: row.qualityCapacityScore,
          qualityDisruptionScore: row.qualityDisruptionScore,
          foodRetailQualityMultiplier: row.foodRetailQualityMultiplier,
          dutyFreeQualityMultiplier: row.dutyFreeQualityMultiplier,
          luxuryQualityMultiplier: row.luxuryQualityMultiplier,
          directCost: row.commercialDirectCost,
          totalRevenue: row.commercial,
          result: row.commercialProfit,
          marginPct: row.commercial ? row.commercialProfit / row.commercial * 100 : 0,
        };
      }
      const quarter = q(row, state.financeScope);
      const selfRevenue = num(quarter.food_retail_revenue_million_cny);
      const dutyFreeRevenue = num(quarter.duty_free_revenue_million_cny);
      const luxuryRevenue = num(quarter.luxury_retail_revenue_million_cny);
      const contractRevenue = num(
        quarter.contract_commercial_revenue_million_cny,
        dutyFreeRevenue + luxuryRevenue
      );
      const fixedCost = num(quarter.food_retail_fixed_operating_cost_million_cny);
      const passengerServiceCost = num(quarter.food_retail_passenger_service_cost_million_cny);
      const salesCost = num(quarter.food_retail_sales_cost_million_cny);
      const foodRetailOperatingCost = num(
        quarter.food_retail_operating_cost_million_cny,
        salesCost + fixedCost + passengerServiceCost
      );
      const foodRetailResult = num(
        quarter.food_retail_operating_profit_million_cny,
        selfRevenue - foodRetailOperatingCost
      );
      const dutyFreeWeightedPassengers = num(quarter.duty_free_weighted_passengers_million);
      const dutyFreeSales = num(quarter.duty_free_sales_million_cny);
      const dutyFreeGuarantee = num(quarter.duty_free_contract_minimum_guarantee_million_cny);
      const dutyFreeShareRevenue = num(quarter.duty_free_contract_share_revenue_million_cny);
      const dutyFreeForecastSales = num(quarter.duty_free_contract_forecast_quarter_sales_million_cny);
      const luxuryWeightedPassengers = num(quarter.luxury_weighted_passengers_million);
      const luxurySales = num(quarter.luxury_sales_million_cny);
      const luxuryGuarantee = num(quarter.luxury_contract_minimum_guarantee_million_cny);
      const luxuryShareRevenue = num(quarter.luxury_contract_share_revenue_million_cny);
      const luxuryForecastSales = num(quarter.luxury_contract_forecast_quarter_sales_million_cny);
      const qualityIndex = num(quarter.city_airport_perceived_quality_index, 100);
      const directCost = num(
        quarter.commercial_direct_cost_million_cny,
        salesCost + fixedCost + passengerServiceCost
      );
      const totalRevenue = num(quarter.commercial_revenue_million_cny, selfRevenue + contractRevenue);
      return {
        selfRevenue,
        dutyFreeRevenue,
        luxuryRevenue,
        contractRevenue,
        fixedCost,
        passengerServiceCost,
        salesCost,
        foodRetailOperatingCost,
        foodRetailResult,
        dutyFreeWeightedPassengers,
        dutyFreeSales,
        dutyFreeGuarantee,
        dutyFreeShareRevenue,
        dutyFreeForecastSales,
        dutyFreeContractBasis: quarter.duty_free_contract_revenue_basis || "-",
        dutyFreeContractCycle: quarter.duty_free_contract_cycle_id || "-",
        dutyFreeContractStatus: quarter.duty_free_contract_status || "-",
        luxuryWeightedPassengers,
        luxurySales,
        luxuryGuarantee,
        luxuryShareRevenue,
        luxuryForecastSales,
        luxuryContractBasis: quarter.luxury_contract_revenue_basis || "-",
        luxuryContractCycle: quarter.luxury_contract_cycle_id || "-",
        luxuryContractStatus: quarter.luxury_contract_status || "-",
        qualityIndex,
        qualitySizeScore: num(quarter.perceived_quality_size_score),
        qualityAgeScore: num(quarter.perceived_quality_age_score),
        qualityCapacityScore: num(quarter.perceived_quality_capacity_score),
        qualityDisruptionScore: num(quarter.perceived_quality_construction_disruption_score),
        foodRetailQualityMultiplier: num(quarter.food_retail_perceived_quality_revenue_multiplier, 1),
        dutyFreeQualityMultiplier: num(quarter.duty_free_perceived_quality_sales_multiplier, 1),
        luxuryQualityMultiplier: num(quarter.luxury_perceived_quality_sales_multiplier, 1),
        directCost,
        totalRevenue,
        result: num(quarter.commercial_operating_profit_million_cny, totalRevenue - directCost),
        marginPct: totalRevenue ? num(quarter.commercial_operating_profit_million_cny, totalRevenue - directCost) / totalRevenue * 100 : 0,
      };
    }

    function financeValue(row, key) {
      if (state.financeSide === "aeronautical") {
        const values = aeronauticalValues(row);
        if (key === "revenue") return values.revenue;
        if (key === "fixedCost") return values.fixedCost;
        if (key === "passengerCost") return values.passengerCost;
        if (key === "congestionCost") return values.congestionCost;
        if (key === "cost") return values.totalCost;
        return values.result;
      }
      if (state.financeSide === "commercial") {
        const values = commercialValues(row);
        if (key === "selfRevenue") return values.selfRevenue;
        if (key === "dutyFreeRevenue") return values.dutyFreeRevenue;
        if (key === "luxuryRevenue") return values.luxuryRevenue;
        if (key === "contractRevenue") return values.contractRevenue;
        if (key === "fixedCost") return values.fixedCost;
        if (key === "passengerServiceCost") return values.passengerServiceCost;
        if (key === "salesCost") return values.salesCost;
        if (key === "cost") return values.directCost;
        if (key === "revenue") return values.totalRevenue;
        return values.result;
      }
      if (state.financeScope === "annual") {
        if (key === "revenue") return row.revenue;
        if (key === "cost") return row.cost;
        return row.profit;
      }
      const quarter = q(row, state.financeScope);
      if (key === "revenue") return num(quarter.total_operating_revenue_million_cny);
      if (key === "cost") return num(quarter.total_operating_cost_million_cny);
      return num(quarter.quarter_operating_profit_million_cny);
    }

    function financeScopeLabel() {
      return state.financeScope === "annual" ? "全年" : state.financeScope;
    }

    function selectedQuarterNumber() {
      if (state.financeScope === "annual") return 4;
      return num(String(state.financeScope).replace("Q", ""), 1);
    }

    function operatingProfitValue(row) {
      if (state.financeScope === "annual") return row.profit;
      return num(q(row, state.financeScope).quarter_operating_profit_million_cny);
    }

    function slotAssetValue(asset, year) {
      const original = num(asset.assetOriginalMillionCny);
      const usefulLife = num(asset.usefulLifeYears);
      if (!original || !usefulLife || !asset.inServiceYear) {
        return {
          ...asset,
          residualFloor: 0,
          annualDepreciation: 0,
          periodDepreciation: 0,
          accumulatedDepreciation: 0,
          bookValue: 0,
          remainingLifeYears: 0,
        };
      }
      const residualFloor = original * num(asset.residualValuePct) / 100;
      const annualDepreciation = (original - residualFloor) / usefulLife;
      const elapsedBeforeYear = Math.min(Math.max(year - asset.inServiceYear, 0), usefulLife);
      const depreciatesThisYear = year >= asset.inServiceYear && year < asset.inServiceYear + usefulLife;
      const quarterNumber = selectedQuarterNumber();
      const elapsedAtPeriodEnd = state.financeScope === "annual"
        ? Math.min(elapsedBeforeYear + (depreciatesThisYear ? 1 : 0), usefulLife)
        : Math.min(elapsedBeforeYear + (depreciatesThisYear ? quarterNumber / 4 : 0), usefulLife);
      const periodDepreciation = depreciatesThisYear
        ? annualDepreciation * (state.financeScope === "annual" ? 1 : 0.25)
        : 0;
      const accumulatedDepreciation = annualDepreciation * elapsedAtPeriodEnd;
      const bookValue = Math.max(original - accumulatedDepreciation, residualFloor);
      return {
        ...asset,
        residualFloor,
        annualDepreciation,
        periodDepreciation,
        accumulatedDepreciation,
        bookValue,
        remainingLifeYears: Math.max(usefulLife - elapsedAtPeriodEnd, 0),
      };
    }

    function assetSlotsForYear(year) {
      return SLOT_ASSETS.map((asset) => slotAssetValue(asset, year));
    }

    function renovationAssetSlot(row) {
      const source = state.financeScope === "annual" ? row : q(row, state.financeScope);
      const original = state.financeScope === "annual"
        ? num(row.renovationAssetOriginal)
        : num(source.renovation_asset_original_million_cny);
      const residualFloor = state.financeScope === "annual"
        ? num(row.renovationAssetResidualFloor)
        : num(source.renovation_asset_residual_floor_million_cny);
      const accumulatedDepreciation = state.financeScope === "annual"
        ? num(row.renovationAssetAccumulatedDepreciation)
        : num(source.renovation_asset_accumulated_depreciation_million_cny);
      const bookValue = state.financeScope === "annual"
        ? num(row.renovationAssetBookValue)
        : num(source.renovation_asset_book_value_million_cny);
      const periodDepreciation = state.financeScope === "annual"
        ? num(row.renovationAssetPeriodDepreciation)
        : num(source.renovation_asset_period_depreciation_million_cny);
      const constructionInProgress = state.financeScope === "annual"
        ? num(row.renovationConstructionInProgress)
        : num(source.renovation_construction_in_progress_million_cny);
      const activeIds = state.financeScope === "annual"
        ? row.renovationActiveEventIds
        : source.renovation_active_event_ids;
      const completedIds = state.financeScope === "annual"
        ? row.renovationCompletedEventIds
        : source.renovation_completed_event_ids;
      const inServicePeriods = state.financeScope === "annual"
        ? row.renovationAssetInServicePeriods
        : source.renovation_asset_in_service_periods;
      if (!original && !bookValue && !constructionInProgress && !activeIds && !completedIds) {
        return null;
      }
      if (!original && constructionInProgress) {
        return {
          airportName: "北京首都",
          slotName: "首都T2航站楼翻新在建工程",
          facilitySize: "large renovation",
          inServiceYear: "施工中",
          assetOriginalMillionCny: constructionInProgress,
          residualFloor: 0,
          accumulatedDepreciation: 0,
          bookValue: constructionInProgress,
          periodDepreciation: 0,
          remainingLifeYears: "-",
        };
      }
      return {
        airportName: "北京首都",
        slotName: "首都T2航站楼翻新资产",
        facilitySize: "large renovation",
        inServiceYear: String(inServicePeriods || "-").split(";")[0],
        assetOriginalMillionCny: original,
        residualFloor,
        accumulatedDepreciation,
        bookValue,
        periodDepreciation,
        remainingLifeYears: "-",
      };
    }

    function constructionAssetSlot(row) {
      const source = state.financeScope === "annual" ? row : q(row, state.financeScope);
      const original = state.financeScope === "annual"
        ? num(row.constructionAssetOriginal)
        : num(source.construction_asset_original_million_cny);
      const residualFloor = state.financeScope === "annual"
        ? num(row.constructionAssetResidualFloor)
        : num(source.construction_asset_residual_floor_million_cny);
      const accumulatedDepreciation = state.financeScope === "annual"
        ? num(row.constructionAssetAccumulatedDepreciation)
        : num(source.construction_asset_accumulated_depreciation_million_cny);
      const bookValue = state.financeScope === "annual"
        ? num(row.constructionAssetBookValue)
        : num(source.construction_asset_book_value_million_cny);
      const periodDepreciation = state.financeScope === "annual"
        ? num(row.constructionAssetPeriodDepreciation)
        : num(source.construction_asset_period_depreciation_million_cny);
      const constructionInProgress = state.financeScope === "annual"
        ? num(row.constructionInProgress)
        : num(source.construction_in_progress_million_cny);
      const activeIds = state.financeScope === "annual"
        ? row.constructionActiveEventIds
        : source.construction_active_event_ids;
      const completedIds = state.financeScope === "annual"
        ? row.constructionCompletedEventIds
        : source.construction_completed_event_ids;
      const inServicePeriods = state.financeScope === "annual"
        ? row.constructionAssetInServicePeriods
        : source.construction_asset_in_service_periods;
      if (!original && !bookValue && !constructionInProgress && !activeIds && !completedIds) {
        return null;
      }
      if (!original && constructionInProgress) {
        return {
          airportName: "北京大兴",
          slotName: "大兴T2航站楼在建工程",
          facilitySize: "large construction",
          inServiceYear: "施工中",
          assetOriginalMillionCny: constructionInProgress,
          residualFloor: 0,
          accumulatedDepreciation: 0,
          bookValue: constructionInProgress,
          periodDepreciation: 0,
          remainingLifeYears: "-",
        };
      }
      return {
        airportName: "北京大兴",
        slotName: "大兴T2航站楼资产",
        facilitySize: "large construction",
        inServiceYear: String(inServicePeriods || "-").split(";")[0],
        assetOriginalMillionCny: original,
        residualFloor,
        accumulatedDepreciation,
        bookValue,
        periodDepreciation,
        remainingLifeYears: "-",
      };
    }

    function rebuildAssetSlot(row) {
      const source = state.financeScope === "annual" ? row : q(row, state.financeScope);
      const original = state.financeScope === "annual"
        ? num(row.rebuildAssetOriginal)
        : num(source.rebuild_asset_original_million_cny);
      const residualFloor = state.financeScope === "annual"
        ? num(row.rebuildAssetResidualFloor)
        : num(source.rebuild_asset_residual_floor_million_cny);
      const accumulatedDepreciation = state.financeScope === "annual"
        ? num(row.rebuildAssetAccumulatedDepreciation)
        : num(source.rebuild_asset_accumulated_depreciation_million_cny);
      const bookValue = state.financeScope === "annual"
        ? num(row.rebuildAssetBookValue)
        : num(source.rebuild_asset_book_value_million_cny);
      const periodDepreciation = state.financeScope === "annual"
        ? num(row.rebuildAssetPeriodDepreciation)
        : num(source.rebuild_asset_period_depreciation_million_cny);
      const constructionInProgress = state.financeScope === "annual"
        ? num(row.rebuildConstructionInProgress)
        : num(source.rebuild_construction_in_progress_million_cny);
      const activeIds = state.financeScope === "annual"
        ? row.rebuildActiveEventIds
        : source.rebuild_active_event_ids;
      const completedIds = state.financeScope === "annual"
        ? row.rebuildCompletedEventIds
        : source.rebuild_completed_event_ids;
      const inServicePeriods = state.financeScope === "annual"
        ? row.rebuildAssetInServicePeriods
        : source.rebuild_asset_in_service_periods;
      if (!original && !bookValue && !constructionInProgress && !activeIds && !completedIds) {
        return null;
      }
      if (!original && constructionInProgress) {
        return {
          airportName: "北京首都",
          slotName: "首都T2航站楼重建在建工程",
          facilitySize: "extra_large rebuild",
          inServiceYear: "施工中",
          assetOriginalMillionCny: constructionInProgress,
          residualFloor: 0,
          accumulatedDepreciation: 0,
          bookValue: constructionInProgress,
          periodDepreciation: 0,
          remainingLifeYears: "-",
        };
      }
      return {
        airportName: "北京首都",
        slotName: "首都T2航站楼重建资产",
        facilitySize: "extra_large rebuild",
        inServiceYear: String(inServicePeriods || "-").split(";")[0],
        assetOriginalMillionCny: original,
        residualFloor,
        accumulatedDepreciation,
        bookValue,
        periodDepreciation,
        remainingLifeYears: "-",
      };
    }

    function hasPekSlot2RebuildStarted(row) {
      const source = state.financeScope === "annual" ? row : q(row, state.financeScope);
      const ids = state.financeScope === "annual"
        ? `${row.rebuildActiveEventIds || ""};${row.rebuildStartedEventIds || ""};${row.rebuildCompletedEventIds || ""}`
        : `${source.rebuild_active_event_ids || ""};${source.rebuild_started_event_ids || ""};${source.rebuild_completed_event_ids || ""}`;
      return ids.includes("PEK_SLOT_2_REBUILD_2056Q1");
    }

    function assetSlotsForRow(row) {
      const baseSlots = assetSlotsForYear(row.year).filter((slot) => (
        !hasPekSlot2RebuildStarted(row) || !String(slot.slotName || "").includes("首都T2航站楼")
      ));
      const renovationSlot = renovationAssetSlot(row);
      const constructionSlot = constructionAssetSlot(row);
      const rebuildSlot = rebuildAssetSlot(row);
      return [
        ...baseSlots,
        ...(renovationSlot ? [renovationSlot] : []),
        ...(constructionSlot ? [constructionSlot] : []),
        ...(rebuildSlot ? [rebuildSlot] : []),
      ];
    }

    function assetValues(row) {
      const slots = assetSlotsForRow(row);
      const financial = balanceValues(row);
      if (
        financial.fixedAssetOriginal ||
        financial.fixedAssetBook ||
        financial.fixedAssetAccumulatedDepreciation ||
        financial.fixedAssetResidualFloor
      ) {
        return {
          original: financial.fixedAssetOriginal,
          residualFloor: financial.fixedAssetResidualFloor,
          accumulatedDepreciation: financial.fixedAssetAccumulatedDepreciation,
          bookValue: financial.fixedAssetBook,
          periodDepreciation: financial.depreciation,
          accountingProfit: financial.accountingProfit,
          slots,
        };
      }
      const totals = slots.reduce(
        (sum, slot) => ({
          original: sum.original + slot.assetOriginalMillionCny,
          residualFloor: sum.residualFloor + slot.residualFloor,
          accumulatedDepreciation: sum.accumulatedDepreciation + slot.accumulatedDepreciation,
          bookValue: sum.bookValue + slot.bookValue,
          periodDepreciation: sum.periodDepreciation + slot.periodDepreciation,
        }),
        { original: 0, residualFloor: 0, accumulatedDepreciation: 0, bookValue: 0, periodDepreciation: 0 }
      );
      return {
        ...totals,
        accountingProfit: operatingProfitValue(row) - totals.periodDepreciation,
        slots,
      };
    }

    function financeLabels() {
      if (state.financeSide === "aeronautical") {
        return {
          chartName: "航运侧成本拆分图",
          revenue: "航运收入",
          cost: "机场运行成本",
          fixedCost: "槽位固定成本",
          passengerCost: "旅客接待成本",
          congestionCost: "拥挤/宽松调整",
          profit: "航运经营结果",
          revenueSmall: "客群结构 + 市场环境 + 容量修正",
          costSmall: "槽位固定 + 客流变动 + 拥挤/宽松调整",
          fixedCostSmall: "规格基准 × 建筑年龄 × 宏观 × 季节",
          passengerCostSmall: "接待旅客带来的变动成本",
          congestionCostSmall: "低利用率可为负，超设计/最大容量转为惩罚",
          profitSmall: "航运收入 - 机场运行成本",
        };
      }
      if (state.financeSide === "commercial") {
        return {
          chartName: "商业侧经营图",
          revenue: "商业收入",
          selfRevenue: "自营收入",
          contractRevenue: "合同收入",
          dutyFreeRevenue: "免税合同收入",
          luxuryRevenue: "奢侈品合同收入",
          fixedCost: "自营固定成本",
          salesCost: "自营销售成本",
          passengerServiceCost: "自营客流服务成本",
          cost: "商业直接成本",
          profit: "商业经营结果",
          selfRevenueSmall: "餐饮 + 普通零售 + 电子零售",
          contractRevenueSmall: "免税 + 奢侈品合同收入",
          dutyFreeRevenueSmall: "免税合同保底或分成",
          luxuryRevenueSmall: "奢侈品合同保底或分成",
          fixedCostSmall: "启用槽位带来的自营刚性成本",
          salesCostSmall: "商品采购、原料、损耗和渠道成本",
          passengerServiceCostSmall: "承接旅客带来的服务成本",
          profitSmall: "商业收入 - 自营销售/固定/服务成本",
        };
      }
      return {
        chartName: "经营损益图",
        revenue: "经营收入",
        cost: "经营成本",
        profit: "经营结果",
        revenueSmall: "经营收入",
        costSmall: "经营成本",
        profitSmall: "经营收入 - 经营成本",
      };
    }

    function passengerValues(row) {
      if (state.financeScope === "annual") {
        return {
          potentialPassengers: row.potentialPassengers,
          passengers: row.passengers,
          airlineSupply: row.airlineSupply,
          airlineSupplyIndex: row.airlineSupplyIndex,
          airlineSupplyFulfillment: row.airlineSupplyFulfillment,
          airlineSupplyGap: row.airlineSupplyGap,
          airlineSupplyVolatilityRegime: row.airlineSupplyVolatilityRegime,
          passengerComponents: row.passengerComponents || [],
          designCapacity: row.designCapacity,
          maxCapacity: row.maxCapacity,
          designUtilization: row.designCapacity ? row.passengers / row.designCapacity * 100 : 0,
          maxUtilization: row.maxCapacity ? row.passengers / row.maxCapacity * 100 : 0,
        };
      }
      const quarter = q(row, state.financeScope);
      const potentialPassengers = num(quarter.quarter_city_potential_passengers_million, num(quarter.quarter_served_passengers_million));
      const passengers = num(quarter.quarter_served_passengers_million);
      const airlineSupply = num(quarter.quarter_airline_supply_passengers_million, potentialPassengers);
      const designCapacity = num(quarter.quarter_design_capacity_million);
      const maxCapacity = num(quarter.quarter_max_capacity_million);
      const passengerComponents = PASSENGER_COMPONENTS.map((component) => {
        const potential = num(
          quarter[`${component.key}_quarter_potential_passengers_million`],
          num(quarter[`${component.key}_quarter_served_passengers_million`])
        );
        const supplyFallback = potentialPassengers ? airlineSupply * potential / potentialPassengers : potential;
        return {
          ...component,
          potential,
          airlineSupply: num(quarter[`${component.key}_quarter_airline_supply_passengers_million`], supplyFallback),
          passengers: num(quarter[`${component.key}_quarter_served_passengers_million`]),
        };
      });
      return {
        potentialPassengers,
        passengers,
        airlineSupply,
        airlineSupplyIndex: num(quarter.annual_city_airline_supply_index, row.airlineSupplyIndex),
        airlineSupplyFulfillment: num(quarter.quarter_airline_supply_fulfillment_pct, potentialPassengers ? airlineSupply / potentialPassengers * 100 : 100),
        airlineSupplyGap: num(quarter.quarter_airline_supply_gap_million, Math.max(0, potentialPassengers - airlineSupply)),
        airlineSupplyVolatilityRegime: quarter.annual_city_airline_supply_volatility_regime || row.airlineSupplyVolatilityRegime,
        passengerComponents,
        designCapacity,
        maxCapacity,
        designUtilization: num(quarter.quarter_design_utilization_pct, designCapacity ? passengers / designCapacity * 100 : 0),
        maxUtilization: num(quarter.quarter_max_utilization_pct, maxCapacity ? passengers / maxCapacity * 100 : 0),
      };
    }

    function financialRowForSelection(row) {
      if (state.financeScope === "annual") {
        return financialAnnualMap().get(row.year) || null;
      }
      const annual = financialAnnualMap().get(row.year);
      return annual?.quarters?.[state.financeScope] || null;
    }

    function balanceValues(row) {
      const financial = financialRowForSelection(row);
      if (!financial) {
        return {
          beginCash: 0,
          endCash: 0,
          operatingProfit: 0,
          depreciation: 0,
          pretaxAccountingProfit: 0,
          taxableIncomeBeforeLoss: 0,
          taxableIncome: 0,
          taxPrepayment: 0,
          taxSettlement: 0,
          cashTaxPaid: 0,
          taxLossUsed: 0,
          taxLossGenerated: 0,
          taxLossExpired: 0,
          taxLossCarryforwardEnding: 0,
          incomeTax: 0,
          effectiveTaxRatePct: 0,
          accountingProfit: 0,
          capex: 0,
          rebuildCapex: 0,
          rebuildDemolitionExpense: 0,
          rebuildInitialWriteoff: 0,
          rebuildRenovationWriteoff: 0,
          rebuildOldAssetWriteoff: 0,
          freeCashFlow: 0,
          interestExpense: 0,
          loanDrawdown: 0,
          interestPayment: 0,
          principalRepayment: 0,
          debtService: 0,
          financingCashFlow: 0,
          loanActiveIds: "",
          loanDrawdownIds: "",
          loanPrincipalRepaymentIds: "",
          loanWeightedInterestRatePct: 0,
          loanDrawdownWeightedInterestRatePct: 0,
          loanDrawdownLeverageBeforePct: 0,
          loanDrawdownLeverageAfterPct: 0,
          loanDrawdownLeverageSpreadBps: 0,
          loanBlockedIds: "",
          loanBlockedReasons: "",
          fixedAssetOriginal: 0,
          fixedAssetResidualFloor: 0,
          fixedAssetAccumulatedDepreciation: 0,
          fixedAssetBook: 0,
          constructionInProgress: 0,
          totalNoncurrentAssets: 0,
          totalAssets: 0,
          shortTermDebt: 0,
          longTermDebt: 0,
          totalLiabilities: 0,
          contributedCapital: 0,
          retainedEarnings: 0,
          totalEquity: 0,
          balanceCheck: 0,
        };
      }
      if (state.financeScope === "annual") {
        return financial;
      }
      return {
        beginCash: num(financial.period_begin_cash_million_cny),
        endCash: num(financial.period_end_cash_million_cny),
        operatingProfit: num(financial.period_operating_profit_million_cny),
        depreciation: num(financial.period_accounting_depreciation_million_cny),
        pretaxAccountingProfit: num(financial.period_pretax_accounting_profit_million_cny),
        taxableIncomeBeforeLoss: num(financial.period_taxable_income_million_cny),
        taxableIncome: num(financial.period_taxable_income_million_cny),
        taxPrepayment: num(financial.period_income_tax_prepayment_million_cny),
        taxSettlement: num(financial.period_income_tax_settlement_million_cny),
        cashTaxPaid: num(financial.period_cash_tax_paid_million_cny),
        taxLossUsed: num(financial.period_tax_loss_used_million_cny),
        taxLossGenerated: num(financial.period_tax_loss_generated_million_cny),
        taxLossExpired: num(financial.period_tax_loss_expired_million_cny),
        taxLossCarryforwardEnding: num(financial.period_tax_loss_carryforward_ending_million_cny),
        incomeTax: num(financial.period_income_tax_expense_million_cny),
        effectiveTaxRatePct: num(financial.period_effective_tax_rate_pct),
        accountingProfit: num(financial.period_accounting_profit_million_cny),
        capex: num(financial.period_total_capex_outlay_million_cny),
        rebuildCapex: num(financial.period_rebuild_capex_outlay_million_cny),
        rebuildDemolitionExpense: num(financial.period_rebuild_demolition_expense_million_cny),
        rebuildInitialWriteoff: num(financial.period_rebuild_old_initial_asset_writeoff_million_cny),
        rebuildRenovationWriteoff: num(financial.period_rebuild_old_renovation_asset_writeoff_million_cny),
        rebuildOldAssetWriteoff: num(financial.period_rebuild_old_asset_writeoff_million_cny),
        freeCashFlow: num(financial.period_free_cash_flow_before_financing_million_cny),
        interestExpense: num(financial.period_interest_expense_million_cny),
        loanDrawdown: num(financial.period_loan_drawdown_million_cny),
        interestPayment: num(financial.period_interest_payment_million_cny),
        principalRepayment: num(financial.period_principal_repayment_million_cny),
        debtService: num(financial.period_debt_service_million_cny),
        financingCashFlow: num(financial.period_financing_cash_flow_million_cny),
        loanActiveIds: financial.loan_active_ids || "",
        loanDrawdownIds: financial.loan_drawdown_ids || "",
        loanPrincipalRepaymentIds: financial.loan_principal_repayment_ids || "",
        loanWeightedInterestRatePct: num(financial.loan_weighted_interest_rate_pct),
        loanDrawdownWeightedInterestRatePct: num(financial.loan_drawdown_weighted_interest_rate_pct),
        loanDrawdownLeverageBeforePct: num(financial.loan_drawdown_leverage_before_pct),
        loanDrawdownLeverageAfterPct: num(financial.loan_drawdown_leverage_after_pct),
        loanDrawdownLeverageSpreadBps: num(financial.loan_drawdown_leverage_spread_bps),
        loanBlockedIds: financial.loan_blocked_ids || "",
        loanBlockedReasons: financial.loan_blocked_reasons || "",
        fixedAssetOriginal: num(financial.fixed_asset_original_million_cny),
        fixedAssetResidualFloor: num(financial.fixed_asset_residual_floor_million_cny),
        fixedAssetAccumulatedDepreciation: num(financial.fixed_asset_accumulated_depreciation_million_cny),
        fixedAssetBook: num(financial.fixed_asset_book_value_million_cny),
        constructionInProgress: num(financial.construction_in_progress_million_cny),
        totalNoncurrentAssets: num(financial.total_noncurrent_assets_million_cny),
        totalAssets: num(financial.total_assets_million_cny),
        shortTermDebt: num(financial.short_term_debt_million_cny),
        longTermDebt: num(financial.long_term_debt_million_cny),
        totalLiabilities: num(financial.total_liabilities_million_cny),
        contributedCapital: num(financial.contributed_capital_million_cny),
        retainedEarnings: num(financial.retained_earnings_million_cny),
        totalEquity: num(financial.total_equity_million_cny),
        balanceCheck: num(financial.balance_check_million_cny),
      };
    }

    function trajectorySeries() {
      if (state.chartMode === "passenger") {
        return [
          { key: "potentialPassengers", label: "潜在客流", color: "#ef4444", value: (row) => passengerValues(row).potentialPassengers / 100 },
          { key: "passengers", label: "承接客流", color: "#2563eb", value: (row) => passengerValues(row).passengers / 100 },
          { key: "airlineSupply", label: "航司供给", color: "#14b8a6", value: (row) => passengerValues(row).airlineSupply / 100 },
          { key: "designCapacity", label: "设计容量", color: "#f59e0b", value: (row) => passengerValues(row).designCapacity / 100 },
          { key: "maxCapacity", label: "最大容量", color: "#22c55e", value: (row) => passengerValues(row).maxCapacity / 100 },
        ];
      }
      if (state.chartMode === "valuation") {
        return [
          { key: "equityValue", label: "股权净资产", color: "#60a5fa", value: (row) => valuationValues(row).equityValue / 100 },
          { key: "enterpriseValue", label: "净资产EV", color: "#34d399", value: (row) => valuationValues(row).enterpriseValue / 100 },
          { key: "marketEnterpriseValue", label: "DCF观察值", color: "#a78bfa", value: (row) => valuationValues(row).marketEnterpriseValue / 100 },
        ];
      }
      if (state.chartMode === "asset") {
        return [
          { key: "original", label: "资产原值", color: "#60a5fa", value: (row) => assetValues(row).original / 100 },
          { key: "accumulatedDepreciation", label: "累计折旧", color: "#f59e0b", value: (row) => assetValues(row).accumulatedDepreciation / 100 },
          { key: "bookValue", label: "账面净值", color: "#34d399", value: (row) => assetValues(row).bookValue / 100 },
          { key: "periodDepreciation", label: state.financeScope === "annual" ? "当年折旧" : "当季折旧", color: "#f472b6", value: (row) => assetValues(row).periodDepreciation / 100 },
        ];
      }
      if (state.chartMode === "balance") {
        return [
          { key: "cash", label: "现金", color: "#60a5fa", value: (row) => balanceValues(row).endCash / 100 },
          { key: "fixedAssetBook", label: "固定资产净值", color: "#34d399", value: (row) => balanceValues(row).fixedAssetBook / 100 },
          { key: "cip", label: "在建工程", color: "#f59e0b", value: (row) => balanceValues(row).constructionInProgress / 100 },
          { key: "liabilities", label: "负债合计", color: "#fb7185", value: (row) => balanceValues(row).totalLiabilities / 100 },
          { key: "equity", label: "所有者权益", color: "#a78bfa", value: (row) => balanceValues(row).totalEquity / 100 },
          { key: "assets", label: "总资产", color: "#22d3ee", value: (row) => balanceValues(row).totalAssets / 100 },
        ];
      }
      const labels = financeLabels();
      if (state.financeSide === "aeronautical") {
        return [
          { key: "revenue", label: labels.revenue, color: "#60a5fa", value: (row) => financeValue(row, "revenue") / 100 },
          { key: "fixedCost", label: labels.fixedCost, color: "#fb7185", value: (row) => financeValue(row, "fixedCost") / 100 },
          { key: "passengerCost", label: labels.passengerCost, color: "#f59e0b", value: (row) => financeValue(row, "passengerCost") / 100 },
          { key: "congestionCost", label: labels.congestionCost, color: "#a78bfa", value: (row) => financeValue(row, "congestionCost") / 100 },
          { key: "profit", label: labels.profit, color: "#34d399", value: (row) => financeValue(row, "profit") / 100 },
        ];
      }
      if (state.financeSide === "commercial") {
        return [
          { key: "selfRevenue", label: labels.selfRevenue, color: "#60a5fa", value: (row) => financeValue(row, "selfRevenue") / 100 },
          { key: "dutyFreeRevenue", label: labels.dutyFreeRevenue, color: "#22d3ee", value: (row) => financeValue(row, "dutyFreeRevenue") / 100 },
          { key: "luxuryRevenue", label: labels.luxuryRevenue, color: "#f472b6", value: (row) => financeValue(row, "luxuryRevenue") / 100 },
          { key: "salesCost", label: labels.salesCost, color: "#ef4444", value: (row) => financeValue(row, "salesCost") / 100 },
          { key: "fixedCost", label: labels.fixedCost, color: "#fb7185", value: (row) => financeValue(row, "fixedCost") / 100 },
          { key: "passengerServiceCost", label: labels.passengerServiceCost, color: "#f59e0b", value: (row) => financeValue(row, "passengerServiceCost") / 100 },
          { key: "profit", label: labels.profit, color: "#34d399", value: (row) => financeValue(row, "profit") / 100 },
        ];
      }
      return [
        { key: "revenue", label: labels.revenue, color: "#60a5fa", value: (row) => financeValue(row, "revenue") / 100 },
        { key: "cost", label: labels.cost, color: "#fb7185", value: (row) => financeValue(row, "cost") / 100 },
        { key: "profit", label: labels.profit, color: "#34d399", value: (row) => financeValue(row, "profit") / 100 },
      ];
    }

    function updateChartModeButtons() {
      el.chartModeSwitch.querySelectorAll("button").forEach((button) => {
        button.setAttribute("aria-pressed", String(button.dataset.chartMode === state.chartMode));
      });
      el.financeSideTools.classList.toggle("is-hidden", state.chartMode !== "finance");
      el.financeSideSwitch.querySelectorAll("button").forEach((button) => {
        button.setAttribute("aria-pressed", String(button.dataset.financeSide === state.financeSide));
      });
    }

    function renderTrajectoryLegend(series) {
      el.trajectoryLegend.innerHTML = series.map((item) => (
        `<span><i class="swatch" style="background: ${item.color}"></i>${item.label}</span>`
      )).join("");
    }

    function pathFromPoints(points) {
      return points.map((point, index) => `${index ? "L" : "M"} ${point[0].toFixed(2)} ${point[1].toFixed(2)}`).join(" ");
    }

    function renderTrajectoryChart(data) {
      if (!data.length) {
        el.financeChart.innerHTML = `<div class="empty">No data</div>`;
        return;
      }
      const width = 980;
      const height = 330;
      const margin = { top: 20, right: 28, bottom: 38, left: 62 };
      const plotW = width - margin.left - margin.right;
      const plotH = height - margin.top - margin.bottom;
      const series = trajectorySeries();
      renderTrajectoryLegend(series);
      const minYear = Math.min(...data.map((row) => row.year));
      const maxYear = Math.max(...data.map((row) => row.year));
      const values = data.flatMap((row) => series.map((item) => item.value(row)));
      const maxY = Math.max(...values, 1) * 1.08;
      const minY = Math.min(0, Math.min(...values));
      const spanY = maxY - minY || 1;
      const x = (year) => margin.left + (maxYear === minYear ? 0 : (year - minYear) / (maxYear - minYear) * plotW);
      const y = (value) => margin.top + (maxY - value) / spanY * plotH;
      const selected = data.find((row) => row.year === state.selectedYear) || data[0];
      const selectedX = x(selected.year);
      const axisFormat = state.chartMode === "passenger"
        ? (value) => value.toFixed(value >= 1 ? 1 : 2)
        : (value) => value.toFixed(0);
      const gridValues = [0, 0.25, 0.5, 0.75, 1].map((part) => minY + spanY * part);
      const grid = gridValues.map((value) => {
        const gy = y(value);
        return `<line x1="${margin.left}" y1="${gy.toFixed(2)}" x2="${width - margin.right}" y2="${gy.toFixed(2)}" stroke="#223044" /><text x="${margin.left - 10}" y="${(gy + 4).toFixed(2)}" text-anchor="end" font-size="11" fill="#94a3b8">${axisFormat(value)}</text>`;
      }).join("");
      const lines = series.map((item) => {
        const points = data.map((row) => [x(row.year), y(item.value(row))]);
        const dotY = y(item.value(selected));
        return `
          <path d="${pathFromPoints(points)}" fill="none" stroke="${item.color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
          <circle cx="${selectedX.toFixed(2)}" cy="${dotY.toFixed(2)}" r="4.5" fill="${item.color}" stroke="#080b10" stroke-width="2" />
        `;
      }).join("");
      const yearTicks = [minYear, Math.round((minYear + maxYear) / 2), maxYear];
      const ticks = [...new Set(yearTicks)].map((year) => `<text x="${x(year).toFixed(2)}" y="${height - 12}" text-anchor="middle" font-size="11" fill="#94a3b8">${year}</text>`).join("");
      const scopeLabel = financeScopeLabel();
      const unitLabel = state.chartMode === "passenger" ? "亿人次" : "亿元";
      const chartName = state.chartMode === "passenger"
        ? "客流容量图"
        : state.chartMode === "valuation"
          ? "估值曲线"
        : state.chartMode === "asset"
          ? "资产折旧图"
          : state.chartMode === "balance"
            ? "资产负债表"
            : financeLabels().chartName;

      el.financeChart.innerHTML = `
        <svg viewBox="0 0 ${width} ${height}" width="100%" height="100%" role="img" aria-label="北京机场${scopeLabel}${chartName}">
          <rect x="0" y="0" width="${width}" height="${height}" fill="transparent"></rect>
          ${grid}
          <line x1="${margin.left}" y1="${height - margin.bottom}" x2="${width - margin.right}" y2="${height - margin.bottom}" stroke="#43536c" />
          <line x1="${selectedX.toFixed(2)}" y1="${margin.top}" x2="${selectedX.toFixed(2)}" y2="${height - margin.bottom}" stroke="#64748b" stroke-dasharray="4 6" />
          ${lines}
          ${ticks}
          <text x="${selectedX.toFixed(2)}" y="${margin.top - 6}" text-anchor="middle" font-size="11" fill="#bfdbfe">${selected.year}</text>
          <text x="${width - margin.right}" y="16" text-anchor="end" font-size="12" fill="#94a3b8">${scopeLabel} / ${unitLabel}</text>
        </svg>
      `;
    }

    function metricCard(label, value, small, className = "") {
      const strongClass = className ? ` class="${className}"` : "";
      return `<article class="finance-metric"><span>${label}</span><strong${strongClass}>${value}</strong><small>${small}</small></article>`;
    }

    function commercialSection(title, subtitle, cards) {
      return `
        <section class="commercial-section">
          <div class="commercial-section-head"><span>${title}</span><small>${subtitle}</small></div>
          <div class="commercial-section-grid">${cards.join("")}</div>
        </section>
      `;
    }

    function renderTrajectoryMetrics(data) {
      const selected = data.find((row) => row.year === state.selectedYear) || data[0];
      const scopeLabel = financeScopeLabel();
      el.financeMetrics.className = "finance-metrics";
      if (state.chartMode === "balance") {
        const values = balanceValues(selected);
        const liabilityRatio = values.totalAssets ? values.totalLiabilities / values.totalAssets * 100 : 0;
        el.financeMetrics.innerHTML = [
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}总资产</span><strong>${fmtBillion(values.totalAssets)}</strong><small>现金 + 固定资产净值 + 在建工程</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}现金</span><strong>${fmtBillion(values.endCash)}</strong><small>期初 ${fmtBillion(values.beginCash)}</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}固定资产净值</span><strong>${fmtBillion(values.fixedAssetBook)}</strong><small>初始资产 + 翻新/新建/重建资产</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}在建工程</span><strong>${fmtBillion(values.constructionInProgress)}</strong><small>未转固的翻新/新建/重建投入</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}负债合计</span><strong>${fmtBillion(values.totalLiabilities)}</strong><small>短债 ${fmtBillion(values.shortTermDebt)} / 长债 ${fmtBillion(values.longTermDebt)}</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}资产负债率</span><strong class="${toneClass(liabilityRatio, 60, 80)}">${fmtPct(liabilityRatio)}</strong><small>禁贷线 80.0%</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}贷款提款</span><strong>${fmtBillion(values.loanDrawdown)}</strong><small>${loanIdsLabel(values.loanDrawdownIds)}</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}还本</span><strong>${fmtBillion(values.principalRepayment)}</strong><small>${loanIdsLabel(values.loanPrincipalRepaymentIds)}</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}付息</span><strong>${fmtBillion(values.interestPayment)}</strong><small>计入利息费用</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}债务服务</span><strong>${fmtBillion(values.debtService)}</strong><small>还本 + 付息</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}贷款利率</span><strong>${fmtPct(values.loanWeightedInterestRatePct)}</strong><small>活跃本金加权</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}提款锁定利率</span><strong>${fmtPct(values.loanDrawdownWeightedInterestRatePct)}</strong><small>本期新增贷款加权</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}提款后杠杆</span><strong>${fmtPct(values.loanDrawdownLeverageAfterPct)}</strong><small>提款前 ${fmtPct(values.loanDrawdownLeverageBeforePct)}</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}杠杆利差</span><strong>${fmtBps(values.loanDrawdownLeverageSpreadBps)}</strong><small>按提款金额加权</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}被拒贷款</span><strong>${uniqueSemiList(values.loanBlockedIds).length}</strong><small>${loanIdsLabel(values.loanBlockedIds)}</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}活跃贷款</span><strong>${uniqueSemiList(values.loanActiveIds).length}</strong><small>${loanIdsLabel(values.loanActiveIds)}</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}所有者权益</span><strong>${fmtBillion(values.totalEquity)}</strong><small>资本金 + 留存收益</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}留存收益</span><strong class="${profitClass(values.retainedEarnings)}">${fmtBillion(values.retainedEarnings)}</strong><small>2025 起累计会计利润</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}税前利润</span><strong class="${profitClass(values.pretaxAccountingProfit)}">${fmtBillion(values.pretaxAccountingProfit)}</strong><small>经营利润 - 折旧 - 拆除费 - 核销 - 利息</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}所得税</span><strong>${fmtBillion(values.incomeTax)}</strong><small>应税利润 ${fmtBillion(values.taxableIncome)} / 有效税率 ${fmtPct(values.effectiveTaxRatePct)}</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}税务汇算</span><strong>${fmtBillion(values.taxSettlement)}</strong><small>预缴 ${fmtBillion(values.taxPrepayment)} / 亏损抵扣 ${fmtBillion(values.taxLossUsed)} / 结转 ${fmtBillion(values.taxLossCarryforwardEnding)}</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}${state.financeScope === "annual" ? "税后会计利润" : "当季税后利润"}</span><strong class="${profitClass(values.accountingProfit)}">${fmtBillion(values.accountingProfit)}</strong><small>税前利润 - 所得税</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}${state.financeScope === "annual" ? "自由现金流" : "当季自由现金流"}</span><strong class="${profitClass(values.freeCashFlow)}">${fmtBillion(values.freeCashFlow)}</strong><small>经营利润 - capex - 拆除费 - 所得税</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}重建资本开支</span><strong>${fmtBillion(values.rebuildCapex)}</strong><small>资本化为重建资产</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}拆除费用</span><strong>${fmtBillion(values.rebuildDemolitionExpense)}</strong><small>期间费用，不形成资产</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}旧资产核销</span><strong>${fmtBillion(values.rebuildOldAssetWriteoff)}</strong><small>初始 ${fmtBillion(values.rebuildInitialWriteoff)} / 翻新 ${fmtBillion(values.rebuildRenovationWriteoff)}</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}平衡差额</span><strong class="${Math.abs(values.balanceCheck) < 0.01 ? "positive" : "danger"}">${fmtBillion(values.balanceCheck)}</strong><small>资产 - 负债 - 权益</small></article>`,
        ].join("");
        return;
      }
      if (state.chartMode === "asset") {
        const values = assetValues(selected);
        el.financeMetrics.innerHTML = [
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}资产原值</span><strong>${fmtBillion(values.original)}</strong><small>已启用槽位资产口径</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}累计折旧</span><strong>${fmtBillion(values.accumulatedDepreciation)}</strong><small>截至当前口径期末</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}账面净值</span><strong>${fmtBillion(values.bookValue)}</strong><small>资产原值 - 累计折旧</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}${state.financeScope === "annual" ? "当年" : "当季"}折旧</span><strong>${fmtBillion(values.periodDepreciation)}</strong><small>直线折旧，非现金成本</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}残值下限</span><strong>${fmtBillion(values.residualFloor)}</strong><small>资产原值的残值保留</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}税后会计利润</span><strong class="${profitClass(values.accountingProfit)}">${fmtBillion(values.accountingProfit)}</strong><small>经营结果 - 折旧 - 税费等</small></article>`,
        ].join("");
        return;
      }
      if (state.chartMode === "valuation") {
        const values = valuationValues(selected);
        if (!values.row) {
          el.financeMetrics.innerHTML = `<article class="finance-metric"><span>${selected.year} ${scopeLabel}估值</span><strong>-</strong><small>当前口径没有估值数据</small></article>`;
          return;
        }
        const asOfLabel = `${values.asOfYear} ${values.asOfQuarter}`;
        const riskClass = values.riskTags === "normal" ? "positive" : "warning";
        const marketAdjustmentClass = values.marketAdjustmentPct >= 0 ? "positive" : "warning";
        const marketPeClass = values.marketEquityValuationAdjustmentPct >= 0 ? "positive" : "warning";
        el.financeMetrics.innerHTML = [
          `<article class="finance-metric"><span>${asOfLabel} 股权净资产</span><strong>${fmtBillion(values.equityValue)}</strong><small>当前主估值口径，P/B ${fmtValuationMultiple(values.priceToBook)}</small></article>`,
          `<article class="finance-metric"><span>${asOfLabel} 净资产EV</span><strong>${fmtBillion(values.enterpriseValue)}</strong><small>股权净资产 + 净债务</small></article>`,
          `<article class="finance-metric"><span>${asOfLabel} 净债务</span><strong class="${values.netDebt > 0 ? "warning" : "positive"}">${fmtBillion(values.netDebt)}</strong><small>现金 ${fmtBillion(values.recognizedCash)} / 债务 ${fmtBillion(values.totalDebt)}</small></article>`,
          `<article class="finance-metric"><span>${asOfLabel} 经营结果</span><strong class="${profitClass(values.currentAccountingProfit)}">${fmtBillion(values.currentAccountingProfit)}</strong><small>经营利润 ${fmtBillion(values.currentOperatingProfit)} / 会计PE ${fmtValuationMultiple(values.priceToAccountingProfit)}</small></article>`,
          `<article class="finance-metric"><span>${asOfLabel} DCF观察EV</span><strong>${fmtBillion(values.marketEnterpriseValue)}</strong><small>非主口径，经营EV ${fmtBillion(values.operatingEnterpriseValue)}，倍数 ${fmtMultiplier(values.marketEvToOperatingProfit)}</small></article>`,
          `<article class="finance-metric"><span>${asOfLabel} DCF观察股权</span><strong>${fmtBillion(values.experimentalEquityValue)}</strong><small>市场化观察，不参与当前净资产定价</small></article>`,
          `<article class="finance-metric"><span>${asOfLabel} 市场环境观察</span><strong class="${marketAdjustmentClass}">${fmtPct(values.marketAdjustmentPct)}</strong><small>利率 ${fmtPct(values.marketRateAdjustmentPct)} / 信用 ${fmtPct(values.marketCreditAdjustmentPct)} / PE ${fmtPct(values.marketEquityValuationAdjustmentPct)} / 情绪 ${fmtPct(values.marketEquitySentimentAdjustmentPct)}</small></article>`,
          `<article class="finance-metric"><span>${asOfLabel} 市场PE水位</span><strong class="${marketPeClass}">${fmtValuationMultiple(values.marketEquityValuationPe)}</strong><small>只用于 DCF 观察口径</small></article>`,
          `<article class="finance-metric"><span>${asOfLabel} 经营现金流观察</span><strong class="${profitClass(values.operatingNormalizedFcffSum)}">${fmtBillion(values.operatingNormalizedFcffSum)}</strong><small>原始5年FCFF ${fmtBillion(values.forecastFcffSum)} / 终值FCFF ${fmtBillion(values.normalizedTerminalFcff)}</small></article>`,
          `<article class="finance-metric"><span>${asOfLabel} 状态标签</span><strong class="${riskClass}">${valuationRiskLabel(values.riskTags)}</strong><small>主口径按净资产，DCF区间 ${fmtPct(values.uncertaintyRangePct)}</small></article>`,
        ].join("");
        return;
      }
      if (state.chartMode === "passenger") {
        const values = passengerValues(selected);
        const airlineFulfillmentClass = values.airlineSupplyFulfillment >= 99
          ? "positive"
          : values.airlineSupplyFulfillment >= 92
            ? "warning"
            : "danger";
        const airlineGapClass = values.airlineSupplyGap <= 0.01
          ? "positive"
          : values.airlineSupplyFulfillment >= 92
            ? "warning"
            : "danger";
        const componentCards = values.passengerComponents.map((component) => {
          const coverage = component.potential ? component.airlineSupply / component.potential * 100 : 100;
          const gap = Math.max(0, component.potential - component.airlineSupply);
          const coverageClass = coverage >= 99 ? "positive" : coverage >= 90 ? "warning" : "danger";
          return metricCard(
            `${component.label}供给覆盖`,
            fmtPct(coverage),
            `潜在 ${fmtPassengerShort(component.potential)} / 供给 ${fmtPassengerShort(component.airlineSupply)} / 承接 ${fmtPassengerShort(component.passengers)} / 缺口 ${fmtPassengerShort(gap)}`,
            coverageClass
          );
        });
        el.financeMetrics.className = "finance-metrics commercial-breakdown";
        el.financeMetrics.innerHTML = [
          commercialSection("总览", `${selected.year} ${scopeLabel}`, [
            metricCard("潜在客流", fmtPassenger(values.potentialPassengers), "城市长期需求主轴"),
            metricCard("承接客流", fmtPassenger(values.passengers), bottleneckLabel(selected.bottleneck)),
            metricCard(
              "航司供给",
              fmtPassenger(values.airlineSupply),
              `供给指数 ${values.airlineSupplyIndex.toFixed(1)} / ${airlineSupplyVolatilityLabel(values.airlineSupplyVolatilityRegime)}`
            ),
            metricCard("航司满足率", fmtPct(values.airlineSupplyFulfillment), `缺口 ${fmtPassengerShort(values.airlineSupplyGap)}`, airlineFulfillmentClass),
            metricCard("航司缺口", fmtPassenger(values.airlineSupplyGap), "潜在客流 - 航司供给", airlineGapClass),
            metricCard(
              "设计客流使用率",
              fmtPct(values.designUtilization),
              `容量 ${fmtPassengerShort(values.designCapacity)}`,
              toneClass(values.designUtilization, 95, 120)
            ),
            metricCard(
              "最大客流使用率",
              fmtPct(values.maxUtilization),
              `容量 ${fmtPassengerShort(values.maxCapacity)}`,
              toneClass(values.maxUtilization, 90, 100)
            ),
          ]),
          commercialSection("分项潜在与航司供给", "商务 / 休闲 / 探亲访友 / 长途 / 中转", componentCards),
        ].join("");
        return;
      }
      const revenue = financeValue(selected, "revenue");
      const cost = financeValue(selected, "cost");
      const profit = financeValue(selected, "profit");
      const labels = financeLabels();
      if (state.financeSide === "aeronautical") {
        const values = aeronauticalValues(selected);
        el.financeMetrics.innerHTML = [
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}${labels.revenue}</span><strong>${fmtBillion(values.revenue)}</strong><small>${labels.revenueSmall}</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}${labels.fixedCost}</span><strong>${fmtBillion(values.fixedCost)}</strong><small>${labels.fixedCostSmall}</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}${labels.passengerCost}</span><strong>${fmtBillion(values.passengerCost)}</strong><small>${labels.passengerCostSmall}</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}${labels.congestionCost}</span><strong>${fmtBillion(values.congestionCost)}</strong><small>${labels.congestionCostSmall}</small></article>`,
          `<article class="finance-metric"><span>${selected.year} ${scopeLabel}${labels.profit}</span><strong class="${profitClass(values.result)}">${fmtBillion(values.result)}</strong><small>${labels.profitSmall}</small></article>`,
        ].join("");
        return;
      }
      if (state.financeSide === "commercial") {
        const values = commercialValues(selected);
        const commercialMarginClass = values.marginPct >= 80 ? "warning" : "positive";
        const dutyFreeTakeRate = values.dutyFreeSales ? values.dutyFreeRevenue / values.dutyFreeSales * 100 : 0;
        const luxuryTakeRate = values.luxurySales ? values.luxuryRevenue / values.luxurySales * 100 : 0;
        const qualityBreakdown = `规格 ${values.qualitySizeScore.toFixed(1)} / 新旧 ${values.qualityAgeScore.toFixed(1)} / 容量 ${values.qualityCapacityScore.toFixed(1)} / 施工 ${values.qualityDisruptionScore.toFixed(1)}`;
        el.financeMetrics.className = "finance-metrics commercial-breakdown";
        el.financeMetrics.innerHTML = [
          commercialSection("总览", `${selected.year} ${scopeLabel}`, [
            metricCard(labels.revenue, fmtBillion(values.totalRevenue), "自营 + 合同盘"),
            metricCard(labels.cost, fmtBillion(values.directCost), "当前直接成本口径"),
            metricCard(labels.profit, fmtBillion(values.result), labels.profitSmall, profitClass(values.result)),
            metricCard("商业利润率", fmtPct(values.marginPct), "收入 / 直接成本口径", commercialMarginClass),
            metricCard(
              "机场感知品质",
              values.qualityIndex.toFixed(1),
              qualityBreakdown,
              values.qualityIndex >= 100 ? "positive" : "warning"
            ),
            metricCard(
              "品质商业乘数",
              fmtMultiplier(values.luxuryQualityMultiplier),
              `自营 ${fmtMultiplier(values.foodRetailQualityMultiplier)} / 免税 ${fmtMultiplier(values.dutyFreeQualityMultiplier)} / 奢侈品`,
            ),
          ]),
          commercialSection("自营餐饮零售", labels.selfRevenueSmall, [
            metricCard(labels.selfRevenue, fmtBillion(values.selfRevenue), "餐饮、普通零售、电子零售"),
            metricCard(labels.salesCost, fmtBillion(values.salesCost), labels.salesCostSmall),
            metricCard(labels.fixedCost, fmtBillion(values.fixedCost), labels.fixedCostSmall),
            metricCard(labels.passengerServiceCost, fmtBillion(values.passengerServiceCost), labels.passengerServiceCostSmall),
            metricCard("自营经营结果", fmtBillion(values.foodRetailResult), "自营收入 - 自营成本", profitClass(values.foodRetailResult)),
          ]),
          commercialSection("免税合同", labels.dutyFreeRevenueSmall, [
            metricCard(labels.dutyFreeRevenue, fmtBillion(values.dutyFreeRevenue), "机场合同收入"),
            metricCard("免税估算销售额", fmtBillion(values.dutyFreeSales), "运营商销售盘"),
            metricCard("合同预测销售额", fmtBillion(values.dutyFreeForecastSales), values.dutyFreeContractCycle),
            metricCard("合同保底收入", fmtBillion(values.dutyFreeGuarantee), contractStatusLabel(values.dutyFreeContractStatus)),
            metricCard("免税有效客流", fmtPassenger(values.dutyFreeWeightedPassengers), "长途 / 中转 / 商务等加权"),
            metricCard("合同收入率", fmtPct(dutyFreeTakeRate), contractBasisLabel(values.dutyFreeContractBasis)),
          ]),
          commercialSection("奢侈品合同", labels.luxuryRevenueSmall, [
            metricCard(labels.luxuryRevenue, fmtBillion(values.luxuryRevenue), "机场合同收入"),
            metricCard("奢侈品估算销售额", fmtBillion(values.luxurySales), "运营商品牌销售盘"),
            metricCard("合同预测销售额", fmtBillion(values.luxuryForecastSales), values.luxuryContractCycle),
            metricCard("合同保底收入", fmtBillion(values.luxuryGuarantee), contractStatusLabel(values.luxuryContractStatus)),
            metricCard("奢侈品有效客流", fmtPassenger(values.luxuryWeightedPassengers), "商务 / 长途 / 中转等加权"),
            metricCard("合同收入率", fmtPct(luxuryTakeRate), contractBasisLabel(values.luxuryContractBasis)),
          ]),
        ].join("");
        return;
      }
      const statementValues = balanceValues(selected);
      el.financeMetrics.innerHTML = [
        `<article class="finance-metric"><span>${selected.year} ${scopeLabel}${labels.revenue}</span><strong>${fmtBillion(revenue)}</strong><small>${labels.revenueSmall}</small></article>`,
        `<article class="finance-metric"><span>${selected.year} ${scopeLabel}${labels.cost}</span><strong>${fmtBillion(cost)}</strong><small>${labels.costSmall}</small></article>`,
        `<article class="finance-metric"><span>${selected.year} ${scopeLabel}${labels.profit}</span><strong class="${profitClass(profit)}">${fmtBillion(profit)}</strong><small>${labels.profitSmall}</small></article>`,
        `<article class="finance-metric"><span>${selected.year} ${scopeLabel}税前利润</span><strong class="${profitClass(statementValues.pretaxAccountingProfit)}">${fmtBillion(statementValues.pretaxAccountingProfit)}</strong><small>经营结果 - 折旧 - 拆除费 - 核销 - 利息</small></article>`,
        `<article class="finance-metric"><span>${selected.year} ${scopeLabel}所得税</span><strong>${fmtBillion(statementValues.incomeTax)}</strong><small>应税利润 ${fmtBillion(statementValues.taxableIncome)} / 有效税率 ${fmtPct(statementValues.effectiveTaxRatePct)}</small></article>`,
        `<article class="finance-metric"><span>${selected.year} ${scopeLabel}税务汇算</span><strong>${fmtBillion(statementValues.taxSettlement)}</strong><small>预缴 ${fmtBillion(statementValues.taxPrepayment)} / 亏损抵扣 ${fmtBillion(statementValues.taxLossUsed)} / 结转 ${fmtBillion(statementValues.taxLossCarryforwardEnding)}</small></article>`,
        `<article class="finance-metric"><span>${selected.year} ${scopeLabel}${state.financeScope === "annual" ? "税后会计利润" : "当季税后利润"}</span><strong class="${profitClass(statementValues.accountingProfit)}">${fmtBillion(statementValues.accountingProfit)}</strong><small>税前利润 - 所得税</small></article>`,
        `<article class="finance-metric"><span>${selected.year} ${scopeLabel}${state.financeScope === "annual" ? "自由现金流" : "当季自由现金流"}</span><strong class="${profitClass(statementValues.freeCashFlow)}">${fmtBillion(statementValues.freeCashFlow)}</strong><small>经营利润 - capex - 拆除费 - 所得税</small></article>`,
      ].join("");
    }

    function renderAssetSlotDetails(data) {
      const selected = data.find((row) => row.year === state.selectedYear) || data[0];
      if (state.chartMode !== "asset") {
        el.assetDetailPanel.classList.add("is-hidden");
        el.assetSlotTable.innerHTML = "";
        return;
      }
      const scopeLabel = financeScopeLabel();
      const slots = assetSlotsForRow(selected);
      el.assetDetailPanel.classList.remove("is-hidden");
      el.assetDetailNote.textContent = `${selected.year} ${scopeLabel}，金额单位：亿元`;
      el.assetSlotTable.innerHTML = slots.map((slot) => {
        const slotLabel = `${slot.airportName} ${slot.slotName}`;
        const statusClass = slot.assetOriginalMillionCny ? (slot.remainingLifeYears > 0 ? "" : "muted") : "muted";
        const remaining = typeof slot.remainingLifeYears === "number" ? fmtYears(slot.remainingLifeYears) : "-";
        return `
          <tr>
            <td>${slotLabel}</td>
            <td>${slot.facilitySize}</td>
            <td>${slot.inServiceYear || "-"}</td>
            <td>${fmtBillion(slot.assetOriginalMillionCny)}</td>
            <td>${fmtBillion(slot.residualFloor)}</td>
            <td>${fmtBillion(slot.accumulatedDepreciation)}</td>
            <td class="${statusClass}">${fmtBillion(slot.bookValue)}</td>
            <td>${fmtBillion(slot.periodDepreciation)}</td>
            <td>${remaining}</td>
          </tr>
        `;
      }).join("");
    }

    function render() {
      const fullData = annualRows();
      if (!fullData.length) {
        document.querySelector("main").innerHTML = `<div class="empty">No data loaded</div>`;
        return;
      }
      const data = chartRowsForMode(fullData);
      if (!data.length) {
        const emptyLabel = state.chartMode === "valuation" ? "没有可用估值数据" : "没有可用图表数据";
        el.financeChart.innerHTML = `<div class="empty">${emptyLabel}</div>`;
        el.financeMetrics.innerHTML = "";
        el.assetDetailPanel.classList.add("is-hidden");
        return;
      }
      const years = data.map((row) => row.year);
      if (!years.includes(state.selectedYear)) {
        state.selectedYear = years[0];
      }
      el.financeYearRange.min = String(years[0]);
      el.financeYearRange.max = String(years[years.length - 1]);
      el.financeYearRange.value = String(state.selectedYear);
      updateChartModeButtons();
      renderSummary(fullData);
      renderTrajectoryChart(data);
      renderTrajectoryMetrics(data);
      renderAssetSlotDetails(data);
      el.statusText.textContent = `北京数据：${fullData.length} 年，${rowsForSeed().length} 个季度`;
    }

