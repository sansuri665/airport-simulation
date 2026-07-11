    function reportRow(label, value) {
      return `<div class="report-row"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
    }

    function reportBlock(title, rows) {
      return `<section class="report-block"><h3>${escapeHtml(title)}</h3>${rows.join("")}</section>`;
    }

    function pills(values, kind = "") {
      if (!values.length) return `<span class="pill">无</span>`;
      return values.map((value) => `<span class="pill ${kind}">${escapeHtml(value)}</span>`).join("");
    }

    function operationWindow() {
      if (!state.operations) return [];
      const currentIndex = state.operationsQuarterIndex ?? state.operations.playerStartIndex ?? 0;
      const startIndex = Math.max(state.operations.playerStartIndex ?? 0, currentIndex - 7);
      return state.operations.quarters.slice(startIndex, currentIndex + 1);
    }

    function quarterNumber(quarter) {
      const raw = String(quarter?.quarter || "");
      const match = raw.match(/\d+/);
      return Number(match ? match[0] : 0);
    }

    function sumNetProfit(quarters) {
      return quarters.reduce((total, quarter) => total + (Number(quarter.finance.accountingProfit) || 0), 0);
    }

    function financialMetricConfig(metric = state.financialMetric) {
      const sum = (quarters, getter) => quarters.reduce((total, quarter) => total + (Number(getter(quarter)) || 0), 0);
      const last = (quarters, getter) => {
        if (!quarters.length) return 0;
        return Number(getter(quarters[quarters.length - 1])) || 0;
      };
      const revenue = (quarters) => sum(quarters, (quarter) => quarter.operations.totalRevenue);
      const ratio = (numerator, denominator) => (denominator ? (numerator / denominator) * 100 : 0);
      const absoluteMoneyGrowth = {
        growthFormat: fmtMoney,
        growthLabel: "同比变化",
        growthMode: "absoluteChange",
        rightPad: 76,
      };
      const pointPctGrowth = {
        growthFormat: fmtPctPoint,
        growthLabel: "同比变化",
        growthMode: "pointChange",
      };
      const configs = {
        netProfit: {
          label: "净利润",
          value: (quarters) => sum(quarters, (quarter) => quarter.finance.accountingProfit),
          valueFormat: fmtMoney,
          leftFormat: fmtMoney,
          growthFormat: fmtPct,
          growthLabel: "同比增幅",
          growthMode: "percentChange",
        },
        totalRevenue: {
          label: "营业总收入",
          value: (quarters) => sum(quarters, (quarter) => quarter.operations.totalRevenue),
          valueFormat: fmtMoney,
          leftFormat: fmtMoney,
          growthFormat: fmtPct,
          growthLabel: "同比增幅",
          growthMode: "percentChange",
        },
        operatingProfit: {
          label: "经营利润",
          value: (quarters) => sum(quarters, (quarter) => quarter.operations.operatingProfit),
          valueFormat: fmtMoney,
          leftFormat: fmtMoney,
          growthFormat: fmtPct,
          growthLabel: "同比增幅",
          growthMode: "percentChange",
        },
        netMargin: {
          label: "净利率",
          value: (quarters) => ratio(sum(quarters, (quarter) => quarter.finance.accountingProfit), revenue(quarters)),
          valueFormat: fmtPct,
          leftFormat: fmtPct,
          ...pointPctGrowth,
        },
        operatingMargin: {
          label: "经营利润率",
          value: (quarters) => ratio(sum(quarters, (quarter) => quarter.operations.operatingProfit), revenue(quarters)),
          valueFormat: fmtPct,
          leftFormat: fmtPct,
          ...pointPctGrowth,
        },
        pretaxProfit: {
          label: "税前利润",
          value: (quarters) => sum(quarters, (quarter) => quarter.finance.pretaxProfit),
          valueFormat: fmtMoney,
          leftFormat: fmtMoney,
          growthFormat: fmtPct,
          growthLabel: "同比增幅",
          growthMode: "percentChange",
        },
        depreciation: {
          label: "折旧",
          value: (quarters) => sum(quarters, (quarter) => quarter.finance.accountingDepreciation),
          valueFormat: fmtMoney,
          leftFormat: fmtMoney,
          growthFormat: fmtPct,
          growthLabel: "同比增幅",
          growthMode: "percentChange",
        },
        incomeTaxExpense: {
          label: "所得税费用",
          value: (quarters) => sum(quarters, (quarter) => quarter.finance.incomeTaxExpense ?? quarter.finance.cashTaxPaid),
          valueFormat: fmtMoney,
          leftFormat: fmtMoney,
          ...absoluteMoneyGrowth,
        },
        endCash: {
          label: "期末现金",
          value: (quarters) => last(quarters, (quarter) => quarter.finance.endCash),
          valueFormat: fmtMoney,
          leftFormat: fmtMoney,
          ...absoluteMoneyGrowth,
        },
        netDebt: {
          label: "净债务",
          value: (quarters) => last(quarters, (quarter) => quarter.finance.netDebt ?? ((Number(quarter.finance.totalLiabilities) || 0) - (Number(quarter.finance.endCash) || 0))),
          valueFormat: fmtMoney,
          leftFormat: fmtMoney,
          ...absoluteMoneyGrowth,
        },
        totalAssets: {
          label: "总资产",
          value: (quarters) => last(quarters, (quarter) => quarter.finance.totalAssets),
          valueFormat: fmtMoney,
          leftFormat: fmtMoney,
          ...absoluteMoneyGrowth,
        },
        netAssets: {
          label: "净资产",
          value: (quarters) => last(quarters, (quarter) => quarter.finance.totalEquity),
          valueFormat: fmtMoney,
          leftFormat: fmtMoney,
          ...absoluteMoneyGrowth,
        },
        interestExpense: {
          label: "利息费用",
          value: (quarters) => sum(quarters, (quarter) => quarter.finance.interestExpense),
          valueFormat: fmtMoney,
          leftFormat: fmtMoney,
          ...absoluteMoneyGrowth,
        },
        debtService: {
          label: "债务服务",
          value: (quarters) => sum(quarters, (quarter) => quarter.finance.debtService),
          valueFormat: fmtMoney,
          leftFormat: fmtMoney,
          ...absoluteMoneyGrowth,
        },
        liabilityRatio: {
          label: "资产负债率",
          value: (quarters) => last(quarters, (quarter) => quarter.finance.liabilityRatioPct),
          valueFormat: fmtPct,
          leftFormat: fmtPct,
          ...pointPctGrowth,
        },
        capexOutlay: {
          label: "资本开支",
          value: (quarters) => sum(quarters, (quarter) => quarter.finance.capexOutlay),
          valueFormat: fmtMoney,
          leftFormat: fmtMoney,
          ...absoluteMoneyGrowth,
        },
        freeCashFlow: {
          label: "自由现金流",
          value: (quarters) => sum(quarters, (quarter) => quarter.finance.freeCashFlowBeforeFinancing),
          valueFormat: fmtMoney,
          leftFormat: fmtMoney,
          ...absoluteMoneyGrowth,
        },
        roe: {
          label: "ROE",
          value: (quarters) => ratio(
            sum(quarters, (quarter) => quarter.finance.accountingProfit),
            last(quarters, (quarter) => quarter.finance.totalEquity),
          ),
          valueFormat: fmtPct,
          leftFormat: fmtPct,
          ...pointPctGrowth,
        },
        roa: {
          label: "ROA",
          value: (quarters) => ratio(
            sum(quarters, (quarter) => quarter.finance.accountingProfit),
            last(quarters, (quarter) => quarter.finance.totalAssets),
          ),
          valueFormat: fmtPct,
          leftFormat: fmtPct,
          ...pointPctGrowth,
        },
      };
      return configs[metric] || configs.netProfit;
    }

    function sumFinancialMetric(quarters, metric = state.financialMetric) {
      const config = financialMetricConfig(metric);
      return Number(config.value(quarters)) || 0;
    }

    function financialGrowth(currentValue, previousValue, config) {
      if (config.growthMode === "pointChange" || config.growthMode === "absoluteChange") return currentValue - previousValue;
      return previousValue !== 0 ? ((currentValue - previousValue) / Math.abs(previousValue)) * 100 : 0;
    }

    function financialScopeLabel(scope) {
      return {
        latest: "最新",
        annual: "年报",
        half: "半年报",
        q1: "一季报",
        q3: "三季报",
        current: "当前季度",
        year: "本年总览",
      }[scope] || "最新";
    }

    function financialScopeQuarterNo(scope, currentQuarterNo) {
      if (scope === "annual") return 4;
      if (scope === "half") return 2;
      if (scope === "q1") return 1;
      if (scope === "q3") return 3;
      return currentQuarterNo || 4;
    }

    function financialPeriodLabel(year, quarterNo, scope) {
      if (quarterNo === 4) return `${year} 年报`;
      if (scope === "half" || quarterNo === 2) return `${year} 半年报`;
      if (scope === "q1" || quarterNo === 1) return `${year} 一季报`;
      if (scope === "q3" || quarterNo === 3) return `${year} 三季报`;
      return `${year} Q${quarterNo}累计`;
    }

    function netProfitPeriodsAll(scope = state.financialReportScope, metric = state.financialMetric) {
      if (!state.operations || !state.operations.quarters.length) return [];
      const metricConfig = financialMetricConfig(metric);
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
        const metricValue = sumFinancialMetric(periodQuarters, metric);
        const previousMetricValue = sumFinancialMetric(previousQuarters, metric);
        const yoyPct = previousQuarters.length ? financialGrowth(metricValue, previousMetricValue, metricConfig) : 0;
        const endQuarter = periodQuarters[periodQuarters.length - 1];
        const periodLabel = financialPeriodLabel(year, endQuarterNo, scope);
        rows.push({
          index: endQuarter.index,
          year,
          quarter: financialPeriodLabel("", endQuarterNo, scope).trim(),
          label: periodLabel,
          scope: financialScopeLabel(scope),
          endQuarterNo,
          value: metricValue,
          previousValue: previousMetricValue,
          netProfit: metricValue,
          previousNetProfit: previousMetricValue,
          yoyPct,
        });
      }
      return rows;
    }

    function netProfitVisiblePeriods(rows) {
      if (!rows.length) return [];
      const maxStart = Math.max(0, rows.length - NET_PROFIT_WINDOW_SIZE);
      if (state.netProfitWindowPinnedToLatest || state.netProfitWindowStart == null) {
        state.netProfitWindowStart = maxStart;
      }
      state.netProfitWindowStart = Math.max(0, Math.min(maxStart, Number(state.netProfitWindowStart) || 0));
      return rows.slice(state.netProfitWindowStart, state.netProfitWindowStart + NET_PROFIT_WINDOW_SIZE);
    }

    function metricRange(rows, series) {
      const values = rows.flatMap((quarter) => series.map((item) => Number(item.value(quarter)) || 0));
      const rawMin = Math.min(0, ...values);
      const rawMax = Math.max(1, ...values);
      const span = Math.max(1, rawMax - rawMin);
      return {
        min: rawMin < 0 ? rawMin - span * 0.12 : 0,
        max: rawMax + span * 0.12,
      };
    }

    function stackedMetricRange(rows, series) {
      const values = rows.flatMap((quarter) => {
        let positive = 0;
        let negative = 0;
        series.forEach((item) => {
          const raw = Number(item.value(quarter)) || 0;
          if (raw >= 0) positive += raw;
          else negative += raw;
        });
        return [positive, negative];
      });
      const rawMin = Math.min(0, ...values);
      const rawMax = Math.max(1, ...values);
      const span = Math.max(1, rawMax - rawMin);
      return {
        min: rawMin < 0 ? rawMin - span * 0.12 : 0,
        max: rawMax + span * 0.12,
      };
    }

    function lineRange(rows, line) {
      const values = rows.map((quarter) => Number(line.value(quarter)) || 0);
      const min = Math.min(0, ...values);
      const max = Math.max(1, ...values);
      return { min, max: max === min ? max + 1 : max };
    }

    function renderComboChart(container, rows, config) {
      if (!rows.length) {
        container.innerHTML = `<div class="empty">暂无数据</div>`;
        return;
      }
      const styles = getComputedStyle(document.documentElement);
      const gridColor = styles.getPropertyValue("--grid").trim() || "#202838";
      const muted = styles.getPropertyValue("--muted").trim() || "#91a0b5";
      const width = 420;
      const height = 230;
      const pad = { left: 44, right: config.rightPad || 38, top: 18, bottom: 42 };
      const plotWidth = width - pad.left - pad.right;
      const plotHeight = height - pad.top - pad.bottom;
      const stacked = Boolean(config.stackedBars);
      const barSeries = config.stackedBars || config.bars;
      const groupWidth = plotWidth / rows.length;
      const innerGap = 2;
      const barWidth = stacked
        ? Math.max(8, Math.min(22, groupWidth - 16))
        : Math.max(4, Math.min(16, (groupWidth - 12) / barSeries.length - innerGap));
      const leftRange = stacked ? stackedMetricRange(rows, barSeries) : metricRange(rows, barSeries);
      const line = config.line;
      const rightRange = line ? lineRange(rows, line) : { min: 0, max: 1 };
      const xCenter = (index) => pad.left + groupWidth * index + groupWidth / 2;
      const yLeft = (value) => {
        const unit = (value - leftRange.min) / Math.max(1, leftRange.max - leftRange.min);
        return pad.top + plotHeight - unit * plotHeight;
      };
      const yRight = (value) => {
        const unit = (value - rightRange.min) / Math.max(1, rightRange.max - rightRange.min);
        return pad.top + plotHeight - unit * plotHeight;
      };
      const zeroY = yLeft(0);
      const yTicks = leftRange.min < 0
        ? [leftRange.min, 0, leftRange.max]
        : [0, leftRange.max / 2, leftRange.max];
      const grid = yTicks.map((value) => `
        <line x1="${pad.left}" y1="${yLeft(value)}" x2="${width - pad.right}" y2="${yLeft(value)}" stroke="${gridColor}"/>
        <text x="${pad.left - 8}" y="${yLeft(value) + 4}" text-anchor="end" font-size="10" fill="${muted}">${config.leftFormat(value)}</text>
      `).join("");
      const rightLabels = line ? [rightRange.min, (rightRange.min + rightRange.max) / 2, rightRange.max].map((value) => `
        <text x="${width - pad.right + 8}" y="${yRight(value) + 4}" text-anchor="start" font-size="10" fill="${muted}">${line.format(value)}</text>
      `).join("") : "";
      const bars = stacked ? rows.map((quarter, rowIndex) => {
        let positiveBase = 0;
        let negativeBase = 0;
        const x = xCenter(rowIndex) - barWidth / 2;
        const selected = quarter.index === state.operationsQuarterIndex;
        return barSeries.map((item) => {
          const raw = Number(item.value(quarter)) || 0;
          if (raw === 0) return "";
          const base = raw >= 0 ? positiveBase : negativeBase;
          const next = base + raw;
          if (raw >= 0) positiveBase = next;
          else negativeBase = next;
          const y = raw >= 0 ? yLeft(next) : yLeft(base);
          const barHeight = Math.abs(yLeft(base) - yLeft(next));
          return `
            <rect x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" rx="2" fill="${item.color}" opacity="${selected ? 1 : 0.74}"/>
          `;
        }).join("");
      }).join("") : rows.map((quarter, rowIndex) => {
        const totalBarsWidth = barSeries.length * barWidth + (barSeries.length - 1) * innerGap;
        const startX = xCenter(rowIndex) - totalBarsWidth / 2;
        return barSeries.map((item, seriesIndex) => {
          const raw = Number(item.value(quarter)) || 0;
          const barHeight = Math.abs(yLeft(raw) - zeroY);
          const x = startX + seriesIndex * (barWidth + innerGap);
          const y = raw >= 0 ? yLeft(raw) : zeroY;
          const selected = quarter.index === state.operationsQuarterIndex;
          return `
            <rect x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" rx="3" fill="${item.color}" opacity="${selected ? 1 : 0.72}"/>
          `;
        }).join("");
      }).join("");
      const linePath = line ? rows.map((quarter, index) => {
        const command = index ? "L" : "M";
        return `${command} ${xCenter(index).toFixed(2)} ${yRight(Number(line.value(quarter)) || 0).toFixed(2)}`;
      }).join(" ") : "";
      const lineNodes = line ? `
        <path d="${linePath}" fill="none" stroke="${line.color}" stroke-width="2.4"/>
        ${rows.map((quarter, index) => {
          const selected = quarter.index === state.operationsQuarterIndex;
          return `<circle cx="${xCenter(index)}" cy="${yRight(Number(line.value(quarter)) || 0)}" r="${selected ? 4 : 3}" fill="${line.color}"/>`;
        }).join("")}
      ` : "";
      const xLabels = rows.map((quarter, index) => `
        <text x="${xCenter(index)}" y="${height - 20}" text-anchor="middle" font-size="10" fill="${muted}">${quarter.year}</text>
        <text x="${xCenter(index)}" y="${height - 7}" text-anchor="middle" font-size="10" fill="${muted}">${quarter.quarter}</text>
      `).join("");
      const hitZones = rows.map((quarter, index) => `
        <rect class="chart-hit" data-quarter-index="${quarter.index}" x="${pad.left + groupWidth * index}" y="${pad.top}" width="${groupWidth}" height="${plotHeight}" fill="transparent">
          <title>${escapeHtml([
            quarter.label,
            ...barSeries.map((item) => `${item.label}: ${(item.format || config.leftFormat)(Number(item.value(quarter)) || 0)}`),
            ...(line ? [`${line.label}: ${line.format(Number(line.value(quarter)) || 0)}`] : []),
          ].join("\n"))}</title>
        </rect>
      `).join("");
      const legend = [
        ...barSeries.map((item) => `<span><i class="swatch" style="background:${item.color}"></i>${escapeHtml(item.label)}</span>`),
        ...(line ? [`<span><i class="swatch" style="background:${line.color}"></i>${escapeHtml(line.label)}</span>`] : []),
      ].join("");
      container.innerHTML = `
        <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(config.title)}">
          <rect x="0" y="0" width="${width}" height="${height}" fill="#070b10"/>
          ${grid}
          ${rightLabels}
          <line x1="${pad.left}" y1="${zeroY}" x2="${width - pad.right}" y2="${zeroY}" stroke="#465366"/>
          ${bars}
          ${lineNodes}
          ${xLabels}
          ${hitZones}
        </svg>
        <div class="legend">${legend}</div>
      `;
    }

    function aggregateTrafficPeriod(quarters) {
      const sum = (getter) => quarters.reduce((total, quarter) => total + (Number(getter(quarter)) || 0), 0);
      const potential = sum((quarter) => quarter.demand.quarterPotential);
      const airlineSupply = sum((quarter) => quarter.demand.quarterAirlineSupply);
      const effectiveDemand = Math.min(potential, airlineSupply);
      const served = sum((quarter) => quarter.demand.quarterServed);
      const componentServed = {
        business: sum((quarter) => quarter.demand.componentServed?.business),
        leisure: sum((quarter) => quarter.demand.componentServed?.leisure),
        vfr: sum((quarter) => quarter.demand.componentServed?.vfr),
        longHaul: sum((quarter) => quarter.demand.componentServed?.longHaul),
        transfer: sum((quarter) => quarter.demand.componentServed?.transfer),
      };
      const designCapacity = sum((quarter) => quarter.capacity.quarterDesignCapacity);
      const maxCapacity = sum((quarter) => quarter.capacity.quarterMaxCapacity);
      const capacityLoss = sum((quarter) => quarter.demand.capacityLost);
      return {
        potential,
        airlineSupply,
        effectiveDemand,
        served,
        componentServed,
        designCapacity,
        maxCapacity,
        capacityLoss,
        airlineGap: Math.max(0, potential - airlineSupply),
        unmetPotential: Math.max(0, potential - served),
        servedPotentialPct: potential ? served / potential * 100 : 0,
        designUtilizationPct: designCapacity ? served / designCapacity * 100 : 0,
        maxUtilizationPct: maxCapacity ? served / maxCapacity * 100 : 0,
      };
    }

    function trafficCapacityMetricConfig(section = state.opsBreakdownSection) {
      const styles = getComputedStyle(document.documentElement);
      const colors = {
        blue: styles.getPropertyValue("--blue").trim() || "#62a8ff",
        green: styles.getPropertyValue("--green").trim() || "#35d392",
        amber: styles.getPropertyValue("--amber").trim() || "#f7b84b",
        red: styles.getPropertyValue("--red").trim() || "#fb7185",
        muted: styles.getPropertyValue("--muted").trim() || "#91a0b5",
        violet: "#a78bfa",
        cyan: "#38bdf8",
      };
      const configs = {
        potentialTraffic: {
          label: "潜在客流",
          caption: "柱：潜在客流 / 线：同比增幅",
          leftFormat: (value) => fmt(value, 0),
          bars: [
            { label: "潜在客流", color: colors.amber, value: (row) => row.potential, format: fmtPassenger },
          ],
          line: {
            label: "同比增幅",
            color: colors.green,
            value: (row) => row.yoyPct,
            format: fmtPct,
          },
          valueText: (row) => fmtPassenger(row.potential),
          growthHeader: "同比增幅",
          growthText: (row) => fmtPct(row.yoyPct),
          metricValue: (aggregate) => aggregate.potential,
        },
        airlineSupply: {
          label: "航司供给",
          caption: "柱：航司供给 / 线：同比增幅",
          leftFormat: (value) => fmt(value, 0),
          bars: [
            { label: "航司供给", color: colors.green, value: (row) => row.airlineSupply, format: fmtPassenger },
          ],
          line: {
            label: "同比增幅",
            color: colors.red,
            value: (row) => row.yoyPct,
            format: fmtPct,
          },
          valueText: (row) => fmtPassenger(row.airlineSupply),
          growthHeader: "同比增幅",
          growthText: (row) => fmtPct(row.yoyPct),
          metricValue: (aggregate) => aggregate.airlineSupply,
        },
        effectiveDemand: {
          label: "有效需求",
          caption: "柱：有效需求 / 线：同比增幅",
          leftFormat: (value) => fmt(value, 0),
          bars: [
            { label: "有效需求", color: colors.amber, value: (row) => row.effectiveDemand, format: fmtPassenger },
          ],
          line: {
            label: "同比增幅",
            color: colors.green,
            value: (row) => row.yoyPct,
            format: fmtPct,
          },
          valueText: (row) => fmtPassenger(row.effectiveDemand),
          growthHeader: "同比增幅",
          growthText: (row) => fmtPct(row.yoyPct),
          metricValue: (aggregate) => aggregate.effectiveDemand,
        },
        servedTraffic: {
          label: "承接客流",
          caption: "柱：承接客流 / 线：同比增幅",
          leftFormat: (value) => fmt(value, 0),
          bars: [
            { label: "承接客流", color: colors.blue, value: (row) => row.served, format: fmtPassenger },
          ],
          line: {
            label: "同比增幅",
            color: colors.green,
            value: (row) => row.yoyPct,
            format: fmtPct,
          },
          valueText: (row) => fmtPassenger(row.served),
          growthHeader: "同比增幅",
          growthText: (row) => fmtPct(row.yoyPct),
          metricValue: (aggregate) => aggregate.served,
        },
        componentServedTraffic: {
          label: "分项承接客流",
          caption: "堆叠柱：商务/休闲/探亲/长航线/中转 / 线：总承接同比",
          leftFormat: (value) => fmt(value, 0),
          rightPad: 76,
          stackedBars: [
            { label: "商务", color: colors.blue, value: (row) => row.componentServed.business, format: fmtPassenger },
            { label: "休闲", color: colors.green, value: (row) => row.componentServed.leisure, format: fmtPassenger },
            { label: "探亲", color: colors.amber, value: (row) => row.componentServed.vfr, format: fmtPassenger },
            { label: "长航线", color: colors.violet, value: (row) => row.componentServed.longHaul, format: fmtPassenger },
            { label: "中转", color: colors.cyan, value: (row) => row.componentServed.transfer, format: fmtPassenger },
          ],
          line: {
            label: "总承接同比",
            color: colors.red,
            value: (row) => row.yoyPct,
            format: fmtPct,
          },
          valueText: (row) => [
            `商 ${fmtPassenger(row.componentServed.business)}`,
            `休 ${fmtPassenger(row.componentServed.leisure)}`,
            `探 ${fmtPassenger(row.componentServed.vfr)}`,
            `长 ${fmtPassenger(row.componentServed.longHaul)}`,
            `中 ${fmtPassenger(row.componentServed.transfer)}`,
          ].join(" / "),
          growthHeader: "总承接同比",
          growthText: (row) => fmtPct(row.yoyPct),
          metricValue: (aggregate) => aggregate.served,
        },
        designCapacity: {
          label: "设计容量",
          caption: "柱：设计容量 / 线：设计利用率",
          leftFormat: (value) => fmt(value, 0),
          bars: [
            { label: "设计容量", color: colors.blue, value: (row) => row.designCapacity, format: fmtPassenger },
          ],
          line: {
            label: "设计利用率",
            color: colors.amber,
            value: (row) => row.designUtilizationPct,
            format: fmtPct,
          },
          valueText: (row) => fmtPassenger(row.designCapacity),
          growthHeader: "设计利用率",
          growthText: (row) => fmtPct(row.designUtilizationPct),
          metricValue: (aggregate) => aggregate.designCapacity,
        },
        maxCapacity: {
          label: "极限容量",
          caption: "柱：极限容量 / 线：极限利用率",
          leftFormat: (value) => fmt(value, 0),
          bars: [
            { label: "极限容量", color: colors.muted, value: (row) => row.maxCapacity, format: fmtPassenger },
          ],
          line: {
            label: "极限利用率",
            color: colors.red,
            value: (row) => row.maxUtilizationPct,
            format: fmtPct,
          },
          valueText: (row) => fmtPassenger(row.maxCapacity),
          growthHeader: "极限利用率",
          growthText: (row) => fmtPct(row.maxUtilizationPct),
          metricValue: (aggregate) => aggregate.maxCapacity,
        },
      };
      return configs[section] || configs.potentialTraffic;
    }

    function trafficCapacityPeriodsAll(scope = state.trafficCapacityReportScope, section = state.opsBreakdownSection) {
      if (!state.operations || !state.operations.quarters.length) return [];
      const metricConfig = trafficCapacityMetricConfig(section);
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
        const aggregate = aggregateTrafficPeriod(periodQuarters);
        const previousAggregate = aggregateTrafficPeriod(previousQuarters);
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

    function trafficCapacityVisiblePeriods(rows) {
      if (!rows.length) return [];
      const maxStart = Math.max(0, rows.length - TRAFFIC_CAPACITY_WINDOW_SIZE);
      if (state.trafficCapacityWindowPinnedToLatest || state.trafficCapacityWindowStart == null) {
        state.trafficCapacityWindowStart = maxStart;
      }
      state.trafficCapacityWindowStart = Math.max(0, Math.min(maxStart, Number(state.trafficCapacityWindowStart) || 0));
      return rows.slice(state.trafficCapacityWindowStart, state.trafficCapacityWindowStart + TRAFFIC_CAPACITY_WINDOW_SIZE);
    }

    function renderTrafficCapacityAnalysis() {
      const config = trafficCapacityMetricConfig();
      const allRows = trafficCapacityPeriodsAll();
      const rows = trafficCapacityVisiblePeriods(allRows);
      const maxStart = Math.max(0, allRows.length - TRAFFIC_CAPACITY_WINDOW_SIZE);
      el.opsBreakdownButtons.forEach((button) => {
        button.setAttribute("aria-selected", String(button.getAttribute("data-ops-breakdown-section") === state.opsBreakdownSection));
      });
      el.trafficCapacityMetricTitle.textContent = config.label;
      el.trafficCapacityValueHeader.textContent = config.label;
      el.trafficCapacityGrowthHeader.textContent = config.growthHeader;
      el.trafficCapacityScopeSelect.value = state.trafficCapacityReportScope;
      el.trafficCapacityRangeInput.min = "0";
      el.trafficCapacityRangeInput.max = String(maxStart);
      el.trafficCapacityRangeInput.value = String(state.trafficCapacityWindowStart || 0);
      el.trafficCapacityRangeInput.disabled = maxStart === 0;
      el.trafficCapacityTicks.style.gridTemplateColumns = allRows.length
        ? `repeat(${Math.min(allRows.length, TRAFFIC_CAPACITY_WINDOW_SIZE)}, minmax(0, 1fr))`
        : "1fr";
      el.trafficCapacityTicks.innerHTML = rows.map((row) => `<span class="financial-tick">${escapeHtml(row.year)}</span>`).join("");
      if (!state.operations || !allRows.length || !rows.length) {
        el.trafficCapacityMetricCaption.textContent = config.caption;
        el.trafficCapacityMetricChart.innerHTML = `<div class="empty">加载运营后显示${config.label}。</div>`;
        el.trafficCapacityMetricRows.innerHTML = `<tr><td colspan="3" style="text-align:center;color:var(--muted)">暂无数据</td></tr>`;
        el.trafficCapacityWindowLabel.textContent = "年度轴";
        el.trafficCapacityWindowHint.textContent = "暂无历史";
        return;
      }
      const first = rows[0];
      const last = rows[rows.length - 1];
      const scopeLabel = financialScopeLabel(state.trafficCapacityReportScope);
      el.trafficCapacityMetricCaption.textContent = `${first.label} - ${last.label}；${scopeLabel}；${config.caption}`;
      el.trafficCapacityWindowLabel.textContent = `${first.label} - ${last.label}`;
      el.trafficCapacityWindowHint.textContent = maxStart > 0 ? "拖动查看历史年份" : "当前口径历史已全部显示";
      renderComboChart(el.trafficCapacityMetricChart, rows, {
        title: config.label,
        leftFormat: config.leftFormat,
        rightPad: config.rightPad,
        bars: config.bars,
        stackedBars: config.stackedBars,
        line: config.line,
      });
      el.trafficCapacityMetricRows.innerHTML = rows.slice().reverse().map((row) => `
        <tr>
          <td>${escapeHtml(row.label)}</td>
          <td>${escapeHtml(config.valueText(row))}</td>
          <td>${escapeHtml(config.growthText(row))}</td>
        </tr>
      `).join("");
    }

