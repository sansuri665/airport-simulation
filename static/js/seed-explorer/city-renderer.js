    function sortedCities() {
      if (!state.data) return [];
      const query = el.searchInput.value.trim().toLowerCase();
      const key = el.sortSelect.value;
      return state.data.cities
        .filter((city) => {
          if (!query) return true;
          return `${city.name} ${city.id} ${city.marketTier} ${city.marketType}`.toLowerCase().includes(query);
        })
        .sort((a, b) => Number(b[key] || 0) - Number(a[key] || 0));
    }

    function selectedCity() {
      if (!state.data) return null;
      return state.data.cities.find((city) => city.id === state.selectedCityId) || state.data.cities[0] || null;
    }

    function metric(label, value, sub = "") {
      return `<div class="metric"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong><span>${escapeHtml(sub)}</span></div>`;
    }

    function renderCityList() {
      const cities = sortedCities();
      if (!cities.length) {
        el.cityList.innerHTML = `<div class="empty">没有匹配城市</div>`;
        return;
      }
      el.cityList.innerHTML = cities.map((city, index) => `
        <button class="city-row" type="button" data-city-id="${escapeHtml(city.id)}" aria-pressed="${city.id === state.selectedCityId}">
          <span class="city-name"><span>${index + 1}. ${escapeHtml(city.name)}</span><span>${fmt(city.finalEffective, 0)}</span></span>
          <span class="city-meta"><span>${escapeHtml(city.marketTier || city.id)}</span><span>供给 ${fmt(city.finalAirlineSupply, 0)} / 缺口 ${fmt(city.finalSupplyGap, 0)}</span></span>
        </button>
      `).join("");
      el.cityList.querySelectorAll("[data-city-id]").forEach((button) => {
        button.addEventListener("click", () => {
          state.selectedCityId = button.getAttribute("data-city-id");
          render();
        });
      });
    }

    function chartPath(points, x, y, key) {
      return points.map((point, index) => `${index ? "L" : "M"} ${x(point.year).toFixed(2)} ${y(point[key]).toFixed(2)}`).join(" ");
    }

    function renderChart(city) {
      if (!city || !city.points.length) {
        el.chart.innerHTML = `<div class="empty">暂无曲线</div>`;
        return;
      }
      const styles = getComputedStyle(document.documentElement);
      const colors = {
        potential: styles.getPropertyValue("--blue").trim() || "#62a8ff",
        airlineSupply: styles.getPropertyValue("--green").trim() || "#35d392",
        effective: styles.getPropertyValue("--amber").trim() || "#f7b84b",
        grid: styles.getPropertyValue("--grid").trim() || "#202838",
        muted: styles.getPropertyValue("--muted").trim() || "#91a0b5",
      };
      const width = 1120;
      const height = 500;
      const pad = { left: 64, right: 24, top: 28, bottom: 44 };
      const years = city.points.map((point) => point.year);
      const minYear = Math.min(...years);
      const maxYear = Math.max(...years);
      const maxValue = Math.max(...city.points.flatMap((point) => [point.potential, point.airlineSupply, point.effective]), 1);
      const yMax = maxValue * 1.08;
      const x = (year) => pad.left + (year - minYear) / Math.max(1, maxYear - minYear) * (width - pad.left - pad.right);
      const y = (value) => height - pad.bottom - value / yMax * (height - pad.top - pad.bottom);
      const yTicks = [0, 0.25, 0.5, 0.75, 1].map((unit) => yMax * unit);
      const xTicks = [];
      for (let year = minYear; year <= maxYear; year += 10) xTicks.push(year);
      if (!xTicks.includes(maxYear)) xTicks.push(maxYear);
      const grid = [
        ...yTicks.map((value) => `<line x1="${pad.left}" y1="${y(value)}" x2="${width - pad.right}" y2="${y(value)}" stroke="${colors.grid}"/><text x="${pad.left - 10}" y="${y(value) + 4}" text-anchor="end" font-size="12" fill="${colors.muted}">${fmt(value, 0)}</text>`),
        ...xTicks.map((year) => `<line x1="${x(year)}" y1="${pad.top}" x2="${x(year)}" y2="${height - pad.bottom}" stroke="${colors.grid}"/><text x="${x(year)}" y="${height - 16}" text-anchor="middle" font-size="12" fill="${colors.muted}">${year}</text>`),
      ].join("");
      const paths = [
        `<path d="${chartPath(city.points, x, y, "potential")}" fill="none" stroke="${colors.potential}" stroke-width="3"/>`,
        `<path d="${chartPath(city.points, x, y, "airlineSupply")}" fill="none" stroke="${colors.airlineSupply}" stroke-width="3"/>`,
        `<path d="${chartPath(city.points, x, y, "effective")}" fill="none" stroke="${colors.effective}" stroke-width="3"/>`,
      ].join("");
      const marks = city.points
        .filter((_, index) => index % 5 === 0 || index === city.points.length - 1)
        .map((point) => `<circle cx="${x(point.year)}" cy="${y(point.effective)}" r="3" fill="${colors.effective}"><title>${point.year}: 有效 ${fmtPassenger(point.effective)}, 潜在 ${fmtPassenger(point.potential)}, 供给 ${fmtPassenger(point.airlineSupply)}</title></circle>`)
        .join("");
      const hitWidth = Math.max(10, (width - pad.left - pad.right) / Math.max(1, city.points.length - 1));
      const hitZones = city.points
        .map((point, index) => {
          const center = x(point.year);
          const left = Math.max(pad.left, center - hitWidth / 2);
          const right = Math.min(width - pad.right, center + hitWidth / 2);
          return `<rect class="year-hit" tabindex="0" data-index="${index}" x="${left}" y="${pad.top}" width="${Math.max(4, right - left)}" height="${height - pad.top - pad.bottom}" fill="transparent"/>`;
        })
        .join("");
      el.chart.innerHTML = `
        <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(city.name)}城市客流曲线">
          <rect x="0" y="0" width="${width}" height="${height}" fill="#070b10"/>
          ${grid}
          <line x1="${pad.left}" y1="${height - pad.bottom}" x2="${width - pad.right}" y2="${height - pad.bottom}" stroke="#465366"/>
          <line x1="${pad.left}" y1="${pad.top}" x2="${pad.left}" y2="${height - pad.bottom}" stroke="#465366"/>
          ${paths}
          ${marks}
          <g id="hoverLayer" style="display:none">
            <line id="hoverLine" x1="0" y1="${pad.top}" x2="0" y2="${height - pad.bottom}" stroke="#d7dee9" stroke-width="1" stroke-dasharray="4 4" opacity="0.75"/>
            <circle id="hoverPotential" r="5" fill="${colors.potential}" stroke="#070b10" stroke-width="2"/>
            <circle id="hoverSupply" r="5" fill="${colors.airlineSupply}" stroke="#070b10" stroke-width="2"/>
            <circle id="hoverEffective" r="5" fill="${colors.effective}" stroke="#070b10" stroke-width="2"/>
          </g>
          ${hitZones}
        </svg>
        <div class="chart-tooltip" id="chartTooltip"></div>
      `;
      const svg = el.chart.querySelector("svg");
      const tooltip = el.chart.querySelector("#chartTooltip");
      const hoverLayer = el.chart.querySelector("#hoverLayer");
      const hoverLine = el.chart.querySelector("#hoverLine");
      const hoverPotential = el.chart.querySelector("#hoverPotential");
      const hoverSupply = el.chart.querySelector("#hoverSupply");
      const hoverEffective = el.chart.querySelector("#hoverEffective");
      const placeTooltip = (point) => {
        const svgRect = svg.getBoundingClientRect();
        const chartRect = el.chart.getBoundingClientRect();
        const scaleX = svgRect.width / width;
        const scaleY = svgRect.height / height;
        let left = svgRect.left - chartRect.left + x(point.year) * scaleX + 14;
        let top = svgRect.top - chartRect.top + Math.min(y(point.potential), y(point.airlineSupply), y(point.effective)) * scaleY - 8;
        const maxLeft = Math.max(8, chartRect.width - tooltip.offsetWidth - 8);
        const maxTop = Math.max(8, chartRect.height - tooltip.offsetHeight - 8);
        tooltip.style.left = `${Math.min(Math.max(8, left), maxLeft)}px`;
        tooltip.style.top = `${Math.min(Math.max(8, top), maxTop)}px`;
      };
      const showHover = (point) => {
        const cursorX = x(point.year);
        hoverLayer.style.display = "";
        hoverLine.setAttribute("x1", cursorX);
        hoverLine.setAttribute("x2", cursorX);
        hoverPotential.setAttribute("cx", cursorX);
        hoverPotential.setAttribute("cy", y(point.potential));
        hoverSupply.setAttribute("cx", cursorX);
        hoverSupply.setAttribute("cy", y(point.airlineSupply));
        hoverEffective.setAttribute("cx", cursorX);
        hoverEffective.setAttribute("cy", y(point.effective));
        tooltip.innerHTML = `
          <strong>${point.year} 年</strong>
          <div class="tooltip-row"><span>潜在客流</span><b>${fmtPassenger(point.potential)}</b></div>
          <div class="tooltip-row"><span>航司供给</span><b>${fmtPassenger(point.airlineSupply)}</b></div>
          <div class="tooltip-row"><span>有效客流</span><b>${fmtPassenger(point.effective)}</b></div>
          <div class="tooltip-row"><span>供给缺口</span><b>${fmtPassenger(point.supplyGap)}</b></div>
          <div class="tooltip-row"><span>满足率</span><b>${fmtPct(point.supplyFulfillmentPct)}</b></div>
          <div class="tooltip-row"><span>瓶颈</span><b>${escapeHtml(bottleneckLabel(point.bindingBottleneck))}</b></div>
        `;
        tooltip.classList.add("visible");
        placeTooltip(point);
      };
      const hideHover = () => {
        hoverLayer.style.display = "none";
        tooltip.classList.remove("visible");
      };
      el.chart.querySelectorAll(".year-hit").forEach((zone) => {
        const point = city.points[Number(zone.getAttribute("data-index"))];
        zone.addEventListener("mouseenter", () => showHover(point));
        zone.addEventListener("mousemove", () => showHover(point));
        zone.addEventListener("focus", () => showHover(point));
        zone.addEventListener("mouseleave", hideHover);
        zone.addEventListener("blur", hideHover);
      });
    }

    function renderTable(city) {
      if (!city) {
        el.detailRows.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--muted)">暂无数据</td></tr>`;
        return;
      }
      el.detailRows.innerHTML = city.points.map((point) => `
        <tr>
          <td>${point.year}</td>
          <td>${fmt(point.potential, 1)}</td>
          <td>${fmt(point.airlineSupply, 1)}</td>
          <td>${fmt(point.effective, 1)}</td>
          <td>${fmt(point.supplyGap, 1)}</td>
          <td>${fmtPct(point.supplyFulfillmentPct)}</td>
          <td>${escapeHtml(bottleneckLabel(point.bindingBottleneck))}</td>
        </tr>
      `).join("");
    }

    function renderSummary(city) {
      if (!city) {
        el.summaryGrid.innerHTML = "";
        return;
      }
      el.summaryGrid.innerHTML = [
        metric("远期有效客流", fmtPassenger(city.finalEffective), `${city.finalYear} 年`),
        metric("远期潜在客流", fmtPassenger(city.finalPotential), "城市需求盘"),
        metric("远期航司供给", fmtPassenger(city.finalAirlineSupply), bottleneckLabel(city.finalBottleneck)),
        metric("有效 CAGR", fmtPct(city.effectiveCagrPct), `${city.startYear}-${city.finalYear}`),
      ].join("");
    }

    function render() {
      const city = selectedCity();
      renderCityList();
      if (!state.data || !city) {
        el.cityTitle.textContent = "等待运行";
        el.runCaption.textContent = "运行全链路后选择城市查看曲线。";
        el.chartCaption.textContent = "潜在 / 供给 / 有效";
        renderSummary(null);
        renderChart(null);
        renderTable(null);
        return;
      }
      el.cityTitle.textContent = `${city.name} 城市市场`;
      el.runCaption.textContent = `Seed ${state.data.seed} / ${state.data.cityCount} 城市 / ${state.data.cached ? "读取已有结果" : "新运行"} / ${state.data.runDir}`;
      el.chartCaption.textContent = `${city.startYear}-${city.finalYear}，瓶颈 ${bottleneckLabel(city.finalBottleneck)}`;
      renderSummary(city);
      renderChart(city);
      renderTable(city);
    }

