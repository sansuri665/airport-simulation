    function loanTypeLabel(value) {
      return {
        short_term: "短期贷款",
        long_term: "长期贷款",
      }[value] || value || "-";
    }

    function loanRepaymentStyleLabel(value) {
      return {
        bullet_principal: "到期一次还本",
        equal_principal: "等额本金",
        grace_then_equal_principal: "宽限后等额本金",
      }[value] || value || "-";
    }

    function periodIndexFromYearQuarter(year, quarter) {
      const match = String(quarter || "").match(/\d+/);
      return Number(year) * 4 + (Number(match ? match[0] : 1) || 1) - 1;
    }

    function loanStartIndex(loan) {
      return periodIndexFromYearQuarter(loan.startYear, loan.startQuarter);
    }

    function operationHistoryThrough(quarter) {
      if (!state.operations || !quarter) return [];
      const index = Number(quarter.index);
      if (!Number.isFinite(index)) return [];
      return state.operations.quarters.slice(0, index + 1);
    }

    function loanDrawdownQuarter(loan, quarter) {
      return operationHistoryThrough(quarter).find((item) => (
        projectIdsContain(item.finance?.loanDrawdownIds, loan.id)
      )) || null;
    }

    function loanBlockedQuarter(loan, quarter) {
      return operationHistoryThrough(quarter).find((item) => (
        projectIdsContain(item.finance?.loanBlockedIds, loan.id)
      )) || null;
    }

    function loanRemainingPrincipal(loan, quarter) {
      const drawdownQuarter = loanDrawdownQuarter(loan, quarter);
      if (!drawdownQuarter) return 0;
      const currentPeriod = periodIndexFromYearQuarter(quarter.year, quarter.quarter);
      const start = loanStartIndex(loan);
      const tenor = Math.max(1, Number(loan.tenorQuarters) || 1);
      const principal = Math.max(0, Number(loan.principal) || 0);
      let balance = principal;
      for (let period = start; period <= currentPeriod; period += 1) {
        const elapsed = period - start;
        if (elapsed < 0 || elapsed >= tenor || balance <= 0) continue;
        let periodPrincipal = 0;
        if (loan.repaymentStyle === "bullet_principal") {
          periodPrincipal = elapsed === tenor - 1 ? balance : 0;
        } else if (loan.repaymentStyle === "grace_then_equal_principal") {
          const grace = Math.min(Math.max(0, Number(loan.graceQuarters) || 0), Math.max(0, tenor - 1));
          const repaymentPeriods = Math.max(1, tenor - grace);
          periodPrincipal = elapsed < grace ? 0 : principal / repaymentPeriods;
          if (elapsed === tenor - 1) periodPrincipal = balance;
        } else {
          periodPrincipal = principal / tenor;
          if (elapsed === tenor - 1) periodPrincipal = balance;
        }
        balance = Math.max(0, balance - Math.min(balance, Math.max(0, periodPrincipal)));
      }
      return balance;
    }

    function loanInterestRateText(loan, quarter) {
      const drawdownQuarter = loanDrawdownQuarter(loan, quarter);
      if (!drawdownQuarter) return "-";
      const drawdownIds = splitProjectIds(drawdownQuarter.finance?.loanDrawdownIds);
      if (drawdownIds.length === 1 && drawdownIds[0] === loan.id) {
        return fmtPct(drawdownQuarter.finance?.loanDrawdownWeightedInterestRatePct);
      }
      const currentActiveIds = splitProjectIds(quarter.finance?.loanActiveIds);
      if (currentActiveIds.length === 1 && currentActiveIds[0] === loan.id) {
        return fmtPct(quarter.finance?.loanWeightedInterestRatePct);
      }
      return "组合利率";
    }

    function debtFinancingLedgerCurrentIndex() {
      if (!state.operations || !state.operations.quarters.length) return -1;
      const minIndex = state.operations.playerStartIndex ?? 0;
      return Math.min(
        Math.max(minIndex, state.operationsQuarterIndex ?? minIndex),
        state.operations.quarters.length - 1,
      );
    }

    function debtFinancingLedgerAvailableQuarters() {
      const index = debtFinancingLedgerCurrentIndex();
      if (index < 0) return [];
      return state.operations.quarters.slice(0, index + 1);
    }

    function debtFinancingLedgerYears() {
      return Array.from(new Set(debtFinancingLedgerAvailableQuarters().map((quarter) => Number(quarter.year))))
        .filter((year) => Number.isFinite(year))
        .sort((a, b) => a - b);
    }

    function selectedDebtFinancingLedgerYear() {
      const currentQuarter = state.operations?.quarters?.[debtFinancingLedgerCurrentIndex()];
      if (!currentQuarter) return null;
      const years = debtFinancingLedgerYears();
      const requested = state.debtFinancingLedgerYear === "latest"
        ? Number(currentQuarter.year)
        : Number(state.debtFinancingLedgerYear);
      if (years.includes(requested)) return requested;
      state.debtFinancingLedgerYear = "latest";
      return Number(currentQuarter.year);
    }

    function debtFinancingLedgerQuarterOptions(year) {
      const yearQuarters = debtFinancingLedgerAvailableQuarters()
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

    function setDebtFinancingLedgerPeriodOptions() {
      const years = debtFinancingLedgerYears();
      if (!years.length) {
        el.debtFinancingLedgerYearSelect.innerHTML = `<option value="latest">最新</option>`;
        el.debtFinancingLedgerQuarterSelect.innerHTML = `<option value="latest">最新季度</option>`;
        state.debtFinancingLedgerYear = "latest";
        state.debtFinancingLedgerQuarter = "latest";
        return;
      }
      const yearValueAllowed = state.debtFinancingLedgerYear === "latest"
        || years.includes(Number(state.debtFinancingLedgerYear));
      if (!yearValueAllowed) state.debtFinancingLedgerYear = "latest";
      el.debtFinancingLedgerYearSelect.innerHTML = [
        `<option value="latest">最新</option>`,
        ...years.map((year) => `<option value="${year}">${year}</option>`),
      ].join("");
      el.debtFinancingLedgerYearSelect.value = state.debtFinancingLedgerYear;

      const selectedYear = selectedDebtFinancingLedgerYear();
      const quarterOptions = debtFinancingLedgerQuarterOptions(selectedYear);
      if (!quarterOptions.some((option) => option.value === state.debtFinancingLedgerQuarter)) {
        state.debtFinancingLedgerQuarter = "latest";
      }
      el.debtFinancingLedgerQuarterSelect.innerHTML = quarterOptions.map((option) => (
        `<option value="${escapeHtml(option.value)}">${escapeHtml(option.label)}</option>`
      )).join("");
      el.debtFinancingLedgerQuarterSelect.value = state.debtFinancingLedgerQuarter;
    }

    function debtFinancingLedgerSelection() {
      const year = selectedDebtFinancingLedgerYear();
      if (!year) return { quarters: [], label: "当前季度", isOverview: false, pointQuarter: null };
      const yearQuarters = debtFinancingLedgerAvailableQuarters()
        .filter((quarter) => Number(quarter.year) === Number(year))
        .sort((a, b) => Number(a.index) - Number(b.index));
      if (!yearQuarters.length) return { quarters: [], label: `${year}`, isOverview: false, pointQuarter: null };
      if (state.debtFinancingLedgerQuarter === "overview") {
        return {
          quarters: yearQuarters,
          label: `${year} 本年总览`,
          isOverview: true,
          pointQuarter: yearQuarters[yearQuarters.length - 1],
        };
      }
      const requestedQuarterNo = String(state.debtFinancingLedgerQuarter || "").match(/\d+/);
      const selectedQuarter = state.debtFinancingLedgerQuarter === "latest"
        ? yearQuarters[yearQuarters.length - 1]
        : yearQuarters.find((quarter) => quarterNumber(quarter) === Number(requestedQuarterNo?.[0])) || yearQuarters[yearQuarters.length - 1];
      return {
        quarters: selectedQuarter ? [selectedQuarter] : [],
        label: selectedQuarter?.label || `${year}`,
        isOverview: false,
        pointQuarter: selectedQuarter || null,
      };
    }

    function loanHasLedgerActivityInScope(loan, quarters) {
      return quarters.some((quarter) => (
        projectIdsContain(quarter.finance?.loanDrawdownIds, loan.id)
        || projectIdsContain(quarter.finance?.loanPrincipalRepaymentIds, loan.id)
        || projectIdsContain(quarter.finance?.loanActiveIds, loan.id)
        || projectIdsContain(quarter.finance?.loanBlockedIds, loan.id)
      ));
    }

    function loanLedgerStatus(loan, selection, pointQuarter, balance) {
      if (!selection.isOverview) {
        const finance = pointQuarter.finance || {};
        const drawnThisQuarter = projectIdsContain(finance.loanDrawdownIds, loan.id);
        const repaidThisQuarter = projectIdsContain(finance.loanPrincipalRepaymentIds, loan.id);
        return balance > 0
          ? (drawnThisQuarter ? "本季提款" : (repaidThisQuarter ? "本季还本" : "存续"))
          : "已结清";
      }
      const quarters = selection.quarters;
      const drawnInYear = quarters.some((quarter) => projectIdsContain(quarter.finance?.loanDrawdownIds, loan.id));
      const repaidInYear = quarters.some((quarter) => projectIdsContain(quarter.finance?.loanPrincipalRepaymentIds, loan.id));
      const activeInYear = quarters.some((quarter) => projectIdsContain(quarter.finance?.loanActiveIds, loan.id));
      const blockedInYear = quarters.some((quarter) => projectIdsContain(quarter.finance?.loanBlockedIds, loan.id));
      if (blockedInYear && !drawnInYear && !activeInYear) return "年内被拒";
      if (balance <= 0) return repaidInYear ? "年内结清" : "已结清";
      const statusParts = [];
      if (drawnInYear) statusParts.push("年内提款");
      if (repaidInYear) statusParts.push("年内还本");
      if (activeInYear) statusParts.push("年内存续");
      return statusParts.length ? Array.from(new Set(statusParts)).join(" / ") : "存续";
    }

    function debtFinancingLoans() {
      const products = state.operations?.financingProducts || {};
      const playerLoans = state.playerActions.filter((action) => action?.type === "draw_loan").map((action) => {
        const product = products[action.productId] || {};
        const quarter = state.operations?.allQuarters?.[Number(action.startedAtIndex)] || state.operations?.quarters?.[Number(action.startedAtIndex)] || {};
        return { id: action.id, name: product.label || "玩家融资", type: product.loan_type || "long_term", startYear: Number(quarter.year), startQuarter: quarter.quarter || "Q1", principal: Number(action.principalMillionCny), tenorQuarters: Number(action.tenorQuarters), repaymentStyle: product.repayment_style || "equal_principal", graceQuarters: Number(action.gracePeriodQuarters || 0) };
      });
      return [...DEBT_FINANCING_LOANS, ...playerLoans];
    }

    function loanLedgerRows(selection = debtFinancingLedgerSelection()) {
      const pointQuarter = selection.pointQuarter;
      if (!pointQuarter) return [];
      return debtFinancingLoans().map((loan) => {
        const drawdownQuarter = loanDrawdownQuarter(loan, pointQuarter);
        const visible = selection.isOverview
          ? loanHasLedgerActivityInScope(loan, selection.quarters)
          : Boolean(drawdownQuarter);
        if (!visible || !drawdownQuarter) return null;
        const balance = loanRemainingPrincipal(loan, pointQuarter);
        return {
          ...loan,
          drawdownQuarter,
          balance,
          status: loanLedgerStatus(loan, selection, pointQuarter, balance),
          interestRateText: loanInterestRateText(loan, pointQuarter),
        };
      }).filter(Boolean);
    }

    function aggregateDebtFinancingPeriod(quarters) {
      const sum = (getter) => quarters.reduce((total, quarter) => total + (Number(getter(quarter)) || 0), 0);
      const last = (getter) => {
        if (!quarters.length) return 0;
        return Number(getter(quarters[quarters.length - 1])) || 0;
      };
      return {
        interestExpense: sum((quarter) => quarter.finance.interestExpense),
        principalRepayment: sum((quarter) => quarter.finance.principalRepayment),
        debtService: sum((quarter) => quarter.finance.debtService),
        loanDrawdown: sum((quarter) => quarter.finance.loanDrawdown),
        financingCashFlow: sum((quarter) => quarter.finance.financingCashFlow),
        grossDebt: last((quarter) => quarter.finance.grossDebt),
        shortTermDebt: last((quarter) => quarter.finance.shortTermDebt),
        longTermDebt: last((quarter) => quarter.finance.longTermDebt),
        netDebt: last((quarter) => quarter.finance.netDebt),
      };
    }

    function debtFinancingPeriodsAll(scope = state.debtFinancingReportScope) {
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
        const aggregate = aggregateDebtFinancingPeriod(periodQuarters);
        const endQuarter = periodQuarters[periodQuarters.length - 1];
        rows.push({
          ...aggregate,
          index: endQuarter.index,
          year,
          quarter: financialPeriodLabel("", endQuarterNo, scope).trim(),
          label: financialPeriodLabel(year, endQuarterNo, scope),
          scope: financialScopeLabel(scope),
          endQuarterNo,
        });
      }
      return rows;
    }

    function debtFinancingVisiblePeriods(rows) {
      if (!rows.length) return [];
      const maxStart = Math.max(0, rows.length - DEBT_FINANCING_WINDOW_SIZE);
      if (state.debtFinancingWindowPinnedToLatest || state.debtFinancingWindowStart == null) {
        state.debtFinancingWindowStart = maxStart;
      }
      state.debtFinancingWindowStart = Math.max(0, Math.min(maxStart, Number(state.debtFinancingWindowStart) || 0));
      return rows.slice(state.debtFinancingWindowStart, state.debtFinancingWindowStart + DEBT_FINANCING_WINDOW_SIZE);
    }

    function setDebtFinancingControlMode(mode) {
      el.debtFinancingScopeControl.hidden = mode !== "scope";
      el.debtFinancingLedgerYearControl.hidden = mode !== "ledger";
      el.debtFinancingLedgerQuarterControl.hidden = mode !== "ledger";
      el.debtFinancingEventStartYearControl.hidden = mode !== "events";
      el.debtFinancingEventStartQuarterControl.hidden = mode !== "events";
      el.debtFinancingEventEndYearControl.hidden = mode !== "events";
      el.debtFinancingEventEndQuarterControl.hidden = mode !== "events";
    }

    function debtFinancingEventAvailableQuarters() {
      return debtFinancingLedgerAvailableQuarters();
    }

    function debtFinancingEventYears() {
      return Array.from(new Set(debtFinancingEventAvailableQuarters().map((quarter) => Number(quarter.year))))
        .filter((year) => Number.isFinite(year))
        .sort((a, b) => a - b);
    }

    function selectedDebtFinancingEventYear(kind) {
      const years = debtFinancingEventYears();
      if (!years.length) return null;
      const stateKey = kind === "start" ? "debtFinancingEventStartYear" : "debtFinancingEventEndYear";
      const defaultValue = kind === "start" ? "earliest" : "latest";
      const edgeYear = kind === "start" ? years[0] : years[years.length - 1];
      const value = state[stateKey];
      if (value === defaultValue) return edgeYear;
      const requested = Number(value);
      if (years.includes(requested)) return requested;
      state[stateKey] = defaultValue;
      return edgeYear;
    }

    function debtFinancingEventQuarterOptions(year, kind) {
      const yearQuarters = debtFinancingEventAvailableQuarters()
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

    function setDebtFinancingEventPeriodOptions() {
      const years = debtFinancingEventYears();
      if (!years.length) {
        el.debtFinancingEventStartYearSelect.innerHTML = `<option value="earliest">最早</option>`;
        el.debtFinancingEventStartQuarterSelect.innerHTML = `<option value="q1">Q1</option>`;
        el.debtFinancingEventEndYearSelect.innerHTML = `<option value="latest">最新</option>`;
        el.debtFinancingEventEndQuarterSelect.innerHTML = `<option value="latest">最新季度</option>`;
        state.debtFinancingEventStartYear = "earliest";
        state.debtFinancingEventStartQuarter = "q1";
        state.debtFinancingEventEndYear = "latest";
        state.debtFinancingEventEndQuarter = "latest";
        return;
      }
      const startYearAllowed = state.debtFinancingEventStartYear === "earliest"
        || years.includes(Number(state.debtFinancingEventStartYear));
      const endYearAllowed = state.debtFinancingEventEndYear === "latest"
        || years.includes(Number(state.debtFinancingEventEndYear));
      if (!startYearAllowed) state.debtFinancingEventStartYear = "earliest";
      if (!endYearAllowed) state.debtFinancingEventEndYear = "latest";
      el.debtFinancingEventStartYearSelect.innerHTML = [
        `<option value="earliest">最早</option>`,
        ...years.map((year) => `<option value="${year}">${year}</option>`),
      ].join("");
      el.debtFinancingEventEndYearSelect.innerHTML = [
        `<option value="latest">最新</option>`,
        ...years.map((year) => `<option value="${year}">${year}</option>`),
      ].join("");
      el.debtFinancingEventStartYearSelect.value = state.debtFinancingEventStartYear;
      el.debtFinancingEventEndYearSelect.value = state.debtFinancingEventEndYear;

      const startYear = selectedDebtFinancingEventYear("start");
      const endYear = selectedDebtFinancingEventYear("end");
      const startQuarterOptions = debtFinancingEventQuarterOptions(startYear, "start");
      const endQuarterOptions = debtFinancingEventQuarterOptions(endYear, "end");
      if (!startQuarterOptions.some((option) => option.value === state.debtFinancingEventStartQuarter)) {
        state.debtFinancingEventStartQuarter = startQuarterOptions[0]?.value || "q1";
      }
      if (!endQuarterOptions.some((option) => option.value === state.debtFinancingEventEndQuarter)) {
        state.debtFinancingEventEndQuarter = "latest";
      }
      el.debtFinancingEventStartQuarterSelect.innerHTML = startQuarterOptions.map((option) => (
        `<option value="${escapeHtml(option.value)}">${escapeHtml(option.label)}</option>`
      )).join("");
      el.debtFinancingEventEndQuarterSelect.innerHTML = endQuarterOptions.map((option) => (
        `<option value="${escapeHtml(option.value)}">${escapeHtml(option.label)}</option>`
      )).join("");
      el.debtFinancingEventStartQuarterSelect.value = state.debtFinancingEventStartQuarter;
      el.debtFinancingEventEndQuarterSelect.value = state.debtFinancingEventEndQuarter;
    }

    function selectedDebtFinancingEventQuarter(kind, year) {
      const quarters = debtFinancingEventAvailableQuarters()
        .filter((quarter) => Number(quarter.year) === Number(year))
        .sort((a, b) => Number(a.index) - Number(b.index));
      if (!quarters.length) return null;
      const stateKey = kind === "start" ? "debtFinancingEventStartQuarter" : "debtFinancingEventEndQuarter";
      if (kind === "end" && state[stateKey] === "latest") return quarters[quarters.length - 1];
      const requestedQuarterNo = Number(String(state[stateKey] || "").match(/\d+/)?.[0]);
      return quarters.find((quarter) => quarterNumber(quarter) === requestedQuarterNo)
        || (kind === "start" ? quarters[0] : quarters[quarters.length - 1]);
    }

    function debtFinancingEventSelection() {
      const startYear = selectedDebtFinancingEventYear("start");
      const endYear = selectedDebtFinancingEventYear("end");
      const startQuarter = selectedDebtFinancingEventQuarter("start", startYear);
      let endQuarter = selectedDebtFinancingEventQuarter("end", endYear);
      if (!startQuarter || !endQuarter) {
        return { quarters: [], label: "融资事件", startQuarter: null, endQuarter: null };
      }
      if (Number(startQuarter.index) > Number(endQuarter.index)) {
        endQuarter = startQuarter;
        state.debtFinancingEventEndYear = String(startQuarter.year);
        state.debtFinancingEventEndQuarter = `q${quarterNumber(startQuarter)}`;
      }
      const quarters = debtFinancingEventAvailableQuarters().filter((quarter) => (
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

    function debtFinancingLoanById(id) {
      return debtFinancingLoans().find((loan) => loan.id === id) || null;
    }

    function loanInterestRatePctValue(loan, quarter) {
      const drawdownQuarter = loanDrawdownQuarter(loan, quarter);
      if (!drawdownQuarter) return null;
      const drawdownIds = splitProjectIds(drawdownQuarter.finance?.loanDrawdownIds);
      if (drawdownIds.length === 1 && drawdownIds[0] === loan.id) {
        const value = Number(drawdownQuarter.finance?.loanDrawdownWeightedInterestRatePct);
        return Number.isFinite(value) ? value : null;
      }
      const currentActiveIds = splitProjectIds(quarter.finance?.loanActiveIds);
      if (currentActiveIds.length === 1 && currentActiveIds[0] === loan.id) {
        const value = Number(quarter.finance?.loanWeightedInterestRatePct);
        return Number.isFinite(value) ? value : null;
      }
      return null;
    }

    function loanPeriodPrincipalRepayment(loan, quarter) {
      const drawdownQuarter = loanDrawdownQuarter(loan, quarter);
      if (!drawdownQuarter) return 0;
      const currentPeriod = periodIndexFromYearQuarter(quarter.year, quarter.quarter);
      const start = loanStartIndex(loan);
      const tenor = Math.max(1, Number(loan.tenorQuarters) || 1);
      const principal = Math.max(0, Number(loan.principal) || 0);
      const elapsedTarget = currentPeriod - start;
      if (elapsedTarget < 0 || elapsedTarget >= tenor) return 0;
      let balance = principal;
      for (let elapsed = 0; elapsed <= elapsedTarget; elapsed += 1) {
        if (balance <= 0) return 0;
        let periodPrincipal = 0;
        if (loan.repaymentStyle === "bullet_principal") {
          periodPrincipal = elapsed === tenor - 1 ? balance : 0;
        } else if (loan.repaymentStyle === "grace_then_equal_principal") {
          const grace = Math.min(Math.max(0, Number(loan.graceQuarters) || 0), Math.max(0, tenor - 1));
          const repaymentPeriods = Math.max(1, tenor - grace);
          periodPrincipal = elapsed < grace ? 0 : principal / repaymentPeriods;
          if (elapsed === tenor - 1) periodPrincipal = balance;
        } else {
          periodPrincipal = principal / tenor;
          if (elapsed === tenor - 1) periodPrincipal = balance;
        }
        periodPrincipal = Math.min(balance, Math.max(0, periodPrincipal));
        if (elapsed === elapsedTarget) return periodPrincipal;
        balance = Math.max(0, balance - periodPrincipal);
      }
      return 0;
    }

    function loanInterestEventRows(quarter, activeIds) {
      const finance = quarter.finance || {};
      const totalInterest = Number(finance.interestExpense) || 0;
      if (totalInterest <= 0) return [];
      const loans = activeIds.map((id) => debtFinancingLoanById(id)).filter(Boolean);
      if (!loans.length) {
        return [{
          period: quarter.label,
          event: "付息",
          loanName: "组合贷款",
          amount: totalInterest,
          direction: "现金流出",
          balance: Number(finance.grossDebt) || 0,
          note: "未能识别活跃贷款明细，按组合利息记录",
          quarterIndex: Number(quarter.index),
          eventOrder: 3,
        }];
      }
      if (loans.length === 1) {
        const loan = loans[0];
        return [{
          period: quarter.label,
          event: "付息",
          loanName: loan.name,
          amount: totalInterest,
          direction: "现金流出",
          balance: loanRemainingPrincipal(loan, quarter),
          note: `按锁定利率 ${loanInterestRateText(loan, quarter)} 计息`,
          quarterIndex: Number(quarter.index),
          eventOrder: 3,
        }];
      }
      const weightedLoans = loans.map((loan) => {
        const repayment = loanPeriodPrincipalRepayment(loan, quarter);
        const balanceBeforeRepayment = loanRemainingPrincipal(loan, quarter) + repayment;
        const rate = loanInterestRatePctValue(loan, quarter);
        const proxy = rate == null
          ? balanceBeforeRepayment
          : balanceBeforeRepayment * rate / 100.0 / 4.0;
        return { loan, proxy: Math.max(0, proxy), balance: loanRemainingPrincipal(loan, quarter) };
      });
      const proxyTotal = weightedLoans.reduce((total, item) => total + item.proxy, 0);
      return weightedLoans.map((item) => ({
        period: quarter.label,
        event: "付息",
        loanName: item.loan.name,
        amount: proxyTotal > 0 ? totalInterest * item.proxy / proxyTotal : totalInterest / weightedLoans.length,
        direction: "现金流出",
        balance: item.balance,
        note: `组合利息拆分；锁定利率 ${loanInterestRateText(item.loan, quarter)}`,
        quarterIndex: Number(quarter.index),
        eventOrder: 3,
      }));
    }

    function financingEventRows(selection = debtFinancingEventSelection()) {
      const rows = [];
      selection.quarters.forEach((quarter) => {
        const finance = quarter.finance || {};
        splitProjectIds(finance.loanBlockedIds).forEach((id) => {
          const loan = debtFinancingLoanById(id);
          rows.push({
            period: quarter.label,
            event: "提款被拒",
            loanName: loan?.name || id,
            amount: loan ? Number(loan.principal) || 0 : 0,
            direction: "未发生",
            balance: Number(finance.grossDebt) || 0,
            note: finance.loanBlockedReasons || "贷款未通过风控约束",
            quarterIndex: Number(quarter.index),
            eventOrder: 0,
          });
        });
        splitProjectIds(finance.loanDrawdownIds).forEach((id) => {
          const loan = debtFinancingLoanById(id);
          rows.push({
            period: quarter.label,
            event: "贷款提款",
            loanName: loan?.name || id,
            amount: loan ? Number(loan.principal) || 0 : Number(finance.loanDrawdown) || 0,
            direction: "现金流入",
            balance: loan ? loanRemainingPrincipal(loan, quarter) : Number(finance.grossDebt) || 0,
            note: loan ? `年利率 ${loanInterestRateText(loan, quarter)}；${loanRepaymentStyleLabel(loan.repaymentStyle)}；期限 ${loan.tenorQuarters} 季度` : "-",
            quarterIndex: Number(quarter.index),
            eventOrder: 1,
          });
        });
        splitProjectIds(finance.loanPrincipalRepaymentIds).forEach((id) => {
          const loan = debtFinancingLoanById(id);
          const amount = loan ? loanPeriodPrincipalRepayment(loan, quarter) : Number(finance.principalRepayment) || 0;
          rows.push({
            period: quarter.label,
            event: loan?.repaymentStyle === "bullet_principal" ? "到期还本" : "本金偿还",
            loanName: loan?.name || id,
            amount,
            direction: "现金流出",
            balance: loan ? loanRemainingPrincipal(loan, quarter) : Number(finance.grossDebt) || 0,
            note: loan ? loanRepaymentStyleLabel(loan.repaymentStyle) : "-",
            quarterIndex: Number(quarter.index),
            eventOrder: 2,
          });
        });
        rows.push(...loanInterestEventRows(quarter, splitProjectIds(finance.loanActiveIds)));
      });
      return rows
        .filter((row) => Number(row.amount) > 0 || row.event === "提款被拒")
        .sort((a, b) => (b.quarterIndex - a.quarterIndex) || (a.eventOrder - b.eventOrder));
    }

    function renderLoanLedger() {
      setDebtFinancingLedgerPeriodOptions();
      const selection = debtFinancingLedgerSelection();
      const rows = loanLedgerRows(selection);
      el.debtFinancingMetricTitle.textContent = "贷款台账";
      el.debtFinancingMetricCaption.textContent = selection.pointQuarter
        ? `${selection.label}；${selection.isOverview ? "显示年内提款、还本或存续过的贷款" : "显示截至该季度已提款的贷款"}`
        : "加载运营后显示贷款台账";
      setDebtFinancingControlMode("ledger");
      el.debtFinancingChartPanel.hidden = true;
      el.debtFinancingHeaderRow.innerHTML = `
        <th>贷款</th>
        <th>类型</th>
        <th>起始季度</th>
        <th>原始本金</th>
        <th>剩余本金</th>
        <th>利率</th>
        <th>期限</th>
        <th>还款方式</th>
        <th>宽限期</th>
        <th>状态</th>
      `;
      el.debtFinancingMetricRows.innerHTML = rows.length ? rows.map((row) => `
        <tr>
          <td>${escapeHtml(row.name)}</td>
          <td>${escapeHtml(loanTypeLabel(row.type))}</td>
          <td>${escapeHtml(row.drawdownQuarter.label)}</td>
          <td>${fmtMoney(row.principal)}</td>
          <td>${fmtMoney(row.balance)}</td>
          <td>${escapeHtml(row.interestRateText)}</td>
          <td>${escapeHtml(`${row.tenorQuarters} 季度`)}</td>
          <td>${escapeHtml(loanRepaymentStyleLabel(row.repaymentStyle))}</td>
          <td>${row.graceQuarters ? escapeHtml(`${row.graceQuarters} 季度`) : "-"}</td>
          <td>${escapeHtml(row.status)}</td>
        </tr>
      `).join("") : `<tr><td colspan="10" style="text-align:center;color:var(--muted)">暂无已发生贷款</td></tr>`;
    }

    function renderDebtService() {
      const allRows = debtFinancingPeriodsAll();
      const rows = debtFinancingVisiblePeriods(allRows);
      const maxStart = Math.max(0, allRows.length - DEBT_FINANCING_WINDOW_SIZE);
      el.debtFinancingMetricTitle.textContent = "还本付息";
      setDebtFinancingControlMode("scope");
      el.debtFinancingScopeSelect.value = state.debtFinancingReportScope;
      el.debtFinancingChartPanel.hidden = false;
      el.debtFinancingHeaderRow.innerHTML = `
        <th>期间</th>
        <th>利息费用</th>
        <th>本金偿还</th>
        <th>债务服务</th>
        <th>贷款提款</th>
        <th>期末债务</th>
        <th>净债务</th>
      `;
      el.debtFinancingRangeInput.min = "0";
      el.debtFinancingRangeInput.max = String(maxStart);
      el.debtFinancingRangeInput.value = String(state.debtFinancingWindowStart || 0);
      el.debtFinancingRangeInput.disabled = maxStart === 0;
      el.debtFinancingTicks.style.gridTemplateColumns = allRows.length
        ? `repeat(${Math.min(allRows.length, DEBT_FINANCING_WINDOW_SIZE)}, minmax(0, 1fr))`
        : "1fr";
      el.debtFinancingTicks.innerHTML = rows.map((row) => `<span class="financial-tick">${escapeHtml(row.year)}</span>`).join("");
      if (!state.operations || !allRows.length || !rows.length) {
        el.debtFinancingMetricCaption.textContent = "加载运营后显示还本付息。";
        el.debtFinancingMetricChart.innerHTML = `<div class="empty">暂无数据</div>`;
        el.debtFinancingMetricRows.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--muted)">暂无数据</td></tr>`;
        el.debtFinancingWindowLabel.textContent = "年度轴";
        el.debtFinancingWindowHint.textContent = "暂无历史";
        return;
      }
      const first = rows[0];
      const last = rows[rows.length - 1];
      const scopeLabel = financialScopeLabel(state.debtFinancingReportScope);
      el.debtFinancingMetricCaption.textContent = `${first.label} - ${last.label}；${scopeLabel}；柱：利息/还本 / 线：期末债务`;
      el.debtFinancingWindowLabel.textContent = `${first.label} - ${last.label}`;
      el.debtFinancingWindowHint.textContent = maxStart > 0 ? "拖动查看历史年份" : "当前口径历史已全部显示";
      const styles = getComputedStyle(document.documentElement);
      renderComboChart(el.debtFinancingMetricChart, rows, {
        title: "还本付息",
        leftFormat: fmtMoney,
        rightPad: 76,
        stackedBars: [
          { label: "利息费用", color: styles.getPropertyValue("--amber").trim() || "#f7b84b", value: (row) => row.interestExpense, format: fmtMoney },
          { label: "本金偿还", color: styles.getPropertyValue("--red").trim() || "#fb7185", value: (row) => row.principalRepayment, format: fmtMoney },
          { label: "贷款提款", color: styles.getPropertyValue("--green").trim() || "#35d392", value: (row) => row.loanDrawdown, format: fmtMoney },
        ],
        line: {
          label: "期末债务",
          color: styles.getPropertyValue("--blue").trim() || "#62a8ff",
          value: (row) => row.grossDebt,
          format: fmtMoney,
        },
      });
      el.debtFinancingMetricRows.innerHTML = rows.slice().reverse().map((row) => `
        <tr>
          <td>${escapeHtml(row.label)}</td>
          <td>${fmtMoney(row.interestExpense)}</td>
          <td>${fmtMoney(row.principalRepayment)}</td>
          <td>${fmtMoney(row.debtService)}</td>
          <td>${fmtMoney(row.loanDrawdown)}</td>
          <td>${fmtMoney(row.grossDebt)}</td>
          <td>${fmtMoney(row.netDebt)}</td>
        </tr>
      `).join("");
    }

    function renderFinancingEvents() {
      setDebtFinancingEventPeriodOptions();
      const selection = debtFinancingEventSelection();
      setDebtFinancingEventPeriodOptions();
      const rows = financingEventRows(selection);
      el.debtFinancingMetricTitle.textContent = "融资事件";
      el.debtFinancingMetricCaption.textContent = selection.startQuarter
        ? `${selection.label}；一项融资动作单独一行`
        : "加载运营后显示融资事件";
      setDebtFinancingControlMode("events");
      el.debtFinancingChartPanel.hidden = true;
      el.debtFinancingHeaderRow.innerHTML = `
        <th>期间</th>
        <th>事件</th>
        <th>贷款</th>
        <th>金额</th>
        <th>方向</th>
        <th>期末剩余本金</th>
        <th>说明</th>
      `;
      el.debtFinancingMetricRows.innerHTML = rows.length ? rows.map((row) => `
        <tr>
          <td>${escapeHtml(row.period)}</td>
          <td>${escapeHtml(row.event)}</td>
          <td>${escapeHtml(row.loanName)}</td>
          <td>${fmtMoney(row.amount)}</td>
          <td>${escapeHtml(row.direction)}</td>
          <td>${fmtMoney(row.balance)}</td>
          <td>${escapeHtml(row.note)}</td>
        </tr>
      `).join("") : `<tr><td colspan="7" style="text-align:center;color:var(--muted)">暂无融资事件</td></tr>`;
    }

    function renderDebtFinancingAnalysis() {
      el.debtFinancingMetricButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-debt-financing-metric") === state.debtFinancingMetric));
      });
      if (state.debtFinancingMetric === "debtService") {
        renderDebtService();
      } else if (state.debtFinancingMetric === "financingEvents") {
        renderFinancingEvents();
      } else {
        renderLoanLedger();
      }
    }
