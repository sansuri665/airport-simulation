(() => {
  const state = window.AirportCityMarketState;
  const data = window.AirportCityMarketData;
  const render = window.AirportCityMarketRender;
  const seedContext = window.AirportSeedContext;
  const byId = (id) => document.getElementById(id);

  function setStatus(message, kind = "") {
    const node = byId("statusText");
    node.textContent = message;
    node.dataset.kind = kind;
  }
  function cityMetaById(id) { return state.index.cities.find((city) => city.id === id); }
  function currentPoint() {
    return state.selectedCity?.points.find((point) => point.year === state.selectedYear) || state.selectedCity?.points.at(-1);
  }
  function rankingCities() {
    const needle = state.search.trim().toLocaleLowerCase("zh-CN");
    return state.index.cities
      .filter((city) => !needle || `${city.name} ${city.id}`.toLocaleLowerCase("zh-CN").includes(needle))
      .sort((left, right) => {
        const a = Number(render.rankingPoint(left, state.selectedYear)?.[state.sortKey]) || 0;
        const b = Number(render.rankingPoint(right, state.selectedYear)?.[state.sortKey]) || 0;
        return b - a;
      });
  }
  function renderRanking() {
    const cities = rankingCities();
    byId("cityCount").textContent = `${cities.length} / ${state.index.cityCount} 城`;
    render.renderCityList(byId("cityList"), cities, state.selectedCityId, state.selectedYear, state.sortKey, selectCity);
  }
  function renderSelectedCity() {
    if (!state.selectedCity) return;
    const point = currentPoint();
    byId("cityTitle").textContent = `${state.selectedCity.name}航空市场`;
    byId("cityMeta").textContent = `${state.selectedCity.marketTier || "未分级"} · ${state.selectedCity.marketType || "未分类"} · ${state.selectedCity.startYear}—${state.selectedCity.finalYear}`;
    const scopeName = render.scopeLabel(state.marketScope);
    byId("trajectoryTitle").textContent = `${scopeName}长期轨迹`;
    byId("supplyStatusTitle").textContent = state.marketScope === "total" ? "航司供给状态" : `${scopeName}供给分配`;
    byId("annualTitle").textContent = `${scopeName}年度明细`;
    byId("marketScopeTabs").querySelectorAll("button").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.marketScope === state.marketScope));
    });
    render.renderSummary(byId("summaryGrid"), point, state.marketScope);
    render.renderLegend(byId("trajectoryLegend"), state.marketScope);
    render.renderMarketChart(byId("marketChart"), state.selectedCity.points, state.selectedYear, state.marketScope);
    render.renderSupplyState(byId("supplyStatusGrid"), point, state.marketScope);
    render.renderAnnualTable(
      byId("annualTableHead"),
      byId("annualTableBody"),
      state.selectedCity.points,
      state.selectedYear,
      state.marketScope,
      setYear
    );
  }

  function setMarketScope(scope) {
    if (scope === state.marketScope) return;
    state.marketScope = scope;
    renderSelectedCity();
  }
  function setYear(year) {
    state.selectedYear = Math.max(state.index.startYear, Math.min(state.index.finalYear, Number(year)));
    byId("yearRange").value = String(state.selectedYear);
    byId("yearLabel").textContent = `${state.selectedYear} 年`;
    renderRanking();
    renderSelectedCity();
  }
  async function selectCity(cityId) {
    const cityMeta = cityMetaById(cityId);
    if (!cityMeta) return;
    state.selectedCityId = cityId;
    renderRanking();
    const token = ++state.loadToken;
    setStatus(`正在读取${cityMeta.name}…`);
    try {
      const cacheKey = data.cacheKey(state.seedContext, cityId);
      let city = state.cityCache.get(cacheKey);
      if (!city) {
        city = await data.loadCity(state.index, cityMeta, state.seedContext);
        state.cityCache.set(cacheKey, city);
      }
      if (token !== state.loadToken) return;
      state.selectedCity = city;
      renderSelectedCity();
      const source = state.index.contextSource === "viewer_release" ? "Viewer Release" : "Seed 缓存";
      setStatus(`${state.index.cityCount} 城 · ${state.seedContext.years} 年 · ${source}`, "ready");
    } catch (error) {
      if (token !== state.loadToken) return;
      setStatus(error.message || "城市数据读取失败", "error");
    }
  }

  function renderContext() {
    const context = state.seedContext;
    if (!context) return;
    const source = state.index?.contextSource === "viewer_release"
      ? "Viewer Release"
      : context.cacheStatus === "ready" ? "Seed 计算缓存" : "数据不可用";
    byId("releaseMeta").textContent = `Seed ${context.seed} · ${context.years} 年`;
    byId("contextSource").textContent = `${source} · 槽位 ${context.slotId} · revision ${context.workspaceRevision}（当前 ${context.currentWorkspaceRevision}）`;
    byId("contextChangeNotice").hidden = !state.contextChanged;
    byId("operationsLink").href = seedContext.href("/seed-explorer", context);
  }

  async function refreshContext() {
    try {
      const refreshed = await seedContext.refresh();
      state.seedContext = refreshed.context;
      state.contextChanged = refreshed.activeSlotChanged || refreshed.slotMissing;
      renderContext();
    } catch (_error) {
      state.contextChanged = true;
      byId("contextChangeNotice").hidden = false;
    }
  }

  function bindControls() {
    byId("yearRange").addEventListener("input", (event) => setYear(event.target.value));
    byId("sortSelect").addEventListener("change", (event) => { state.sortKey = event.target.value; renderRanking(); });
    byId("searchInput").addEventListener("input", (event) => { state.search = event.target.value; renderRanking(); });
    byId("marketScopeTabs").addEventListener("click", (event) => {
      const button = event.target.closest("button[data-market-scope]");
      if (button) setMarketScope(button.dataset.marketScope);
    });
  }

  async function start() {
    try {
      state.seedContext = await seedContext.resolve();
      state.contextChanged = !state.seedContext.isWorkspaceActive;
      state.index = await data.getIndex(state.seedContext);
      state.selectedYear = state.index.finalYear;
      const range = byId("yearRange");
      range.min = String(state.index.startYear);
      range.max = String(state.index.finalYear);
      range.value = String(state.selectedYear);
      byId("yearLabel").textContent = `${state.selectedYear} 年`;
      renderContext();
      bindControls();
      renderRanking();
      const initial = state.index.cities.find((city) => city.id === "beijing_airport_system") || state.index.cities[0];
      await selectCity(initial.id);
    } catch (error) {
      setStatus(error.message || "页面初始化失败", "error");
      byId("cityTitle").textContent = "城市市场数据不可用";
      byId("cityMeta").textContent = "请返回首页选择可用槽位；缓存槽位需要先生成当前世界。";
    }
  }
  start();
  window.setInterval(refreshContext, 2500);
})();
