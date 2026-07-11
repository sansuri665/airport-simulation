    function availableScopeOptions() {
      const lazyEntries = new Map(
        (Array.isArray(state.activeData?.lazyIndex?.regions) ? state.activeData.lazyIndex.regions : [])
          .map((entry) => [entry.regionId, entry])
      );
      if (state.view === "aviation") {
        return SCOPE_OPTIONS.filter((option) => {
          if (option.type !== "regional") return false;
          const entry = lazyEntries.get(option.id);
          return Boolean(state.aviationDatasets[option.id]?.length || (entry && entry.aviationDemandRowCount > 0));
        });
      }
      return SCOPE_OPTIONS.filter((option) => {
        if (option.id === "global") return Boolean(state.datasets.global?.length);
        const entry = lazyEntries.get(option.id);
        return Boolean(state.datasets[option.id]?.length || (entry && entry.regionalMacroRowCount > 0));
      });
    }

    function rowsForScope(scope) {
      return state.view === "aviation"
        ? state.aviationDatasets[scope] || []
        : state.datasets[scope] || [];
    }

    function refreshScopeOptions() {
      const options = availableScopeOptions();
      el.scopeSelect.innerHTML = options
        .map((option) => `<option value="${option.id}">${escapeHtml(option.label)}</option>`)
        .join("");
      el.scopeSelect.value = state.scope;
      el.scopeSelect.disabled = options.length <= 1;
    }

    function updateScopeStatus() {
      const config = scopeConfig();
      const rowCount = state.rows.length;
      const scopeText = state.view === "aviation"
        ? Object.keys(state.supplyDatasets || {}).length ? "区域航空需求/供给" : "区域航空需求"
        : config.type === "regional"
          ? "区域宏观"
          : "全球宏观";
      const sourceText = state.dataLabel ? ` / ${state.dataLabel}` : "";
      el.status.textContent = `${scopeText}: ${config.label} / ${rowCount} rows${sourceText}`;
      const canGenerateSeed = state.view === "macro" && config.type === "global" && state.runId === "current";
      el.randomSeedButton.disabled = !canGenerateSeed;
      el.randomSeedButton.title = canGenerateSeed
        ? "浏览器近似预览，不写入正式 Run"
        : "归档 Run 或区域模式不生成浏览器预览 Seed";
    }

    function applyScope(scope, preferredSeed = state.seed) {
      const options = availableScopeOptions();
      const fallbackScope = options[0]?.id || "global";
      const nextScope = options.some((option) => option.id === scope) ? scope : fallbackScope;
      state.scope = nextScope;
      state.rows = rowsForScope(nextScope);
      state.selectedIndex = 0;
      state.scenario = null;
      state.seeds = [...new Set(state.rows.map((row) => row.seed))].sort((a, b) => a - b);
      state.seed = state.seeds.includes(preferredSeed) ? preferredSeed : state.seeds[0];
      refreshScopeOptions();
      refreshSeedOptions();
      updateScopeStatus();
      render();
    }

    async function loadAndApplyScope(scope, preferredSeed = state.seed) {
      const token = state.regionSelectionToken + 1;
      state.regionSelectionToken = token;
      const options = availableScopeOptions();
      const nextScope = options.some((option) => option.id === scope) ? scope : (options[0]?.id || "global");
      if (nextScope !== "global" && !state.activeData?.loadedRegionIds?.has(nextScope)) {
        const label = SCOPE_OPTIONS.find((option) => option.id === nextScope)?.label || nextScope;
        el.status.textContent = `loading: ${label}`;
      }
      try {
        await ensureRegionLoaded(state.activeData, nextScope);
        if (token !== state.regionSelectionToken) return;
        applyScope(nextScope, preferredSeed);
      } catch (error) {
        if (token === state.regionSelectionToken) el.status.textContent = error.message;
      }
    }

    function refreshSeedOptions() {
      state.seeds = [...new Set(state.rows.map((row) => row.seed))].sort((a, b) => a - b);
      el.seedSelect.innerHTML = state.seeds.map((seed) => {
        const suffix = state.dynamicSeeds.has(seed) ? " browser-preview" : "";
        return `<option value="${seed}">seed ${seed}${suffix}</option>`;
      }).join("");
      el.seedSelect.value = String(state.seed);
    }

    function randomLargeSeed() {
      let seed = 0;
      const used = new Set(state.rows.map((row) => row.seed));
      do {
        seed = Math.floor(1_000_000 + Math.random() * 999_000_000);
      } while (used.has(seed));
      return seed;
    }

    function generateRandomSeed() {
      if (scopeConfig().type !== "global" || state.runId !== "current") return;
      const seed = randomLargeSeed();
      const iterations = 3;
      const passRows = [buildDynamicMacroChain(seed)];
      let feedback = {};
      for (let i = 0; i < iterations; i += 1) {
        feedback = blendDynamicFeedbackPaths(feedback, deriveDynamicFeedbackPath(passRows[passRows.length - 1]));
        passRows.push(buildDynamicMacroChain(seed, feedback));
      }
      const convergence = summarizeDynamicConvergence(passRows);
      const rows = annotateDynamicFeedback(passRows[passRows.length - 1], feedback, convergence, iterations);
      state.rows.push(...rows);
      state.dynamicSeeds.add(seed);
      state.seed = seed;
      state.selectedIndex = 0;
      state.scenario = null;
      refreshSeedOptions();
      el.status.textContent = `浏览器近似预览 Seed ${seed}；未写入正式 Run`;
      render();
    }

    function rowsForSeed() {
      return state.rows.filter((row) => row.seed === state.seed).sort((a, b) => a.year - b.year);
    }

    function selectedRow(rows) {
      return rows[Math.max(0, Math.min(state.selectedIndex, rows.length - 1))];
    }

    function summarize(rows) {
      const data = rows.filter((row) => row.year_index > 0);
      const growths = data.map((row) => row.realized_growth_pct);
      const avg = growths.reduce((acc, value) => acc + value, 0) / Math.max(1, growths.length);
      const minRow = data.reduce((best, row) => row.realized_growth_pct < best.realized_growth_pct ? row : best, data[0] || rows[0]);
      const recessionYears = data.filter((row) => row.realized_growth_pct < 0).length;
      return { avg, minRow, recessionYears };
    }

    const MODE_LABELS = {
      macro: {
        both: "总览",
        gdp: "GDP",
        growth: "增长",
        inflation: "通胀",
        policy: "利率",
        yield: "10Y",
        dollar: "美元",
        credit: "信用",
        asset: "资产",
        oil: "石油",
      },
      aviation: {
        both: "总览",
        gdp: "需求",
        growth: "增长",
        inflation: "结构",
        policy: "价格",
        yield: "弹性",
        dollar: "高端",
        credit: "事件",
        asset: "消费",
        oil: "宏观",
      },
    };

    function updateModeButtons() {
      document.querySelectorAll("button[data-mode]").forEach((button) => {
        button.textContent = MODE_LABELS[state.view]?.[button.dataset.mode] || button.dataset.mode;
        button.setAttribute("aria-pressed", String(button.dataset.mode === state.mode));
      });
    }

    function setupControls() {
      state.runOptions = buildRunOptions();
      refreshRunOptions();
      refreshScopeOptions();
      state.seeds = [...new Set(state.rows.map((row) => row.seed))].sort((a, b) => a - b);
      state.seed = state.seeds[0];
      refreshSeedOptions();
      updateScopeStatus();
      el.runSelect.addEventListener("change", () => {
        state.runId = el.runSelect.value;
        refreshVariantOptions();
        applySelectedRunVariant();
      });
      el.variantSelect.addEventListener("change", () => {
        state.variantId = el.variantSelect.value;
        applySelectedRunVariant();
      });
      el.viewSelect.addEventListener("change", async () => {
        state.view = el.viewSelect.value;
        state.mode = "both";
        updateModeButtons();
        await loadAndApplyScope(state.scope, state.seed);
      });
      el.scopeSelect.addEventListener("change", async () => {
        await loadAndApplyScope(el.scopeSelect.value, state.seed);
      });
      el.seedSelect.addEventListener("change", () => {
        state.seed = Number(el.seedSelect.value);
        state.selectedIndex = 0;
        state.scenario = null;
        render();
      });
      el.randomSeedButton.addEventListener("click", generateRandomSeed);
      el.yearRange.addEventListener("input", () => {
        state.selectedIndex = Number(el.yearRange.value);
        render();
      });
      document.querySelectorAll("button[data-mode]").forEach((button) => {
        button.addEventListener("click", () => {
          state.mode = button.dataset.mode;
          updateModeButtons();
          render();
        });
      });
      updateModeButtons();
    }

