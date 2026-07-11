    window.addEventListener("resize", renderActiveChart);

    loadRows()
      .then(async (rows) => {
        state.canonicalData = captureViewerData(rows);
        state.dataLabel = "当前输出";
        await applyViewerData(state.canonicalData, "global", null);
        setupControls();
        render();
      })
      .catch((error) => {
        el.status.textContent = error.message;
        document.querySelector("main").innerHTML = `<div class="panel empty">没有找到可用数据。</div>`;
      });
