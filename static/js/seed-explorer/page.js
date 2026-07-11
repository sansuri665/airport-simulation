    async function runSeed() {
      const seed = Number(el.seedInput.value);
      const years = Number(el.yearsInput.value || 60);
      if (!Number.isInteger(seed) || seed < 0) {
        status("请输入有效的非负整数 seed。", "error");
        return;
      }
      setLoading(true);
      status("正在运行全链路：宏观、区域航空、城市市场、北京下游样板都会跑。请稍等。");
      const stopTaskProgress = startTaskProgressPolling(seed, years);
      try {
        const payload = await apiClient.requestJson("/api/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ seed, years, force: el.forceInput.checked }),
        });
        if (!payload.ok) throw new Error(payload.error || "run failed");
        state.data = payload;
        state.operations = null;
        state.operationMode = null;
        state.operationsQuarterIndex = null;
        state.selectedCityId = payload.cities[0]?.id || null;
        status(`${payload.cached ? "读取已有结果" : "全链路完成"}：${payload.cityCount} 城市，耗时 ${fmt(payload.elapsedSec, 1)} 秒。`, "ok");
        refreshCachedRuns();
        if (state.view === "operations") {
          renderOperations();
        } else {
          render();
        }
      } catch (error) {
        status(String(error.message || error), "error");
      } finally {
        stopTaskProgress();
        setLoading(false);
      }
    }

    el.runButton.addEventListener("click", runSeed);
    el.randomButton.addEventListener("click", async () => {
      el.randomButton.disabled = true;
      try {
        const payload = await apiClient.requestJson("/api/random-seed");
        if (!payload.ok || !Number.isInteger(payload.seed)) throw new Error(payload.error || "random seed failed");
        el.seedInput.value = String(payload.seed);
        el.cachedRunSelect.value = "";
        resetLoadedData();
        status(`Python 已生成随机 Seed ${payload.seed}，尚未开始计算。`, "ok");
      } catch (error) {
        status(String(error.message || error), "error");
      } finally {
        el.randomButton.disabled = false;
      }
    });
    el.cachedRunSelect.addEventListener("change", () => applyCachedRun(el.cachedRunSelect.value));
    el.operationModeOptionButtons.forEach((button) => {
      button.addEventListener("click", () => {
        setSelectedOperationMode(button.getAttribute("data-operation-mode-option"));
      });
    });
    el.saveSimSlotButton.addEventListener("click", saveCurrentSimulationSlot);
    el.loadSimSlotButton.addEventListener("click", loadSelectedSimulationSlot);
    el.tabButtons.forEach((button) => {
      button.addEventListener("click", () => setView(button.getAttribute("data-view")));
    });
    el.opsModuleButtons.forEach((button) => {
      button.addEventListener("click", () => setOpsModule(button.getAttribute("data-ops-module")));
    });
    el.contractAffairsContractButtons.forEach((button) => {
      button.addEventListener("click", () => {
        setContractAffairsContract(button.getAttribute("data-contract-affairs-contract"));
      });
    });
    el.contractAffairsDecisionList.addEventListener("click", (event) => {
      const button = event.target.closest("[data-contract-action]");
      if (!button) return;
      const action = button.getAttribute("data-contract-action");
      const contractId = button.getAttribute("data-contract-id");
      const cycleId = button.getAttribute("data-cycle-id");
      if (action === "sign") {
        signContractSuggestion(contractId, cycleId);
      } else if (action === "defer") {
        deferContractSuggestion(contractId, cycleId);
      }
    });
    el.financingAffairsProducts.addEventListener("click", (event) => {
      const button = event.target.closest("[data-financing-action='draw']");
      if (button) drawFinancing(button.getAttribute("data-financing-product"), button);
    });
    el.financingAffairsProducts.addEventListener("input", refreshFinancingQuotes);
    el.financingAffairsProducts.addEventListener("change", refreshFinancingQuotes);
    el.projectAffairsSlotList.addEventListener("click", (event) => {
      const button = event.target.closest("[data-project-slot-id]");
      if (!button) return;
      state.projectAffairsSlotId = button.getAttribute("data-project-slot-id") || state.projectAffairsSlotId;
      state.projectAffairsRenamingSlotId = null;
      renderProjectAffairs();
    });
    el.projectAffairsSlotActions.addEventListener("click", (event) => {
      const button = event.target.closest("[data-project-slot-name-action]");
      if (!button) return;
      const selectedSlot = PROJECT_AFFAIRS_SLOTS.find((slot) => slot.slotId === state.projectAffairsSlotId);
      const action = button.getAttribute("data-project-slot-name-action");
      if (action === "edit" && selectedSlot && projectSlotCurrentSize(selectedSlot, currentOperationQuarter()) !== "empty") {
        state.projectAffairsRenamingSlotId = selectedSlot.slotId;
        renderProjectAffairs();
      } else if (action === "cancel") {
        state.projectAffairsRenamingSlotId = null;
        renderProjectAffairs();
      } else if (action === "confirm") {
        renameProjectSlot(selectedSlot, document.getElementById("projectSlotRenameInput")?.value);
      }
    });
    el.projectAffairsPlanList.addEventListener("click", (event) => {
      const button = event.target.closest("[data-project-action='start']");
      if (!button) return;
      startProjectTemplate(button.getAttribute("data-project-template-id"));
    });
    el.projectAffairsPlanList.addEventListener("change", (event) => {
      const select = event.target.closest("[data-rebuild-target-template]");
      if (select) state.projectRebuildTargetByTemplate[select.getAttribute("data-rebuild-target-template")] = select.value;
      const constructionSelect = event.target.closest("[data-construction-target-template]");
      if (constructionSelect) state.projectConstructionTargetByTemplate[constructionSelect.getAttribute("data-construction-target-template")] = constructionSelect.value;
      if (!select && !constructionSelect) return;
      renderProjectAffairs();
    });
    el.opsReportButtons.forEach((button) => {
      button.addEventListener("click", () => setOpsReportSection(button.getAttribute("data-ops-report-section")));
    });
    el.opsBreakdownButtons.forEach((button) => {
      button.addEventListener("click", () => setOpsBreakdownSection(button.getAttribute("data-ops-breakdown-section")));
    });
    el.trafficCapacityScopeSelect.addEventListener("change", () => {
      state.trafficCapacityReportScope = el.trafficCapacityScopeSelect.value;
      state.trafficCapacityWindowStart = null;
      state.trafficCapacityWindowPinnedToLatest = true;
      renderTrafficCapacityAnalysis();
    });
    el.trafficCapacityRangeInput.addEventListener("input", () => {
      state.trafficCapacityWindowStart = Number(el.trafficCapacityRangeInput.value) || 0;
      state.trafficCapacityWindowPinnedToLatest = false;
      renderTrafficCapacityAnalysis();
    });
    el.serviceQualityMetricButtons.forEach((button) => {
      button.addEventListener("click", () => setServiceQualityMetric(button.getAttribute("data-service-quality-metric")));
    });
    el.serviceQualityScopeSelect.addEventListener("change", () => {
      state.serviceQualityReportScope = el.serviceQualityScopeSelect.value;
      state.serviceQualityWindowStart = null;
      state.serviceQualityWindowPinnedToLatest = true;
      renderServiceQualityAnalysis();
    });
    el.serviceQualityRangeInput.addEventListener("input", () => {
      state.serviceQualityWindowStart = Number(el.serviceQualityRangeInput.value) || 0;
      state.serviceQualityWindowPinnedToLatest = false;
      renderServiceQualityAnalysis();
    });
    el.facilitiesProjectMetricButtons.forEach((button) => {
      button.addEventListener("click", () => setFacilitiesProjectMetric(button.getAttribute("data-facilities-project-metric")));
    });
    el.facilitiesProjectScopeSelect.addEventListener("change", () => {
      state.facilitiesProjectReportScope = el.facilitiesProjectScopeSelect.value;
      state.facilitiesProjectWindowStart = null;
      state.facilitiesProjectWindowPinnedToLatest = true;
      renderFacilitiesProjectAnalysis();
    });
    el.facilitiesProjectLedgerYearSelect.addEventListener("change", () => {
      state.facilitiesProjectLedgerYear = el.facilitiesProjectLedgerYearSelect.value;
      state.facilitiesProjectLedgerQuarter = "latest";
      renderFacilitiesProjectAnalysis();
    });
    el.facilitiesProjectLedgerQuarterSelect.addEventListener("change", () => {
      state.facilitiesProjectLedgerQuarter = el.facilitiesProjectLedgerQuarterSelect.value;
      renderFacilitiesProjectAnalysis();
    });
    el.facilitiesProjectRangeInput.addEventListener("input", () => {
      state.facilitiesProjectWindowStart = Number(el.facilitiesProjectRangeInput.value) || 0;
      state.facilitiesProjectWindowPinnedToLatest = false;
      renderFacilitiesProjectAnalysis();
    });
    el.debtFinancingMetricButtons.forEach((button) => {
      button.addEventListener("click", () => setDebtFinancingMetric(button.getAttribute("data-debt-financing-metric")));
    });
    el.debtFinancingScopeSelect.addEventListener("change", () => {
      state.debtFinancingReportScope = el.debtFinancingScopeSelect.value;
      state.debtFinancingWindowStart = null;
      state.debtFinancingWindowPinnedToLatest = true;
      renderDebtFinancingAnalysis();
    });
    el.debtFinancingLedgerYearSelect.addEventListener("change", () => {
      state.debtFinancingLedgerYear = el.debtFinancingLedgerYearSelect.value;
      state.debtFinancingLedgerQuarter = "latest";
      renderDebtFinancingAnalysis();
    });
    el.debtFinancingLedgerQuarterSelect.addEventListener("change", () => {
      state.debtFinancingLedgerQuarter = el.debtFinancingLedgerQuarterSelect.value;
      renderDebtFinancingAnalysis();
    });
    el.debtFinancingEventStartYearSelect.addEventListener("change", () => {
      state.debtFinancingEventStartYear = el.debtFinancingEventStartYearSelect.value;
      state.debtFinancingEventStartQuarter = "q1";
      renderDebtFinancingAnalysis();
    });
    el.debtFinancingEventStartQuarterSelect.addEventListener("change", () => {
      state.debtFinancingEventStartQuarter = el.debtFinancingEventStartQuarterSelect.value;
      renderDebtFinancingAnalysis();
    });
    el.debtFinancingEventEndYearSelect.addEventListener("change", () => {
      state.debtFinancingEventEndYear = el.debtFinancingEventEndYearSelect.value;
      state.debtFinancingEventEndQuarter = "latest";
      renderDebtFinancingAnalysis();
    });
    el.debtFinancingEventEndQuarterSelect.addEventListener("change", () => {
      state.debtFinancingEventEndQuarter = el.debtFinancingEventEndQuarterSelect.value;
      renderDebtFinancingAnalysis();
    });
    el.debtFinancingRangeInput.addEventListener("input", () => {
      state.debtFinancingWindowStart = Number(el.debtFinancingRangeInput.value) || 0;
      state.debtFinancingWindowPinnedToLatest = false;
      renderDebtFinancingAnalysis();
    });
    el.aviationMetricButtons.forEach((button) => {
      button.addEventListener("click", () => setAviationMetric(button.getAttribute("data-aviation-metric")));
    });
    el.aviationScopeSelect.addEventListener("change", () => {
      state.aviationReportScope = el.aviationScopeSelect.value;
      state.aviationWindowStart = null;
      state.aviationWindowPinnedToLatest = true;
      renderAviationBusinessAnalysis();
    });
    el.aviationRangeInput.addEventListener("input", () => {
      state.aviationWindowStart = Number(el.aviationRangeInput.value) || 0;
      state.aviationWindowPinnedToLatest = false;
      renderAviationBusinessAnalysis();
    });
    el.foodRetailMetricButtons.forEach((button) => {
      button.addEventListener("click", () => setFoodRetailMetric(button.getAttribute("data-food-retail-metric")));
    });
    el.foodRetailScopeSelect.addEventListener("change", () => {
      state.foodRetailReportScope = el.foodRetailScopeSelect.value;
      state.foodRetailWindowStart = null;
      state.foodRetailWindowPinnedToLatest = true;
      renderFoodRetailBusinessAnalysis();
    });
    el.foodRetailRangeInput.addEventListener("input", () => {
      state.foodRetailWindowStart = Number(el.foodRetailRangeInput.value) || 0;
      state.foodRetailWindowPinnedToLatest = false;
      renderFoodRetailBusinessAnalysis();
    });
    el.dutyFreeMetricButtons.forEach((button) => {
      button.addEventListener("click", () => setDutyFreeMetric(button.getAttribute("data-duty-free-metric")));
    });
    el.dutyFreeScopeSelect.addEventListener("change", () => {
      state.dutyFreeReportScope = el.dutyFreeScopeSelect.value;
      state.dutyFreeWindowStart = null;
      state.dutyFreeWindowPinnedToLatest = true;
      renderDutyFreeBusinessAnalysis();
    });
    el.dutyFreeRangeInput.addEventListener("input", () => {
      state.dutyFreeWindowStart = Number(el.dutyFreeRangeInput.value) || 0;
      state.dutyFreeWindowPinnedToLatest = false;
      renderDutyFreeBusinessAnalysis();
    });
    el.luxuryMetricButtons.forEach((button) => {
      button.addEventListener("click", () => setLuxuryMetric(button.getAttribute("data-luxury-metric")));
    });
    el.luxuryScopeSelect.addEventListener("change", () => {
      state.luxuryReportScope = el.luxuryScopeSelect.value;
      state.luxuryWindowStart = null;
      state.luxuryWindowPinnedToLatest = true;
      renderLuxuryBusinessAnalysis();
    });
    el.luxuryRangeInput.addEventListener("input", () => {
      state.luxuryWindowStart = Number(el.luxuryRangeInput.value) || 0;
      state.luxuryWindowPinnedToLatest = false;
      renderLuxuryBusinessAnalysis();
    });
    el.contractPartnershipMetricButtons.forEach((button) => {
      button.addEventListener("click", () => setContractPartnershipMetric(button.getAttribute("data-contract-partnership-metric")));
    });
    el.contractPartnershipScopeSelect.addEventListener("change", () => {
      state.contractPartnershipReportScope = el.contractPartnershipScopeSelect.value;
      state.contractPartnershipWindowStart = null;
      state.contractPartnershipWindowPinnedToLatest = true;
      renderContractPartnershipAnalysis();
    });
    el.contractPartnershipRangeInput.addEventListener("input", () => {
      state.contractPartnershipWindowStart = Number(el.contractPartnershipRangeInput.value) || 0;
      state.contractPartnershipWindowPinnedToLatest = false;
      renderContractPartnershipAnalysis();
    });
    el.contractPartnershipLedgerYearSelect.addEventListener("change", () => {
      state.contractPartnershipLedgerYear = el.contractPartnershipLedgerYearSelect.value;
      state.contractPartnershipLedgerQuarter = "latest";
      renderContractPartnershipAnalysis();
    });
    el.contractPartnershipLedgerQuarterSelect.addEventListener("change", () => {
      state.contractPartnershipLedgerQuarter = el.contractPartnershipLedgerQuarterSelect.value;
      renderContractPartnershipAnalysis();
    });
    el.contractPartnershipEventStartYearSelect.addEventListener("change", () => {
      state.contractPartnershipEventStartYear = el.contractPartnershipEventStartYearSelect.value;
      state.contractPartnershipEventStartQuarter = "q1";
      renderContractPartnershipAnalysis();
    });
    el.contractPartnershipEventStartQuarterSelect.addEventListener("change", () => {
      state.contractPartnershipEventStartQuarter = el.contractPartnershipEventStartQuarterSelect.value;
      renderContractPartnershipAnalysis();
    });
    el.contractPartnershipEventEndYearSelect.addEventListener("change", () => {
      state.contractPartnershipEventEndYear = el.contractPartnershipEventEndYearSelect.value;
      state.contractPartnershipEventEndQuarter = "latest";
      renderContractPartnershipAnalysis();
    });
    el.contractPartnershipEventEndQuarterSelect.addEventListener("change", () => {
      state.contractPartnershipEventEndQuarter = el.contractPartnershipEventEndQuarterSelect.value;
      renderContractPartnershipAnalysis();
    });
    el.financialMetricButtons.forEach((button) => {
      button.addEventListener("click", () => {
        state.financialMetric = button.getAttribute("data-financial-metric") || "netProfit";
        state.netProfitWindowStart = null;
        state.netProfitWindowPinnedToLatest = true;
        renderFinancialAnalysis();
      });
    });
    el.financialScopeSelect.addEventListener("change", () => {
      state.financialReportScope = el.financialScopeSelect.value;
      state.netProfitWindowStart = null;
      state.netProfitWindowPinnedToLatest = true;
      renderFinancialAnalysis();
    });
    el.netProfitRangeInput.addEventListener("input", () => {
      state.netProfitWindowStart = Number(el.netProfitRangeInput.value) || 0;
      state.netProfitWindowPinnedToLatest = false;
      renderFinancialAnalysis();
    });
    el.runOpsButton.addEventListener("click", () => loadOperations(state.selectedOperationMode || "replay"));
    el.prevQuarterButton.addEventListener("click", () => moveQuarter(-1));
    el.nextQuarterButton.addEventListener("click", () => moveQuarter(1));
    el.sortSelect.addEventListener("change", render);
    el.searchInput.addEventListener("input", render);
    refreshCachedRuns();
    refreshSimSaveSlots();
    setSelectedOperationMode(state.selectedOperationMode);
    setOpsModule(state.opsModule);
    setOpsReportSection(state.opsReportSection);
    render();
    renderOperations();
