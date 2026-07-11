    function init() {
      const seeds = [...new Set(rawRows.map((row) => num(row.seed)))].sort((a, b) => a - b);
      if (!rawRows.length || !seeds.length) {
        document.querySelector("main").innerHTML = `<div class="empty">No quarterly operations data found</div>`;
        el.statusText.textContent = "no data";
        return;
      }
      state.seed = seeds[0];
      el.seedSelect.innerHTML = seeds.map((seed) => `<option value="${seed}">seed ${seed}</option>`).join("");
      state.selectedYear = Math.min(...rawRows.filter((row) => num(row.seed) === state.seed).map((row) => num(row.year)));

      el.seedSelect.addEventListener("change", () => {
        state.seed = num(el.seedSelect.value);
        const seedYears = rawRows.filter((row) => num(row.seed) === state.seed).map((row) => num(row.year));
        state.selectedYear = Math.min(...seedYears);
        render();
      });
      el.financeScopeSelect.addEventListener("change", () => {
        state.financeScope = el.financeScopeSelect.value;
        render();
      });
      el.chartModeSwitch.querySelectorAll("button").forEach((button) => {
        button.addEventListener("click", async () => {
          const nextMode = button.dataset.chartMode;
          try {
            if (nextMode === "valuation") await ensureValuationLoaded();
            state.chartMode = nextMode;
            render();
          } catch (error) {
            el.statusText.textContent = error.message;
          }
        });
      });
      el.financeSideSwitch.querySelectorAll("button").forEach((button) => {
        button.addEventListener("click", () => {
          state.financeSide = button.dataset.financeSide;
          render();
        });
      });
      el.financeYearRange.addEventListener("input", () => {
        const data = chartRowsForMode(annualRows());
        if (!data.length) return;
        const target = num(el.financeYearRange.value);
        state.selectedYear = data.reduce(
          (closest, row) => Math.abs(row.year - target) < Math.abs(closest - target) ? row.year : closest,
          data[0].year
        );
        render();
      });

      render();
    }

    init();
