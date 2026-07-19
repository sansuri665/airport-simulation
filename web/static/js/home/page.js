(() => {
  const apiClient = window.AirportApiClient;
  const state = {
    workspace: null,
    retentionPlan: null,
    pendingConfirm: null,
    busy: false,
    generationJobId: null,
  };

  const byId = (id) => document.getElementById(id);
  const text = (id, value) => {
    const node = byId(id);
    if (node) node.textContent = value ?? "—";
  };

  const formatBytes = (value) => {
    const bytes = Math.max(0, Number(value) || 0);
    if (bytes < 1024) return `${bytes} B`;
    const units = ["KiB", "MiB", "GiB", "TiB"];
    let scaled = bytes / 1024;
    let unit = units[0];
    for (let index = 1; index < units.length && scaled >= 1024; index += 1) {
      scaled /= 1024;
      unit = units[index];
    }
    return `${scaled.toFixed(scaled >= 100 ? 0 : scaled >= 10 ? 1 : 2)} ${unit}`;
  };

  const statusLabel = (status) => ({
    published: "当前 Viewer Release",
    ready: "缓存可用",
    stale: "缓存需要更新",
    save_only: "仅有玩家存档",
    draft: "尚未生成",
  }[status] || status || "未知");

  const sourceLabel = (source) => ({
    registry: "工作区注册表",
    viewer_release: "Viewer Release",
    seed_cache: "Seed 缓存",
    player_save: "玩家存档",
  }[source] || source);

  const blockerLabel = (reason) => ({
    active_slot: "当前活动槽位",
    current_viewer_release: "当前 Viewer Release",
    pinned_cache: "固定缓存",
    cache_missing: "缓存已不存在",
    save_missing: "玩家存档已不存在",
    run_active: "Seed 正在运行",
    changed_since_preview: "预览后文件发生变化",
  }[reason] || reason);

  function notify(message, kind = "") {
    const node = byId("workspaceNotice");
    node.classList.remove("success", "error");
    if (kind) node.classList.add(kind);
    node.textContent = message;
  }

  async function requestJson(resource, options) {
    const payload = await apiClient.requestJson(resource, options);
    if (!payload || payload.ok === false) {
      throw new Error(payload?.error || "本地服务返回了无效响应");
    }
    return payload;
  }

  function postWorkspace(payload) {
    return requestJson("/api/seed-workspace", {
      method: "POST",
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  function mutationsAllowed() {
    return state.workspace?.registry?.status === "ready";
  }

  function updateControls() {
    const allowed = mutationsAllowed() && !state.busy;
    byId("suggestRandomSeedButton").disabled = !allowed;
    byId("importSeedButton").disabled = !allowed;
    byId("planRetentionButton").disabled = !allowed;
    byId("saveRetentionButton").disabled = !allowed;
    byId("generateWorldButton").disabled = !allowed || !state.workspace?.activeSlotId || Boolean(state.generationJobId);
    byId("applyRetentionButton").disabled = !allowed || !state.retentionPlan || state.retentionPlan.candidateCount === 0;
    document.querySelectorAll("[data-seed-action]").forEach((button) => {
      button.disabled = !allowed || button.dataset.disabled === "true";
    });
  }

  function setBusy(value) {
    state.busy = value;
    updateControls();
  }

  async function runAction(action, successMessage) {
    setBusy(true);
    try {
      const result = await action();
      state.retentionPlan = null;
      byId("retentionPlan").hidden = true;
      await Promise.all([loadWorkspace(), loadWorkspaceStatus()]);
      notify(successMessage || result.message, "success");
      return result;
    } catch (error) {
      notify(error.message, "error");
      throw error;
    } finally {
      setBusy(false);
    }
  }

  function deletionFallback(slotId) {
    const candidates = state.workspace?.slots.filter((slot) => slot.slotId !== slotId) || [];
    return candidates.find((slot) => slot.isCurrentViewerRelease)
      || candidates.find((slot) => slot.cacheStatus === "ready")
      || candidates[0]
      || null;
  }

  async function deleteSeedSlot(slotId) {
    setBusy(true);
    try {
      let workspace = state.workspace;
      let slot = workspace?.slots.find((item) => item.slotId === slotId);
      if (!slot) throw new Error("Seed 槽位已经不存在，请刷新后重试");
      if (slot.isCurrentViewerRelease) throw new Error("当前 Viewer Release 不能从 Seed 工作区删除");
      if (slot.isPinnedCache) throw new Error("固定缓存不能删除；请先取消固定状态");

      let revision = workspace.workspaceRevision;
      if (slot.isActive) {
        const fallback = deletionFallback(slotId);
        if (!fallback) throw new Error("唯一活动 Seed 不能删除；请先创建另一个槽位");
        const activated = await postWorkspace({
          action: "activate",
          slotId: fallback.slotId,
          expectedRevision: revision,
        });
        revision = activated.workspaceRevision;
      }

      for (const target of ["cache", "save"]) {
        const exists = target === "cache"
          ? slot.cacheStatus !== "missing"
          : slot.saveStatus !== "missing";
        if (!exists) continue;
        const preview = await postWorkspace({ action: "plan-delete", slotId, target });
        const plan = preview.plan;
        if (!plan.canExecute) {
          throw new Error(`当前不能删除 ${target === "cache" ? "Seed 缓存" : "玩家存档"}：${plan.blockers.map(blockerLabel).join("、")}`);
        }
        const deleted = await postWorkspace({
          action: "delete",
          target,
          slotId,
          expectedRevision: plan.workspaceRevision,
          planId: plan.planId,
          confirm: true,
        });
        revision = deleted.workspaceRevision;
      }

      await postWorkspace({
        action: "remove-slot",
        slotId,
        expectedRevision: revision,
      });
      state.retentionPlan = null;
      byId("retentionPlan").hidden = true;
      await Promise.all([loadWorkspace(), loadWorkspaceStatus()]);
      notify(`Seed ${slot.seed} 已删除；Viewer Release、正式 Run 和其它 Seed 未受影响`, "success");
    } catch (error) {
      await Promise.all([loadWorkspace(), loadWorkspaceStatus()]).catch(() => {});
      notify(error.message, "error");
      throw error;
    } finally {
      setBusy(false);
    }
  }

  function confirmDeleteSeed(slotId) {
    const slot = state.workspace?.slots.find((item) => item.slotId === slotId);
    if (!slot) return;
    const fallback = slot.isActive ? deletionFallback(slotId) : null;
    const lines = [
      `槽位：${slot.slotId}`,
      `将删除：${slot.cacheStatus === "missing" ? "无缓存" : `Seed 缓存 ${formatBytes(slot.cacheBytes)}`}；${slot.saveStatus === "missing" ? "无玩家存档" : `玩家存档 ${formatBytes(slot.saveBytes)}`}。`,
      "完成后会从工作区移除这个 Seed；Viewer Release、正式 Run 和其它 Seed 不会删除。",
    ];
    if (slot.isActive && fallback) {
      lines.splice(1, 0, `当前活动槽位会先切换到 Seed ${fallback.seed} / ${fallback.years} 年。`);
    }
    openConfirm(
      `确认删除 Seed ${slot.seed}`,
      lines,
      "删除整个 Seed",
      () => deleteSeedSlot(slotId).catch(() => {})
    );
  }

  function makeButton(label, action, slotId, disabled = false, danger = false) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `button ${danger ? "danger-button" : "quiet-button"}`;
    button.textContent = label;
    button.dataset.seedAction = action;
    button.dataset.slotId = slotId;
    button.dataset.disabled = disabled ? "true" : "false";
    button.disabled = disabled || state.busy;
    return button;
  }

  function makePill(label, kind = "") {
    const pill = document.createElement("span");
    pill.className = `fact-pill ${kind}`.trim();
    pill.textContent = label;
    return pill;
  }

  function renderSlot(slot) {
    const article = document.createElement("article");
    article.className = `seed-slot ${slot.isActive ? "active" : ""}`.trim();
    article.dataset.slotId = slot.slotId;

    const identity = document.createElement("div");
    const title = document.createElement("div");
    title.className = "seed-slot-title";
    title.textContent = slot.label || `Seed ${slot.seed}`;
    const subtitle = document.createElement("div");
    subtitle.className = "seed-slot-subtitle";
    subtitle.textContent = `Seed ${slot.seed} · ${slot.years} 年 · ${slot.slotId}`;
    identity.append(title, subtitle);

    const facts = document.createElement("div");
    facts.className = "seed-slot-facts";
    facts.append(makePill(statusLabel(slot.status), slot.cacheStatus === "stale" ? "warn" : "good"));
    facts.append(makePill(`缓存 ${formatBytes(slot.cacheBytes)}`));
    if (slot.hasPlayerSave) facts.append(makePill(`独立存档 ${formatBytes(slot.saveBytes)}`, "good"));
    if (slot.isActive) facts.append(makePill("当前活动", "protected"));
    if (slot.isCurrentViewerRelease) facts.append(makePill("Release 保护", "protected"));
    if (slot.isPinnedCache) facts.append(makePill("固定缓存", "protected"));

    const actions = document.createElement("div");
    actions.className = "slot-actions";
    actions.append(makeButton(slot.isActive ? "已激活" : "激活", "activate", slot.slotId, slot.isActive));
    const directDeleteBlocked = slot.protectedReasons.length > 0;
    if (slot.cacheStatus !== "missing") {
      actions.append(makeButton("清理缓存", "plan-cache", slot.slotId, directDeleteBlocked, true));
    }
    if (slot.saveStatus !== "missing") {
      actions.append(makeButton("删除存档", "plan-save", slot.slotId, directDeleteBlocked, true));
    }
    if (!slot.isCurrentViewerRelease && !slot.isPinnedCache) {
      const cannotDeleteOnlyActive = slot.isActive && !deletionFallback(slot.slotId);
      actions.append(makeButton("删除 Seed", "delete-seed", slot.slotId, cannotDeleteOnlyActive, true));
    }

    article.append(identity, facts, actions);
    return article;
  }

  function renderWorkspace(workspace) {
    state.workspace = workspace;
    const active = workspace.slots.find((slot) => slot.slotId === workspace.activeSlotId) || null;
    const health = byId("seedWorkspaceState");
    health.classList.remove("ready", "error");
    if (workspace.registry.status === "ready") {
      health.classList.add("ready");
      health.textContent = `${workspace.counts.slotCount} 个槽位 · 注册表可写`;
    } else {
      health.classList.add("error");
      health.textContent = `注册表 ${workspace.registry.status} · 已进入只读保护`;
    }
    text("activeSeedValue", active ? active.seed : "未选择");
    text("activeYearsValue", active ? `${active.years} 年` : "—");
    text("activeStatusValue", active ? statusLabel(active.status) : "—");
    text(
      "activeSourceValue",
      active ? active.discoveredFrom.map(sourceLabel).join(" / ") : workspace.activeSelectionSource
    );
    text("workspaceRevisionValue", workspace.workspaceRevision);
    byId("retentionInput").value = workspace.retention.maxCachedRuns;
    text(
      "cacheUsage",
      `${workspace.retention.cacheCount} 个缓存（${workspace.retention.staleCacheCount} 个需更新），共 ${formatBytes(workspace.retention.totalCacheBytes)} / ${workspace.retention.totalCacheFileCount} 个文件`
    );

    const list = byId("seedSlotList");
    list.replaceChildren(...workspace.slots.map(renderSlot));
    if (!workspace.slots.length) {
      const empty = document.createElement("div");
      empty.className = "workspace-notice";
      empty.textContent = "还没有 Seed 槽位，可以输入已知 Seed，或先随机生成一个。";
      list.append(empty);
    }
    const seedExplorerLink = byId("seedExplorerLink");
    const globalViewerLink = byId("globalViewerLink");
    const cityMarketsLink = byId("cityMarketsLink");
    const beijingForecastLink = byId("beijingForecastLink");
    if (active) {
      const query = new URLSearchParams({seed: String(active.seed), years: String(active.years)});
      seedExplorerLink.href = `/seed-explorer?${query.toString()}`;
      seedExplorerLink.removeAttribute("aria-disabled");
      if (active.canOpenGlobal) {
        globalViewerLink.href = `/global-gdp?${query.toString()}`;
        globalViewerLink.removeAttribute("aria-disabled");
        text(
          "globalViewerAction",
          active.isCurrentViewerRelease ? "查看当前 Viewer Release →" : "查看当前 Seed 缓存 →"
        );
      } else {
        globalViewerLink.href = "/";
        globalViewerLink.setAttribute("aria-disabled", "true");
        text("globalViewerAction", "当前 Seed 需要先生成 →");
      }
      if (active.canOpenCityMarkets) {
        cityMarketsLink.href = `/city-markets?${query.toString()}`;
        cityMarketsLink.removeAttribute("aria-disabled");
        text(
          "cityMarketsAction",
          active.isCurrentViewerRelease ? "查看当前 Viewer Release →" : "查看当前 Seed 缓存 →"
        );
      } else {
        cityMarketsLink.href = "/";
        cityMarketsLink.setAttribute("aria-disabled", "true");
        text("cityMarketsAction", "当前 Seed 需要先生成 →");
      }
      if (active.canOpenForecastPlayer) {
        beijingForecastLink.href = `/beijing-forecast?${query.toString()}`;
        beijingForecastLink.removeAttribute("aria-disabled");
        text(
          "beijingForecastAction",
          active.isCurrentViewerRelease ? "查看当前 Viewer Release →" : "查看当前 Seed 缓存 →"
        );
      } else {
        beijingForecastLink.href = "/";
        beijingForecastLink.setAttribute("aria-disabled", "true");
        text("beijingForecastAction", "当前 Seed 需要先生成 →");
      }
    } else {
      seedExplorerLink.href = "/";
      seedExplorerLink.setAttribute("aria-disabled", "true");
      globalViewerLink.href = "/";
      globalViewerLink.setAttribute("aria-disabled", "true");
      text("globalViewerAction", "请先选择 Seed →");
      cityMarketsLink.href = "/";
      cityMarketsLink.setAttribute("aria-disabled", "true");
      text("cityMarketsAction", "请先选择 Seed →");
      beijingForecastLink.href = "/";
      beijingForecastLink.setAttribute("aria-disabled", "true");
      text("beijingForecastAction", "请先选择 Seed →");
    }
    updateControls();
  }

  async function loadWorkspace() {
    const workspace = await requestJson("/api/seed-workspace", { cache: "no-store" });
    renderWorkspace(workspace);
    return workspace;
  }

  async function loadWorkspaceStatus() {
    const serviceState = byId("serviceState");
    try {
      const status = await requestJson("/api/workspace-status", { cache: "no-store" });
      const release = status.viewerRelease || {};
      serviceState.classList.remove("error");
      serviceState.classList.add("ready");
      text("serviceStateText", "本地服务正常");
      text("releaseMode", release.mode === "versioned_release" ? "版本化发布" : "发布不可用");
      text("releaseRun", release.runId || "—");
      text("releaseVariant", release.variant || "—");
      text("releaseSeed", release.seed ?? "—");
      text("releaseModel", release.modelVersion || `服务 ${status.modelVersion}`);
      text("releaseTime", release.generatedAt || "—");
      text("cachedRunCount", status.cachedRunCount ?? 0);
      text("saveCount", status.saveCount ?? 0);
    } catch (error) {
      serviceState.classList.add("error");
      text("serviceStateText", "无法读取本地服务状态");
      text("releaseMode", "状态不可用");
    }
  }

  function openConfirm(title, lines, confirmLabel, callback) {
    const dialog = byId("actionDialog");
    text("actionDialogTitle", title);
    const body = byId("actionDialogBody");
    body.replaceChildren();
    lines.forEach((line) => {
      const paragraph = document.createElement("p");
      paragraph.textContent = line;
      body.append(paragraph);
    });
    byId("actionDialogConfirm").textContent = confirmLabel;
    state.pendingConfirm = callback;
    if (typeof dialog.showModal === "function") dialog.showModal();
    else dialog.setAttribute("open", "");
  }

  function closeConfirm() {
    const dialog = byId("actionDialog");
    if (typeof dialog.close === "function") dialog.close();
    else dialog.removeAttribute("open");
  }

  async function previewDelete(slotId, target) {
    setBusy(true);
    try {
      const response = await postWorkspace({ action: "plan-delete", slotId, target });
      const plan = response.plan;
      if (!plan.canExecute) {
        notify(`当前不能清理：${plan.blockers.map(blockerLabel).join("、")}`, "error");
        return;
      }
      const targetLabel = target === "cache" ? "Seed 缓存" : "玩家存档";
      const preserved = plan.preserves.map(sourceLabel).join("、") || "无";
      openConfirm(
        `确认删除${targetLabel}`,
        [
          `槽位：${slotId}`,
          `将删除：${plan.path}（${formatBytes(plan.bytes)}，${plan.fileCount} 个文件）`,
          `明确保留：${preserved}。预览后只要文件、revision 或运行锁变化，执行就会拒绝。`,
        ],
        `删除${targetLabel}`,
        () => runAction(
          () => postWorkspace({
            action: "delete",
            target,
            slotId,
            expectedRevision: plan.workspaceRevision,
            planId: plan.planId,
            confirm: true,
          }),
          `${targetLabel}已删除；其他数据未受影响`
        )
      );
    } catch (error) {
      notify(error.message, "error");
    } finally {
      setBusy(false);
    }
  }

  async function previewRetention() {
    setBusy(true);
    try {
      const maximum = Number(byId("retentionInput").value);
      const response = await postWorkspace({ action: "plan-retention", maxCachedRuns: maximum });
      state.retentionPlan = response.plan;
      const plan = response.plan;
      byId("retentionPlan").hidden = false;
      text(
        "retentionPlanText",
        plan.candidateCount
          ? `会清理 ${plan.candidateCount} 个非活动、非 Release、非固定缓存，预计释放 ${formatBytes(plan.reclaimableBytes)}。玩家存档不会删除。`
          : "当前没有符合条件的缓存需要清理；保存上限不会删除任何文件。"
      );
      updateControls();
      notify("清理预览已生成，尚未删除任何文件");
    } catch (error) {
      notify(error.message, "error");
    } finally {
      setBusy(false);
    }
  }

  function confirmRetention() {
    const plan = state.retentionPlan;
    if (!plan || !plan.candidateCount) return;
    const names = plan.candidates.map((item) => item.slotId).join("、");
    openConfirm(
      "确认应用缓存保留策略",
      [
        `保留上限：${plan.maxCachedRuns} 个就绪缓存。`,
        `将清理：${names}。`,
        `预计释放 ${formatBytes(plan.reclaimableBytes)}；活动槽位、当前 Release、固定缓存和玩家存档均受保护。`,
      ],
      "应用并清理",
      () => runAction(
        () => postWorkspace({
          action: "apply-retention",
          maxCachedRuns: plan.maxCachedRuns,
          expectedRevision: plan.workspaceRevision,
          planId: plan.planId,
          confirm: true,
        }),
        "缓存保留策略已应用"
      )
    );
  }

  async function pollGeneration(jobId) {
    if (state.generationJobId !== jobId) return;
    try {
      const job = await requestJson(`/api/jobs/${encodeURIComponent(jobId)}`, { cache: "no-store" });
      const label = job.status === "queued" ? "等待后台执行" : job.status === "running" ? "正在生成世界" : job.status;
      text("generationStatus", `${label} · ${job.jobId}`);
      if (job.status === "complete") {
        state.generationJobId = null;
        text("generationStatus", job.result?.cached ? "缓存已存在，直接复用完成" : "世界生成完成，缓存已登记");
        await Promise.all([loadWorkspace(), loadWorkspaceStatus()]);
        notify("当前 Seed 世界已经可用", "success");
        updateControls();
        return;
      }
      if (job.status === "failed") {
        state.generationJobId = null;
        text("generationStatus", `生成失败：${job.error || "请查看服务日志"}`);
        notify("后台生成失败，现有数据没有被覆盖", "error");
        updateControls();
        return;
      }
      window.setTimeout(() => pollGeneration(jobId), 900);
    } catch (error) {
      state.generationJobId = null;
      text("generationStatus", `无法读取任务状态：${error.message}`);
      notify(error.message, "error");
      updateControls();
    }
  }

  async function generateActiveWorld() {
    const active = state.workspace?.slots.find((slot) => slot.slotId === state.workspace.activeSlotId);
    if (!active) return;
    setBusy(true);
    try {
      const job = await requestJson("/api/run-job", {
        method: "POST",
        cache: "no-store",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ seed: active.seed, years: active.years, force: false }),
      });
      state.generationJobId = job.jobId;
      text("generationStatus", job.deduplicated ? "已接入正在执行的同一任务" : "后台任务已提交");
      notify(`正在为 Seed ${active.seed} / ${active.years} 年生成世界`);
      pollGeneration(job.jobId);
    } catch (error) {
      notify(error.message, "error");
    } finally {
      setBusy(false);
    }
  }

  function selectedCreationYears() {
    return Number(byId("importYearsInput").value || 60);
  }

  function updateCreationMode() {
    const years = selectedCreationYears();
    text("newSeedModeValue", years === 60 ? "标准游戏" : "高级分析");
    text("newSeedYearsValue", Number.isFinite(years) ? `${years} 年` : "年数无效");
  }

  async function suggestRandomSeed() {
    setBusy(true);
    try {
      const years = selectedCreationYears();
      let suggestion = null;
      for (let attempt = 0; attempt < 8; attempt += 1) {
        const candidate = await requestJson("/api/random-seed", { cache: "no-store" });
        const occupied = state.workspace.slots.some(
          (slot) => Number(slot.seed) === Number(candidate.seed) && Number(slot.years) === years
        );
        if (!occupied) {
          suggestion = candidate.seed;
          break;
        }
      }
      if (suggestion === null) throw new Error("连续生成的随机 Seed 已被占用，请重试");
      byId("importSeedInput").value = String(suggestion);
      byId("importSeedInput").focus();
      byId("importSeedInput").select();
      notify(`已填入安全随机 Seed ${suggestion}；尚未创建槽位或运行模型`, "success");
    } catch (error) {
      notify(error.message, "error");
    } finally {
      setBusy(false);
    }
  }

  byId("seedCreateForm").addEventListener("submit", (event) => {
    event.preventDefault();
    const rawSeed = byId("importSeedInput").value.trim();
    if (!rawSeed) {
      notify("请输入 Seed，或先点击“随机生成”", "error");
      return;
    }
    const years = selectedCreationYears();
    runAction(
      () => postWorkspace({
        action: "import",
        seed: Number(rawSeed),
        years,
        expectedRevision: state.workspace.workspaceRevision,
      }),
      `Seed ${rawSeed} / ${years} 年已创建或复用并激活；模型尚未运行`
    ).catch(() => {});
  });

  byId("suggestRandomSeedButton").addEventListener("click", suggestRandomSeed);
  byId("importYearsInput").addEventListener("input", updateCreationMode);
  updateCreationMode();

  byId("seedSlotList").addEventListener("click", (event) => {
    const button = event.target.closest("[data-seed-action]");
    if (!button || button.disabled) return;
    const slotId = button.dataset.slotId;
    if (button.dataset.seedAction === "activate") {
      runAction(
        () => postWorkspace({
          action: "activate",
          slotId,
          expectedRevision: state.workspace.workspaceRevision,
        }),
        "活动 Seed 已切换；经营、全球、城市和预测入口已更新，已打开页面保持原上下文"
      ).catch(() => {});
    } else if (button.dataset.seedAction === "plan-cache") {
      previewDelete(slotId, "cache");
    } else if (button.dataset.seedAction === "plan-save") {
      previewDelete(slotId, "save");
    } else if (button.dataset.seedAction === "delete-seed") {
      confirmDeleteSeed(slotId);
    }
  });

  byId("generateWorldButton").addEventListener("click", generateActiveWorld);
  byId("planRetentionButton").addEventListener("click", previewRetention);
  byId("applyRetentionButton").addEventListener("click", confirmRetention);
  byId("saveRetentionButton").addEventListener("click", () => {
    runAction(
      () => postWorkspace({
        action: "set-retention",
        maxCachedRuns: Number(byId("retentionInput").value),
        expectedRevision: state.workspace.workspaceRevision,
      }),
      "缓存保留上限已保存，没有立即删除文件"
    ).catch(() => {});
  });

  byId("actionDialogConfirm").addEventListener("click", (event) => {
    event.preventDefault();
    const callback = state.pendingConfirm;
    state.pendingConfirm = null;
    closeConfirm();
    if (callback) Promise.resolve(callback()).catch(() => {});
  });
  byId("actionDialogCancel").addEventListener("click", () => {
    state.pendingConfirm = null;
  });
  byId("actionDialog").addEventListener("cancel", () => {
    state.pendingConfirm = null;
  });

  Promise.all([loadWorkspaceStatus(), loadWorkspace()]).catch((error) => {
    const workspaceState = byId("seedWorkspaceState");
    workspaceState.classList.add("error");
    workspaceState.textContent = "无法读取 Seed 工作区";
    notify(error.message, "error");
    updateControls();
  });
})();
