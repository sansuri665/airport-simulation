(() => {
  const apiClient = window.AirportApiClient;
  const state = {
    context: null,
    workspace: null,
  };

  function integer(value, label, minimum, maximum = null) {
    const number = Number(value);
    if (!Number.isInteger(number) || number < minimum || (maximum !== null && number > maximum)) {
      const range = maximum === null ? `${minimum} 以上` : `${minimum}–${maximum}`;
      throw new Error(`${label} 必须是 ${range}的整数`);
    }
    return number;
  }

  function identityFromUrl() {
    const url = new URL(window.location.href);
    const seedText = url.searchParams.get("seed");
    const yearsText = url.searchParams.get("years");
    if (seedText === null && yearsText === null) return null;
    if (seedText === null || yearsText === null) {
      throw new Error("页面地址必须同时包含 seed 和 years");
    }
    return {
      seed: integer(seedText, "Seed", 0),
      years: integer(yearsText, "年数", 5, 90),
    };
  }

  function slotFor(workspace, identity) {
    return workspace.slots.find(
      (slot) => Number(slot.seed) === identity.seed && Number(slot.years) === identity.years
    ) || null;
  }

  function contextFrom(slot, workspace, initialRevision) {
    return {
      seed: Number(slot.seed),
      years: Number(slot.years),
      slotId: slot.slotId,
      status: slot.status,
      cacheStatus: slot.cacheStatus,
      saveStatus: slot.saveStatus,
      hasPlayerSave: Boolean(slot.hasPlayerSave),
      isCurrentViewerRelease: Boolean(slot.isCurrentViewerRelease),
      availableSources: [...(slot.availableSources || [])],
      workspaceRevision: initialRevision,
      currentWorkspaceRevision: Number(workspace.workspaceRevision),
      activeSlotId: workspace.activeSlotId,
      isWorkspaceActive: workspace.activeSlotId === slot.slotId,
    };
  }

  async function readWorkspace() {
    const workspace = await apiClient.requestJson("/api/seed-workspace", {cache: "no-store"});
    if (!workspace?.ok) throw new Error(workspace?.error || "无法读取 Seed 工作区");
    return workspace;
  }

  async function resolve() {
    const workspace = await readWorkspace();
    let identity = identityFromUrl();
    if (identity === null) {
      const active = workspace.slots.find((slot) => slot.slotId === workspace.activeSlotId) || null;
      if (!active) throw new Error("首页尚未选择 Seed，请先返回 Seed 中心");
      identity = {seed: Number(active.seed), years: Number(active.years)};
      const url = new URL(window.location.href);
      url.searchParams.set("seed", String(identity.seed));
      url.searchParams.set("years", String(identity.years));
      window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
    }
    const slot = slotFor(workspace, identity);
    if (!slot) throw new Error(`工作区没有 Seed ${identity.seed} / ${identity.years} 年槽位`);
    state.workspace = workspace;
    state.context = contextFrom(slot, workspace, Number(workspace.workspaceRevision));
    return {...state.context};
  }

  function current() {
    if (!state.context) throw new Error("Seed 上下文尚未就绪");
    return {...state.context};
  }

  function requestBody(extra = {}) {
    const context = current();
    return {...extra, seed: context.seed, years: context.years};
  }

  function assertResponse(payload, label = "服务响应") {
    const context = current();
    const candidates = [payload, payload?.context, payload?.result, payload?.summary, payload?.save]
      .filter((candidate) => candidate && typeof candidate === "object");
    for (const candidate of candidates) {
      if (candidate.seed !== undefined && Number(candidate.seed) !== context.seed) {
        throw new Error(`${label} Seed 与当前页面不一致，已拒绝渲染`);
      }
      if (candidate.years !== undefined && Number(candidate.years) !== context.years) {
        throw new Error(`${label} 年数与当前页面不一致，已拒绝渲染`);
      }
      if (candidate.slotId !== undefined && String(candidate.slotId) !== context.slotId) {
        throw new Error(`${label} 槽位与当前页面不一致，已拒绝渲染`);
      }
      if (candidate.cacheRunId !== undefined && String(candidate.cacheRunId) !== context.slotId) {
        throw new Error(`${label} 缓存身份与当前页面不一致，已拒绝渲染`);
      }
    }
    return payload;
  }

  async function refresh() {
    const previous = current();
    const workspace = await readWorkspace();
    const slot = slotFor(workspace, previous);
    state.workspace = workspace;
    if (slot) {
      state.context = contextFrom(slot, workspace, previous.workspaceRevision);
    } else {
      state.context = {
        ...previous,
        status: "missing",
        cacheStatus: "missing",
        saveStatus: "missing",
        hasPlayerSave: false,
        availableSources: [],
        currentWorkspaceRevision: Number(workspace.workspaceRevision),
        activeSlotId: workspace.activeSlotId,
        isWorkspaceActive: false,
      };
    }
    return {
      context: {...state.context},
      workspaceRevisionChanged: Number(workspace.workspaceRevision) !== previous.workspaceRevision,
      activeSlotChanged: workspace.activeSlotId !== previous.slotId,
      slotMissing: !slot,
    };
  }

  function href(path, context = current()) {
    const url = new URL(path, window.location.origin);
    url.searchParams.set("seed", String(context.seed));
    url.searchParams.set("years", String(context.years));
    return `${url.pathname}${url.search}`;
  }

  window.AirportSeedContext = Object.freeze({
    resolve,
    current,
    requestBody,
    assertResponse,
    refresh,
    href,
  });
})();
