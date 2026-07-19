    window.addEventListener("resize", renderActiveChart);

    function renderGlobalContext() {
      const context = state.seedContext;
      if (!context) return;
      const source = state.activeData?.contextSource === "viewer_release"
        ? "Viewer Release"
        : context.cacheStatus === "ready" ? "Seed 计算缓存" : "数据不可用";
      document.getElementById("contextMeta").textContent = `Seed ${context.seed} · ${context.years} 年`;
      document.getElementById("contextSource").textContent = `${source} · 槽位 ${context.slotId} · revision ${context.workspaceRevision}（当前 ${context.currentWorkspaceRevision}）`;
      document.getElementById("contextChangeNotice").hidden = !state.contextChanged;
      document.getElementById("cityMarketsLink").href = sharedSeedContext.href("/city-markets", context);
    }

    async function refreshGlobalContext() {
      try {
        const refreshed = await sharedSeedContext.refresh();
        state.seedContext = refreshed.context;
        state.contextChanged = refreshed.activeSlotChanged || refreshed.slotMissing;
        renderGlobalContext();
      } catch (_error) {
        state.contextChanged = true;
        document.getElementById("contextChangeNotice").hidden = false;
      }
    }

    async function startGlobalViewer() {
      try {
        state.seedContext = await sharedSeedContext.resolve();
        state.contextChanged = !state.seedContext.isWorkspaceActive;
        renderGlobalContext();
        state.releaseData = await loadViewerData(state.seedContext);
        state.dataLabel = state.releaseData.contextSource === "viewer_release"
          ? "Viewer Release"
          : "Seed 缓存";
        await applyViewerData(state.releaseData, "global", state.seedContext.seed);
        renderGlobalContext();
        setupControls();
        render();
      } catch (error) {
        el.status.textContent = error.message;
        document.querySelector("main").innerHTML = `<div class="panel empty">没有找到可用数据。请返回首页选择槽位；缓存槽位需要先生成当前世界。</div>`;
      }
    }

    startGlobalViewer();
    window.setInterval(refreshGlobalContext, 2500);
