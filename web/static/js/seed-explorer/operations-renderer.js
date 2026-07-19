    function renderOperationCharts() {
      const rows = operationWindow();
      const styles = getComputedStyle(document.documentElement);
      const colors = {
        blue: styles.getPropertyValue("--blue").trim() || "#62a8ff",
        green: styles.getPropertyValue("--green").trim() || "#35d392",
        amber: styles.getPropertyValue("--amber").trim() || "#f7b84b",
        red: styles.getPropertyValue("--red").trim() || "#fb7185",
        muted: styles.getPropertyValue("--muted").trim() || "#91a0b5",
      };
      renderTrafficCapacityAnalysis();
      renderFacilitiesProjectAnalysis();
      renderAviationBusinessAnalysis();
      renderFoodRetailBusinessAnalysis();
      renderDutyFreeBusinessAnalysis();
      renderLuxuryBusinessAnalysis();
      renderContractPartnershipAnalysis();
      renderComboChart(el.opsTrafficChart, rows, {
        title: "客流与容量",
        leftFormat: (value) => fmt(value, 0),
        bars: [
          { label: "承接客流", color: colors.blue, value: (q) => q.demand.quarterServed, format: fmtPassenger },
        ],
        line: {
          label: "设计利用率",
          color: colors.amber,
          value: (q) => q.capacity.designUtilizationPct,
          format: (value) => fmtPct(value),
        },
      });
      renderComboChart(el.opsProfitChart, rows, {
        title: "经营损益",
        leftFormat: (value) => fmtMoney(value),
        bars: [
          { label: "收入", color: colors.blue, value: (q) => q.operations.totalRevenue, format: fmtMoney },
          { label: "成本", color: colors.red, value: (q) => q.operations.totalCost, format: fmtMoney },
          { label: "利润", color: colors.green, value: (q) => q.operations.operatingProfit, format: fmtMoney },
        ],
        line: {
          label: "利润率",
          color: colors.amber,
          value: (q) => q.operations.operatingMarginPct,
          format: (value) => fmtPct(value),
        },
      });
      renderComboChart(el.opsCashChart, rows, {
        title: "现金与债务",
        leftFormat: (value) => fmtMoney(value),
        bars: [
          { label: "现金", color: colors.blue, value: (q) => q.finance.endCash, format: fmtMoney },
          { label: "资本开支", color: colors.amber, value: (q) => q.finance.capexOutlay, format: fmtMoney },
          { label: "债务服务", color: colors.red, value: (q) => q.finance.debtService, format: fmtMoney },
        ],
        line: {
          label: "资产负债率",
          color: colors.green,
          value: (q) => q.finance.liabilityRatioPct,
          format: (value) => fmtPct(value),
        },
      });
    }

    function renderCashFlowAnalysis() {
      const allRows = cashFlowPeriodsAll();
      const rows = netProfitVisiblePeriods(allRows);
      const maxStart = Math.max(0, allRows.length - NET_PROFIT_WINDOW_SIZE);
      el.financialMetricTitle.textContent = "现金流分析";
      el.financialHeaderRow.closest("table")?.classList.add("cash-flow-table");
      el.financialHeaderRow.innerHTML = `
        <th>期间</th>
        <th>经营现金流</th>
        <th>投资现金流</th>
        <th>融资前自由现金流</th>
        <th>贷款提款</th>
        <th>本金偿还</th>
        <th>利息支付</th>
        <th>现金净变化</th>
        <th>期末现金</th>
      `;
      el.netProfitRangeInput.min = "0";
      el.netProfitRangeInput.max = String(maxStart);
      el.netProfitRangeInput.value = String(state.netProfitWindowStart || 0);
      el.netProfitRangeInput.disabled = maxStart === 0;
      el.netProfitTicks.style.gridTemplateColumns = allRows.length
        ? `repeat(${Math.min(allRows.length, NET_PROFIT_WINDOW_SIZE)}, minmax(0, 1fr))`
        : "1fr";
      el.netProfitTicks.innerHTML = rows.map((row) => `<span class="financial-tick">${escapeHtml(row.year)}</span>`).join("");
      if (!allRows.length || !rows.length) {
        el.financialCashFlowSummary.hidden = true;
        el.financialCashFlowSummary.innerHTML = "";
        el.netProfitCaption.textContent = "堆叠柱：经营/投资/融资/利息；线：本期现金净变化（同轴）";
        el.netProfitChart.innerHTML = `<div class="empty">加载运营后显示现金流构成与本期现金净变化。</div>`;
        el.netProfitRows.innerHTML = `<tr><td colspan="9" style="text-align:center;color:var(--muted)">暂无数据</td></tr>`;
        el.netProfitWindowLabel.textContent = "年度轴";
        el.netProfitWindowHint.textContent = "暂无历史";
        return;
      }
      const first = rows[0];
      const last = rows[rows.length - 1];
      const scopeLabel = financialScopeLabel(state.financialReportScope);
      el.financialCashFlowSummary.hidden = false;
      el.financialCashFlowSummary.innerHTML = [
        metric("融资前自由现金流", fmtMoney(last.freeCashFlowBeforeFinancing), `${last.label}；经营现金流 + 投资现金流`),
        metric("净融资现金流", fmtMoney(last.financingCashFlow), `提款 ${fmtMoney(last.loanDrawdown)} / 还本 ${fmtMoney(last.principalRepayment)}`),
        metric("利息支付", fmtMoney(last.interestPayment), "现金流出以负数显示"),
        metric("本期现金净变化", fmtMoney(last.cashNetChange), `期末现金 ${fmtMoney(last.endCash)}`),
      ].join("");
      el.netProfitCaption.textContent = `${first.label} - ${last.label}；${scopeLabel}；简化经营现金流 = 经营利润 - 现金税；折线与柱形共用金额轴`;
      el.netProfitWindowLabel.textContent = `${first.label} - ${last.label}`;
      el.netProfitWindowHint.textContent = maxStart > 0 ? "拖动查看历史年份" : "当前口径历史已全部显示";
      const styles = getComputedStyle(document.documentElement);
      renderComboChart(el.netProfitChart, rows, {
        title: "现金流分析",
        leftFormat: fmtMoney,
        stackedBars: [
          { label: "经营现金流", color: styles.getPropertyValue("--green").trim() || "#35d392", value: (row) => row.operatingCashFlow, format: fmtMoney },
          { label: "投资现金流", color: styles.getPropertyValue("--amber").trim() || "#f7b84b", value: (row) => row.investingCashFlow, format: fmtMoney },
          { label: "净融资现金流", color: "#a78bfa", value: (row) => row.financingCashFlow, format: fmtMoney },
          { label: "利息支付", color: styles.getPropertyValue("--red").trim() || "#fb7185", value: (row) => row.interestPayment, format: fmtMoney },
        ],
        line: {
          label: "本期现金净变化",
          color: styles.getPropertyValue("--blue").trim() || "#62a8ff",
          value: (row) => row.cashNetChange,
          format: fmtMoney,
          axis: "left",
        },
      });
      el.netProfitRows.innerHTML = rows.slice().reverse().map((row) => `
        <tr>
          <td>${escapeHtml(row.label)}</td>
          <td>${fmtMoney(row.operatingCashFlow)}</td>
          <td>${fmtMoney(row.investingCashFlow)}</td>
          <td>${fmtMoney(row.freeCashFlowBeforeFinancing)}</td>
          <td>${fmtMoney(row.loanDrawdown)}</td>
          <td>${fmtMoney(row.principalRepayment)}</td>
          <td>${fmtMoney(row.interestPayment)}</td>
          <td>${fmtMoney(row.cashNetChange)}</td>
          <td>${fmtMoney(row.endCash)}</td>
        </tr>
      `).join("");
    }

    function renderFinancialAnalysis() {
      el.financialMetricButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-financial-metric") === state.financialMetric));
      });
      el.financialScopeSelect.value = state.financialReportScope;
      if (state.financialMetric === "freeCashFlow") {
        renderCashFlowAnalysis();
        return;
      }
      const metricConfig = financialMetricConfig();
      const allRows = netProfitPeriodsAll();
      const rows = netProfitVisiblePeriods(allRows);
      const maxStart = Math.max(0, allRows.length - NET_PROFIT_WINDOW_SIZE);
      el.financialCashFlowSummary.hidden = true;
      el.financialCashFlowSummary.innerHTML = "";
      el.financialHeaderRow.closest("table")?.classList.remove("cash-flow-table");
      el.financialHeaderRow.innerHTML = `
        <th>期间</th>
        <th>${escapeHtml(metricConfig.label)}</th>
        <th>${escapeHtml(metricConfig.growthLabel)}</th>
      `;
      el.financialMetricTitle.textContent = metricConfig.label;
      el.netProfitRangeInput.min = "0";
      el.netProfitRangeInput.max = String(maxStart);
      el.netProfitRangeInput.value = String(state.netProfitWindowStart || 0);
      el.netProfitRangeInput.disabled = maxStart === 0;
      el.netProfitTicks.style.gridTemplateColumns = allRows.length
        ? `repeat(${Math.min(allRows.length, NET_PROFIT_WINDOW_SIZE)}, minmax(0, 1fr))`
        : "1fr";
      el.netProfitTicks.innerHTML = rows.map((row) => `<span class="financial-tick">${escapeHtml(row.year)}</span>`).join("");
      if (!allRows.length || !rows.length) {
        el.netProfitCaption.textContent = `柱：${metricConfig.label} / 线：${metricConfig.growthLabel}`;
        el.netProfitChart.innerHTML = `<div class="empty">加载运营后显示${metricConfig.label}与${metricConfig.growthLabel}。</div>`;
        el.netProfitRows.innerHTML = `<tr><td colspan="3" style="text-align:center;color:var(--muted)">暂无数据</td></tr>`;
        el.netProfitWindowLabel.textContent = "年度轴";
        el.netProfitWindowHint.textContent = "暂无历史";
        return;
      }
      const styles = getComputedStyle(document.documentElement);
      const colors = {
        blue: styles.getPropertyValue("--blue").trim() || "#62a8ff",
        amber: styles.getPropertyValue("--amber").trim() || "#f7b84b",
      };
      const first = rows[0];
      const last = rows[rows.length - 1];
      const scopeLabel = financialScopeLabel(state.financialReportScope);
      el.netProfitCaption.textContent = `${first.label} - ${last.label}；${scopeLabel}；柱：${metricConfig.label} / 线：${metricConfig.growthLabel}`;
      el.netProfitWindowLabel.textContent = `${first.label} - ${last.label}`;
      el.netProfitWindowHint.textContent = maxStart > 0 ? "拖动查看历史年份" : "当前口径历史已全部显示";
      renderComboChart(el.netProfitChart, rows, {
        title: metricConfig.label,
        leftFormat: metricConfig.leftFormat,
        rightPad: metricConfig.rightPad,
        bars: [
          { label: metricConfig.label, color: colors.blue, value: (row) => row.value, format: metricConfig.valueFormat },
        ],
        line: {
          label: metricConfig.growthLabel,
          color: colors.amber,
          value: (row) => row.yoyPct,
          format: metricConfig.growthFormat,
        },
      });
      el.netProfitRows.innerHTML = rows.slice().reverse().map((row) => `
        <tr>
          <td>${escapeHtml(row.label)}</td>
          <td>${metricConfig.valueFormat(row.value)}</td>
          <td>${metricConfig.growthFormat(row.yoyPct)}</td>
        </tr>
      `).join("");
    }

    function renderOperations() {
      const quarter = currentOperationQuarter();
      if (!state.operations || !quarter) {
        setOperationModeVisual(null);
        renderSimSaveSlots();
        el.opsTitle.textContent = "北京运营模拟";
        el.opsCaption.textContent = "使用当前 seed 的北京季度经营和财务输出；第一版先按季度推进查看报表。";
        el.opsQuarterCaption.textContent = "尚未加载";
        renderFinancialAnalysis();
        el.opsSummaryGrid.innerHTML = "";
        renderTrafficCapacityAnalysis();
        renderServiceQualityAnalysis();
        renderAviationBusinessAnalysis();
        renderFoodRetailBusinessAnalysis();
        renderDebtFinancingAnalysis();
        renderContractPartnershipAnalysis();
        renderContractAffairs();
        renderProjectAffairs();
        renderFinancingAffairs();
        el.opsTrafficChart.innerHTML = `<div class="empty">暂无数据</div>`;
        el.opsProfitChart.innerHTML = `<div class="empty">暂无数据</div>`;
        el.opsCashChart.innerHTML = `<div class="empty">暂无数据</div>`;
        el.opsReportGrid.innerHTML = `<div class="empty">加载运营后，从 2030Q1 开始逐季查看。</div>`;
        el.opsRiskBody.innerHTML = `<div class="empty">暂无季度</div>`;
        el.opsComponentRows.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--muted)">暂无数据</td></tr>`;
        renderFacilitiesProjectAnalysis();
        el.prevQuarterButton.disabled = true;
        el.nextQuarterButton.disabled = !contextCacheReady();
        return;
      }

      const index = state.operationsQuarterIndex;
      const demand = quarter.demand;
      const capacity = quarter.capacity;
      const operations = quarter.operations;
      const finance = quarter.finance;
      const cashFlow = aggregateCashFlowPeriod([quarter]);
      const projects = quarter.projects;
      const playerStartIndex = state.operations.playerStartIndex ?? 0;
      const playerQuarterIndex = index - playerStartIndex + 1;
      const worldPeriodCount = Number(state.operations.worldPeriodCount || state.operations.quarters.length);
      const playerQuarterCount = worldPeriodCount - playerStartIndex;
      const operationMode = state.operations.mode || "replay";
      setOperationModeVisual(operationMode);
      renderSimSaveSlots();
      el.opsTitle.textContent = `北京运营模拟：${quarter.label}`;
      el.opsCaption.textContent = `Seed ${state.operations.seed} / 已推进 ${state.operations.periodCount} / 共 ${worldPeriodCount} 个季度 / ${operationModeLabel(operationMode)} / ${operationCacheLabel(state.operations)} / ${state.operations.runDir}`;
      el.opsQuarterCaption.textContent = `${phaseLabel(quarter.gamePhase)}，玩家期第 ${playerQuarterIndex} / ${playerQuarterCount} 季`;
      el.opsRiskCaption.textContent = quarter.warnings.length ? "本季有需要关注的压力" : "本季无显著警告";
      el.prevQuarterButton.disabled = index <= playerStartIndex;
      el.nextQuarterButton.disabled = index >= Number(state.operations.worldPeriodCount || state.operations.quarters.length) - 1;

      el.opsSummaryGrid.innerHTML = [
        metric("本季承接客流", fmtPassenger(demand.quarterServed), `瓶颈 ${bottleneckLabel(demand.bindingBottleneck)}`),
        metric("经营利润", fmtMoney(operations.operatingProfit), `利润率 ${fmtPct(operations.operatingMarginPct)}`),
        metric("期末现金", fmtMoney(finance.endCash), `本期净变化 ${fmtMoney(cashFlow.cashNetChange)}；融资前 ${fmtMoney(cashFlow.freeCashFlowBeforeFinancing)}`),
        metric("资产负债率", fmtPct(finance.liabilityRatioPct), `负债 ${fmtMoney(finance.totalLiabilities)}`),
      ].join("");
      renderFinancialAnalysis();
      if (state.opsReportSection === "debtFinancing") renderDebtFinancingAnalysis();
      if (state.opsReportSection === "contractPartnership") renderContractPartnershipAnalysis();
      if (state.opsReportSection === "serviceQuality") renderServiceQualityAnalysis();
      if (state.opsModule === "contractAffairs") renderContractAffairs();
      if (state.opsModule === "projectAffairs") renderProjectAffairs();
      if (state.opsModule === "financingAffairs") renderFinancingAffairs();
      renderOperationCharts();

      el.opsReportGrid.innerHTML = [
        reportBlock("客流", [
          reportRow("季度潜在客流", fmtPassenger(demand.quarterPotential)),
          reportRow("航司供给", fmtPassenger(demand.quarterAirlineSupply)),
          reportRow("可服务需求", fmtPassenger(demand.quarterServiceableDemand)),
          reportRow("实际承接", fmtPassenger(demand.quarterServed)),
          reportRow("容量损失", fmtPassenger(demand.capacityLost)),
        ]),
        reportBlock("容量", [
          reportRow("季度设计容量", fmtPassenger(capacity.quarterDesignCapacity)),
          reportRow("季度极限容量", fmtPassenger(capacity.quarterMaxCapacity)),
          reportRow("设计利用率", fmtPct(capacity.designUtilizationPct)),
          reportRow("极限利用率", fmtPct(capacity.maxUtilizationPct)),
          reportRow("感知质量", fmt(capacity.perceivedQualityIndex, 1)),
        ]),
        reportBlock("经营损益", [
          reportRow("总收入", fmtMoney(operations.totalRevenue)),
          reportRow("总成本", fmtMoney(operations.totalCost)),
          reportRow("航空收入", fmtMoney(operations.aeronauticalRevenue)),
          reportRow("商业收入", fmtMoney(operations.commercialRevenue)),
          reportRow("拥挤成本", fmtMoney(operations.congestionCost)),
        ]),
        reportBlock("财务", [
          reportRow("期初现金", fmtMoney(finance.beginCash)),
          reportRow("期末现金", fmtMoney(finance.endCash)),
          reportRow("经营现金流（简化）", fmtMoney(cashFlow.operatingCashFlow)),
          reportRow("投资现金流", fmtMoney(cashFlow.investingCashFlow)),
          reportRow("融资前自由现金流", fmtMoney(cashFlow.freeCashFlowBeforeFinancing)),
          reportRow("净融资现金流", fmtMoney(cashFlow.financingCashFlow)),
          reportRow("本期现金净变化", fmtMoney(cashFlow.cashNetChange)),
          reportRow("折旧", fmtMoney(finance.accountingDepreciation)),
          reportRow("利息", fmtMoney(finance.interestExpense)),
          reportRow("现金税", fmtMoney(finance.cashTaxPaid)),
          reportRow("资本开支", fmtMoney(finance.capexOutlay)),
          reportRow("贷款提款", fmtMoney(finance.loanDrawdown)),
          reportRow("债务服务", fmtMoney(finance.debtService)),
        ]),
        reportBlock("商业", [
          reportRow("餐饮零售收入", fmtMoney(operations.foodRetailRevenue)),
          reportRow("免税收入", fmtMoney(operations.dutyFreeRevenue)),
          reportRow("精品收入", fmtMoney(operations.luxuryRevenue)),
          reportRow("商业利润", fmtMoney(operations.commercialProfit)),
          reportRow("单客收入", fmtCny(operations.revenuePerPassengerCny)),
          reportRow("单客成本", fmtCny(operations.costPerPassengerCny)),
        ]),
        reportBlock("账面", [
          reportRow("总资产", fmtMoney(finance.totalAssets)),
          reportRow("总负债", fmtMoney(finance.totalLiabilities)),
          reportRow("所有者权益", fmtMoney(finance.totalEquity)),
          reportRow("税前利润", fmtMoney(finance.pretaxProfit)),
          reportRow("净利润", fmtMoney(finance.accountingProfit)),
        ]),
      ].join("");

      el.opsRiskBody.innerHTML = `
        <div class="report-block">
          <h3>本季警告</h3>
          <div class="pills">${pills(quarter.warnings, "warn")}</div>
        </div>
        <div class="report-block">
          <h3>在建项目</h3>
          <div class="pills">${pills(projects.activeProjectIds)}</div>
        </div>
        <div class="report-block">
          <h3>完成项目</h3>
          <div class="pills">${pills(projects.completedProjectIds)}</div>
        </div>
        <div class="report-block">
          <h3>贷款</h3>
          ${reportRow("活跃贷款", finance.loanActiveIds || "无")}
          ${reportRow("本季提款", finance.loanDrawdownIds || "无")}
          ${reportRow("贷款被拒", finance.loanBlockedIds || "无")}
        </div>
        <div class="report-block">
          <h3>合同</h3>
          ${reportRow("免税周期", operations.dutyFreeContractCycle || "无")}
          ${reportRow("免税状态", contractOverviewStatusLabel(operations.dutyFreeContractStatus))}
          ${reportRow("精品周期", operations.luxuryContractCycle || "无")}
          ${reportRow("精品状态", contractOverviewStatusLabel(operations.luxuryContractStatus))}
        </div>
      `;

      el.opsComponentRows.innerHTML = `
        <tr>
          <td>承接客流</td>
          <td>${fmt(demand.componentServed.business, 2)}</td>
          <td>${fmt(demand.componentServed.leisure, 2)}</td>
          <td>${fmt(demand.componentServed.vfr, 2)}</td>
          <td>${fmt(demand.componentServed.longHaul, 2)}</td>
          <td>${fmt(demand.componentServed.transfer, 2)}</td>
        </tr>
      `;
    }

    async function loadOperations(mode = "replay", restoreSave = null) {
      const context = requireSeedContext();
      const {seed, years} = context;
      if (!contextCacheReady()) {
        status("当前槽位没有可用经营缓存，请先点击“生成当前世界”。玩家存档不会因此丢失。", "error");
        return;
      }
      if (mode === "simulate_default" && years < PLAYER_SIMULATION_MIN_YEARS) {
        status(`模拟运营需要 ${PLAYER_SIMULATION_MIN_YEARS} 年标准世界；请在首页为同一 Seed 创建 60 年槽位。`, "error");
        return;
      }
      const requestedActions = mode === "simulate_default"
        ? cleanSavedPlayerActions(restoreSave?.playerActions)
        : [];
      const restoredIndex = restoreSave
        ? Number(restoreSave.currentQuarterIndex)
        : NaN;
      setSelectedOperationMode(mode);
      state.operationMode = mode;
      setOperationModeVisual(mode);
      setOpsLoading(true, mode);
      status(mode === "simulate_default"
        ? "正在进入北京模拟运营：使用默认初始配置，不预设贷款和项目。"
        : "正在加载当前 Seed 的北京历史运营结果。");
      try {
        const payload = await apiClient.requestJson(mode === "simulate_default" ? "/api/player-simulation" : "/api/beijing-operations", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(contextRequestBody(mode === "simulate_default"
            ? {
              force: el.forceInput.checked,
              playerActions: requestedActions,
              currentQuarterIndex: Number.isFinite(restoredIndex) ? restoredIndex : undefined,
            }
            : {force: el.forceInput.checked, mode})),
        });
        if (!payload.ok) throw new Error(payload.error || "operations failed");
        assertContextResponse(payload, "经营响应");
        if (payload.mode && payload.mode !== mode) {
          throw new Error(`后端返回了${operationModeLabel(payload.mode)}，不是当前请求的${operationModeLabel(mode)}。请重启动态测试服务。`);
        }
        if (!payload.mode && mode !== "replay") {
          state.operations = null;
          throw new Error("当前动态测试服务仍是旧版本，暂不支持模拟运营。请重启 start_seed_explorer.bat 后再试。");
        }
        state.operations = payload;
        state.operationMode = payload.mode || mode;
        captureOperationBaseSnapshots();
        const defaultIndex = payload.playerStartIndex || 0;
        state.operationsQuarterIndex = Number.isFinite(restoredIndex)
          ? Math.min(Math.max(defaultIndex, restoredIndex), payload.quarters.length - 1)
          : (Number(payload.currentQuarterIndex) || defaultIndex);
        state.contractSignatures = restoreSave?.contractSignatures && typeof restoreSave.contractSignatures === "object"
          ? restoreSave.contractSignatures
          : {};
        state.playerActions = cleanSavedPlayerActions(payload.playerActions || requestedActions);
        state.operationOverrides = {};
        state.contractAffairsContractId = restoreSave?.contractAffairsContractId || state.contractAffairsContractId;
        state.netProfitWindowStart = null;
        state.netProfitWindowPinnedToLatest = true;
        state.trafficCapacityWindowStart = null;
        state.trafficCapacityWindowPinnedToLatest = true;
        state.serviceQualityWindowStart = null;
        state.serviceQualityWindowPinnedToLatest = true;
        state.facilitiesProjectWindowStart = null;
        state.facilitiesProjectWindowPinnedToLatest = true;
        state.facilitiesProjectLedgerYear = "latest";
        state.facilitiesProjectLedgerQuarter = "latest";
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
        const loadedLabel = payload.quarters[state.operationsQuarterIndex]?.label || payload.startLabel;
        status(restoreSave
          ? `${operationModeLabel(state.operationMode)}已读取当前 seed 存档：${loadedLabel}。`
          : (state.operationMode === "simulate_default"
            ? `模拟运营已进入：服务端已重算至 ${loadedLabel}。`
            : `历史运营已加载：${payload.periodCount} 个季度，从 ${loadedLabel} 开始。`), "ok");
        renderOperations();
        refreshSeedContext();
        refreshSimSaveSlots();
      } catch (error) {
        status(String(error.message || error), "error");
      } finally {
        setOpsLoading(false);
      }
    }

    async function refreshPlayerSimulation(currentQuarterIndex, successMessage = "") {
      if (!state.operations || state.operations.mode !== "simulate_default") return false;
      const payload = await apiClient.requestJson("/api/player-simulation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(contextRequestBody({
          force: false,
          playerActions: state.playerActions,
          currentQuarterIndex,
        })),
      });
      if (!payload.ok) throw new Error(payload.error || "player simulation failed");
      assertContextResponse(payload, "玩家行动响应");
      state.operations = payload;
      state.operationMode = "simulate_default";
      state.operationsQuarterIndex = Number(payload.currentQuarterIndex ?? currentQuarterIndex);
      state.playerActions = cleanSavedPlayerActions(payload.playerActions || state.playerActions);
      state.operationOverrides = {};
      captureOperationBaseSnapshots();
      renderOperations();
      renderSimSaveSlots();
      if (successMessage) status(successMessage, "ok");
      return true;
    }

    async function saveCurrentSimulationSlot() {
      if (!state.operations || state.operations.mode !== "simulate_default") {
        status("请先加载模拟运营，再保存动态测试存档。", "error");
        return;
      }
      const quarter = currentOperationQuarter();
      if (!quarter) {
        status("当前没有可保存的季度。", "error");
        return;
      }
      el.saveSimSlotButton.disabled = true;
      try {
        const payload = await apiClient.requestJson("/api/sim-save", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(contextRequestBody({
            action: "save",
            mode: "simulate_default",
            runId: state.operations.runId,
            runDir: state.operations.runDir,
            currentQuarterIndex: state.operationsQuarterIndex,
            currentLabel: quarter.label,
            contractSignatures: state.contractSignatures,
            contractAffairsContractId: state.contractAffairsContractId,
            playerActions: state.playerActions,
          })),
        });
        if (!payload.ok) throw new Error(payload.error || "save failed");
        assertContextResponse(payload, "存档保存响应");
        state.simSaveSummary = payload.summary || state.simSaveSummary;
        renderSimSaveSlots();
        status(`当前 seed 存档已保存：${quarter.label}。`, "ok");
      } catch (error) {
        const message = String(error.message || error);
        status(message === "not found" ? "当前动态测试服务没有存档接口，请重启服务。" : message, "error");
      } finally {
        renderSimSaveSlots();
      }
    }

    async function loadSelectedSimulationSlot() {
      el.loadSimSlotButton.disabled = true;
      try {
        const payload = await apiClient.requestJson("/api/sim-save", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(contextRequestBody({action: "load"})),
        });
        if (!payload.ok) throw new Error(payload.error || "load save failed");
        assertContextResponse(payload, "存档读取响应");
        const save = payload.save;
        state.simSaveSummary = payload.summary || state.simSaveSummary;
        el.forceInput.checked = false;
        await loadOperations("simulate_default", save);
      } catch (error) {
        const message = String(error.message || error);
        status(message === "not found" ? "当前动态测试服务没有存档接口，请重启服务。" : message, "error");
      } finally {
        renderSimSaveSlots();
      }
    }

    async function moveQuarter(delta) {
      if (!state.operations) {
        await loadOperations(state.selectedOperationMode || "replay");
        return;
      }
      const minIndex = state.operations.playerStartIndex ?? 0;
      const maxStartBeforeMove = Math.max(0, netProfitPeriodsAll().length - NET_PROFIT_WINDOW_SIZE);
      if (state.netProfitWindowStart == null || state.netProfitWindowStart >= maxStartBeforeMove) {
        state.netProfitWindowPinnedToLatest = true;
      }
      const maxTrafficStartBeforeMove = Math.max(0, trafficCapacityPeriodsAll().length - TRAFFIC_CAPACITY_WINDOW_SIZE);
      if (state.trafficCapacityWindowStart == null || state.trafficCapacityWindowStart >= maxTrafficStartBeforeMove) {
        state.trafficCapacityWindowPinnedToLatest = true;
      }
      const maxServiceQualityStartBeforeMove = Math.max(0, serviceQualityPeriodsAll().length - SERVICE_QUALITY_WINDOW_SIZE);
      if (state.serviceQualityWindowStart == null || state.serviceQualityWindowStart >= maxServiceQualityStartBeforeMove) {
        state.serviceQualityWindowPinnedToLatest = true;
      }
      const maxFacilitiesProjectStartBeforeMove = Math.max(0, facilitiesProjectPeriodsAll().length - FACILITIES_PROJECT_WINDOW_SIZE);
      if (state.facilitiesProjectWindowStart == null || state.facilitiesProjectWindowStart >= maxFacilitiesProjectStartBeforeMove) {
        state.facilitiesProjectWindowPinnedToLatest = true;
      }
      const maxDebtFinancingStartBeforeMove = Math.max(0, debtFinancingPeriodsAll().length - DEBT_FINANCING_WINDOW_SIZE);
      if (state.debtFinancingWindowStart == null || state.debtFinancingWindowStart >= maxDebtFinancingStartBeforeMove) {
        state.debtFinancingWindowPinnedToLatest = true;
      }
      const maxAviationStartBeforeMove = Math.max(0, aviationPeriodsAll().length - AVIATION_WINDOW_SIZE);
      if (state.aviationWindowStart == null || state.aviationWindowStart >= maxAviationStartBeforeMove) {
        state.aviationWindowPinnedToLatest = true;
      }
      const maxFoodRetailStartBeforeMove = Math.max(0, foodRetailPeriodsAll().length - FOOD_RETAIL_WINDOW_SIZE);
      if (state.foodRetailWindowStart == null || state.foodRetailWindowStart >= maxFoodRetailStartBeforeMove) {
        state.foodRetailWindowPinnedToLatest = true;
      }
      const maxDutyFreeStartBeforeMove = Math.max(0, dutyFreePeriodsAll().length - DUTY_FREE_WINDOW_SIZE);
      if (state.dutyFreeWindowStart == null || state.dutyFreeWindowStart >= maxDutyFreeStartBeforeMove) {
        state.dutyFreeWindowPinnedToLatest = true;
      }
      const maxLuxuryStartBeforeMove = Math.max(0, luxuryPeriodsAll().length - LUXURY_WINDOW_SIZE);
      if (state.luxuryWindowStart == null || state.luxuryWindowStart >= maxLuxuryStartBeforeMove) {
        state.luxuryWindowPinnedToLatest = true;
      }
      const maxContractStartBeforeMove = Math.max(0, contractPartnershipPeriodsAll().length - CONTRACT_PARTNERSHIP_WINDOW_SIZE);
      if (state.contractPartnershipWindowStart == null || state.contractPartnershipWindowStart >= maxContractStartBeforeMove) {
        state.contractPartnershipWindowPinnedToLatest = true;
      }
      const maxIndex = Math.max(
        minIndex,
        Number(state.operations.worldPeriodCount || state.operations.quarters.length) - 1,
      );
      const targetIndex = Math.min(
        Math.max(minIndex, (state.operationsQuarterIndex ?? minIndex) + delta),
        maxIndex,
      );
      if (state.operations.mode !== "simulate_default") {
        state.operationsQuarterIndex = targetIndex;
        renderOperations();
        return;
      }
      if (targetIndex === state.operationsQuarterIndex) return;
      const cachedQuarters = state.operations.allQuarters || [];
      if (cachedQuarters[targetIndex]) {
        state.operations.quarters = cachedQuarters.slice(0, targetIndex + 1);
        state.operations.periodCount = state.operations.quarters.length;
        state.operations.currentQuarterIndex = targetIndex;
        state.operations.finalLabel = state.operations.quarters[targetIndex].label;
        state.operationsQuarterIndex = targetIndex;
        renderOperations();
        status(`模拟运营已推进至 ${state.operations.finalLabel}。`, "ok");
        return;
      }
      setOpsLoading(true, "simulate_default");
      status(`正在读取下一季度：服务端缓存不可用，按 ${state.playerActions.length} 个玩家行动重算。`);
      try {
        await refreshPlayerSimulation(targetIndex, `模拟运营已推进至 ${state.operations?.finalLabel || "当前季度"}。`);
      } catch (error) {
        status(String(error.message || error), "error");
      } finally {
        setOpsLoading(false);
      }
    }
