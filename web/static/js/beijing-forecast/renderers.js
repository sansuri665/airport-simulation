window.AirportForecastRenderers = (() => {
  function num(value, fallback = 0) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function fmt(value, digits = 1) {
    if (!Number.isFinite(Number(value))) return "-";
    return Number(value).toLocaleString("zh-CN", {
      maximumFractionDigits: digits,
      minimumFractionDigits: digits,
    });
  }

  function makeScale(domainMin, domainMax, rangeMin, rangeMax) {
    const span = domainMax - domainMin || 1;
    return (value) => rangeMin + (value - domainMin) / span * (rangeMax - rangeMin);
  }

  function chart({
    rows,
    asOfYear,
    currentValue,
    scopeLabel,
    color,
    mode,
    predictedValue,
    predictedLow,
    predictedHigh,
    trueValue,
  }) {
    if (!rows.length) return '<div class="empty">没有预测数据</div>';
    const width = 1120;
    const height = 430;
    const margin = { top: 28, right: 28, bottom: 46, left: 66 };
    const targetYears = rows.map((row) => row.forecast_year);
    const values = [currentValue];
    rows.forEach((row) => {
      values.push(predictedLow(row), predictedValue(row), predictedHigh(row));
      if (mode === "audit") values.push(trueValue(row));
    });
    const xMin = asOfYear;
    const xMax = Math.max(...targetYears);
    const yMin = Math.max(0, Math.min(...values) * 0.88);
    const yMax = Math.max(...values) * 1.08;
    const x = makeScale(xMin, xMax, margin.left, width - margin.right);
    const y = makeScale(yMin, yMax, height - margin.bottom, margin.top);
    const parts = [];
    for (let index = 0; index <= 5; index += 1) {
      const value = yMin + (yMax - yMin) * index / 5;
      const yy = y(value);
      parts.push(`<line x1="${margin.left}" y1="${yy}" x2="${width - margin.right}" y2="${yy}" stroke="#1f2937"/>`);
      parts.push(`<text x="${margin.left - 10}" y="${yy + 4}" fill="#94a3b8" font-size="11" text-anchor="end">${fmt(value, 0)}</text>`);
    }
    const tickStep = xMax - xMin > 16 ? 2 : 1;
    for (let year = xMin; year <= xMax; year += tickStep) {
      parts.push(`<text x="${x(year)}" y="${height - 16}" fill="#94a3b8" font-size="11" text-anchor="middle">${year}</text>`);
    }
    const bandTop = rows.map((row) => `${x(row.forecast_year)},${y(predictedHigh(row))}`);
    const bandBottom = [...rows].reverse().map((row) => `${x(row.forecast_year)},${y(predictedLow(row))}`);
    parts.push(`<polygon points="${[...bandTop, ...bandBottom].join(" ")}" fill="${color}" opacity="0.13"/>`);
    const predictedPoints = [
      `${x(asOfYear)},${y(currentValue)}`,
      ...rows.map((row) => `${x(row.forecast_year)},${y(predictedValue(row))}`),
    ];
    parts.push(`<polyline points="${predictedPoints.join(" ")}" fill="none" stroke="${color}" stroke-width="3" stroke-linejoin="round"/>`);
    rows.forEach((row) => {
      const value = predictedValue(row);
      parts.push(`<circle cx="${x(row.forecast_year)}" cy="${y(value)}" r="3.5" fill="${color}"><title>${row.forecast_year}: ${fmt(value)} 百万人</title></circle>`);
    });
    if (mode === "audit") {
      const truePoints = [
        `${x(asOfYear)},${y(currentValue)}`,
        ...rows.map((row) => `${x(row.forecast_year)},${y(trueValue(row))}`),
      ];
      parts.push(`<polyline points="${truePoints.join(" ")}" fill="none" stroke="#f5f7fb" stroke-width="2.4" stroke-dasharray="7 5"/>`);
      rows.forEach((row) => {
        const predicted = predictedValue(row);
        const truth = trueValue(row);
        const gap = predicted - truth;
        const gapPct = Math.abs(truth) > 1e-9 ? gap / truth * 100 : 0;
        const direction = gap > 0.0005
          ? `高估 ${fmt(Math.abs(gap))} 百万人（${fmt(Math.abs(gapPct))}%）`
          : gap < -0.0005
            ? `低估 ${fmt(Math.abs(gap))} 百万人（${fmt(Math.abs(gapPct))}%）`
            : "与真实值基本一致";
        const stroke = gap > 0.0005 ? "#fb923c" : gap < -0.0005 ? "#38bdf8" : "#a7f3d0";
        parts.push(`<circle class="true-point" cx="${x(row.forecast_year)}" cy="${y(truth)}" r="5" fill="#f5f7fb" stroke="${stroke}" stroke-width="2"><title>${row.forecast_year}: 真实值 ${fmt(truth)} 百万人；预测值 ${fmt(predicted)} 百万人；${direction}</title></circle>`);
      });
    }
    parts.push(`<text x="18" y="22" fill="#94a3b8" font-size="12">${escapeHtml(scopeLabel)} / 百万人</text>`);
    return `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(scopeLabel)}预测路径">${parts.join("")}</svg>`;
  }

  return { num, escapeHtml, fmt, chart };
})();
