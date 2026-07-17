(() => {
  const COMPONENTS = [
    ["business", "商务"],
    ["leisure", "休闲"],
    ["vfr", "探亲访友"],
    ["long_haul", "长途"],
    ["transfer", "中转"],
  ];
  const COMPONENT_LABELS = Object.fromEntries(COMPONENTS);
  const PHASE_LABELS = {
    balanced: "均衡调整", expansion: "扩张", overexpansion: "过度扩张",
    contraction: "收缩", trough: "周期谷底", pessimistic_contraction: "悲观收缩", recovery: "恢复",
  };
  const VOLATILITY_LABELS = {
    normal_airline_supply_cycle: "常规供给周期", volatile_airline_supply: "波动供给周期",
    highly_volatile_airline_supply: "高波动供给周期",
  };
  const SUPPLY_REGIME_LABELS = {
    comfortable_airline_supply: "供给宽松", tight_airline_supply: "供给偏紧",
    airline_supply_shortage: "航司供给不足", severe_airline_supply_bottleneck: "严重供给瓶颈",
  };

  function number(value, digits = 1) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed.toLocaleString("zh-CN", { maximumFractionDigits: digits, minimumFractionDigits: digits }) : "—";
  }
  function million(value) { return `${number(value)} 百万人`; }
  function pct(value) { return `${number(value)}%`; }
  function signedPct(value) {
    const parsed = Number(value);
    if (!Number.isFinite(parsed)) return "—";
    return `${parsed > 0 ? "+" : ""}${number(parsed)}%`;
  }
  function labelFor(map, value) { return map[value] || value || "—"; }
  function clear(node) { node.replaceChildren(); }
  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function rankingPoint(city, year) {
    return city.rankingPoints.find((point) => point.year === year) || city.rankingPoints.at(-1);
  }

  function scopeLabel(scope) {
    return scope === "total" ? "总客流" : COMPONENT_LABELS[scope] || "总客流";
  }

  function scopePoint(point, scope) {
    if (scope === "total") {
      return {
        year: point.year,
        potential: point.potential,
        offered: point.airlineOffered,
        effective: point.serviceable,
        airlineSupply: point.airlineSupply,
        unused: point.unusedAirlineCapacity,
        gap: point.supplyGap,
        fulfillment: point.supplyFulfillmentPct,
      };
    }
    const component = point.components?.[scope] || {};
    return {
      year: point.year,
      potential: component.potential,
      offered: component.offeredCapacity,
      effective: component.airlineSupply,
      airlineSupply: component.airlineSupply,
      unused: Math.max(0, Number(component.offeredCapacity || 0) - Number(component.airlineSupply || 0)),
      gap: component.supplyGap,
      fulfillment: component.supplyFulfillmentPct,
      potentialShare: component.potentialSharePct,
      supplyShare: component.supplySharePct,
      priorityWeight: component.priorityWeight,
    };
  }

  function renderCityList(node, cities, selectedId, year, sortKey, onSelect) {
    clear(node);
    cities.forEach((city, index) => {
      const point = rankingPoint(city, year);
      const button = el("button", `city-row${city.id === selectedId ? " active" : ""}`);
      button.type = "button";
      button.dataset.cityId = city.id;
      button.append(el("span", "rank", String(index + 1)));
      const copy = el("span", "city-row-copy");
      const supplyState = Number(point.supplyGap) > 0.00005 ? "航司供给不足" : "航司供给充足";
      copy.append(el("strong", "", city.name), el("small", "", supplyState));
      button.append(copy);
      const value = sortKey === "supplyFulfillmentPct" ? pct(point[sortKey]) : million(point[sortKey]);
      button.append(el("span", "city-value", value));
      button.addEventListener("click", () => onSelect(city.id));
      node.append(button);
    });
  }

  function card(label, value, note, tone = "") {
    const node = el("article", `metric-card ${tone}`.trim());
    node.append(el("span", "metric-label", label), el("strong", "metric-value", value), el("small", "metric-note", note));
    return node;
  }

  function renderSummary(node, point, scope) {
    clear(node);
    const value = scopePoint(point, scope);
    if (scope !== "total") {
      node.append(
        card("潜在需求", million(value.potential), `${scopeLabel(scope)}客群需求`),
        card("分配座位", million(value.offered), "按客群权重获得的座位", "blue"),
        card("有效航司供给", million(value.effective), "需求上限内可实际使用的供给", "cyan"),
        card("航司供给缺口", million(value.gap), "潜在需求超过有效供给的部分", "amber"),
        card("供给满足率", pct(value.fulfillment), `供给占比 ${pct(value.supplyShare)}`),
        card("分配优先权重", number(value.priorityWeight, 2), `需求占比 ${pct(value.potentialShare)}`)
      );
      return;
    }
    node.append(
      card("潜在客流", million(point.potential), "城市潜在航空需求"),
      card("航司座位投放", million(point.airlineOffered), "航司向城市市场投入的座位", "blue"),
      card("有效航司供给", million(point.airlineSupply), "可用于承载旅客的城市供给", "blue"),
      card("供给约束后需求", million(point.serviceable), `航司满足率 ${pct(point.supplyFulfillmentPct)}`, "cyan"),
      card("航司供给缺口", million(point.supplyGap), "潜在需求超过有效供给的部分", "amber"),
      card("闲置航司座位", million(point.unusedAirlineCapacity), "供给未被潜在需求使用的部分")
    );
  }

  function renderLegend(node, scope) {
    clear(node);
    const labels = scope === "total"
      ? ["潜在客流", "航司座位投放", "供给约束后需求"]
      : ["潜在需求", "分配座位", "有效航司供给"];
    [["potential", labels[0]], ["offered", labels[1]], ["effective", labels[2]]].forEach(([className, label]) => {
      const item = el("span");
      item.append(el("i", `swatch ${className}`), document.createTextNode(label));
      node.append(item);
    });
  }

  function svgNode(name, attributes = {}) {
    const node = document.createElementNS("http://www.w3.org/2000/svg", name);
    Object.entries(attributes).forEach(([key, value]) => node.setAttribute(key, String(value)));
    return node;
  }
  function svgText(x, y, text, anchor = "middle") {
    const node = svgNode("text", { x, y, "text-anchor": anchor, class: "axis-label" });
    node.textContent = text;
    return node;
  }

  function renderMarketChart(node, points, selectedYear, scope) {
    clear(node);
    if (!points.length) return;
    const scopedPoints = points.map((point) => scopePoint(point, scope));
    const width = 1120, height = 430, left = 72, right = 24, top = 28, bottom = 58;
    const innerW = width - left - right, innerH = height - top - bottom;
    const series = [
      ["potential", "#a78bfa"], ["offered", "#4f8ef7"],
      ["effective", "#22c7d9"],
    ];
    const maximum = Math.max(1, ...scopedPoints.flatMap((point) => series.map(([key]) => Number(point[key]) || 0))) * 1.08;
    const x = (index) => left + (scopedPoints.length === 1 ? innerW / 2 : (index / (scopedPoints.length - 1)) * innerW);
    const y = (value) => top + innerH - ((Number(value) || 0) / maximum) * innerH;
    const svg = svgNode("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", "aria-label": `${scopeLabel(scope)}长期轨迹` });
    for (let tick = 0; tick <= 4; tick += 1) {
      const value = (maximum * tick) / 4;
      const yy = y(value);
      svg.append(svgNode("line", { x1: left, x2: width - right, y1: yy, y2: yy, class: "grid-line" }));
      svg.append(svgText(left - 12, yy + 5, number(value, 0), "end"));
    }
    const tickIndexes = [...new Set([0, Math.floor((scopedPoints.length - 1) * 0.25), Math.floor((scopedPoints.length - 1) * 0.5), Math.floor((scopedPoints.length - 1) * 0.75), scopedPoints.length - 1])];
    tickIndexes.forEach((index) => svg.append(svgText(x(index), height - 22, String(scopedPoints[index].year))));
    const selectedIndex = Math.max(0, scopedPoints.findIndex((point) => point.year === selectedYear));
    svg.append(svgNode("line", { x1: x(selectedIndex), x2: x(selectedIndex), y1: top, y2: top + innerH, class: "selected-line" }));
    series.forEach(([key, color]) => {
      const d = scopedPoints.map((point, index) => `${index ? "L" : "M"}${x(index).toFixed(2)},${y(point[key]).toFixed(2)}`).join(" ");
      svg.append(svgNode("path", { d, fill: "none", stroke: color, class: "series-line" }));
      svg.append(svgNode("circle", { cx: x(selectedIndex), cy: y(scopedPoints[selectedIndex][key]), r: 5, fill: color, class: "selected-dot" }));
    });
    svg.append(svgText(18, top + innerH / 2, "百万人", "middle"));
    node.append(svg);
  }

  function renderSupplyState(node, point, scope) {
    clear(node);
    if (scope !== "total") {
      const value = scopePoint(point, scope);
      const allocationTilt = Number(value.supplyShare || 0) - Number(value.potentialShare || 0);
      node.append(
        card("潜在需求占比", pct(value.potentialShare), `${scopeLabel(scope)}占城市潜在客流的比例`),
        card("航司供给占比", pct(value.supplyShare), "该客群获得的有效供给比例"),
        card("供给分配倾斜", signedPct(allocationTilt), "供给占比减去需求占比"),
        card("分配优先权重", number(value.priorityWeight, 2), "用于统一客群供给分配"),
        card("客群供给满足率", pct(value.fulfillment), `缺口 ${million(value.gap)}`),
        card("共享城市供给阶段", labelFor(PHASE_LABELS, point.supplyBehaviorPhase), "五类客群共用同一城市航司周期")
      );
      return;
    }
    node.append(
      card("供给周期阶段", labelFor(PHASE_LABELS, point.supplyBehaviorPhase), `第 ${point.supplyCycleNumber || 0} 轮 · 已持续 ${number(point.supplyPhaseAgeYears, 0)} 年`),
      card("短期波动状态", labelFor(VOLATILITY_LABELS, point.supplyVolatilityRegime), labelFor(SUPPLY_REGIME_LABELS, point.supplyRegime)),
      card("偏离基本面", signedPct(point.supplyDeviationFromFundamentalPct), "供给相对基本面目标"),
      card("偏离潜在需求", signedPct(point.supplyDeviationFromPotentialPct), `高于潜在需求 ${signedPct(point.supplyExcessOverPotentialPct)}`),
      card("供给冲击", signedPct(point.supplyShockImpulsePct), `事件脉冲 ${signedPct(point.supplyEventImpulsePct)}`),
      card(
        "航司供需余量",
        Number(point.supplyGap) > 0.00005 ? `缺口 ${million(point.supplyGap)}` : `富余 ${million(Math.max(0, point.airlineSupply - point.potential))}`,
        `航司满足率 ${pct(point.supplyFulfillmentPct)}`
      )
    );
  }

  function renderAnnualTable(headNode, bodyNode, points, selectedYear, scope, onSelectYear) {
    clear(headNode);
    clear(bodyNode);
    const headers = scope === "total"
      ? ["年份", "航司座位投放", "潜在客流", "有效航司供给", "供给约束后", "闲置座位", "供给缺口", "供给满足率", "供给阶段"]
      : ["年份", "潜在需求", "分配座位", "有效航司供给", "供给缺口", "供给满足率", "需求占比", "供给占比", "优先权重"];
    const headRow = document.createElement("tr");
    headers.forEach((header) => headRow.append(el("th", "", header)));
    headNode.append(headRow);
    [...points].reverse().forEach((point) => {
      const value = scopePoint(point, scope);
      const row = document.createElement("tr");
      if (point.year === selectedYear) row.className = "selected-year";
      const values = scope === "total"
        ? [String(point.year), million(value.offered), million(value.potential), million(value.airlineSupply), million(value.effective), million(value.unused), million(value.gap), pct(value.fulfillment), labelFor(PHASE_LABELS, point.supplyBehaviorPhase)]
        : [String(point.year), million(value.potential), million(value.offered), million(value.effective), million(value.gap), pct(value.fulfillment), pct(value.potentialShare), pct(value.supplyShare), number(value.priorityWeight, 2)];
      values.forEach((textValue, index) => {
        const cell = document.createElement(index === 0 ? "th" : "td");
        cell.textContent = textValue;
        row.append(cell);
      });
      row.addEventListener("click", () => onSelectYear(point.year));
      bodyNode.append(row);
    });
  }

  window.AirportCityMarketRender = {
    rankingPoint, scopeLabel, renderCityList, renderSummary, renderLegend,
    renderMarketChart, renderSupplyState, renderAnnualTable,
  };
})();
