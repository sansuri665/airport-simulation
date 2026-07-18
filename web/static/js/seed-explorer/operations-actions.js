    function contractTypeLabel(value) {
      return {
        minimum_guarantee_plus_share: "保底 + 分成",
        forecast_minimum_guarantee_plus_share: "预测保底 + 分成",
        revenue_share: "销售分成",
      }[value] || value || "-";
    }

    function contractStatusLabel(value) {
      return {
        startup_history_fixed: "历史固定合同",
        startup_history_forward_priced: "历史预定价合同",
        auto_forecast_renewal: "自动续约",
        player_signed: "玩家签署",
        active: "有效",
        expired: "到期",
      }[value] || value || "-";
    }

    function contractOverviewStatusLabel(value) {
      return {
        startup_history_fixed: "履约中",
        startup_history_forward_priced: "履约中",
        auto_forecast_renewal: "履约中",
        player_signed: "履约中",
        active: "履约中",
        negotiation_open: "谈判中",
        pending_signature: "待签署",
        expired: "已到期",
      }[value] || "-";
    }

    function contractBasisLabel(value) {
      return {
        minimum_guarantee: "保底收入",
        revenue_share: "销售分成",
      }[value] || value || "-";
    }

    function contractPartnershipControlMode(mode) {
      el.contractPartnershipScopeControl.hidden = mode !== "scope";
      el.contractPartnershipLedgerYearControl.hidden = mode !== "ledger";
      el.contractPartnershipLedgerQuarterControl.hidden = mode !== "ledger";
      el.contractPartnershipEventStartYearControl.hidden = mode !== "events";
      el.contractPartnershipEventStartQuarterControl.hidden = mode !== "events";
      el.contractPartnershipEventEndYearControl.hidden = mode !== "events";
      el.contractPartnershipEventEndQuarterControl.hidden = mode !== "events";
      el.contractPartnershipChartPanel.hidden = mode !== "scope";
    }

    function contractPartnershipCurrentIndex() {
      if (!state.operations || !state.operations.quarters.length) return -1;
      const minIndex = state.operations.playerStartIndex ?? 0;
      return Math.min(
        Math.max(minIndex, state.operationsQuarterIndex ?? minIndex),
        state.operations.quarters.length - 1,
      );
    }

    function contractPartnershipAvailableQuarters() {
      const index = contractPartnershipCurrentIndex();
      if (index < 0) return [];
      return state.operations.quarters.slice(0, index + 1);
    }

    function contractPartnershipYears() {
      return Array.from(new Set(contractPartnershipAvailableQuarters().map((quarter) => Number(quarter.year))))
        .filter((year) => Number.isFinite(year))
        .sort((a, b) => a - b);
    }

    function selectedContractPartnershipLedgerYear() {
      const currentQuarter = state.operations?.quarters?.[contractPartnershipCurrentIndex()];
      if (!currentQuarter) return null;
      const years = contractPartnershipYears();
      const requested = state.contractPartnershipLedgerYear === "latest"
        ? Number(currentQuarter.year)
        : Number(state.contractPartnershipLedgerYear);
      if (years.includes(requested)) return requested;
      state.contractPartnershipLedgerYear = "latest";
      return Number(currentQuarter.year);
    }

    function contractPartnershipQuarterOptions(year) {
      const yearQuarters = contractPartnershipAvailableQuarters()
        .filter((quarter) => Number(quarter.year) === Number(year));
      const seen = new Set();
      const quarterOptions = yearQuarters
        .map((quarter) => quarterNumber(quarter))
        .filter((quarterNo) => {
          if (!quarterNo || seen.has(quarterNo)) return false;
          seen.add(quarterNo);
          return true;
        })
        .sort((a, b) => a - b)
        .map((quarterNo) => ({ value: `q${quarterNo}`, label: `Q${quarterNo}` }));
      return [
        { value: "latest", label: "最新季度" },
        { value: "overview", label: "本年总览" },
        ...quarterOptions,
      ];
    }

    function setContractPartnershipLedgerPeriodOptions() {
      const years = contractPartnershipYears();
      if (!years.length) {
        el.contractPartnershipLedgerYearSelect.innerHTML = `<option value="latest">最新</option>`;
        el.contractPartnershipLedgerQuarterSelect.innerHTML = `<option value="latest">最新季度</option>`;
        state.contractPartnershipLedgerYear = "latest";
        state.contractPartnershipLedgerQuarter = "latest";
        return;
      }
      const yearAllowed = state.contractPartnershipLedgerYear === "latest"
        || years.includes(Number(state.contractPartnershipLedgerYear));
      if (!yearAllowed) state.contractPartnershipLedgerYear = "latest";
      el.contractPartnershipLedgerYearSelect.innerHTML = [
        `<option value="latest">最新</option>`,
        ...years.map((year) => `<option value="${year}">${year}</option>`),
      ].join("");
      el.contractPartnershipLedgerYearSelect.value = state.contractPartnershipLedgerYear;

      const selectedYear = selectedContractPartnershipLedgerYear();
      const quarterOptions = contractPartnershipQuarterOptions(selectedYear);
      if (!quarterOptions.some((option) => option.value === state.contractPartnershipLedgerQuarter)) {
        state.contractPartnershipLedgerQuarter = "latest";
      }
      el.contractPartnershipLedgerQuarterSelect.innerHTML = quarterOptions.map((option) => (
        `<option value="${escapeHtml(option.value)}">${escapeHtml(option.label)}</option>`
      )).join("");
      el.contractPartnershipLedgerQuarterSelect.value = state.contractPartnershipLedgerQuarter;
    }

    function contractPartnershipLedgerSelection() {
      const year = selectedContractPartnershipLedgerYear();
      if (!year) return { quarters: [], label: "当前季度", isOverview: false, pointQuarter: null };
      const yearQuarters = contractPartnershipAvailableQuarters()
        .filter((quarter) => Number(quarter.year) === Number(year))
        .sort((a, b) => Number(a.index) - Number(b.index));
      if (!yearQuarters.length) return { quarters: [], label: `${year}`, isOverview: false, pointQuarter: null };
      if (state.contractPartnershipLedgerQuarter === "overview") {
        return {
          quarters: yearQuarters,
          label: `${year} 本年总览`,
          isOverview: true,
          pointQuarter: yearQuarters[yearQuarters.length - 1],
        };
      }
      const requestedQuarterNo = String(state.contractPartnershipLedgerQuarter || "").match(/\d+/);
      const selectedQuarter = state.contractPartnershipLedgerQuarter === "latest"
        ? yearQuarters[yearQuarters.length - 1]
        : yearQuarters.find((quarter) => quarterNumber(quarter) === Number(requestedQuarterNo?.[0])) || yearQuarters[yearQuarters.length - 1];
      return {
        quarters: selectedQuarter ? [selectedQuarter] : [],
        label: selectedQuarter?.label || `${year}`,
        isOverview: false,
        pointQuarter: selectedQuarter || null,
      };
    }

    function contractValue(contract, quarter, keyName) {
      return Number(quarter?.operations?.[contract[keyName]]) || 0;
    }

    function contractText(contract, quarter, keyName) {
      return quarter?.operations?.[contract[keyName]] || "";
    }

    function contractById(contractId) {
      return CONTRACT_DEFINITIONS.find((contract) => contract.id === contractId) || null;
    }

    function contractSignatureKey(contract, cycleId) {
      return `${state.operations?.runId || "run"}:${state.operations?.mode || "mode"}:${contract.id}:${cycleId || "cycle"}`;
    }

    function contractSignature(contract, cycleId) {
      return state.contractSignatures[contractSignatureKey(contract, cycleId)] || null;
    }

    function setContractSignature(contract, cycleId, signature) {
      if (!cycleId) return;
      state.contractSignatures[contractSignatureKey(contract, cycleId)] = signature;
    }

    function operationOverrideKey(quarter) {
      return String(quarter?.index ?? "");
    }

    function quarterBaseOperations(quarter) {
      return quarter?.__baseOperations || quarter?.operations || {};
    }

    function quarterBaseFinance(quarter) {
      return quarter?.__baseFinance || quarter?.finance || {};
    }

    function captureOperationBaseSnapshots() {
      if (!state.operations?.quarters?.length) return;
      state.operations.quarters.forEach((quarter) => {
        if (!quarter.__baseOperations) quarter.__baseOperations = { ...(quarter.operations || {}) };
        if (!quarter.__baseFinance) quarter.__baseFinance = { ...(quarter.finance || {}) };
      });
    }

    function resetOperationsToBase() {
      if (!state.operations?.quarters?.length) return;
      state.operations.quarters.forEach((quarter) => {
        if (quarter.__baseOperations) quarter.operations = { ...quarter.__baseOperations };
        if (quarter.__baseFinance) quarter.finance = { ...quarter.__baseFinance };
        delete quarter.operationOverrideSources;
      });
    }

    function cleanSavedPlayerActions(actions) {
      return Array.isArray(actions)
        ? actions.filter((action) => action && typeof action === "object").map((action) => ({ ...action }))
        : [];
    }

    function cleanSavedOperationOverrides(overrides) {
      if (!overrides || typeof overrides !== "object" || Array.isArray(overrides)) return {};
      return Object.fromEntries(Object.entries(overrides)
        .filter(([, value]) => value && typeof value === "object" && !Array.isArray(value))
        .map(([key, value]) => [String(key), {
          ...value,
          operations: value.operations && typeof value.operations === "object" ? { ...value.operations } : {},
          finance: value.finance && typeof value.finance === "object" ? { ...value.finance } : {},
          sources: Array.isArray(value.sources) ? value.sources.slice() : [],
        }]));
    }

    function contractBaseText(contract, quarter, keyName) {
      const key = contract[keyName];
      return key ? String(quarterBaseOperations(quarter)[key] || "") : "";
    }

    function playerActionKey(action) {
      if (action?.type === "start_project") return `start_project:${action?.projectId || action?.templateId || ""}`;
      if (action?.type === "rename_slot") return `rename_slot:${action?.slotId || ""}`;
      if (action?.type === "draw_loan") return `draw_loan:${action?.startedAtIndex || ""}`;
      return `${action?.type || ""}:${action?.contractId || ""}:${action?.cycleId || ""}`;
    }

    function upsertPlayerAction(action) {
      const key = playerActionKey(action);
      state.playerActions = state.playerActions.filter((item) => playerActionKey(item) !== key);
      state.playerActions.push(action);
    }

    function signedContractTermsFromAffair(affair) {
      const next = affair?.nextTerm;
      return {
        contractType: next?.type || "forecast_minimum_guarantee_plus_share",
        revenueSharePct: round4(next?.sharePct),
        minimumGuaranteeCoveragePct: round4(next?.coveragePct),
        quarterMinimumGuarantee: round4(next?.guarantee),
        forecastQuarterSales: round4(next?.forecastQuarterSales),
        forecastAnnualSales: round4(next?.forecastAnnualSales),
        historyYearsUsed: round4(next?.historyYearsUsed),
        trendMultiplier: round4(next?.trendMultiplier),
        macroRiskDiscountMultiplier: round4(next?.macroRiskDiscountMultiplier),
        bargainingPowerMultiplier: round4(next?.bargainingPowerMultiplier),
        source: "suggested_terms",
      };
    }

    function contractActionFromAffair(affair) {
      const contract = affair.contract;
      const range = contractCycleRange(contract, affair.nextTerm?.cycleId);
      const quarter = affair.quarter;
      const actionId = `${contract.id}:${affair.nextTerm?.cycleId || ""}:${Number(quarter.index)}`;
      return {
        id: actionId,
        type: "sign_contract",
        contractId: contract.id,
        contractName: contract.name,
        segment: contract.segment,
        cycleId: affair.nextTerm?.cycleId || "",
        signedAtIndex: Number(quarter.index),
        signedAtLabel: quarter.label,
        effectiveStartIndex: range?.startIndex ?? null,
        effectiveEndIndex: range?.endIndex ?? null,
        effectiveStartLabel: range?.startQuarter?.label || "",
        effectiveEndLabel: range?.endQuarter?.label || "",
        terms: signedContractTermsFromAffair(affair),
      };
    }

    function contractRevenueForTerms(contract, quarter, terms) {
      const baseOps = quarterBaseOperations(quarter);
      const sales = finiteNumber(baseOps[contract.salesKey]);
      const sharePct = finiteNumber(terms.revenueSharePct);
      const coveragePct = finiteNumber(terms.minimumGuaranteeCoveragePct);
      const forecastQuarterSales = finiteNumber(
        baseOps[contract.forecastQuarterSalesKey],
        finiteNumber(terms.forecastQuarterSales),
      );
      let guarantee = finiteNumber(terms.quarterMinimumGuarantee, NaN);
      if (!Number.isFinite(guarantee)) {
        guarantee = forecastQuarterSales * sharePct / 100 * coveragePct / 100;
      }
      const shareRevenue = sales * sharePct / 100;
      const contractType = terms.contractType || baseOps[contract.typeKey] || "forecast_minimum_guarantee_plus_share";
      const hasGuarantee = ["minimum_guarantee_plus_share", "forecast_minimum_guarantee_plus_share"].includes(contractType);
      const revenue = hasGuarantee ? Math.max(guarantee, shareRevenue) : shareRevenue;
      return {
        sales: round4(sales),
        revenue: round4(revenue),
        guarantee: round4(guarantee),
        shareRevenue: round4(shareRevenue),
        basis: hasGuarantee && guarantee > shareRevenue ? "minimum_guarantee" : "revenue_share",
        contractType,
        sharePct: round4(sharePct),
        coveragePct: round4(coveragePct),
        forecastQuarterSales: round4(forecastQuarterSales),
      };
    }

    function addContractOverrideForQuarter(overrides, contract, quarter, action) {
      const key = operationOverrideKey(quarter);
      if (!key) return;
      const baseOps = quarterBaseOperations(quarter);
      const baseFinance = quarterBaseFinance(quarter);
      const existing = overrides[key] || {
        schemaVersion: CONTRACT_OVERRIDE_SCHEMA_VERSION,
        quarterIndex: Number(quarter.index),
        label: quarter.label,
        operations: {},
        finance: {},
        sources: [],
      };
      const workingOps = { ...baseOps, ...(existing.operations || {}) };
      const workingFinance = { ...baseFinance, ...(existing.finance || {}) };
      const revenueData = contractRevenueForTerms(contract, quarter, action.terms || {});
      const previousRevenue = finiteNumber(workingOps[contract.revenueKey]);
      const deltaRevenue = revenueData.revenue - previousRevenue;
      const newCommercialRevenue = finiteNumber(workingOps.commercialRevenue) + deltaRevenue;
      const newCommercialProfit = finiteNumber(workingOps.commercialProfit) + deltaRevenue;
      const newTotalRevenue = finiteNumber(workingOps.totalRevenue) + deltaRevenue;
      const newOperatingProfit = finiteNumber(workingOps.operatingProfit) + deltaRevenue;
      const servedPassengers = finiteNumber(quarter.demand?.quarterServed);

      existing.operations = {
        ...(existing.operations || {}),
        [contract.revenueKey]: revenueData.revenue,
        [contract.guaranteeKey]: revenueData.guarantee,
        [contract.shareRevenueKey]: revenueData.shareRevenue,
        [contract.revenueSharePctKey]: revenueData.sharePct,
        [contract.coveragePctKey]: revenueData.coveragePct,
        [contract.basisKey]: revenueData.basis,
        [contract.typeKey]: revenueData.contractType,
        [contract.statusKey]: "player_signed",
        [contract.forecastQuarterSalesKey]: revenueData.forecastQuarterSales,
        commercialRevenue: round4(newCommercialRevenue),
        commercialProfit: round4(newCommercialProfit),
        totalRevenue: round4(newTotalRevenue),
        operatingProfit: round4(newOperatingProfit),
        operatingMarginPct: newTotalRevenue ? round4(newOperatingProfit / newTotalRevenue * 100) : 0,
        revenuePerPassengerCny: servedPassengers ? round4(newTotalRevenue / servedPassengers) : 0,
      };

      const pretaxBefore = finiteNumber(workingFinance.pretaxProfit);
      const pretaxAfter = pretaxBefore + deltaRevenue;
      const taxableDelta = Math.max(0, pretaxAfter) - Math.max(0, pretaxBefore);
      const rawTaxDelta = taxableDelta * CONTRACT_OVERRIDE_TAX_RATE_PCT / 100;
      const incomeTaxBefore = finiteNumber(workingFinance.incomeTaxExpense);
      const cashTaxBefore = finiteNumber(workingFinance.cashTaxPaid);
      const incomeTaxAfter = Math.max(0, incomeTaxBefore + rawTaxDelta);
      const cashTaxAfter = Math.max(0, cashTaxBefore + rawTaxDelta);
      const incomeTaxDelta = incomeTaxAfter - incomeTaxBefore;
      const cashTaxDelta = cashTaxAfter - cashTaxBefore;
      const accountingProfitDelta = deltaRevenue - incomeTaxDelta;
      const cashDelta = deltaRevenue - cashTaxDelta;
      const totalAssetsAfter = finiteNumber(workingFinance.totalAssets) + cashDelta;
      const totalLiabilities = finiteNumber(workingFinance.totalLiabilities);
      const endCashAfter = finiteNumber(workingFinance.endCash) + cashDelta;

      existing.finance = {
        ...(existing.finance || {}),
        pretaxProfit: round4(pretaxAfter),
        incomeTaxExpense: round4(incomeTaxAfter),
        cashTaxPaid: round4(cashTaxAfter),
        accountingProfit: round4(finiteNumber(workingFinance.accountingProfit) + accountingProfitDelta),
        operatingCashFlow: round4(
          finiteNumber(
            workingFinance.operatingCashFlow,
            finiteNumber(workingOps.operatingProfit) - cashTaxBefore,
          ) + cashDelta
        ),
        freeCashFlowBeforeFinancing: round4(finiteNumber(workingFinance.freeCashFlowBeforeFinancing) + cashDelta),
        endCash: round4(endCashAfter),
        cashNetChange: round4(
          finiteNumber(
            workingFinance.cashNetChange,
            finiteNumber(workingFinance.endCash) - finiteNumber(workingFinance.beginCash),
          ) + cashDelta
        ),
        totalAssets: round4(totalAssetsAfter),
        netDebt: round4(finiteNumber(workingFinance.grossDebt) - endCashAfter),
        totalEquity: round4(finiteNumber(workingFinance.totalEquity) + accountingProfitDelta),
        liabilityRatioPct: totalAssetsAfter ? round4(totalLiabilities / totalAssetsAfter * 100) : 0,
      };

      const source = {
        actionId: action.id,
        type: action.type,
        contractId: contract.id,
        cycleId: action.cycleId,
        deltaRevenue: round4(deltaRevenue),
      };
      existing.sources = (existing.sources || []).filter((item) => item.actionId !== action.id);
      existing.sources.push(source);
      overrides[key] = existing;
    }

    function rebuildOperationOverridesFromPlayerActions() {
      captureOperationBaseSnapshots();
      const overrides = {};
      const actions = cleanSavedPlayerActions(state.playerActions)
        .filter((action) => action.type === "sign_contract" && action.cycleId && contractById(action.contractId));
      actions.forEach((action) => {
        const contract = contractById(action.contractId);
        state.operations?.quarters?.forEach((quarter) => {
          if (contractBaseText(contract, quarter, "cycleKey") !== action.cycleId) return;
          addContractOverrideForQuarter(overrides, contract, quarter, action);
        });
      });
      state.playerActions = actions;
      state.operationOverrides = overrides;
      return Object.keys(overrides).length;
    }

    function applyOperationOverrides() {
      captureOperationBaseSnapshots();
      resetOperationsToBase();
      const overrides = cleanSavedOperationOverrides(state.operationOverrides);
      state.operationOverrides = overrides;
      if (!state.operations?.quarters?.length) return;
      state.operations.quarters.forEach((quarter) => {
        const override = overrides[operationOverrideKey(quarter)];
        if (!override) return;
        quarter.operations = {
          ...quarterBaseOperations(quarter),
          ...(override.operations || {}),
        };
        quarter.finance = {
          ...quarterBaseFinance(quarter),
          ...(override.finance || {}),
        };
        quarter.operationOverrideSources = override.sources || [];
      });
    }

    function contractCycleRange(contract, cycleId, quarters = state.operations?.quarters || []) {
      const cycleQuarters = quarters.filter((quarter) => contractText(contract, quarter, "cycleKey") === cycleId);
      if (!cycleQuarters.length) return null;
      return {
        cycleId,
        startIndex: Number(cycleQuarters[0].index),
        endIndex: Number(cycleQuarters[cycleQuarters.length - 1].index),
        startQuarter: cycleQuarters[0],
        endQuarter: cycleQuarters[cycleQuarters.length - 1],
      };
    }

    function contractNextCycleQuarter(contract, currentCycleId, quarters = state.operations?.quarters || []) {
      const currentRange = contractCycleRange(contract, currentCycleId, quarters);
      if (!currentRange) return null;
      return quarters.find((quarter) => (
        Number(quarter.index) > currentRange.endIndex
        && contractText(contract, quarter, "cycleKey")
        && contractText(contract, quarter, "cycleKey") !== currentCycleId
      )) || null;
    }

    function contractTermInfo(contract, quarter) {
      if (!quarter) return null;
      const cycleId = contractText(contract, quarter, "cycleKey");
      if (!cycleId) return null;
      return {
        cycleId,
        status: contractText(contract, quarter, "statusKey"),
        type: contractText(contract, quarter, "typeKey"),
        revenue: contractValue(contract, quarter, "revenueKey"),
        sales: contractValue(contract, quarter, "salesKey"),
        guarantee: contractValue(contract, quarter, "guaranteeKey"),
        shareRevenue: contractValue(contract, quarter, "shareRevenueKey"),
        sharePct: contractValue(contract, quarter, "revenueSharePctKey"),
        coveragePct: contractValue(contract, quarter, "coveragePctKey"),
        basis: contractText(contract, quarter, "basisKey"),
        forecastQuarterSales: contractValue(contract, quarter, "forecastQuarterSalesKey"),
        forecastAnnualSales: contractValue(contract, quarter, "forecastAnnualSalesKey"),
        historyYearsUsed: contractValue(contract, quarter, "historyYearsUsedKey"),
        trendMultiplier: contractValue(contract, quarter, "trendMultiplierKey"),
        macroRiskDiscountMultiplier: contractValue(contract, quarter, "macroRiskDiscountMultiplierKey"),
        bargainingPowerMultiplier: contractValue(contract, quarter, "bargainingPowerMultiplierKey"),
        cycleStartYear: contractValue(contract, quarter, "cycleStartYearKey"),
        cycleEndYear: contractValue(contract, quarter, "cycleEndYearKey"),
      };
    }

    function contractAffairState(contract, quarter = currentOperationQuarter()) {
      if (!state.operations || !quarter) return null;
      const currentTerm = contractTermInfo(contract, quarter);
      if (!currentTerm) return null;
      const visibleQuarters = state.operations.quarters || [];
      const hasFullHorizon = Boolean(state.operations.allQuarters?.length);
      const fullQuarters = hasFullHorizon
        ? state.operations.allQuarters
        : visibleQuarters;
      // contractPreviews belongs to the quarter returned by the last server call.
      // Local quarter navigation keeps allQuarters but does not refresh that
      // object, so prefer the full horizon and use the server preview only as a
      // compatibility fallback for older responses without allQuarters.
      const preview = hasFullHorizon
        ? null
        : (state.operations.contractPreviews?.[contract.id] || null);
      const visibleRange = contractCycleRange(contract, currentTerm.cycleId, visibleQuarters);
      const fullRange = contractCycleRange(contract, currentTerm.cycleId, fullQuarters);
      const currentRange = preview && Number.isFinite(Number(preview.currentCycleEndIndex))
        ? { ...(visibleRange || {}), cycleId: currentTerm.cycleId, endIndex: Number(preview.currentCycleEndIndex) }
        : (fullRange || visibleRange);
      const currentIndex = Number(quarter.index);
      const remainingQuarters = preview && Number.isFinite(Number(preview.remainingQuarters))
        ? Number(preview.remainingQuarters)
        : (currentRange ? Math.max(0, currentRange.endIndex - currentIndex + 1) : 0);
      const canOperate = state.operations.mode === "simulate_default" && Boolean(quarter.playerDecisionEnabled);
      const futureCycleQuarter = contractNextCycleQuarter(contract, currentTerm.cycleId, fullQuarters);
      const withinNegotiationWindow = Boolean(
        quarter.playerDecisionEnabled && remainingQuarters <= 4 && remainingQuarters >= 1
      );
      const nextQuarter = withinNegotiationWindow ? futureCycleQuarter : null;
      const nextTerm = preview?.nextTerm || contractTermInfo(contract, nextQuarter) || null;
      const hasNextCycle = Boolean(futureCycleQuarter || preview?.nextTerm);
      const open = Boolean(nextTerm && quarter.playerDecisionEnabled && remainingQuarters <= 4 && remainingQuarters >= 1);
      const required = Boolean(open && remainingQuarters <= 1);
      const currentSignature = contractSignature(contract, currentTerm.cycleId);
      const targetSignature = nextTerm ? contractSignature(contract, nextTerm.cycleId) : null;
      return {
        contract,
        quarter,
        currentTerm,
        currentRange,
        nextQuarter,
        nextTerm,
        hasNextCycle,
        remainingQuarters,
        canOperate,
        open,
        required,
        currentSignature,
        targetSignature,
      };
    }

    function ensureContractAutoSignatures() {
      if (!state.operations || state.operations.mode !== "simulate_default") return;
      const currentIndex = state.operationsQuarterIndex ?? state.operations.playerStartIndex ?? 0;
      const playerStartIndex = state.operations.playerStartIndex ?? 0;
      CONTRACT_DEFINITIONS.forEach((contract) => {
        const seenCycles = new Set();
        state.operations.quarters.forEach((quarter) => {
          const cycleId = contractText(contract, quarter, "cycleKey");
          if (!cycleId || seenCycles.has(cycleId)) return;
          seenCycles.add(cycleId);
          const range = contractCycleRange(contract, cycleId);
          if (!range || range.startIndex <= playerStartIndex || range.startIndex > currentIndex) return;
          if (contractSignature(contract, cycleId)) return;
          const previousQuarter = state.operations.quarters[range.startIndex - 1];
          setContractSignature(contract, cycleId, {
            status: "auto",
            label: "系统续签",
            signedAtIndex: previousQuarter ? Number(previousQuarter.index) : range.startIndex,
            signedAtLabel: previousQuarter?.label || range.startQuarter?.label || "",
          });
        });
      });
    }

    function contractAffairStatusMeta(affair) {
      if (!affair) return { label: "未加载", className: "inactive" };
      if (affair.targetSignature?.status === "signed") return { label: "已签署", className: "signed" };
      if (affair.targetSignature?.status === "auto") return { label: "系统续签", className: "signed" };
      if (affair.required) return { label: "本季必须确认", className: "required" };
      if (affair.open) return { label: "可谈判", className: "open" };
      if (affair.currentSignature?.status === "signed") return { label: "已签署", className: "signed" };
      if (affair.currentSignature?.status === "auto") return { label: "系统续签", className: "signed" };
      return { label: "有效中", className: "inactive" };
    }

    function contractKv(label, value) {
      return `<div class="contract-kv"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
    }

    function contractMultiplierText(value) {
      const number = Number(value);
      if (!Number.isFinite(number) || number <= 0) return "-";
      return `${fmt(number, 3)}x`;
    }

    function renderContractAffairsAlert(affair) {
      const meta = contractAffairStatusMeta(affair);
      const contract = affair.contract;
      if (affair.targetSignature) {
        return `
          <div class="contract-alert signed">
            <strong>${escapeHtml(contract.segment)}下一期已确定</strong>
            <span>${escapeHtml(affair.nextTerm?.cycleId || affair.currentTerm.cycleId)}，${escapeHtml(affair.targetSignature.label)}于 ${escapeHtml(affair.targetSignature.signedAtLabel || "-")}。</span>
          </div>
        `;
      }
      if (affair.required) {
        return `
          <div class="contract-alert urgent">
            <strong>${escapeHtml(contract.segment)}合同本季必须确认</strong>
            <span>当前 ${escapeHtml(affair.currentTerm.cycleId)} 剩余 1 季；下一期 ${escapeHtml(affair.nextTerm?.cycleId || "-")} 已生成建议条款。</span>
          </div>
        `;
      }
      if (affair.open) {
        return `
          <div class="contract-alert">
            <strong>${escapeHtml(contract.segment)}合同开放谈判</strong>
            <span>当前 ${escapeHtml(affair.currentTerm.cycleId)} 还剩 ${escapeHtml(affair.remainingQuarters)} 季；可确认下一期 ${escapeHtml(affair.nextTerm?.cycleId || "-")}。</span>
          </div>
        `;
      }
      if (!affair.nextTerm && !affair.hasNextCycle) {
        return `
          <div class="contract-alert">
            <strong>${escapeHtml(contract.segment)}合同有效中</strong>
            <span>${escapeHtml(affair.currentTerm.cycleId)} 是当前可见模拟期内最后一份合同。</span>
          </div>
        `;
      }
      return `
        <div class="contract-alert">
          <strong>${escapeHtml(contract.segment)}合同${escapeHtml(meta.label)}</strong>
          <span>${escapeHtml(affair.currentTerm.cycleId)} 还剩 ${escapeHtml(affair.remainingQuarters)} 季；到期前 4 季进入谈判窗口。</span>
        </div>
      `;
    }

    function renderContractAffairsCard(affair) {
      const meta = contractAffairStatusMeta(affair);
      const contract = affair.contract;
      const current = affair.currentTerm;
      const next = affair.nextTerm;
      const targetCycle = next?.cycleId || "";
      const canUseActions = affair.canOperate && affair.open && !affair.targetSignature;
      const canDefer = canUseActions && !affair.required;
      const actionDisabled = canUseActions ? "" : " disabled";
      const deferDisabled = canDefer ? "" : " disabled";
      const actionTitle = affair.canOperate
        ? (affair.open ? "" : "尚未进入谈判窗口")
        : "只有模拟运营可以签署合同";
      const currentSignatureText = affair.currentSignature
        ? `${affair.currentSignature.label}于 ${affair.currentSignature.signedAtLabel || "-"}`
        : contractStatusLabel(current.status);
      const nextTitle = next ? `下一期建议条款：${next.cycleId}` : "下一期建议条款";
      const nextBody = next ? `
        <div class="contract-kv-grid">
          ${contractKv("分成比例", fmtPct(next.sharePct))}
          ${contractKv("保底覆盖", fmtPct(next.coveragePct))}
          ${contractKv("预测季度销售额", fmtMoney(next.forecastQuarterSales))}
          ${contractKv("季度保底", fmtMoney(next.guarantee))}
          ${contractKv("预测年销售额", fmtMoney(next.forecastAnnualSales))}
          ${contractKv("历史样本", `${fmt(next.historyYearsUsed, 0)} 年`)}
          ${contractKv("趋势修正", contractMultiplierText(next.trendMultiplier))}
          ${contractKv("宏观折扣", contractMultiplierText(next.macroRiskDiscountMultiplier))}
          ${contractKv("议价修正", contractMultiplierText(next.bargainingPowerMultiplier))}
          ${contractKv("合同类型", contractTypeLabel(next.type))}
        </div>
      ` : `<div class="empty">${affair.hasNextCycle ? "下一期条款将在到期前 4 季开放。" : "当前模拟期内没有下一期合同条款。"}</div>`;
      return `
        <section class="contract-affairs-card">
          <div class="contract-affairs-head">
            <div>
              <h3>${escapeHtml(contract.name)}</h3>
              <div class="caption">当前 ${escapeHtml(current.cycleId)}；${escapeHtml(affair.remainingQuarters)} 季后到期</div>
            </div>
            <span class="contract-status-badge ${escapeHtml(meta.className)}">${escapeHtml(meta.label)}</span>
          </div>
          <div class="contract-affairs-body">
            <div class="contract-kv-grid">
              ${contractKv("当前状态", currentSignatureText)}
              ${contractKv("本季确认口径", contractBasisLabel(current.basis))}
              ${contractKv("当前分成", fmtPct(current.sharePct))}
              ${contractKv("当前保底覆盖", fmtPct(current.coveragePct))}
              ${contractKv("本季合同收入", fmtMoney(current.revenue))}
              ${contractKv("本季保底", fmtMoney(current.guarantee))}
            </div>
            <div class="contract-note">${escapeHtml(nextTitle)}</div>
            ${nextBody}
            <div class="contract-action-row">
              <button class="primary" type="button" data-contract-action="sign" data-contract-id="${escapeHtml(contract.id)}" data-cycle-id="${escapeHtml(targetCycle)}"${actionDisabled} title="${escapeHtml(actionTitle)}">确认签署</button>
              <button type="button" data-contract-action="defer" data-contract-id="${escapeHtml(contract.id)}" data-cycle-id="${escapeHtml(targetCycle)}"${deferDisabled}>暂缓决定</button>
            </div>
            <div class="contract-note">
              到期前 4 季开放谈判；到期前 1 季必须确认。若未确认并进入下一周期，系统会按建议条款自动续签。
            </div>
          </div>
        </section>
      `;
    }

    function renderContractAffairs() {
      if (!el.contractAffairsAlerts || !el.contractAffairsDecisionList) return;
      const quarter = currentOperationQuarter();
      const selectedContractId = contractById(state.contractAffairsContractId)
        ? state.contractAffairsContractId
        : CONTRACT_DEFINITIONS[0]?.id || "";
      state.contractAffairsContractId = selectedContractId;
      el.contractAffairsContractButtons.forEach((button) => {
        button.setAttribute(
          "aria-selected",
          String(button.getAttribute("data-contract-affairs-contract") === selectedContractId),
        );
      });
      if (!state.operations || !quarter) {
        el.contractAffairsCaption.textContent = "加载模拟运营后显示合同到期和签署提示。";
        el.contractAffairsModeBadge.className = "contract-status-badge inactive";
        el.contractAffairsModeBadge.textContent = "未加载";
        el.contractAffairsAlerts.innerHTML = `<div class="empty">暂无合同事务</div>`;
        el.contractAffairsDecisionList.innerHTML = `
          <section class="contract-affairs-card">
            <div class="contract-affairs-body"><div class="empty">加载运营后显示免税和奢侈品合同。</div></div>
          </section>
        `;
        return;
      }
      ensureContractAutoSignatures();
      const affairs = CONTRACT_DEFINITIONS
        .map((contract) => contractAffairState(contract, quarter))
        .filter(Boolean);
      const modeIsSimulation = state.operations.mode === "simulate_default";
      const requiredCount = affairs.filter((affair) => affair.required && !affair.targetSignature).length;
      const openCount = affairs.filter((affair) => affair.open && !affair.targetSignature).length;
      el.contractAffairsCaption.textContent = `${quarter.label}；${modeIsSimulation ? "可执行签署动作" : "回放模式仅查看合同提示"}`;
      el.contractAffairsModeBadge.className = `contract-status-badge ${requiredCount ? "required" : openCount ? "open" : "inactive"}`;
      el.contractAffairsModeBadge.textContent = requiredCount ? `${requiredCount} 项必须确认` : openCount ? `${openCount} 项可谈判` : "无待办";
      el.contractAffairsAlerts.innerHTML = affairs.length
        ? affairs.map(renderContractAffairsAlert).join("")
        : `<div class="empty">暂无合同事务</div>`;
      const selectedAffair = affairs.find((affair) => affair.contract.id === selectedContractId) || affairs[0] || null;
      el.contractAffairsDecisionList.innerHTML = selectedAffair
        ? renderContractAffairsCard(selectedAffair)
        : `<section class="contract-affairs-card"><div class="contract-affairs-body"><div class="empty">暂无合同。</div></div></section>`;
    }

    async function signContractSuggestion(contractId, cycleId) {
      const contract = contractById(contractId);
      const quarter = currentOperationQuarter();
      if (!contract || !quarter || !cycleId) return;
      const affair = contractAffairState(contract, quarter);
      if (!affair?.open || affair.targetSignature) return;
      if (state.operations?.mode !== "simulate_default") {
        status("回放模式只能查看合同提示，不能签署。", "error");
        return;
      }
      const action = contractActionFromAffair(affair);
      upsertPlayerAction(action);
      setContractSignature(contract, cycleId, {
        status: "signed",
        label: "玩家签署",
        signedAtIndex: Number(quarter.index),
        signedAtLabel: quarter.label,
        actionId: action.id,
        terms: action.terms,
      });
      setOpsLoading(true, "simulate_default");
      status(`${contract.segment} ${cycleId} 已确认，正在由服务端重算经营和财务结果。`);
      try {
        await refreshPlayerSimulation(
          Number(quarter.index),
          `${contract.segment} ${cycleId} 已签署，经营、税务、现金和资产负债表已按行动日志重算。`,
        );
      } catch (error) {
        state.playerActions = state.playerActions.filter((item) => playerActionKey(item) !== playerActionKey(action));
        delete state.contractSignatures[contractSignatureKey(contract, cycleId)];
        status(String(error.message || error), "error");
      } finally {
        setOpsLoading(false);
      }
    }

    function deferContractSuggestion(contractId, cycleId) {
      const contract = contractById(contractId);
      const quarter = currentOperationQuarter();
      if (!contract || !quarter || !cycleId) return;
      const affair = contractAffairState(contract, quarter);
      if (!affair?.open || affair.required) return;
      status(`${contract.segment} ${cycleId} 已暂缓，本周期剩余 ${affair.remainingQuarters} 季。`, "ok");
      renderContractAffairs();
    }

    function projectTypeLabel(value) {
      return {
        renovation: "翻新",
        construction: "新建",
        rebuild: "拆除重建",
        demolition: "拆除",
      }[value] || value || "-";
    }

    function slotDisplayName(slotId, fallback) {
      const custom = state.operations?.slotNames?.[slotId];
      if (typeof custom === "string" && custom.trim()) return custom.trim();
      const currentQuarter = currentOperationQuarter();
      const constructed = currentQuarter
        ? latestCompletedSlotProject(slotId, "新建", currentQuarter)
        : null;
      return constructed?.project?.terminalName || fallback;
    }

    function projectDisplayName(project) {
      const suffix = {
        "翻新": "翻新工程",
        "新建": "新建工程",
        "拆除重建": "拆除重建工程",
        "拆除": "拆除工程",
      }[project?.type] || "工程";
      const fallbackSlotName = String(project?.name || "项目").replace(/(翻新|新建|拆除重建|拆除)工程$/, "");
      return `${slotDisplayName(project?.slotId, fallbackSlotName)}${suffix}`;
    }

    function projectTemplateById(templateId) {
      return (state.operations?.projectCatalog || []).find((item) => item.templateId === templateId) || null;
    }

    function projectActionsForTemplate(templateId) {
      return state.playerActions.filter((action) => (
        action?.type === "start_project" && action?.templateId === templateId
      ));
    }

    function projectActionForTemplate(templateId) {
      return projectActionsForTemplate(templateId)[0] || null;
    }

    function activeRenovationActionForTemplate(template, quarter) {
      if (!template || template.projectType !== "renovation") return null;
      return projectActionsForTemplate(template.templateId).find((action) => {
        const project = projectById(action.projectId);
        return project && projectActiveNow(project, quarter);
      }) || null;
    }

    function activeRebuildActionForTemplate(template, quarter) {
      if (!template || template.projectType !== "rebuild") return null;
      return projectActionsForTemplate(template.templateId).find((action) => {
        const project = projectById(action.projectId);
        return project && projectActiveNow(project, quarter);
      }) || null;
    }

    function activeDemolitionActionForTemplate(template, quarter) {
      if (!template || template.projectType !== "demolition") return null;
      return projectActionsForTemplate(template.templateId).find((action) => {
        const project = projectById(action.projectId);
        return project && projectActiveNow(project, quarter);
      }) || null;
    }

    function activeConstructionActionForTemplate(template, quarter) {
      if (!template || template.projectType !== "construction") return null;
      return projectActionsForTemplate(template.templateId).find((action) => {
        const project = projectById(action.projectId);
        return project && projectActiveNow(project, quarter);
      }) || null;
    }

    function demolitionClearanceEndIndex(slotId, quarter) {
      const completed = slotProjects(slotId, "拆除")
        .map((project) => ({ project, completion: projectCompletionQuarter(project, quarter) }))
        .filter((item) => item.completion)
        .map((item) => Number(item.completion.index) + 4)
        .filter(Number.isFinite);
      return completed.length ? Math.max(...completed) : null;
    }

    function renovationCooldownEndIndex(template, quarter) {
      if (!template || template.projectType !== "renovation") return null;
      const currentIndex = Number(quarter?.index);
      const completedRenovations = projectActionsForTemplate(template.templateId)
        .map((action) => ({ action, project: projectById(action.projectId) }))
        .filter(({ action, project }) => project && projectCompletedThrough(project, quarter))
        .map(({ action }) => {
          const duration = Math.max(1, Number(action.eventConfig?.duration_quarters ?? template.durationQuarters) || 1);
          return Number(action.startedAtIndex) + duration + 24;
        })
        .filter(Number.isFinite);
      const completedRebuilds = slotProjects(template.slotId, "拆除重建")
        .filter((project) => projectCompletedThrough(project, quarter))
        .map((project) => {
          const action = playerActionForLedgerProject(project);
          return Number(action?.startedAtIndex) + Math.max(1, Number(action?.eventConfig?.duration_quarters) || 1) + 24;
        })
        .filter(Number.isFinite);
      const completedConstructions = slotProjects(template.slotId, "新建")
        .filter((project) => projectCompletedThrough(project, quarter))
        .map((project) => {
          const action = playerActionForLedgerProject(project);
          return Number(action?.startedAtIndex) + Math.max(1, Number(action?.eventConfig?.duration_quarters) || 1) + 24;
        })
        .filter(Number.isFinite);
      const cooldownEnds = [...completedRenovations, ...completedRebuilds, ...completedConstructions];
      if (!cooldownEnds.length || !Number.isFinite(currentIndex)) return null;
      return Math.max(...cooldownEnds);
    }

    function rebuildCooldownEndIndex(template, quarter) {
      if (!template || template.projectType !== "rebuild") return null;
      const completed = projectActionsForTemplate(template.templateId)
        .map((action) => ({ action, project: projectById(action.projectId) }))
        .filter(({ project }) => project && projectCompletedThrough(project, quarter))
        .map(({ action }) => Number(action.startedAtIndex) + Math.max(1, Number(action.eventConfig?.duration_quarters) || 1) + 80)
        .filter(Number.isFinite);
      return completed.length ? Math.max(...completed) : null;
    }

    function projectQuarterLabel(index) {
      const first = state.operations?.quarters?.[0];
      if (!first || !Number.isFinite(Number(index))) return "-";
      const startYear = Number(first.year);
      const safeIndex = Number(index);
      return `${startYear + Math.floor(safeIndex / 4)} Q${safeIndex % 4 + 1}`;
    }

    function projectRecordForTemplate(template) {
      if (template?.projectType === "renovation") {
        return activeSlotProject(template.slotId, "翻新", currentOperationQuarter());
      }
      if (template?.projectType === "rebuild") {
        return activeSlotProject(template.slotId, "拆除重建", currentOperationQuarter());
      }
      if (template?.projectType === "demolition") {
        return activeSlotProject(template.slotId, "拆除", currentOperationQuarter())
          || latestCompletedSlotProject(template.slotId, "拆除", currentOperationQuarter())?.project
          || null;
      }
      if (template?.projectType === "construction") {
        return activeSlotProject(template.slotId, "新建", currentOperationQuarter())
          || latestCompletedSlotProject(template.slotId, "新建", currentOperationQuarter())?.project
          || null;
      }
      return template ? projectById(template.projectId) : null;
    }

    function projectTemplateDisplayName(template) {
      const project = projectRecordForTemplate(template);
      if (project) return projectDisplayName(project);
      const suffix = {
        renovation: "翻新工程",
        construction: "新建工程",
        rebuild: "拆除重建工程",
        demolition: "拆除工程",
      }[template?.projectType] || "工程";
      return template ? `${slotDisplayName(template.slotId, template.slotName)}${suffix}` : "项目";
    }

    function projectStatusForTemplate(template, quarter) {
      const action = template?.projectType === "renovation"
        ? activeRenovationActionForTemplate(template, quarter)
        : (template?.projectType === "rebuild"
          ? activeRebuildActionForTemplate(template, quarter)
          : (template?.projectType === "demolition"
            ? activeDemolitionActionForTemplate(template, quarter)
            : (template?.projectType === "construction"
              ? activeConstructionActionForTemplate(template, quarter)
              : projectActionForTemplate(template?.templateId))));
      if (!action) return "未启动";
      const project = projectRecordForTemplate(template);
      if (project?.type === "翻新" && renovationAssetWrittenOffThrough(quarter)) return "已被重建减记";
      if (project && projectCompletedThrough(project, quarter)) return "已完成";
      if (project && projectActiveNow(project, quarter)) return "施工中";
      return "已启动";
    }

    function projectSlotCurrentSize(slot, quarter) {
      const effective = String(quarter?.capacity?.effectiveFacilitySlots || "")
        .split(";")
        .map((value) => value.trim().split(":"))
        .find(([slotId]) => slotId === slot.slotId);
      return effective?.[1] || "empty";
    }

    function projectSlotHasActiveWork(slotId, quarter) {
      return slotProjects(slotId).some((project) => projectActiveNow(project, quarter));
    }

    function projectSlotHasCompletedRebuild(slotId, quarter) {
      return slotProjects(slotId, "拆除重建").some((project) => projectCompletedThrough(project, quarter));
    }

    function projectTemplateAvailability(template, slot, quarter) {
      if (state.operations?.mode !== "simulate_default" || !quarter?.playerDecisionEnabled) {
        return { available: false, reason: "仅模拟运营的玩家期可开工" };
      }
      if (projectSlotHasActiveWork(slot.slotId, quarter)) return { available: false, reason: "该槽位已有施工中工程" };
      if (!['renovation', 'rebuild', 'demolition', 'construction'].includes(template.projectType)) {
        const action = projectActionForTemplate(template.templateId);
        if (action) return { available: false, reason: projectStatusForTemplate(template, quarter) };
      }
      const currentSize = projectSlotCurrentSize(slot, quarter);
      if (template.projectType === "construction" && currentSize !== "empty") {
        return { available: false, reason: "该槽位已经投运" };
      }
      if (template.projectType === "construction") {
        const clearanceEndIndex = demolitionClearanceEndIndex(slot.slotId, quarter);
        if (clearanceEndIndex != null && Number(quarter.index) < clearanceEndIndex) {
          return { available: false, reason: `清场中，${projectQuarterLabel(clearanceEndIndex)}可重新新建` };
        }
      }
      if (template.projectType !== "construction" && currentSize === "empty") {
        return { available: false, reason: "该槽位尚未投运" };
      }
      if (template.projectType === "renovation") {
        const cooldownEndIndex = renovationCooldownEndIndex(template, quarter);
        if (cooldownEndIndex != null && Number(quarter.index) < cooldownEndIndex) {
          return { available: false, reason: `冷却中，${projectQuarterLabel(cooldownEndIndex)}可再次翻新` };
        }
      }
      if (["rebuild", "construction"].includes(template.projectType)) {
        if (Number(quarter.finance?.endCash) < 0) return { available: false, reason: `当前现金为负，不能启动${template.projectType === "construction" ? "新建" : "重建"}` };
      }
      if (template.projectType === "rebuild") {
        const cooldownEndIndex = rebuildCooldownEndIndex(template, quarter);
        if (cooldownEndIndex != null && Number(quarter.index) < cooldownEndIndex) {
          return { available: false, reason: `冷却中，${projectQuarterLabel(cooldownEndIndex)}可再次重建` };
        }
      }
      return { available: true, reason: "可在本季开工" };
    }

    function projectPlanCapacityText(template) {
      if (template.projectType === "renovation") {
        return `施工期保留 ${fmtPct(Number(template.constructionCapacityMultiplier) * 100)} 容量`;
      }
      if (template.projectType === "rebuild") return "施工期槽位关闭";
      if (template.projectType === "demolition") return "施工期槽位关闭，完工后恢复空白";
      return "施工期不新增容量";
    }

    function projectPlanExpectedCash(template, quarter) {
      const duration = Math.max(1, Number(template.durationQuarters) || 1);
      const firstQuarterOutlay = Number(template.totalCapex || 0) / duration
        + Number(template.demolitionExpense || 0) / duration;
      return Number(quarter?.finance?.endCash || 0) - firstQuarterOutlay;
    }

    function renovationEventTerms(template, action = null, facilitySize = null) {
      const eventConfig = action?.eventConfig || {};
      const option = !action && facilitySize ? template?.renovationOptions?.[facilitySize] || {} : {};
      return {
        durationQuarters: Number(eventConfig.duration_quarters ?? option.durationQuarters ?? template?.durationQuarters ?? 0),
        capacityMultiplier: Number(eventConfig.construction_capacity_multiplier ?? template?.constructionCapacityMultiplier ?? 0),
        capex: Number(eventConfig.capex_million_cny ?? option.totalCapex ?? template?.totalCapex ?? 0),
        usefulLifeYears: Number(eventConfig.useful_life_years ?? template?.usefulLifeYears ?? 0),
        residualValuePct: Number(eventConfig.residual_value_pct ?? template?.residualValuePct ?? 0),
      };
    }

    function projectPlanAction(template, quarter, targetFacilitySize = null) {
      const index = Number(quarter.index);
      const isRenovation = template.projectType === "renovation";
      const isRebuild = template.projectType === "rebuild";
      const isConstruction = template.projectType === "construction";
      const isDemolition = template.projectType === "demolition";
      return {
        id: isRenovation ? `renovation:${template.templateId}:${index}` : (isRebuild ? `rebuild:${template.templateId}:${index}` : (isConstruction ? `construction:${template.templateId}:${index}` : (isDemolition ? `demolition:${template.templateId}:${index}` : `${template.templateId}:${index}`))),
        type: "start_project",
        templateId: template.templateId,
        projectId: (isRenovation || isRebuild || isConstruction || isDemolition) ? `${template.projectId}__${index}` : template.projectId,
        ...((isRebuild || isConstruction) ? { targetFacilitySize } : {}),
        startedAtIndex: index,
        startedAtLabel: quarter.label,
      };
    }

    async function renameProjectSlot(slot, rawName) {
      const quarter = currentOperationQuarter();
      const name = String(rawName || "").trim().replace(/\s+/g, " ");
      if (!slot || !quarter || projectSlotCurrentSize(slot, quarter) === "empty") return;
      if (name.length < 2 || name.length > 24) {
        status("航站楼名称请保持在 2 到 24 个字符之间。", "error");
        return;
      }
      const action = {
        id: `rename:${slot.slotId}:${Number(quarter.index)}`,
        type: "rename_slot",
        slotId: slot.slotId,
        name,
        renamedAtIndex: Number(quarter.index),
        renamedAtLabel: quarter.label,
      };
      upsertPlayerAction(action);
      setOpsLoading(true, "simulate_default");
      status(`${slot.name} 正在更名为 ${name}。`);
      try {
        await refreshPlayerSimulation(
          Number(quarter.index),
          `${name} 已改名，相关项目与台账展示已同步更新。`,
        );
        state.projectAffairsRenamingSlotId = null;
      } catch (error) {
        state.playerActions = state.playerActions.filter((item) => playerActionKey(item) !== playerActionKey(action));
        status(String(error.message || error), "error");
      } finally {
        setOpsLoading(false);
      }
    }

    function financingQuote(product, principalMillion, tenor, grace, quarter) {
      const policy = state.operations?.financingPolicy || {};
      const finance = quarter?.finance || {};
      const base = Number(finance.macroTenYearYieldPct) > 0 ? Number(finance.macroTenYearYieldPct) : Number(product.loan_type === "short_term" ? policy.fallback_short_term_rate_pct : policy.fallback_long_term_rate_pct);
      const adjustment = Number(product.loan_type === "short_term" ? policy.short_term_reference_adjustment_pct : policy.long_term_reference_adjustment_pct) || 0;
      const typeSpread = Number(product.loan_type === "short_term" ? policy.short_term_spread_bps : policy.long_term_spread_bps) || 0;
      const hyStress = Math.max(0, (Number(finance.macroHySpreadBps) || Number(policy.hy_spread_baseline_bps) || 420) - (Number(policy.hy_spread_baseline_bps) || 420)) * (Number(policy.hy_spread_capture_ratio) || 0) / 100;
      const assets = Number(finance.totalAssets) || 0, liabilities = Number(finance.totalLiabilities) || 0;
      const postLeverage = assets + principalMillion > 0 ? (liabilities + principalMillion) / (assets + principalMillion) * 100 : 0;
      const curve = (policy.leverage_spread_model?.spread_curve || []).map((point) => [Number(point.liability_ratio_pct), Number(point.additional_spread_bps) || 0]);
      let leverageBps = 0; for (let index = 1; index < curve.length; index += 1) { const [leftRatio,leftSpread]=curve[index-1], [rightRatio,rightSpread]=curve[index]; if (postLeverage <= rightRatio) { leverageBps = postLeverage <= leftRatio ? leftSpread : leftSpread + (rightSpread-leftSpread)*(postLeverage-leftRatio)/(rightRatio-leftRatio); break; } leverageBps=rightSpread; }
      const termBps = Number(product.tenor_spread_bps?.[tenor] || 0) + Number(product.grace_spread_bps?.[grace] || 0);
      const blocked = postLeverage >= Number(policy.leverage_spread_model?.block_if_post_draw_ratio_at_or_above_pct || 80);
      const rate = blocked ? null : Math.max(Number(policy.min_annual_interest_rate_pct) || 1, Math.min(Number(policy.max_annual_interest_rate_pct) || 9.5, base + adjustment + (typeSpread + termBps + leverageBps) / 100 + hyStress));
      return { rate, termBps, leverageBps, postLeverage, blocked };
    }

    function refreshFinancingQuotes() {
      const quarter = currentOperationQuarter();
      el.financingAffairsProducts.querySelectorAll("[data-financing-product-card]").forEach((card) => { const id=card.getAttribute("data-financing-product-card"), product=state.operations?.financingProducts?.[id]; if(!product||!quarter)return; const amount=Number(card.querySelector("[data-loan-amount]")?.value)*100, tenor=Number(card.querySelector("[data-loan-tenor]")?.value), grace=Number(card.querySelector("[data-loan-grace]")?.value||0), quote=financingQuote(product,amount,tenor,grace,quarter); const out=card.querySelector("[data-loan-quote]"); if(out) out.textContent=quote.blocked ? "拒绝提款" : fmtPct(quote.rate); const detail=card.querySelector("[data-loan-quote-detail]"); if(detail) detail.textContent=`期限/宽限 +${fmt(quote.termBps,0)}bp；杠杆 +${fmt(quote.leverageBps,0)}bp；提款后负债率 ${fmtPct(quote.postLeverage)}`; });
    }

    function renderFinancingAffairs() {
      const quarter = currentOperationQuarter();
      if (!state.operations || !quarter || state.operations.mode !== "simulate_default") {
        el.financingAffairsCaption.textContent = "仅模拟运营可发起融资。";
        el.financingAffairsStatus.innerHTML = "";
        el.financingAffairsRules.innerHTML = "";
        el.financingAffairsProducts.innerHTML = `<div class="empty">加载模拟运营后显示融资方案。</div>`;
        el.financingAffairsLoans.innerHTML = `<div class="empty">暂无已生效融资</div>`;
        return;
      }
      const products = state.operations.financingProducts || {};
      const debt = quarter.finance || {};
      const policy = state.operations.financingPolicy || {};
      const leverage = policy.leverage_spread_model || {};
      const rateText = Number(debt.loanWeightedInterestRatePct) > 0 ? fmtPct(debt.loanWeightedInterestRatePct) : "暂无存续贷款";
      el.financingAffairsCaption.textContent = `${quarter.label}；选择产品、融资额和期限后确认提款。实际利率在提款季锁定。`;
      el.financingAffairsStatus.innerHTML = `<div><span>期末现金</span><strong>${fmtMoney(debt.endCash)}</strong></div><div><span>资产负债率</span><strong>${fmtPct(debt.liabilityRatioPct)}</strong></div><div><span>当前贷款利率</span><strong>${rateText}</strong></div>`;
      el.financingAffairsRules.innerHTML = `<div class="financing-rule"><span>定价基础</span><strong>10年利率 + 产品/期限利差 + 信用压力 + 杠杆加点</strong></div><div class="financing-rule"><span>杠杆加点</span><strong>45%以下 +0bp；45%-80% 按曲线线性加点，60%约 +60bp、70%约 +150bp</strong></div><div class="financing-rule"><span>授信拒绝线</span><strong>提款前或提款后资产负债率达到 ${fmt(leverage.block_if_post_draw_ratio_at_or_above_pct || 80, 0)}% 即拒绝提款，不生成贷款利率</strong></div>`;
      const alreadyDrawn = state.playerActions.some((action) => action?.type === "draw_loan" && Number(action.startedAtIndex) === Number(quarter.index));
      el.financingAffairsProducts.innerHTML = Object.entries(products).map(([id, product]) => {
        const tenors = product.tenors || [];
        const grace = product.grace || [0];
        const quote = financingQuote(product, 10000, tenors[0], grace[0], quarter);
        return `<section class="financing-product" data-financing-product-card="${escapeHtml(id)}"><div class="financing-product-head"><div><h3>${escapeHtml(product.label)}</h3><span>${escapeHtml(product.repayment_style === "bullet_principal" ? "到期一次还本" : (product.repayment_style === "equal_principal" ? "等额本金" : "宽限后等额本金"))}</span></div><span>提款季锁定</span></div><div class="financing-product-grid"><div class="financing-field"><label>融资额（亿元）</label><input type="number" min="10" max="1000" step="10" value="100" data-loan-amount="${escapeHtml(id)}"></div><div class="financing-field"><label>期限</label><select data-loan-tenor="${escapeHtml(id)}">${tenors.map((value) => `<option value="${value}">${value} 季</option>`).join("")}</select></div>${grace[0] ? `<div class="financing-field"><label>宽限期</label><select data-loan-grace="${escapeHtml(id)}">${grace.map((value) => `<option value="${value}">${value} 季</option>`).join("")}</select></div>` : `<div class="financing-rate"><span>还款安排</span><strong>${escapeHtml(product.repayment_style === "bullet_principal" ? "到期归还本金" : "每季等额还本")}</strong></div>`}<div class="financing-rate"><span>当前年利率报价</span><strong data-loan-quote>${fmtPct(quote.rate)}</strong><span data-loan-quote-detail>期限/宽限 +${fmt(quote.termBps,0)}bp；提款后负债率 ${fmtPct(quote.postLeverage)}</span></div></div><div class="financing-submit"><span class="project-plan-note">本季最多新增一笔；超过拒绝线不提款。</span><button class="primary" type="button" data-financing-action="draw" data-financing-product="${escapeHtml(id)}"${alreadyDrawn ? " disabled" : ""}>确认提款</button></div></section>`;
      }).join("");
      const loans = state.playerActions.filter((action) => action?.type === "draw_loan" && Number(action.startedAtIndex) <= Number(quarter.index));
      el.financingAffairsLoans.innerHTML = loans.length ? loans.map((loan) => `<section class="project-plan"><div class="project-plan-head"><div><h3>${escapeHtml(products[loan.productId]?.label || "贷款")}</h3><span>${escapeHtml(loan.startedAtLabel || projectQuarterLabel(loan.startedAtIndex))} 提款</span></div><span>${fmtMoney(loan.principalMillionCny)}</span></div><div class="project-plan-grid"><div class="project-plan-kv"><span>期限</span><strong>${fmt(loan.tenorQuarters, 0)} 季</strong></div><div class="project-plan-kv"><span>本季利息</span><strong>${fmtMoney(debt.interestExpense)}</strong></div><div class="project-plan-kv"><span>贷款余额</span><strong>${fmtMoney((debt.grossDebt || 0))}</strong></div></div></section>`).join("") : `<div class="empty">暂无已生效融资</div>`;
    }

    async function drawFinancing(productId, button) {
      const quarter = currentOperationQuarter();
      const product = state.operations?.financingProducts?.[productId];
      if (!quarter || !product) return;
      const amount = Number(el.financingAffairsProducts.querySelector(`[data-loan-amount="${productId}"]`)?.value) * 100;
      const tenor = Number(el.financingAffairsProducts.querySelector(`[data-loan-tenor="${productId}"]`)?.value);
      const grace = Number(el.financingAffairsProducts.querySelector(`[data-loan-grace="${productId}"]`)?.value || 0);
      if (!Number.isFinite(amount) || amount < 1000 || amount > 100000) { status("融资额请设在 10 至 1000 亿元之间。", "error"); return; }
      const action = { id: `loan:${productId}:${quarter.index}`, type: "draw_loan", productId, principalMillionCny: amount, tenorQuarters: tenor, gracePeriodQuarters: grace, startedAtIndex: Number(quarter.index), startedAtLabel: quarter.label };
      upsertPlayerAction(action); setOpsLoading(true, "simulate_default");
      try { await refreshPlayerSimulation(Number(quarter.index), `${product.label} 已提交，提款结果已计入本季财务。`); } catch (error) { state.playerActions = state.playerActions.filter((item) => playerActionKey(item) !== playerActionKey(action)); status(String(error.message || error), "error"); } finally { setOpsLoading(false); }
    }

    function renderProjectAffairs() {
      const quarter = currentOperationQuarter();
      if (!state.operations || !quarter) {
        el.projectAffairsCaption.textContent = "加载模拟运营后按槽位选择可执行工程。";
        el.projectAffairsSlotList.innerHTML = `<div class="empty">暂无槽位</div>`;
        el.projectAffairsSlotTitle.textContent = "槽位方案";
        el.projectAffairsSlotCaption.textContent = "选择一个槽位查看翻新、新建或拆除重建方案。";
        el.projectAffairsSlotActions.innerHTML = "";
        el.projectAffairsSlotOverview.innerHTML = "";
        el.projectAffairsPlanList.innerHTML = `<div class="empty">暂无可执行方案</div>`;
        el.projectAffairsStartedTitle.textContent = "本槽位已启动项目";
        el.projectAffairsStartedCaption.textContent = "选择槽位后显示对应的真实工程。";
        el.projectAffairsStartedRows.innerHTML = `<tr><td colspan="8" style="text-align:center;color:var(--muted)">暂无已启动项目</td></tr>`;
        return;
      }
      const selectedSlot = PROJECT_AFFAIRS_SLOTS.find((slot) => slot.slotId === state.projectAffairsSlotId)
        || PROJECT_AFFAIRS_SLOTS[0];
      state.projectAffairsSlotId = selectedSlot.slotId;
      const catalogs = state.operations.projectCatalog || [];
      el.projectAffairsCaption.textContent = `${quarter.label}；按槽位选择方案，确认开工后才写入项目台账。`;
      el.projectAffairsSlotList.innerHTML = PROJECT_AFFAIRS_SLOTS.map((slot) => {
        const currentSize = projectSlotCurrentSize(slot, quarter);
        const active = projectSlotHasActiveWork(slot.slotId, quarter);
        const rebuildDone = projectSlotHasCompletedRebuild(slot.slotId, quarter);
        const isBlankSlot = currentSize === "empty" && !active;
        const statusText = active ? "施工中" : (isBlankSlot ? "空白" : (currentSize !== "empty" ? (rebuildDone ? "重建后使用中" : "使用中") : "可建设"));
        const sizeText = isBlankSlot ? "空白" : facilitySizeLabel(currentSize);
        return `
          <button class="project-slot-button" type="button" data-project-slot-id="${escapeHtml(slot.slotId)}" aria-selected="${slot.slotId === selectedSlot.slotId}">
            <span class="project-slot-title"><strong>${escapeHtml(slotDisplayName(slot.slotId, slot.name))}</strong><span>${escapeHtml(slotDisplayLabel(slot.slotRole, slot.slotId))}</span></span>
            <span class="project-slot-meta"><span>${escapeHtml(slot.slotId)} / ${escapeHtml(slot.airport)} / ${escapeHtml(sizeText)}</span><span>${escapeHtml(statusText)}</span></span>
          </button>
        `;
      }).join("");
      const selectedSize = projectSlotCurrentSize(selectedSlot, quarter);
      const selectedSlotName = slotDisplayName(selectedSlot.slotId, selectedSlot.name);
      const selectedCapacity = currentSlotAvailableCapacity(selectedSlot, quarter);
      const maintenanceAnchor = slotMaintenanceAnchor(selectedSlot.slotId, quarter);
      const activeRebuild = activeSlotProject(selectedSlot.slotId, "拆除重建", quarter);
      const activeConstruction = activeSlotProject(selectedSlot.slotId, "新建", quarter);
      const maintenanceAgeScore = activeRebuild || activeConstruction
        ? null
        : perceivedMaintenanceAgeScore(maintenanceAnchor?.effectiveAgeYears);
      const constructionQualityImpact = slotConstructionQualityImpact(selectedSlot, quarter);
      const statusText = activeRebuild ? "施工关闭" : (projectSlotHasActiveWork(selectedSlot.slotId, quarter) ? "施工中" : (selectedSize === "empty" ? "未投运" : "使用中"));
      el.projectAffairsSlotTitle.textContent = `${selectedSlotName} / ${slotDisplayLabel(selectedSlot.slotRole, selectedSlot.slotId)}`;
      el.projectAffairsSlotCaption.textContent = selectedSize === "empty" && !projectSlotHasActiveWork(selectedSlot.slotId, quarter)
        ? `${selectedSlot.slotId}；${selectedSlot.airport}；空白辅助槽位，尚未配置航站楼、容量或工程。`
        : `${selectedSlot.slotId}；${selectedSlot.airport}。`;
      el.projectAffairsSlotOverview.innerHTML = selectedSize === "empty" ? "" : `
        <div class="project-slot-overview-item"><span>状态与规格</span><strong>${escapeHtml(statusText)} / ${escapeHtml(currentSlotFacilitySize(selectedSlot, quarter))}</strong></div>
        <div class="project-slot-overview-item"><span>标准 / 当前可用容量</span><strong>${fmt(selectedCapacity.standardDesign, 1)} / ${fmt(selectedCapacity.standardMax, 1)} -> ${fmt(selectedCapacity.availableDesign, 1)} / ${fmt(selectedCapacity.availableMax, 1)} 百万人</strong></div>
        <div class="project-slot-overview-item"><span>等效维护年龄</span><strong>${activeRebuild ? "施工关闭，不计维护年龄" : `${fmtMaintenanceAge(maintenanceAnchor?.effectiveAgeYears)}${maintenanceAnchor?.source ? ` / ${escapeHtml(maintenanceAnchor.source)}` : ""}`}</strong></div>
        <div class="project-slot-overview-item"><span>维护年龄分</span><strong>${maintenanceAgeScore == null ? "不参与感知质量" : fmtQualityScoreDelta(maintenanceAgeScore)}</strong></div>
        <div class="project-slot-overview-item"><span>工程影响分</span><strong>${activeRebuild ? "施工关闭，不参与" : (activeConstruction ? "未投运，不参与" : fmtQualityScoreDelta(constructionQualityImpact))}</strong></div>
        <div class="project-slot-overview-item"><span>当前工程状态</span><strong>${escapeHtml(slotProjectStatusSummary(selectedSlot, quarter))}</strong></div>
      `;
      if (selectedSize !== "empty") {
        const isRenaming = state.projectAffairsRenamingSlotId === selectedSlot.slotId;
        el.projectAffairsSlotActions.innerHTML = isRenaming ? `
          <input id="projectSlotRenameInput" value="${escapeHtml(selectedSlotName)}" maxlength="24" aria-label="航站楼名称">
          <button class="primary" type="button" data-project-slot-name-action="confirm">确认</button>
          <button type="button" data-project-slot-name-action="cancel">取消</button>
        ` : `<button type="button" data-project-slot-name-action="edit">改名</button>`;
      } else {
        el.projectAffairsSlotActions.innerHTML = "";
      }
      const templates = catalogs.filter((template) => {
        if (template.slotId !== selectedSlot.slotId) return false;
        if (template.projectType === "construction") {
          return selectedSize === "empty" || projectSlotHasActiveWork(selectedSlot.slotId, quarter);
        }
        return true;
      });
      el.projectAffairsPlanList.innerHTML = templates.length ? templates.map((template) => {
        const availability = projectTemplateAvailability(template, selectedSlot, quarter);
        const action = template.projectType === "renovation"
          ? activeRenovationActionForTemplate(template, quarter)
          : (template.projectType === "rebuild"
            ? activeRebuildActionForTemplate(template, quarter)
            : (template.projectType === "demolition"
              ? activeDemolitionActionForTemplate(template, quarter)
              : (template.projectType === "construction"
                ? activeConstructionActionForTemplate(template, quarter)
                : projectActionForTemplate(template.templateId))));
        const statusText = action ? projectStatusForTemplate(template, quarter) : availability.reason;
        const renovationFacilitySize = action?.eventConfig?.facility_size || selectedSize;
        const renovation = template.projectType === "renovation" ? renovationEventTerms(template, action, renovationFacilitySize) : null;
        const cooldownEndIndex = template.projectType === "renovation"
          ? renovationCooldownEndIndex(template, quarter)
          : null;
        const rebuildTargetSizes = template.projectType === "rebuild" ? (template.rebuildAllowedTargetSizes || []) : [];
        const rebuildTarget = rebuildTargetSizes.includes(state.projectRebuildTargetByTemplate[template.templateId])
          ? state.projectRebuildTargetByTemplate[template.templateId]
          : (rebuildTargetSizes.includes(template.targetFacilitySize) ? template.targetFacilitySize : rebuildTargetSizes[0]);
        const rebuildSourceSize = action?.eventConfig?.source_facility_size || selectedSize;
        const rebuildDetails = template.projectType === "rebuild"
          ? (template.rebuildTargetOptionsBySource?.[rebuildSourceSize]?.[rebuildTarget] || template.rebuildTargetOptions?.[rebuildTarget] || {})
          : {};
        const demolitionSourceSize = action?.eventConfig?.source_facility_size || selectedSize;
        const demolitionDetails = template.projectType === "demolition"
          ? (template.demolitionOptionsBySource?.[demolitionSourceSize] || {})
          : {};
        const constructionTargetSizes = template.projectType === "construction" ? (template.constructionAllowedTargetSizes || []) : [];
        const constructionTarget = constructionTargetSizes.includes(state.projectConstructionTargetByTemplate[template.templateId])
          ? state.projectConstructionTargetByTemplate[template.templateId]
          : constructionTargetSizes[0];
        const constructionDetails = template.projectType === "construction"
          ? (template.constructionTargetOptions?.[constructionTarget] || {})
          : {};
        const rebuildCooldownEndsAt = template.projectType === "rebuild"
          ? rebuildCooldownEndIndex(template, quarter)
          : null;
        const planDuration = Number(action?.eventConfig?.duration_quarters ?? (template.projectType === "rebuild" ? rebuildDetails.durationQuarters : (template.projectType === "demolition" ? demolitionDetails.durationQuarters : (template.projectType === "construction" ? constructionDetails.durationQuarters : template.durationQuarters)))) || 0;
        const planCapex = Number(action?.eventConfig?.[template.projectType === "construction" ? "capex_million_cny" : "asset_capex_million_cny"] ?? (renovation?.capex ?? (template.projectType === "rebuild" ? rebuildDetails.totalCapex : (template.projectType === "construction" ? constructionDetails.totalCapex : template.totalCapex)))) || 0;
        const planDemolition = Number(action?.eventConfig?.demolition_expense_million_cny ?? (template.projectType === "rebuild" ? rebuildDetails.demolitionExpense : (template.projectType === "demolition" ? demolitionDetails.demolitionExpense : template.demolitionExpense))) || 0;
        const rebuildDemolitionDuration = Number(action?.eventConfig?.demolition_duration_quarters ?? rebuildDetails.demolitionDurationQuarters) || 0;
        const rebuildConstructionDuration = Number(action?.eventConfig?.construction_duration_quarters ?? rebuildDetails.constructionDurationQuarters) || 0;
        const renovationEventDetails = renovation ? `
          <section class="project-renovation-event">
            <h4>标准翻新事件${action ? "（参数已冻结）" : ""}</h4>
            <div class="project-plan-grid">
              <div class="project-plan-kv"><span>开工</span><strong>${escapeHtml(action?.startedAtLabel || "确认后本季开工")}</strong></div>
              <div class="project-plan-kv"><span>预计完工</span><strong>${escapeHtml(action ? projectQuarterLabel(Number(action.startedAtIndex) + renovation.durationQuarters) : `开工后 ${fmt(renovation.durationQuarters, 0)} 季`)}</strong></div>
              <div class="project-plan-kv"><span>施工期容量影响</span><strong>保留 ${fmtPct(renovation.capacityMultiplier * 100)} / 设计少 ${fmt(template.renovationOptions?.[renovationFacilitySize]?.designCapacityLoss ?? template.designCapacityLoss, 1)} 百万人</strong></div>
              <div class="project-plan-kv"><span>维护年龄保留</span><strong>${fmtPct(Number(template.maintenanceAgeRetentionRatio) * 100)}，最低 ${fmt(template.minimumEffectiveMaintenanceAgeYears, 0)} 年</strong></div>
              <div class="project-plan-kv"><span>翻新资产折旧</span><strong>${fmt(renovation.usefulLifeYears, 0)} 年 / 残值 ${fmtPct(renovation.residualValuePct)}</strong></div>
              <div class="project-plan-kv"><span>再次翻新</span><strong>${action ? "本工程完工后冷却 6 年" : (cooldownEndIndex != null && Number(quarter.index) < cooldownEndIndex ? `${projectQuarterLabel(cooldownEndIndex)}可再次发起` : "当前可发起")}</strong></div>
            </div>
          </section>
        ` : "";
        const startDisabled = availability.available ? "" : " disabled";
        const className = action && projectStatusForTemplate(template, quarter) === "施工中" ? " active" : "";
        return `
          <section class="project-plan${className}">
            <div class="project-plan-head">
              <div><h3>${escapeHtml(projectTemplateDisplayName(template))}</h3><span>${escapeHtml(template.projectType === "renovation" ? "标准翻新事件" : projectTypeLabel(template.projectType))} / ${escapeHtml(statusText)}</span></div>
              <span>${escapeHtml(template.projectType === "construction" ? `建成 ${facilitySizeLabel(action?.eventConfig?.target_facility_size || constructionTarget)}` : (template.projectType === "rebuild" ? `${facilitySizeLabel(rebuildSourceSize)} -> ${facilitySizeLabel(action?.eventConfig?.target_facility_size || rebuildTarget)}` : (template.projectType === "demolition" ? `${facilitySizeLabel(demolitionSourceSize)} -> 空白` : `保持 ${facilitySizeLabel(renovationFacilitySize)}`)))}</span>
            </div>
            <div class="project-plan-grid">
              ${template.projectType === "rebuild" ? `<div class="project-plan-kv"><span>目标规格</span><strong><select data-rebuild-target-template="${escapeHtml(template.templateId)}"${action ? " disabled" : ""}>${rebuildTargetSizes.map((size) => `<option value="${escapeHtml(size)}"${size === rebuildTarget ? " selected" : ""}>${escapeHtml(facilitySizeLabel(size))}</option>`).join("")}</select></strong></div>` : ""}
              ${template.projectType === "construction" ? `<div class="project-plan-kv"><span>目标规格</span><strong><select data-construction-target-template="${escapeHtml(template.templateId)}"${action ? " disabled" : ""}>${constructionTargetSizes.map((size) => `<option value="${escapeHtml(size)}"${size === constructionTarget ? " selected" : ""}>${escapeHtml(facilitySizeLabel(size))}</option>`).join("")}</select></strong></div>` : ""}
              <div class="project-plan-kv"><span>施工周期</span><strong>${fmt(planDuration, 0)} 季</strong></div>
              ${template.projectType === "rebuild" ? `<div class="project-plan-kv"><span>工期组成</span><strong>拆除 ${fmt(rebuildDemolitionDuration, 0)} 季 + 新建 ${fmt(rebuildConstructionDuration, 0)} 季</strong></div>` : ""}
              <div class="project-plan-kv"><span>资本化支出</span><strong>${fmtMoney(planCapex)}</strong></div>
              ${renovation ? "" : `<div class="project-plan-kv"><span>拆除费用</span><strong>${planDemolition ? fmtMoney(planDemolition) : "-"}</strong></div>`}
              ${renovation ? "" : `<div class="project-plan-kv"><span>施工期容量</span><strong>${escapeHtml(projectPlanCapacityText(template))}</strong></div>`}
              ${template.projectType === "rebuild" ? `<div class="project-plan-kv"><span>维护年龄</span><strong>完工后重置为 0 年</strong></div><div class="project-plan-kv"><span>再次重建</span><strong>${action ? "本工程完工后冷却 20 年" : (rebuildCooldownEndsAt != null && Number(quarter.index) < rebuildCooldownEndsAt ? `${projectQuarterLabel(rebuildCooldownEndsAt)}可再次发起` : "当前可发起")}</strong></div>` : ""}
              ${template.projectType === "construction" ? `<div class="project-plan-kv"><span>维护年龄</span><strong>完工后从 0 年起算</strong></div><div class="project-plan-kv"><span>后续翻新</span><strong>完工后冷却 6 年</strong></div>` : ""}
              ${template.projectType === "demolition" ? `<div class="project-plan-kv"><span>清场期</span><strong>完工后 4 季可重新新建</strong></div>` : ""}
              ${renovation || template.projectType === "demolition" ? "" : `<div class="project-plan-kv"><span>完成后设计容量</span><strong>${fmt(template.projectType === "rebuild" ? rebuildDetails.targetDesignCapacity : (template.projectType === "construction" ? constructionDetails.targetDesignCapacity : template.targetDesignCapacity), 1)} 百万人</strong></div>`}
            </div>
            ${renovationEventDetails}
            <div class="project-plan-actions">
              <span class="project-plan-note">开工后，资本开支、施工容量影响、转固、折旧和税务均由服务端按季度重算。</span>
              <button class="primary" type="button" data-project-action="start" data-project-template-id="${escapeHtml(template.templateId)}"${startDisabled}>${action ? "已启动" : (renovation ? "发起翻新" : (template.projectType === "rebuild" ? "启动重建" : (template.projectType === "demolition" ? "启动拆除" : "启动新建")))}</button>
            </div>
          </section>
        `;
      }).join("") : `<div class="empty">该槽位当前没有可启动工程。</div>`;
      el.projectAffairsStartedTitle.textContent = `${selectedSlotName}施工中项目`;
      el.projectAffairsStartedCaption.textContent = `只显示${slotDisplayLabel(selectedSlot.slotRole, selectedSlot.slotId)}当前施工中的工程；完工项目转入经营报告的设施与项目台账。`;
      const started = state.playerActions
        .filter((action) => action?.type === "start_project")
        .map((action) => ({ action, template: projectTemplateById(action.templateId), project: projectById(action.projectId) }))
        .filter((item) => item.template?.slotId === selectedSlot.slotId && item.project && projectActiveNow(item.project, quarter));
      el.projectAffairsStartedRows.innerHTML = started.length ? started.map(({ action, template }) => {
        const project = projectById(action.projectId);
        const statusText = projectStatusForTemplate(template, quarter);
        const active = Boolean(project && projectActiveNow(project, quarter));
        const renovationTerms = template.projectType === "renovation" ? renovationEventTerms(template, action) : null;
        const duration = Number(renovationTerms?.durationQuarters ?? action.eventConfig?.duration_quarters ?? template.durationQuarters) || 0;
        const completionIndex = Number(action.startedAtIndex) + duration;
        const currentOutlay = active
          ? Number((renovationTerms?.capex ?? action.eventConfig?.asset_capex_million_cny ?? template.totalCapex) || 0) / Math.max(1, duration || 1)
            + Number((action.eventConfig?.demolition_expense_million_cny ?? template.demolitionExpense) || 0) / Math.max(1, duration || 1)
          : 0;
        return `
          <tr>
            <td>${escapeHtml(projectTemplateDisplayName(template))}</td>
            <td>${escapeHtml(slotDisplayLabel(template.slotRole, template.slotId))}</td>
            <td>${escapeHtml(projectTypeLabel(template.projectType))}</td>
            <td>${escapeHtml(statusText)}</td>
            <td>${escapeHtml(action.startedAtLabel || projectQuarterLabel(action.startedAtIndex))}</td>
            <td>${escapeHtml(projectQuarterLabel(completionIndex))}</td>
            <td>${fmtMoney(currentOutlay)}</td>
            <td>${escapeHtml(projectPlanCapacityText(template))}</td>
          </tr>
        `;
      }).join("") : `<tr><td colspan="8" style="text-align:center;color:var(--muted)">暂无本槽位已启动项目</td></tr>`;
    }

    async function startProjectTemplate(templateId) {
      const template = projectTemplateById(templateId);
      const quarter = currentOperationQuarter();
      const slot = PROJECT_AFFAIRS_SLOTS.find((item) => item.slotId === template?.slotId);
      if (!template || !quarter || !slot) return;
      const availability = projectTemplateAvailability(template, slot, quarter);
      if (!availability.available) {
        status(availability.reason, "error");
        return;
      }
      const targetFacilitySize = template.projectType === "rebuild"
        ? state.projectRebuildTargetByTemplate[template.templateId] || template.targetFacilitySize
        : (template.projectType === "construction"
          ? state.projectConstructionTargetByTemplate[template.templateId] || template.constructionAllowedTargetSizes?.[0]
          : null);
      if (template.projectType === "rebuild" && !(template.rebuildAllowedTargetSizes || []).includes(targetFacilitySize)) {
        status("请选择该槽位允许的重建目标规格。", "error");
        return;
      }
      if (template.projectType === "construction" && !(template.constructionAllowedTargetSizes || []).includes(targetFacilitySize)) {
        status("请选择该槽位允许的新建目标规格。", "error");
        return;
      }
      const action = projectPlanAction(template, quarter, targetFacilitySize);
      upsertPlayerAction(action);
      setOpsLoading(true, "simulate_default");
      status(`${template.name} 已确认开工，正在由服务端重算容量、工程资产和财务结果。`);
      try {
        await refreshPlayerSimulation(
          Number(quarter.index),
          `${template.name} 已于 ${quarter.label} 开工；经营报告和台账已更新。`,
        );
      } catch (error) {
        state.playerActions = state.playerActions.filter((item) => playerActionKey(item) !== playerActionKey(action));
        status(String(error.message || error), "error");
      } finally {
        setOpsLoading(false);
      }
    }

    function contractLedgerRows(selection = contractPartnershipLedgerSelection()) {
      if (!selection.quarters.length || !selection.pointQuarter) return [];
      const lastQuarter = selection.pointQuarter;
      return CONTRACT_DEFINITIONS.map((contract) => {
        const revenue = selection.quarters.reduce((total, quarter) => total + contractValue(contract, quarter, "revenueKey"), 0);
        const guarantee = selection.quarters.reduce((total, quarter) => total + contractValue(contract, quarter, "guaranteeKey"), 0);
        const shareRevenue = selection.quarters.reduce((total, quarter) => total + contractValue(contract, quarter, "shareRevenueKey"), 0);
        const sales = selection.quarters.reduce((total, quarter) => total + contractValue(contract, quarter, "salesKey"), 0);
        const cycles = Array.from(new Set(selection.quarters.map((quarter) => contractText(contract, quarter, "cycleKey")).filter(Boolean)));
        return {
          contract,
          name: contract.name,
          segment: contract.segment,
          cycle: cycles.join(" / ") || contractText(contract, lastQuarter, "cycleKey") || "-",
          type: contractTypeLabel(contractText(contract, lastQuarter, "typeKey")),
          revenue,
          guarantee,
          shareRevenue,
          sales,
          sharePct: contractValue(contract, lastQuarter, "revenueSharePctKey"),
          coveragePct: shareRevenue ? (guarantee / shareRevenue) * 100.0 : contractValue(contract, lastQuarter, "coveragePctKey"),
          basis: contractBasisLabel(contractText(contract, lastQuarter, "basisKey")),
          status: contractStatusLabel(contractText(contract, lastQuarter, "statusKey")),
        };
      }).filter((row) => row.revenue > 0 || row.sales > 0 || row.cycle !== "-");
    }

    function aggregateContractPartnershipPeriod(quarters) {
      const sumContract = (contract, keyName) => quarters.reduce((total, quarter) => total + contractValue(contract, quarter, keyName), 0);
      const duty = CONTRACT_DEFINITIONS[0];
      const luxury = CONTRACT_DEFINITIONS[1];
      const dutyRevenue = sumContract(duty, "revenueKey");
      const luxuryRevenue = sumContract(luxury, "revenueKey");
      const dutyGuarantee = sumContract(duty, "guaranteeKey");
      const luxuryGuarantee = sumContract(luxury, "guaranteeKey");
      const dutyShareRevenue = sumContract(duty, "shareRevenueKey");
      const luxuryShareRevenue = sumContract(luxury, "shareRevenueKey");
      return {
        dutyRevenue,
        luxuryRevenue,
        totalRevenue: dutyRevenue + luxuryRevenue,
        dutyGuarantee,
        luxuryGuarantee,
        totalGuarantee: dutyGuarantee + luxuryGuarantee,
        dutyShareRevenue,
        luxuryShareRevenue,
        totalShareRevenue: dutyShareRevenue + luxuryShareRevenue,
      };
    }

    function contractPartnershipPeriodsAll(scope = state.contractPartnershipReportScope) {
      if (!state.operations || !state.operations.quarters.length) return [];
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
        const aggregate = aggregateContractPartnershipPeriod(periodQuarters);
        const previousAggregate = aggregateContractPartnershipPeriod(previousQuarters);
        const yoyPct = previousQuarters.length && previousAggregate.totalRevenue !== 0
          ? ((aggregate.totalRevenue - previousAggregate.totalRevenue) / Math.abs(previousAggregate.totalRevenue)) * 100
          : 0;
        const endQuarter = periodQuarters[periodQuarters.length - 1];
        rows.push({
          ...aggregate,
          index: endQuarter.index,
          year,
          label: financialPeriodLabel(year, endQuarterNo, scope),
          scope: financialScopeLabel(scope),
          endQuarterNo,
          yoyPct,
        });
      }
      return rows;
    }

    function contractPartnershipVisiblePeriods(rows) {
      if (!rows.length) return [];
      const maxStart = Math.max(0, rows.length - CONTRACT_PARTNERSHIP_WINDOW_SIZE);
      if (state.contractPartnershipWindowPinnedToLatest || state.contractPartnershipWindowStart == null) {
        state.contractPartnershipWindowStart = maxStart;
      }
      state.contractPartnershipWindowStart = Math.max(0, Math.min(maxStart, Number(state.contractPartnershipWindowStart) || 0));
      return rows.slice(state.contractPartnershipWindowStart, state.contractPartnershipWindowStart + CONTRACT_PARTNERSHIP_WINDOW_SIZE);
    }

    function selectedContractPartnershipEventYear(kind) {
      const years = contractPartnershipYears();
      if (!years.length) return null;
      const stateKey = kind === "start" ? "contractPartnershipEventStartYear" : "contractPartnershipEventEndYear";
      const defaultValue = kind === "start" ? "earliest" : "latest";
      const edgeYear = kind === "start" ? years[0] : years[years.length - 1];
      const value = state[stateKey];
      if (value === defaultValue) return edgeYear;
      const requested = Number(value);
      if (years.includes(requested)) return requested;
      state[stateKey] = defaultValue;
      return edgeYear;
    }

    function contractPartnershipEventQuarterOptions(year, kind) {
      const yearQuarters = contractPartnershipAvailableQuarters()
        .filter((quarter) => Number(quarter.year) === Number(year));
      const seen = new Set();
      const quarterOptions = yearQuarters
        .map((quarter) => quarterNumber(quarter))
        .filter((quarterNo) => {
          if (!quarterNo || seen.has(quarterNo)) return false;
          seen.add(quarterNo);
          return true;
        })
        .sort((a, b) => a - b)
        .map((quarterNo) => ({ value: `q${quarterNo}`, label: `Q${quarterNo}` }));
      return kind === "end"
        ? [{ value: "latest", label: "最新季度" }, ...quarterOptions]
        : quarterOptions;
    }

    function setContractPartnershipEventPeriodOptions() {
      const years = contractPartnershipYears();
      if (!years.length) {
        el.contractPartnershipEventStartYearSelect.innerHTML = `<option value="earliest">最早</option>`;
        el.contractPartnershipEventStartQuarterSelect.innerHTML = `<option value="q1">Q1</option>`;
        el.contractPartnershipEventEndYearSelect.innerHTML = `<option value="latest">最新</option>`;
        el.contractPartnershipEventEndQuarterSelect.innerHTML = `<option value="latest">最新季度</option>`;
        state.contractPartnershipEventStartYear = "earliest";
        state.contractPartnershipEventStartQuarter = "q1";
        state.contractPartnershipEventEndYear = "latest";
        state.contractPartnershipEventEndQuarter = "latest";
        return;
      }
      const startAllowed = state.contractPartnershipEventStartYear === "earliest"
        || years.includes(Number(state.contractPartnershipEventStartYear));
      const endAllowed = state.contractPartnershipEventEndYear === "latest"
        || years.includes(Number(state.contractPartnershipEventEndYear));
      if (!startAllowed) state.contractPartnershipEventStartYear = "earliest";
      if (!endAllowed) state.contractPartnershipEventEndYear = "latest";
      el.contractPartnershipEventStartYearSelect.innerHTML = [
        `<option value="earliest">最早</option>`,
        ...years.map((year) => `<option value="${year}">${year}</option>`),
      ].join("");
      el.contractPartnershipEventEndYearSelect.innerHTML = [
        `<option value="latest">最新</option>`,
        ...years.map((year) => `<option value="${year}">${year}</option>`),
      ].join("");
      el.contractPartnershipEventStartYearSelect.value = state.contractPartnershipEventStartYear;
      el.contractPartnershipEventEndYearSelect.value = state.contractPartnershipEventEndYear;

      const startYear = selectedContractPartnershipEventYear("start");
      const endYear = selectedContractPartnershipEventYear("end");
      const startOptions = contractPartnershipEventQuarterOptions(startYear, "start");
      const endOptions = contractPartnershipEventQuarterOptions(endYear, "end");
      if (!startOptions.some((option) => option.value === state.contractPartnershipEventStartQuarter)) {
        state.contractPartnershipEventStartQuarter = startOptions[0]?.value || "q1";
      }
      if (!endOptions.some((option) => option.value === state.contractPartnershipEventEndQuarter)) {
        state.contractPartnershipEventEndQuarter = "latest";
      }
      el.contractPartnershipEventStartQuarterSelect.innerHTML = startOptions.map((option) => (
        `<option value="${escapeHtml(option.value)}">${escapeHtml(option.label)}</option>`
      )).join("");
      el.contractPartnershipEventEndQuarterSelect.innerHTML = endOptions.map((option) => (
        `<option value="${escapeHtml(option.value)}">${escapeHtml(option.label)}</option>`
      )).join("");
      el.contractPartnershipEventStartQuarterSelect.value = state.contractPartnershipEventStartQuarter;
      el.contractPartnershipEventEndQuarterSelect.value = state.contractPartnershipEventEndQuarter;
    }

    function selectedContractPartnershipEventQuarter(kind, year) {
      const quarters = contractPartnershipAvailableQuarters()
        .filter((quarter) => Number(quarter.year) === Number(year))
        .sort((a, b) => Number(a.index) - Number(b.index));
      if (!quarters.length) return null;
      const stateKey = kind === "start" ? "contractPartnershipEventStartQuarter" : "contractPartnershipEventEndQuarter";
      if (kind === "end" && state[stateKey] === "latest") return quarters[quarters.length - 1];
      const requestedQuarterNo = Number(String(state[stateKey] || "").match(/\d+/)?.[0]);
      return quarters.find((quarter) => quarterNumber(quarter) === requestedQuarterNo)
        || (kind === "start" ? quarters[0] : quarters[quarters.length - 1]);
    }

    function contractPartnershipEventSelection() {
      const startYear = selectedContractPartnershipEventYear("start");
      const endYear = selectedContractPartnershipEventYear("end");
      const startQuarter = selectedContractPartnershipEventQuarter("start", startYear);
      let endQuarter = selectedContractPartnershipEventQuarter("end", endYear);
      if (!startQuarter || !endQuarter) return { quarters: [], label: "合同事件", startQuarter: null, endQuarter: null };
      if (Number(startQuarter.index) > Number(endQuarter.index)) {
        endQuarter = startQuarter;
        state.contractPartnershipEventEndYear = String(startQuarter.year);
        state.contractPartnershipEventEndQuarter = `q${quarterNumber(startQuarter)}`;
      }
      const quarters = contractPartnershipAvailableQuarters().filter((quarter) => (
        Number(quarter.index) >= Number(startQuarter.index)
        && Number(quarter.index) <= Number(endQuarter.index)
      ));
      return {
        quarters,
        label: `${startQuarter.label} - ${endQuarter.label}`,
        startQuarter,
        endQuarter,
      };
    }

    function previousContractQuarter(quarter) {
      if (!state.operations || !quarter) return null;
      const index = Number(quarter.index);
      if (!Number.isFinite(index) || index <= 0) return null;
      return state.operations.quarters[index - 1] || null;
    }

    function contractEventRows(selection = contractPartnershipEventSelection()) {
      const rows = [];
      selection.quarters.forEach((quarter) => {
        const previous = previousContractQuarter(quarter);
        CONTRACT_DEFINITIONS.forEach((contract) => {
          const currentCycle = contractText(contract, quarter, "cycleKey");
          const previousCycle = contractText(contract, previous, "cycleKey");
          const currentStatus = contractText(contract, quarter, "statusKey");
          const previousStatus = contractText(contract, previous, "statusKey");
          const currentType = contractText(contract, quarter, "typeKey");
          const previousType = contractText(contract, previous, "typeKey");
          const currentBasis = contractText(contract, quarter, "basisKey");
          const previousBasis = contractText(contract, previous, "basisKey");
          const revenue = contractValue(contract, quarter, "revenueKey");
          const baseRow = {
            period: quarter.label,
            contractName: contract.name,
            segment: contract.segment,
            amount: revenue,
            quarterIndex: Number(quarter.index),
          };
          if (currentCycle && !previousCycle) {
            rows.push({
              ...baseRow,
              event: "合同生效",
              impact: "合同状态",
              note: `${currentCycle}；${contractTypeLabel(currentType)}；${contractStatusLabel(currentStatus)}`,
              eventOrder: 0,
            });
          } else if (currentCycle && previousCycle && currentCycle !== previousCycle) {
            rows.push({
              ...baseRow,
              event: "合同续期",
              impact: "新合同周期",
              note: `${previousCycle} -> ${currentCycle}；${contractTypeLabel(currentType)}`,
              eventOrder: 1,
            });
          }
          if (currentStatus && previousStatus && currentStatus !== previousStatus && currentCycle === previousCycle) {
            rows.push({
              ...baseRow,
              event: "状态变更",
              impact: "合同状态",
              note: `${contractStatusLabel(previousStatus)} -> ${contractStatusLabel(currentStatus)}`,
              eventOrder: 2,
            });
          }
          if (currentType && previousType && currentType !== previousType && currentCycle === previousCycle) {
            rows.push({
              ...baseRow,
              event: "条款调整",
              impact: "合同类型",
              note: `${contractTypeLabel(previousType)} -> ${contractTypeLabel(currentType)}`,
              eventOrder: 3,
            });
          }
          if (currentBasis && previousBasis && currentBasis !== previousBasis) {
            rows.push({
              ...baseRow,
              event: "收入口径切换",
              impact: "收入确认",
              note: `${contractBasisLabel(previousBasis)} -> ${contractBasisLabel(currentBasis)}`,
              eventOrder: 4,
            });
          }
        });
      });
      return rows.sort((a, b) => (b.quarterIndex - a.quarterIndex) || (a.eventOrder - b.eventOrder));
    }

    function renderContractLedger() {
      setContractPartnershipLedgerPeriodOptions();
      const selection = contractPartnershipLedgerSelection();
      const rows = contractLedgerRows(selection);
      contractPartnershipControlMode("ledger");
      el.contractPartnershipMetricTitle.textContent = "合同台账";
      el.contractPartnershipMetricCaption.textContent = selection.pointQuarter
        ? `${selection.label}；${selection.isOverview ? "显示年内合同口径汇总" : "显示该季度合同状态"}`
        : "加载运营后显示合同台账";
      el.contractPartnershipHeaderRow.innerHTML = `
        <th>合同</th>
        <th>板块</th>
        <th>周期</th>
        <th>类型</th>
        <th>收入</th>
        <th>保底</th>
        <th>分成收入</th>
        <th>分成率</th>
        <th>收入口径</th>
        <th>状态</th>
      `;
      el.contractPartnershipMetricRows.innerHTML = rows.length ? rows.map((row) => `
        <tr>
          <td>${escapeHtml(row.name)}</td>
          <td>${escapeHtml(row.segment)}</td>
          <td>${escapeHtml(row.cycle)}</td>
          <td>${escapeHtml(row.type)}</td>
          <td>${fmtMoney(row.revenue)}</td>
          <td>${fmtMoney(row.guarantee)}</td>
          <td>${fmtMoney(row.shareRevenue)}</td>
          <td>${fmtPct(row.sharePct)}</td>
          <td>${escapeHtml(row.basis)}</td>
          <td>${escapeHtml(row.status)}</td>
        </tr>
      `).join("") : `<tr><td colspan="10" style="text-align:center;color:var(--muted)">暂无合同台账</td></tr>`;
    }

    function renderContractRevenue() {
      const allRows = contractPartnershipPeriodsAll();
      const rows = contractPartnershipVisiblePeriods(allRows);
      const maxStart = Math.max(0, allRows.length - CONTRACT_PARTNERSHIP_WINDOW_SIZE);
      contractPartnershipControlMode("scope");
      el.contractPartnershipMetricTitle.textContent = "合同收入";
      el.contractPartnershipScopeSelect.value = state.contractPartnershipReportScope;
      el.contractPartnershipRangeInput.min = "0";
      el.contractPartnershipRangeInput.max = String(maxStart);
      el.contractPartnershipRangeInput.value = String(state.contractPartnershipWindowStart || 0);
      el.contractPartnershipRangeInput.disabled = maxStart === 0;
      el.contractPartnershipTicks.style.gridTemplateColumns = allRows.length
        ? `repeat(${Math.min(allRows.length, CONTRACT_PARTNERSHIP_WINDOW_SIZE)}, minmax(0, 1fr))`
        : "1fr";
      el.contractPartnershipTicks.innerHTML = rows.map((row) => `<span class="financial-tick">${escapeHtml(row.year)}</span>`).join("");
      el.contractPartnershipHeaderRow.innerHTML = `
        <th>期间</th>
        <th>合同收入</th>
        <th>免税收入</th>
        <th>奢侈品收入</th>
        <th>保底合计</th>
        <th>同比增幅</th>
      `;
      if (!state.operations || !allRows.length || !rows.length) {
        el.contractPartnershipMetricCaption.textContent = "柱：免税/奢侈品合同收入 / 线：总合同收入同比";
        el.contractPartnershipMetricChart.innerHTML = `<div class="empty">加载运营后显示合同收入。</div>`;
        el.contractPartnershipMetricRows.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--muted)">暂无数据</td></tr>`;
        el.contractPartnershipWindowLabel.textContent = "年度轴";
        el.contractPartnershipWindowHint.textContent = "暂无历史";
        return;
      }
      const first = rows[0];
      const last = rows[rows.length - 1];
      const scopeLabel = financialScopeLabel(state.contractPartnershipReportScope);
      el.contractPartnershipMetricCaption.textContent = `${first.label} - ${last.label}；${scopeLabel}；柱：免税/奢侈品合同收入 / 线：总合同收入同比`;
      el.contractPartnershipWindowLabel.textContent = `${first.label} - ${last.label}`;
      el.contractPartnershipWindowHint.textContent = maxStart > 0 ? "拖动查看历史年份" : "当前口径历史已全部显示";
      const styles = getComputedStyle(document.documentElement);
      renderComboChart(el.contractPartnershipMetricChart, rows, {
        title: "合同收入",
        leftFormat: fmtMoney,
        rightPad: 76,
        stackedBars: [
          { label: "免税合同收入", color: styles.getPropertyValue("--blue").trim() || "#62a8ff", value: (row) => row.dutyRevenue, format: fmtMoney },
          { label: "奢侈品合同收入", color: styles.getPropertyValue("--green").trim() || "#35d392", value: (row) => row.luxuryRevenue, format: fmtMoney },
        ],
        line: {
          label: "同比增幅",
          color: styles.getPropertyValue("--amber").trim() || "#f7b84b",
          value: (row) => row.yoyPct,
          format: fmtPct,
        },
      });
      el.contractPartnershipMetricRows.innerHTML = rows.slice().reverse().map((row) => `
        <tr>
          <td>${escapeHtml(row.label)}</td>
          <td>${fmtMoney(row.totalRevenue)}</td>
          <td>${fmtMoney(row.dutyRevenue)}</td>
          <td>${fmtMoney(row.luxuryRevenue)}</td>
          <td>${fmtMoney(row.totalGuarantee)}</td>
          <td>${fmtPct(row.yoyPct)}</td>
        </tr>
      `).join("");
    }

    function renderContractEvents() {
      setContractPartnershipEventPeriodOptions();
      const selection = contractPartnershipEventSelection();
      setContractPartnershipEventPeriodOptions();
      const rows = contractEventRows(selection);
      contractPartnershipControlMode("events");
      el.contractPartnershipMetricTitle.textContent = "合同事件";
      el.contractPartnershipMetricCaption.textContent = selection.startQuarter
        ? `${selection.label}；记录合同周期、状态和收入确认口径变化`
        : "加载运营后显示合同事件";
      el.contractPartnershipHeaderRow.innerHTML = `
        <th>期间</th>
        <th>事件</th>
        <th>合同</th>
        <th>板块</th>
        <th>本期收入</th>
        <th>影响</th>
        <th>说明</th>
      `;
      el.contractPartnershipMetricRows.innerHTML = rows.length ? rows.map((row) => `
        <tr>
          <td>${escapeHtml(row.period)}</td>
          <td>${escapeHtml(row.event)}</td>
          <td>${escapeHtml(row.contractName)}</td>
          <td>${escapeHtml(row.segment)}</td>
          <td>${fmtMoney(row.amount)}</td>
          <td>${escapeHtml(row.impact)}</td>
          <td>${escapeHtml(row.note)}</td>
        </tr>
      `).join("") : `<tr><td colspan="7" style="text-align:center;color:var(--muted)">暂无合同事件</td></tr>`;
    }

    function renderContractPartnershipAnalysis() {
      el.contractPartnershipMetricButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-contract-partnership-metric") === state.contractPartnershipMetric));
      });
      if (state.contractPartnershipMetric === "contractRevenue") {
        renderContractRevenue();
      } else if (state.contractPartnershipMetric === "contractEvents") {
        renderContractEvents();
      } else {
        renderContractLedger();
      }
    }
