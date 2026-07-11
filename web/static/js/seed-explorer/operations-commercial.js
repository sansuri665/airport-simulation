    function aggregateAviationPeriod(quarters) {
      const sum = (getter) => quarters.reduce((total, quarter) => total + (Number(getter(quarter)) || 0), 0);
      const passengers = sum((quarter) => quarter.demand.quarterServed);
      const revenue = sum((quarter) => quarter.operations.aeronauticalRevenue);
      const fixedCost = sum((quarter) => quarter.operations.slotFixedCost);
      const passengerCost = sum((quarter) => quarter.operations.passengerVariableCost);
      const congestionCost = sum((quarter) => quarter.operations.congestionCost);
      const cost = fixedCost + passengerCost + congestionCost;
      const profit = revenue - cost;
      return {
        passengers,
        revenue,
        fixedCost,
        passengerCost,
        congestionCost,
        cost,
        profit,
        revenuePerPassenger: passengers ? revenue / passengers : 0,
        costPerPassenger: passengers ? cost / passengers : 0,
        profitPerPassenger: passengers ? profit / passengers : 0,
      };
    }

    function aviationMetricConfig(metric = state.aviationMetric) {
      const styles = getComputedStyle(document.documentElement);
      const colors = {
        blue: styles.getPropertyValue("--blue").trim() || "#62a8ff",
        green: styles.getPropertyValue("--green").trim() || "#35d392",
        amber: styles.getPropertyValue("--amber").trim() || "#f7b84b",
        red: styles.getPropertyValue("--red").trim() || "#fb7185",
      };
      const moneyMetric = (key, label, color) => ({
        label,
        caption: `柱：${label} / 线：同比增幅`,
        leftFormat: fmtMoney,
        bars: [
          { label, color, value: (row) => row[key], format: fmtMoney },
        ],
        line: {
          label: "同比增幅",
          color: colors.amber,
          value: (row) => row.yoyPct,
          format: fmtPct,
        },
        valueText: (row) => fmtMoney(row[key]),
        growthHeader: "同比增幅",
        growthText: (row) => fmtPct(row.yoyPct),
        metricValue: (aggregate) => aggregate[key],
      });
      const passengerMetric = (key, label, color) => ({
        label,
        caption: `柱：${label} / 线：同比增幅`,
        leftFormat: fmtCny,
        bars: [
          { label, color, value: (row) => row[key], format: fmtCny },
        ],
        line: {
          label: "同比增幅",
          color: colors.amber,
          value: (row) => row.yoyPct,
          format: fmtPct,
        },
        valueText: (row) => fmtCny(row[key]),
        growthHeader: "同比增幅",
        growthText: (row) => fmtPct(row.yoyPct),
        metricValue: (aggregate) => aggregate[key],
      });
      const configs = {
        aviationRevenue: moneyMetric("revenue", "航空收入", colors.blue),
        aviationCost: moneyMetric("cost", "航空成本", colors.red),
        aviationCostBreakdown: {
          label: "航空成本拆解",
          caption: "堆叠柱：固定/变动/拥挤成本 / 线：单客航空成本",
          leftFormat: fmtMoney,
          stackedBars: [
            { label: "固定成本", color: colors.blue, value: (row) => row.fixedCost, format: fmtMoney },
            { label: "旅客变动成本", color: colors.red, value: (row) => row.passengerCost, format: fmtMoney },
            { label: "拥挤/宽松调整", color: colors.amber, value: (row) => row.congestionCost, format: fmtMoney },
          ],
          line: {
            label: "单客航空成本",
            color: colors.green,
            value: (row) => row.costPerPassenger,
            format: fmtCny,
          },
          valueText: (row) => fmtMoney(row.cost),
          growthHeader: "单客航空成本",
          growthText: (row) => fmtCny(row.costPerPassenger),
          metricValue: (aggregate) => aggregate.cost,
        },
        aviationProfit: moneyMetric("profit", "航空利润", colors.green),
        aviationRevenuePerPassenger: passengerMetric("revenuePerPassenger", "单客航空收入", colors.blue),
        aviationCostPerPassenger: passengerMetric("costPerPassenger", "单客航空成本", colors.red),
        aviationProfitPerPassenger: passengerMetric("profitPerPassenger", "单客航空利润", colors.green),
      };
      return configs[metric] || configs.aviationRevenue;
    }

    function aviationPeriodsAll(scope = state.aviationReportScope, metric = state.aviationMetric) {
      if (!state.operations || !state.operations.quarters.length) return [];
      const metricConfig = aviationMetricConfig(metric);
      const quarters = state.operations.quarters;
      const playerStartIndex = state.operations.playerStartIndex ?? 0;
      const currentIndex = state.operationsQuarterIndex ?? playerStartIndex;
      const currentQuarter = quarters[currentIndex];
      if (!currentQuarter) return [];
      const startYear = Number(quarters[0]?.year || quarters[playerStartIndex]?.year || currentQuarter.year);
      const currentYear = Number(currentQuarter.year);
      const currentQuarterNo = quarterNumber(currentQuarter) || 4;
      const rows = [];
      for (let year = startYear; year <= currentYear; year += 1) {
        const endQuarterNo = scope === "latest" && year < currentYear
          ? 4
          : financialScopeQuarterNo(scope, currentQuarterNo);
        if (year === currentYear && endQuarterNo > currentQuarterNo) continue;
        const periodQuarters = quarters.filter((quarter) => (
          Number(quarter.year) === year
          && quarterNumber(quarter) <= endQuarterNo
        ));
        if (!periodQuarters.length) continue;
        const previousQuarters = quarters.filter((quarter) => (
          Number(quarter.year) === year - 1
          && quarterNumber(quarter) <= endQuarterNo
        ));
        const aggregate = aggregateAviationPeriod(periodQuarters);
        const previousAggregate = aggregateAviationPeriod(previousQuarters);
        const metricValue = metricConfig.metricValue(aggregate);
        const previousMetricValue = metricConfig.metricValue(previousAggregate);
        const yoyPct = previousQuarters.length && previousMetricValue !== 0
          ? ((metricValue - previousMetricValue) / Math.abs(previousMetricValue)) * 100
          : 0;
        const endQuarter = periodQuarters[periodQuarters.length - 1];
        rows.push({
          ...aggregate,
          index: endQuarter.index,
          year,
          quarter: financialPeriodLabel("", endQuarterNo, scope).trim(),
          label: financialPeriodLabel(year, endQuarterNo, scope),
          scope: financialScopeLabel(scope),
          endQuarterNo,
          value: metricValue,
          previousValue: previousMetricValue,
          yoyPct,
        });
      }
      return rows;
    }

    function aviationVisiblePeriods(rows) {
      if (!rows.length) return [];
      const maxStart = Math.max(0, rows.length - AVIATION_WINDOW_SIZE);
      if (state.aviationWindowPinnedToLatest || state.aviationWindowStart == null) {
        state.aviationWindowStart = maxStart;
      }
      state.aviationWindowStart = Math.max(0, Math.min(maxStart, Number(state.aviationWindowStart) || 0));
      return rows.slice(state.aviationWindowStart, state.aviationWindowStart + AVIATION_WINDOW_SIZE);
    }

    function renderAviationBusinessAnalysis() {
      const config = aviationMetricConfig();
      const allRows = aviationPeriodsAll();
      const rows = aviationVisiblePeriods(allRows);
      const maxStart = Math.max(0, allRows.length - AVIATION_WINDOW_SIZE);
      el.aviationMetricButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-aviation-metric") === state.aviationMetric));
      });
      el.aviationMetricTitle.textContent = config.label;
      el.aviationValueHeader.textContent = config.label;
      el.aviationGrowthHeader.textContent = config.growthHeader;
      el.aviationScopeSelect.value = state.aviationReportScope;
      el.aviationRangeInput.min = "0";
      el.aviationRangeInput.max = String(maxStart);
      el.aviationRangeInput.value = String(state.aviationWindowStart || 0);
      el.aviationRangeInput.disabled = maxStart === 0;
      el.aviationTicks.style.gridTemplateColumns = allRows.length
        ? `repeat(${Math.min(allRows.length, AVIATION_WINDOW_SIZE)}, minmax(0, 1fr))`
        : "1fr";
      el.aviationTicks.innerHTML = rows.map((row) => `<span class="financial-tick">${escapeHtml(row.year)}</span>`).join("");
      if (!state.operations || !allRows.length || !rows.length) {
        el.aviationMetricCaption.textContent = config.caption;
        el.aviationMetricChart.innerHTML = `<div class="empty">加载运营后显示${config.label}。</div>`;
        el.aviationMetricRows.innerHTML = `<tr><td colspan="3" style="text-align:center;color:var(--muted)">暂无数据</td></tr>`;
        el.aviationWindowLabel.textContent = "年度轴";
        el.aviationWindowHint.textContent = "暂无历史";
        return;
      }
      const first = rows[0];
      const last = rows[rows.length - 1];
      const scopeLabel = financialScopeLabel(state.aviationReportScope);
      el.aviationMetricCaption.textContent = `${first.label} - ${last.label}；${scopeLabel}；${config.caption}`;
      el.aviationWindowLabel.textContent = `${first.label} - ${last.label}`;
      el.aviationWindowHint.textContent = maxStart > 0 ? "拖动查看历史年份" : "当前口径历史已全部显示";
      renderComboChart(el.aviationMetricChart, rows, {
        title: config.label,
        leftFormat: config.leftFormat,
        bars: config.bars,
        stackedBars: config.stackedBars,
        line: config.line,
      });
      el.aviationMetricRows.innerHTML = rows.slice().reverse().map((row) => `
        <tr>
          <td>${escapeHtml(row.label)}</td>
          <td>${escapeHtml(config.valueText(row))}</td>
          <td>${escapeHtml(config.growthText(row))}</td>
        </tr>
      `).join("");
    }

    function aggregateFoodRetailPeriod(quarters) {
      const sum = (getter) => quarters.reduce((total, quarter) => total + (Number(getter(quarter)) || 0), 0);
      const toOptionalNumber = (value) => {
        if (value === null || value === undefined || value === "") return null;
        const number = Number(value);
        return Number.isFinite(number) ? number : null;
      };
      const sumOptional = (getter) => {
        let total = 0;
        let hasValue = false;
        quarters.forEach((quarter) => {
          const value = toOptionalNumber(getter(quarter));
          if (value === null) return;
          total += value;
          hasValue = true;
        });
        return hasValue ? total : null;
      };
      const passengers = sum((quarter) => quarter.demand.quarterServed);
      const revenue = sum((quarter) => quarter.operations.foodRetailRevenue);
      const fixedCostRaw = sumOptional((quarter) => quarter.operations.foodRetailFixedCost);
      const passengerServiceCostRaw = sumOptional((quarter) => quarter.operations.foodRetailPassengerServiceCost);
      const salesCostRaw = sumOptional((quarter) => quarter.operations.foodRetailSalesCost);
      const reportedCost = sumOptional((quarter) => quarter.operations.foodRetailCost);
      const reportedDirectCost = sumOptional((quarter) => quarter.operations.commercialDirectCost);
      const inferredDirectCost = sumOptional((quarter) => {
        const commercialRevenue = toOptionalNumber(quarter.operations.commercialRevenue);
        const commercialProfit = toOptionalNumber(quarter.operations.commercialProfit);
        return commercialRevenue === null || commercialProfit === null ? null : commercialRevenue - commercialProfit;
      });
      const componentCost = fixedCostRaw === null && passengerServiceCostRaw === null && salesCostRaw === null
        ? null
        : (fixedCostRaw || 0) + (passengerServiceCostRaw || 0) + (salesCostRaw || 0);
      const cost = reportedCost ?? componentCost ?? reportedDirectCost ?? inferredDirectCost ?? 0;
      const fixedCost = fixedCostRaw || 0;
      const passengerServiceCost = passengerServiceCostRaw || 0;
      const salesCost = salesCostRaw || 0;
      const knownSplitCost = fixedCost + passengerServiceCost + salesCost;
      const unallocatedCost = Math.max(0, cost - knownSplitCost);
      const reportedProfit = sumOptional((quarter) => quarter.operations.foodRetailProfit);
      const profit = reportedProfit ?? (revenue - cost);
      return {
        passengers,
        revenue,
        fixedCost,
        passengerServiceCost,
        salesCost,
        unallocatedCost,
        cost,
        profit,
        profitMarginPct: revenue ? (profit / revenue) * 100 : 0,
        revenuePerPassenger: passengers ? revenue / passengers : 0,
        costPerPassenger: passengers ? cost / passengers : 0,
      };
    }

    function foodRetailMetricConfig(metric = state.foodRetailMetric) {
      const styles = getComputedStyle(document.documentElement);
      const colors = {
        blue: styles.getPropertyValue("--blue").trim() || "#62a8ff",
        green: styles.getPropertyValue("--green").trim() || "#35d392",
        amber: styles.getPropertyValue("--amber").trim() || "#f7b84b",
        red: styles.getPropertyValue("--red").trim() || "#fb7185",
      };
      const moneyMetric = (key, label, color) => ({
        label,
        caption: `柱：${label} / 线：同比增幅`,
        leftFormat: fmtMoney,
        bars: [
          { label, color, value: (row) => row[key], format: fmtMoney },
        ],
        line: {
          label: "同比增幅",
          color: colors.amber,
          value: (row) => row.yoyPct,
          format: fmtPct,
        },
        valueText: (row) => fmtMoney(row[key]),
        growthHeader: "同比增幅",
        growthText: (row) => fmtPct(row.yoyPct),
        metricValue: (aggregate) => aggregate[key],
      });
      const passengerMetric = (key, label, color) => ({
        label,
        caption: `柱：${label} / 线：同比增幅`,
        leftFormat: fmtCny,
        bars: [
          { label, color, value: (row) => row[key], format: fmtCny },
        ],
        line: {
          label: "同比增幅",
          color: colors.amber,
          value: (row) => row.yoyPct,
          format: fmtPct,
        },
        valueText: (row) => fmtCny(row[key]),
        growthHeader: "同比增幅",
        growthText: (row) => fmtPct(row.yoyPct),
        metricValue: (aggregate) => aggregate[key],
      });
      const configs = {
        foodRetailRevenue: moneyMetric("revenue", "餐饮零售收入", colors.blue),
        foodRetailCost: moneyMetric("cost", "餐饮零售成本", colors.red),
        foodRetailProfit: moneyMetric("profit", "餐饮零售利润", colors.green),
        foodRetailProfitMargin: {
          label: "餐饮零售利润率",
          caption: "柱：餐饮零售利润率 / 线：同比变化",
          leftFormat: fmtPct,
          rightPad: 76,
          bars: [
            { label: "餐饮零售利润率", color: colors.green, value: (row) => row.profitMarginPct, format: fmtPct },
          ],
          line: {
            label: "同比变化",
            color: colors.amber,
            value: (row) => row.yoyPct,
            format: fmtPctPoint,
          },
          valueText: (row) => fmtPct(row.profitMarginPct),
          growthHeader: "同比变化",
          growthText: (row) => fmtPctPoint(row.yoyPct),
          metricValue: (aggregate) => aggregate.profitMarginPct,
          growthMode: "pointChange",
        },
        foodRetailRevenuePerPassenger: passengerMetric("revenuePerPassenger", "单客餐饮零售收入", colors.blue),
        foodRetailCostPerPassenger: passengerMetric("costPerPassenger", "单客餐饮零售成本", colors.red),
        foodRetailCostBreakdown: {
          label: "餐饮零售成本拆解",
          caption: "堆叠柱：固定/旅客服务/销售/未拆分成本 / 线：单客餐饮零售成本",
          leftFormat: fmtMoney,
          stackedBars: [
            { label: "固定成本", color: colors.blue, value: (row) => row.fixedCost, format: fmtMoney },
            { label: "旅客服务成本", color: colors.red, value: (row) => row.passengerServiceCost, format: fmtMoney },
            { label: "销售成本", color: colors.amber, value: (row) => row.salesCost, format: fmtMoney },
            { label: "未拆分成本", color: "#94a3b8", value: (row) => row.unallocatedCost, format: fmtMoney },
          ],
          line: {
            label: "单客餐饮零售成本",
            color: colors.green,
            value: (row) => row.costPerPassenger,
            format: fmtCny,
          },
          valueText: (row) => fmtMoney(row.cost),
          growthHeader: "单客餐饮零售成本",
          growthText: (row) => fmtCny(row.costPerPassenger),
          metricValue: (aggregate) => aggregate.cost,
        },
      };
      return configs[metric] || configs.foodRetailRevenue;
    }

    function foodRetailPeriodsAll(scope = state.foodRetailReportScope, metric = state.foodRetailMetric) {
      if (!state.operations || !state.operations.quarters.length) return [];
      const metricConfig = foodRetailMetricConfig(metric);
      const quarters = state.operations.quarters;
      const playerStartIndex = state.operations.playerStartIndex ?? 0;
      const currentIndex = state.operationsQuarterIndex ?? playerStartIndex;
      const currentQuarter = quarters[currentIndex];
      if (!currentQuarter) return [];
      const startYear = Number(quarters[0]?.year || quarters[playerStartIndex]?.year || currentQuarter.year);
      const currentYear = Number(currentQuarter.year);
      const currentQuarterNo = quarterNumber(currentQuarter) || 4;
      const rows = [];
      for (let year = startYear; year <= currentYear; year += 1) {
        const endQuarterNo = scope === "latest" && year < currentYear
          ? 4
          : financialScopeQuarterNo(scope, currentQuarterNo);
        if (year === currentYear && endQuarterNo > currentQuarterNo) continue;
        const periodQuarters = quarters.filter((quarter) => (
          Number(quarter.year) === year
          && quarterNumber(quarter) <= endQuarterNo
        ));
        if (!periodQuarters.length) continue;
        const previousQuarters = quarters.filter((quarter) => (
          Number(quarter.year) === year - 1
          && quarterNumber(quarter) <= endQuarterNo
        ));
        const aggregate = aggregateFoodRetailPeriod(periodQuarters);
        const previousAggregate = aggregateFoodRetailPeriod(previousQuarters);
        const metricValue = metricConfig.metricValue(aggregate);
        const previousMetricValue = metricConfig.metricValue(previousAggregate);
        const yoyPct = previousQuarters.length ? financialGrowth(metricValue, previousMetricValue, metricConfig) : 0;
        const endQuarter = periodQuarters[periodQuarters.length - 1];
        rows.push({
          ...aggregate,
          index: endQuarter.index,
          year,
          quarter: financialPeriodLabel("", endQuarterNo, scope).trim(),
          label: financialPeriodLabel(year, endQuarterNo, scope),
          scope: financialScopeLabel(scope),
          endQuarterNo,
          value: metricValue,
          previousValue: previousMetricValue,
          yoyPct,
        });
      }
      return rows;
    }

    function foodRetailVisiblePeriods(rows) {
      if (!rows.length) return [];
      const maxStart = Math.max(0, rows.length - FOOD_RETAIL_WINDOW_SIZE);
      if (state.foodRetailWindowPinnedToLatest || state.foodRetailWindowStart == null) {
        state.foodRetailWindowStart = maxStart;
      }
      state.foodRetailWindowStart = Math.max(0, Math.min(maxStart, Number(state.foodRetailWindowStart) || 0));
      return rows.slice(state.foodRetailWindowStart, state.foodRetailWindowStart + FOOD_RETAIL_WINDOW_SIZE);
    }

    function renderFoodRetailBusinessAnalysis() {
      const config = foodRetailMetricConfig();
      const allRows = foodRetailPeriodsAll();
      const rows = foodRetailVisiblePeriods(allRows);
      const maxStart = Math.max(0, allRows.length - FOOD_RETAIL_WINDOW_SIZE);
      el.foodRetailMetricButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-food-retail-metric") === state.foodRetailMetric));
      });
      el.foodRetailMetricTitle.textContent = config.label;
      el.foodRetailValueHeader.textContent = config.label;
      el.foodRetailGrowthHeader.textContent = config.growthHeader;
      el.foodRetailScopeSelect.value = state.foodRetailReportScope;
      el.foodRetailRangeInput.min = "0";
      el.foodRetailRangeInput.max = String(maxStart);
      el.foodRetailRangeInput.value = String(state.foodRetailWindowStart || 0);
      el.foodRetailRangeInput.disabled = maxStart === 0;
      el.foodRetailTicks.style.gridTemplateColumns = allRows.length
        ? `repeat(${Math.min(allRows.length, FOOD_RETAIL_WINDOW_SIZE)}, minmax(0, 1fr))`
        : "1fr";
      el.foodRetailTicks.innerHTML = rows.map((row) => `<span class="financial-tick">${escapeHtml(row.year)}</span>`).join("");
      if (!state.operations || !allRows.length || !rows.length) {
        el.foodRetailMetricCaption.textContent = config.caption;
        el.foodRetailMetricChart.innerHTML = `<div class="empty">加载运营后显示${config.label}。</div>`;
        el.foodRetailMetricRows.innerHTML = `<tr><td colspan="3" style="text-align:center;color:var(--muted)">暂无数据</td></tr>`;
        el.foodRetailWindowLabel.textContent = "年度轴";
        el.foodRetailWindowHint.textContent = "暂无历史";
        return;
      }
      const first = rows[0];
      const last = rows[rows.length - 1];
      const scopeLabel = financialScopeLabel(state.foodRetailReportScope);
      el.foodRetailMetricCaption.textContent = `${first.label} - ${last.label}；${scopeLabel}；${config.caption}`;
      el.foodRetailWindowLabel.textContent = `${first.label} - ${last.label}`;
      el.foodRetailWindowHint.textContent = maxStart > 0 ? "拖动查看历史年份" : "当前口径历史已全部显示";
      renderComboChart(el.foodRetailMetricChart, rows, {
        title: config.label,
        leftFormat: config.leftFormat,
        rightPad: config.rightPad,
        bars: config.bars,
        stackedBars: config.stackedBars,
        line: config.line,
      });
      el.foodRetailMetricRows.innerHTML = rows.slice().reverse().map((row) => `
        <tr>
          <td>${escapeHtml(row.label)}</td>
          <td>${escapeHtml(config.valueText(row))}</td>
          <td>${escapeHtml(config.growthText(row))}</td>
        </tr>
      `).join("");
    }

    function aggregateDutyFreePeriod(quarters) {
      const sum = (getter) => quarters.reduce((total, quarter) => total + (Number(getter(quarter)) || 0), 0);
      const passengers = sum((quarter) => quarter.demand.quarterServed);
      const weightedPassengers = sum((quarter) => quarter.operations.dutyFreeWeightedPassengers);
      const sales = sum((quarter) => quarter.operations.dutyFreeSales);
      const revenue = sum((quarter) => quarter.operations.dutyFreeRevenue);
      const guarantee = sum((quarter) => quarter.operations.dutyFreeMinimumGuarantee);
      const shareRevenue = sum((quarter) => quarter.operations.dutyFreeShareRevenue);
      const guaranteeRevenue = Math.min(revenue, guarantee);
      const excessShareRevenue = Math.max(0, revenue - guaranteeRevenue);
      return {
        passengers,
        weightedPassengers,
        sales,
        revenue,
        guarantee,
        shareRevenue,
        guaranteeRevenue,
        excessShareRevenue,
        salesPerPassenger: passengers ? sales / passengers : 0,
        salesPerWeightedPassenger: weightedPassengers ? sales / weightedPassengers : 0,
        revenueTakeRatePct: sales ? (revenue / sales) * 100 : 0,
        contractCoveragePct: shareRevenue ? (guarantee / shareRevenue) * 100 : 0,
      };
    }

    function dutyFreeMetricConfig(metric = state.dutyFreeMetric) {
      const styles = getComputedStyle(document.documentElement);
      const colors = {
        blue: styles.getPropertyValue("--blue").trim() || "#62a8ff",
        green: styles.getPropertyValue("--green").trim() || "#35d392",
        amber: styles.getPropertyValue("--amber").trim() || "#f7b84b",
        red: styles.getPropertyValue("--red").trim() || "#fb7185",
        muted: styles.getPropertyValue("--muted").trim() || "#91a0b5",
      };
      const moneyMetric = (key, label, color) => ({
        label,
        caption: `柱：${label} / 线：同比增幅`,
        leftFormat: fmtMoney,
        bars: [
          { label, color, value: (row) => row[key], format: fmtMoney },
        ],
        line: {
          label: "同比增幅",
          color: colors.amber,
          value: (row) => row.yoyPct,
          format: fmtPct,
        },
        valueText: (row) => fmtMoney(row[key]),
        growthHeader: "同比增幅",
        growthText: (row) => fmtPct(row.yoyPct),
        metricValue: (aggregate) => aggregate[key],
      });
      const passengerMetric = (key, label, color) => ({
        label,
        caption: `柱：${label} / 线：同比增幅`,
        leftFormat: fmtCny,
        bars: [
          { label, color, value: (row) => row[key], format: fmtCny },
        ],
        line: {
          label: "同比增幅",
          color: colors.amber,
          value: (row) => row.yoyPct,
          format: fmtPct,
        },
        valueText: (row) => fmtCny(row[key]),
        growthHeader: "同比增幅",
        growthText: (row) => fmtPct(row.yoyPct),
        metricValue: (aggregate) => aggregate[key],
      });
      const configs = {
        dutyFreeRevenue: moneyMetric("revenue", "免税收入", colors.green),
        dutyFreeSales: moneyMetric("sales", "免税销售额", colors.blue),
        dutyFreeContractBreakdown: {
          label: "免税合同收入拆解",
          caption: "堆叠柱：保底收入/超额分成 / 线：保底覆盖率",
          leftFormat: fmtMoney,
          rightPad: 76,
          stackedBars: [
            { label: "保底收入", color: colors.blue, value: (row) => row.guaranteeRevenue, format: fmtMoney },
            { label: "超额分成", color: colors.green, value: (row) => row.excessShareRevenue, format: fmtMoney },
          ],
          line: {
            label: "保底覆盖率",
            color: colors.amber,
            value: (row) => row.contractCoveragePct,
            format: fmtPct,
          },
          valueText: (row) => fmtMoney(row.revenue),
          growthHeader: "保底覆盖率",
          growthText: (row) => fmtPct(row.contractCoveragePct),
          metricValue: (aggregate) => aggregate.revenue,
        },
        dutyFreeSalesPerPassenger: passengerMetric("salesPerPassenger", "单客免税销售额", colors.blue),
        dutyFreeContractCoverage: {
          label: "免税合同覆盖率",
          caption: "柱：保底覆盖率 / 线：同比变化",
          leftFormat: fmtPct,
          rightPad: 76,
          bars: [
            { label: "保底覆盖率", color: colors.green, value: (row) => row.contractCoveragePct, format: fmtPct },
          ],
          line: {
            label: "同比变化",
            color: colors.amber,
            value: (row) => row.yoyPct,
            format: fmtPctPoint,
          },
          valueText: (row) => fmtPct(row.contractCoveragePct),
          growthHeader: "同比变化",
          growthText: (row) => fmtPctPoint(row.yoyPct),
          metricValue: (aggregate) => aggregate.contractCoveragePct,
          growthMode: "pointChange",
        },
      };
      return configs[metric] || configs.dutyFreeRevenue;
    }

    function dutyFreePeriodsAll(scope = state.dutyFreeReportScope, metric = state.dutyFreeMetric) {
      if (!state.operations || !state.operations.quarters.length) return [];
      const metricConfig = dutyFreeMetricConfig(metric);
      const quarters = state.operations.quarters;
      const playerStartIndex = state.operations.playerStartIndex ?? 0;
      const currentIndex = state.operationsQuarterIndex ?? playerStartIndex;
      const currentQuarter = quarters[currentIndex];
      if (!currentQuarter) return [];
      const startYear = Number(quarters[0]?.year || quarters[playerStartIndex]?.year || currentQuarter.year);
      const currentYear = Number(currentQuarter.year);
      const currentQuarterNo = quarterNumber(currentQuarter) || 4;
      const rows = [];
      for (let year = startYear; year <= currentYear; year += 1) {
        const endQuarterNo = scope === "latest" && year < currentYear
          ? 4
          : financialScopeQuarterNo(scope, currentQuarterNo);
        if (year === currentYear && endQuarterNo > currentQuarterNo) continue;
        const periodQuarters = quarters.filter((quarter) => (
          Number(quarter.year) === year
          && quarterNumber(quarter) <= endQuarterNo
        ));
        if (!periodQuarters.length) continue;
        const previousQuarters = quarters.filter((quarter) => (
          Number(quarter.year) === year - 1
          && quarterNumber(quarter) <= endQuarterNo
        ));
        const aggregate = aggregateDutyFreePeriod(periodQuarters);
        const previousAggregate = aggregateDutyFreePeriod(previousQuarters);
        const metricValue = metricConfig.metricValue(aggregate);
        const previousMetricValue = metricConfig.metricValue(previousAggregate);
        const yoyPct = previousQuarters.length ? financialGrowth(metricValue, previousMetricValue, metricConfig) : 0;
        const endQuarter = periodQuarters[periodQuarters.length - 1];
        rows.push({
          ...aggregate,
          index: endQuarter.index,
          year,
          quarter: financialPeriodLabel("", endQuarterNo, scope).trim(),
          label: financialPeriodLabel(year, endQuarterNo, scope),
          scope: financialScopeLabel(scope),
          endQuarterNo,
          value: metricValue,
          previousValue: previousMetricValue,
          yoyPct,
        });
      }
      return rows;
    }

    function dutyFreeVisiblePeriods(rows) {
      if (!rows.length) return [];
      const maxStart = Math.max(0, rows.length - DUTY_FREE_WINDOW_SIZE);
      if (state.dutyFreeWindowPinnedToLatest || state.dutyFreeWindowStart == null) {
        state.dutyFreeWindowStart = maxStart;
      }
      state.dutyFreeWindowStart = Math.max(0, Math.min(maxStart, Number(state.dutyFreeWindowStart) || 0));
      return rows.slice(state.dutyFreeWindowStart, state.dutyFreeWindowStart + DUTY_FREE_WINDOW_SIZE);
    }

    function renderDutyFreeBusinessAnalysis() {
      const config = dutyFreeMetricConfig();
      const allRows = dutyFreePeriodsAll();
      const rows = dutyFreeVisiblePeriods(allRows);
      const maxStart = Math.max(0, allRows.length - DUTY_FREE_WINDOW_SIZE);
      el.dutyFreeMetricButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-duty-free-metric") === state.dutyFreeMetric));
      });
      el.dutyFreeMetricTitle.textContent = config.label;
      el.dutyFreeValueHeader.textContent = config.label;
      el.dutyFreeGrowthHeader.textContent = config.growthHeader;
      el.dutyFreeScopeSelect.value = state.dutyFreeReportScope;
      el.dutyFreeRangeInput.min = "0";
      el.dutyFreeRangeInput.max = String(maxStart);
      el.dutyFreeRangeInput.value = String(state.dutyFreeWindowStart || 0);
      el.dutyFreeRangeInput.disabled = maxStart === 0;
      el.dutyFreeTicks.style.gridTemplateColumns = allRows.length
        ? `repeat(${Math.min(allRows.length, DUTY_FREE_WINDOW_SIZE)}, minmax(0, 1fr))`
        : "1fr";
      el.dutyFreeTicks.innerHTML = rows.map((row) => `<span class="financial-tick">${escapeHtml(row.year)}</span>`).join("");
      if (!state.operations || !allRows.length || !rows.length) {
        el.dutyFreeMetricCaption.textContent = config.caption;
        el.dutyFreeMetricChart.innerHTML = `<div class="empty">加载运营后显示${config.label}。</div>`;
        el.dutyFreeMetricRows.innerHTML = `<tr><td colspan="3" style="text-align:center;color:var(--muted)">暂无数据</td></tr>`;
        el.dutyFreeWindowLabel.textContent = "年度轴";
        el.dutyFreeWindowHint.textContent = "暂无历史";
        return;
      }
      const first = rows[0];
      const last = rows[rows.length - 1];
      const scopeLabel = financialScopeLabel(state.dutyFreeReportScope);
      el.dutyFreeMetricCaption.textContent = `${first.label} - ${last.label}；${scopeLabel}；${config.caption}`;
      el.dutyFreeWindowLabel.textContent = `${first.label} - ${last.label}`;
      el.dutyFreeWindowHint.textContent = maxStart > 0 ? "拖动查看历史年份" : "当前口径历史已全部显示";
      renderComboChart(el.dutyFreeMetricChart, rows, {
        title: config.label,
        leftFormat: config.leftFormat,
        rightPad: config.rightPad,
        bars: config.bars,
        stackedBars: config.stackedBars,
        line: config.line,
      });
      el.dutyFreeMetricRows.innerHTML = rows.slice().reverse().map((row) => `
        <tr>
          <td>${escapeHtml(row.label)}</td>
          <td>${escapeHtml(config.valueText(row))}</td>
          <td>${escapeHtml(config.growthText(row))}</td>
        </tr>
      `).join("");
    }

    function aggregateLuxuryPeriod(quarters) {
      const sum = (getter) => quarters.reduce((total, quarter) => total + (Number(getter(quarter)) || 0), 0);
      const passengers = sum((quarter) => quarter.demand.quarterServed);
      const weightedPassengers = sum((quarter) => quarter.operations.luxuryWeightedPassengers);
      const sales = sum((quarter) => quarter.operations.luxurySales);
      const revenue = sum((quarter) => quarter.operations.luxuryRevenue);
      const guarantee = sum((quarter) => quarter.operations.luxuryMinimumGuarantee);
      const shareRevenue = sum((quarter) => quarter.operations.luxuryShareRevenue);
      const guaranteeRevenue = Math.min(revenue, guarantee);
      const excessShareRevenue = Math.max(0, revenue - guaranteeRevenue);
      return {
        passengers,
        weightedPassengers,
        sales,
        revenue,
        guarantee,
        shareRevenue,
        guaranteeRevenue,
        excessShareRevenue,
        salesPerPassenger: passengers ? sales / passengers : 0,
        salesPerWeightedPassenger: weightedPassengers ? sales / weightedPassengers : 0,
        revenueTakeRatePct: sales ? (revenue / sales) * 100 : 0,
        contractCoveragePct: shareRevenue ? (guarantee / shareRevenue) * 100 : 0,
      };
    }

    function luxuryMetricConfig(metric = state.luxuryMetric) {
      const styles = getComputedStyle(document.documentElement);
      const colors = {
        blue: styles.getPropertyValue("--blue").trim() || "#62a8ff",
        green: styles.getPropertyValue("--green").trim() || "#35d392",
        amber: styles.getPropertyValue("--amber").trim() || "#f7b84b",
        red: styles.getPropertyValue("--red").trim() || "#fb7185",
        muted: styles.getPropertyValue("--muted").trim() || "#91a0b5",
      };
      const moneyMetric = (key, label, color) => ({
        label,
        caption: `柱：${label} / 线：同比增幅`,
        leftFormat: fmtMoney,
        bars: [
          { label, color, value: (row) => row[key], format: fmtMoney },
        ],
        line: {
          label: "同比增幅",
          color: colors.amber,
          value: (row) => row.yoyPct,
          format: fmtPct,
        },
        valueText: (row) => fmtMoney(row[key]),
        growthHeader: "同比增幅",
        growthText: (row) => fmtPct(row.yoyPct),
        metricValue: (aggregate) => aggregate[key],
      });
      const passengerMetric = (key, label, color) => ({
        label,
        caption: `柱：${label} / 线：同比增幅`,
        leftFormat: fmtCny,
        bars: [
          { label, color, value: (row) => row[key], format: fmtCny },
        ],
        line: {
          label: "同比增幅",
          color: colors.amber,
          value: (row) => row.yoyPct,
          format: fmtPct,
        },
        valueText: (row) => fmtCny(row[key]),
        growthHeader: "同比增幅",
        growthText: (row) => fmtPct(row.yoyPct),
        metricValue: (aggregate) => aggregate[key],
      });
      const configs = {
        luxuryRevenue: moneyMetric("revenue", "奢侈品收入", colors.green),
        luxurySales: moneyMetric("sales", "奢侈品销售额", colors.blue),
        luxuryContractBreakdown: {
          label: "奢侈品合同收入拆解",
          caption: "堆叠柱：保底收入/超额分成 / 线：保底覆盖率",
          leftFormat: fmtMoney,
          rightPad: 76,
          stackedBars: [
            { label: "保底收入", color: colors.blue, value: (row) => row.guaranteeRevenue, format: fmtMoney },
            { label: "超额分成", color: colors.green, value: (row) => row.excessShareRevenue, format: fmtMoney },
          ],
          line: {
            label: "保底覆盖率",
            color: colors.amber,
            value: (row) => row.contractCoveragePct,
            format: fmtPct,
          },
          valueText: (row) => fmtMoney(row.revenue),
          growthHeader: "保底覆盖率",
          growthText: (row) => fmtPct(row.contractCoveragePct),
          metricValue: (aggregate) => aggregate.revenue,
        },
        luxurySalesPerPassenger: passengerMetric("salesPerPassenger", "单客奢侈品销售额", colors.blue),
        luxuryContractCoverage: {
          label: "奢侈品合同覆盖率",
          caption: "柱：保底覆盖率 / 线：同比变化",
          leftFormat: fmtPct,
          rightPad: 76,
          bars: [
            { label: "保底覆盖率", color: colors.green, value: (row) => row.contractCoveragePct, format: fmtPct },
          ],
          line: {
            label: "同比变化",
            color: colors.amber,
            value: (row) => row.yoyPct,
            format: fmtPctPoint,
          },
          valueText: (row) => fmtPct(row.contractCoveragePct),
          growthHeader: "同比变化",
          growthText: (row) => fmtPctPoint(row.yoyPct),
          metricValue: (aggregate) => aggregate.contractCoveragePct,
          growthMode: "pointChange",
        },
      };
      return configs[metric] || configs.luxuryRevenue;
    }

    function luxuryPeriodsAll(scope = state.luxuryReportScope, metric = state.luxuryMetric) {
      if (!state.operations || !state.operations.quarters.length) return [];
      const metricConfig = luxuryMetricConfig(metric);
      const quarters = state.operations.quarters;
      const playerStartIndex = state.operations.playerStartIndex ?? 0;
      const currentIndex = state.operationsQuarterIndex ?? playerStartIndex;
      const currentQuarter = quarters[currentIndex];
      if (!currentQuarter) return [];
      const startYear = Number(quarters[0]?.year || quarters[playerStartIndex]?.year || currentQuarter.year);
      const currentYear = Number(currentQuarter.year);
      const currentQuarterNo = quarterNumber(currentQuarter) || 4;
      const rows = [];
      for (let year = startYear; year <= currentYear; year += 1) {
        const endQuarterNo = scope === "latest" && year < currentYear
          ? 4
          : financialScopeQuarterNo(scope, currentQuarterNo);
        if (year === currentYear && endQuarterNo > currentQuarterNo) continue;
        const periodQuarters = quarters.filter((quarter) => (
          Number(quarter.year) === year
          && quarterNumber(quarter) <= endQuarterNo
        ));
        if (!periodQuarters.length) continue;
        const previousQuarters = quarters.filter((quarter) => (
          Number(quarter.year) === year - 1
          && quarterNumber(quarter) <= endQuarterNo
        ));
        const aggregate = aggregateLuxuryPeriod(periodQuarters);
        const previousAggregate = aggregateLuxuryPeriod(previousQuarters);
        const metricValue = metricConfig.metricValue(aggregate);
        const previousMetricValue = metricConfig.metricValue(previousAggregate);
        const yoyPct = previousQuarters.length ? financialGrowth(metricValue, previousMetricValue, metricConfig) : 0;
        const endQuarter = periodQuarters[periodQuarters.length - 1];
        rows.push({
          ...aggregate,
          index: endQuarter.index,
          year,
          quarter: financialPeriodLabel("", endQuarterNo, scope).trim(),
          label: financialPeriodLabel(year, endQuarterNo, scope),
          scope: financialScopeLabel(scope),
          endQuarterNo,
          value: metricValue,
          previousValue: previousMetricValue,
          yoyPct,
        });
      }
      return rows;
    }

    function luxuryVisiblePeriods(rows) {
      if (!rows.length) return [];
      const maxStart = Math.max(0, rows.length - LUXURY_WINDOW_SIZE);
      if (state.luxuryWindowPinnedToLatest || state.luxuryWindowStart == null) {
        state.luxuryWindowStart = maxStart;
      }
      state.luxuryWindowStart = Math.max(0, Math.min(maxStart, Number(state.luxuryWindowStart) || 0));
      return rows.slice(state.luxuryWindowStart, state.luxuryWindowStart + LUXURY_WINDOW_SIZE);
    }

    function renderLuxuryBusinessAnalysis() {
      const config = luxuryMetricConfig();
      const allRows = luxuryPeriodsAll();
      const rows = luxuryVisiblePeriods(allRows);
      const maxStart = Math.max(0, allRows.length - LUXURY_WINDOW_SIZE);
      el.luxuryMetricButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-luxury-metric") === state.luxuryMetric));
      });
      el.luxuryMetricTitle.textContent = config.label;
      el.luxuryValueHeader.textContent = config.label;
      el.luxuryGrowthHeader.textContent = config.growthHeader;
      el.luxuryScopeSelect.value = state.luxuryReportScope;
      el.luxuryRangeInput.min = "0";
      el.luxuryRangeInput.max = String(maxStart);
      el.luxuryRangeInput.value = String(state.luxuryWindowStart || 0);
      el.luxuryRangeInput.disabled = maxStart === 0;
      el.luxuryTicks.style.gridTemplateColumns = allRows.length
        ? `repeat(${Math.min(allRows.length, LUXURY_WINDOW_SIZE)}, minmax(0, 1fr))`
        : "1fr";
      el.luxuryTicks.innerHTML = rows.map((row) => `<span class="financial-tick">${escapeHtml(row.year)}</span>`).join("");
      if (!state.operations || !allRows.length || !rows.length) {
        el.luxuryMetricCaption.textContent = config.caption;
        el.luxuryMetricChart.innerHTML = `<div class="empty">加载运营后显示${config.label}。</div>`;
        el.luxuryMetricRows.innerHTML = `<tr><td colspan="3" style="text-align:center;color:var(--muted)">暂无数据</td></tr>`;
        el.luxuryWindowLabel.textContent = "年度轴";
        el.luxuryWindowHint.textContent = "暂无历史";
        return;
      }
      const first = rows[0];
      const last = rows[rows.length - 1];
      const scopeLabel = financialScopeLabel(state.luxuryReportScope);
      el.luxuryMetricCaption.textContent = `${first.label} - ${last.label}；${scopeLabel}；${config.caption}`;
      el.luxuryWindowLabel.textContent = `${first.label} - ${last.label}`;
      el.luxuryWindowHint.textContent = maxStart > 0 ? "拖动查看历史年份" : "当前口径历史已全部显示";
      renderComboChart(el.luxuryMetricChart, rows, {
        title: config.label,
        leftFormat: config.leftFormat,
        rightPad: config.rightPad,
        bars: config.bars,
        stackedBars: config.stackedBars,
        line: config.line,
      });
      el.luxuryMetricRows.innerHTML = rows.slice().reverse().map((row) => `
        <tr>
          <td>${escapeHtml(row.label)}</td>
          <td>${escapeHtml(config.valueText(row))}</td>
          <td>${escapeHtml(config.growthText(row))}</td>
        </tr>
      `).join("");
    }

