window.AirportForecastDataClient = (() => {
  const EXPECTED_INDEX = "airport-forecast-viewer-lazy-index-v2";
  const EXPECTED_CHUNK = "airport-forecast-viewer-report-chunk-v2";
  const EXPECTED_CONTEXT_INDEX = "airport-forecast-viewer-context-index-v1";
  const EXPECTED_CONTEXT_REPORT = "airport-forecast-viewer-context-report-v1";
  const apiClient = window.AirportApiClient;
  const seedContext = window.AirportSeedContext;
  const bootstrap = window.AirportForecastBootstrap;

  function validateIndex(index, context, dataMode) {
    if (
      !index
      || index.schemaVersion !== EXPECTED_INDEX
      || index.dataMode !== dataMode
      || !Array.isArray(index.reports)
      || !Array.isArray(index.seeds)
    ) throw new Error("预测索引协议不匹配");
    if (index.seeds.length !== 1 || Number(index.seeds[0]) !== context.seed) {
      throw new Error("预测索引 Seed 与页面上下文不一致");
    }
    return index;
  }

  function validateChunk(chunk, index, reportId, context) {
    if (
      chunk?.schemaVersion !== EXPECTED_CHUNK
      || chunk?.dataMode !== index.dataMode
      || chunk?.reportId !== reportId
      || !Array.isArray(chunk?.rows)
    ) throw new Error(`报告 ${reportId} 的数据协议不匹配`);
    const report = index.reports.find((item) => item.reportId === reportId);
    if (!report || chunk.rows.length !== report.rowCount) {
      throw new Error(`报告 ${reportId} 的数据行数不匹配`);
    }
    if (chunk.rows.some((row) => Number(row.seed) !== context.seed)) {
      throw new Error(`报告 ${reportId} 的 Seed 与页面上下文不一致`);
    }
    return chunk.rows;
  }

  function sourceIdentity(context, source, payloadContext = null) {
    const identity = source === "viewer_release"
      ? String(payloadContext?.releaseId || context.releaseId || "current")
      : String(payloadContext?.cacheRunId || context.slotId);
    const revision = Number(payloadContext?.workspaceRevision ?? context.workspaceRevision);
    return `${context.slotId}:${source}:${identity}:r${revision}`;
  }

  async function getIndex(context, dataMode) {
    if (context.isCurrentViewerRelease) {
      const playerIndex = await bootstrap.loadPlayerIndex();
      const index = dataMode === "audit"
        ? await bootstrap.loadAuditIndex(playerIndex)
        : playerIndex;
      const release = window.AIRPORT_VIEWER_RELEASE_INFO || {};
      if (Number(release.seed) !== context.seed || Number(release.years) !== context.years) {
        throw new Error("Viewer Release 与预测页面上下文不一致");
      }
      return {
        ...validateIndex(index, context, dataMode),
        contextSource: "viewer_release",
        contextKey: sourceIdentity(context, "viewer_release", {releaseId: release.release_id}),
      };
    }
    if (context.cacheStatus !== "ready") {
      throw new Error("当前 Seed 的预测缓存尚未生成或已经过期，请先返回首页生成当前世界");
    }
    const query = new URLSearchParams({
      seed: String(context.seed),
      years: String(context.years),
      mode: dataMode,
    });
    const payload = await apiClient.requestJson(
      `/api/forecast-viewer/index?${query.toString()}`,
      {cache: "no-store"},
    );
    if (!payload?.ok || payload.schemaVersion !== EXPECTED_CONTEXT_INDEX) {
      throw new Error(payload?.message || payload?.error || "预测缓存索引读取失败");
    }
    seedContext.assertResponse(payload, "预测缓存索引");
    if (payload.context?.dataMode !== dataMode || payload.context?.source !== "seed_cache") {
      throw new Error("预测缓存索引来源或信息层级不匹配");
    }
    return {
      ...validateIndex(payload.index, context, dataMode),
      contextSource: "seed_cache",
      contextKey: sourceIdentity(context, "seed_cache", payload.context),
      sourceContext: payload.context,
    };
  }

  async function loadReport(index, reportId, context) {
    const report = (index?.reports || []).find((item) => item.reportId === reportId);
    if (!report) throw new Error(`预测目录中不存在报告 ${reportId}`);
    if (!String(index.contextKey || "").startsWith(`${context.slotId}:`)) {
      throw new Error("预测内存索引与页面 Seed 槽位不一致");
    }
    if (index.contextSource === "viewer_release") {
      const response = await fetch(new URL(report.file, index.baseUrl), {cache: "force-cache"});
      if (!response.ok) throw new Error(`报告 ${reportId} 加载失败：HTTP ${response.status}`);
      return validateChunk(await response.json(), index, reportId, context);
    }
    const query = new URLSearchParams({
      seed: String(context.seed),
      years: String(context.years),
      mode: index.dataMode,
      report: reportId,
    });
    const payload = await apiClient.requestJson(
      `/api/forecast-viewer/report?${query.toString()}`,
      {cache: "no-store"},
    );
    if (!payload?.ok || payload.schemaVersion !== EXPECTED_CONTEXT_REPORT) {
      throw new Error(payload?.message || payload?.error || `报告 ${reportId} 读取失败`);
    }
    seedContext.assertResponse(payload, `预测报告 ${reportId}`);
    if (
      payload.context?.dataMode !== index.dataMode
      || payload.context?.source !== "seed_cache"
      || sourceIdentity(context, "seed_cache", payload.context) !== index.contextKey
    ) throw new Error(`报告 ${reportId} 的来源上下文与索引不一致`);
    return validateChunk(payload.chunk, index, reportId, context);
  }

  async function readApiResponse(response) {
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || payload.ok !== true) {
      throw new Error(payload.message || payload.error || `本地服务请求失败：HTTP ${response.status}`);
    }
    return payload;
  }

  function assertCandidateContext(payload, context, source) {
    seedContext.assertResponse(payload, "候选报告");
    const actual = payload?.context || {};
    if (actual.source !== source || actual.dataMode !== "audit") {
      throw new Error("候选报告来源上下文不匹配");
    }
    if (source === "seed_cache" && actual.cacheRunId !== context.slotId) {
      throw new Error("候选报告缓存身份不匹配");
    }
    return payload;
  }

  async function loadCandidateCatalog(context, source) {
    const query = new URLSearchParams({
      seed: String(context.seed),
      years: String(context.years),
      source,
    });
    const response = await fetch(`/api/forecast-candidate-catalog?${query.toString()}`, {cache: "no-store"});
    return assertCandidateContext(await readApiResponse(response), context, source);
  }

  async function generateCandidate(request, context, source) {
    const response = await fetch("/api/forecast-candidate", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({...request, seed: context.seed, years: context.years, source}),
    });
    return assertCandidateContext(await readApiResponse(response), context, source);
  }

  return {getIndex, loadReport, loadCandidateCatalog, generateCandidate, sourceIdentity};
})();
