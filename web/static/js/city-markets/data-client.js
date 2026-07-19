(() => {
  const EXPECTED_INDEX = "airport-city-market-viewer-lazy-index-v2";
  const EXPECTED_CHUNK = "airport-city-market-viewer-chunk-v2";
  const EXPECTED_CONTEXT_INDEX = "airport-city-market-context-index-v1";
  const EXPECTED_CONTEXT_CHUNK = "airport-city-market-context-chunk-v1";
  const apiClient = window.AirportApiClient;
  const seedContext = window.AirportSeedContext;
  const bootstrap = window.AirportCityMarketBootstrap;

  function validateIndex(index, context) {
    if (!index || index.schemaVersion !== EXPECTED_INDEX || !Array.isArray(index.cities)) {
      throw new Error("当前 Seed 缺少城市市场索引。");
    }
    if (Number(index.seed) !== context.seed) throw new Error("城市索引 Seed 与页面上下文不一致。");
    if (Number(index.finalYear) - Number(index.startYear) !== context.years) {
      throw new Error("城市索引年数与页面上下文不一致。");
    }
    return index;
  }

  function validateChunk(payload, cityMeta) {
    if (
      payload?.schemaVersion !== EXPECTED_CHUNK
      || payload?.marketId !== cityMeta.id
      || payload?.city?.id !== cityMeta.id
      || !Array.isArray(payload?.city?.points)
    ) {
      throw new Error("城市数据分块与当前 Seed 不匹配。");
    }
    return payload.city;
  }

  async function getIndex(context) {
    if (context.isCurrentViewerRelease) {
      const index = validateIndex(await bootstrap.loadReleaseIndex(), context);
      const release = window.AIRPORT_VIEWER_RELEASE_INFO || {};
      if (Number(release.seed) !== context.seed || Number(release.years) !== context.years) {
        throw new Error("Viewer Release 与页面 Seed 上下文不一致。");
      }
      return {...index, contextSource: "viewer_release", contextKey: context.slotId};
    }
    if (context.cacheStatus !== "ready") {
      throw new Error("当前 Seed 的城市缓存尚未生成或已经过期，请先返回首页生成当前世界。");
    }
    const query = new URLSearchParams({seed: String(context.seed), years: String(context.years)});
    const payload = await apiClient.requestJson(`/api/city-market-viewer/index?${query.toString()}`, {cache: "no-store"});
    if (!payload?.ok || payload.schemaVersion !== EXPECTED_CONTEXT_INDEX) {
      throw new Error(payload?.error || "城市缓存索引读取失败。");
    }
    seedContext.assertResponse(payload, "城市缓存索引");
    const index = validateIndex(payload.index, context);
    return {...index, contextSource: "seed_cache", contextKey: context.slotId};
  }

  async function loadCity(index, cityMeta, context) {
    if (index.contextKey !== context.slotId) throw new Error("城市内存索引与页面上下文不一致。");
    if (index.contextSource === "viewer_release") {
      const baseUrl = String(index.baseUrl || "");
      if (!baseUrl || !cityMeta?.file) throw new Error("城市数据分块地址无效。");
      const response = await fetch(new URL(cityMeta.file, baseUrl).href);
      if (!response.ok) throw new Error(`城市数据读取失败（HTTP ${response.status}）。`);
      return validateChunk(await response.json(), cityMeta);
    }
    const query = new URLSearchParams({
      seed: String(context.seed),
      years: String(context.years),
      city: cityMeta.id,
    });
    const payload = await apiClient.requestJson(`/api/city-market-viewer/chunk?${query.toString()}`, {cache: "no-store"});
    if (!payload?.ok || payload.schemaVersion !== EXPECTED_CONTEXT_CHUNK) {
      throw new Error(payload?.error || "城市缓存分块读取失败。");
    }
    seedContext.assertResponse(payload, "城市缓存分块");
    return validateChunk(payload.chunk, cityMeta);
  }

  function cacheKey(context, cityId) {
    return `${context.slotId}:${cityId}`;
  }

  window.AirportCityMarketData = Object.freeze({getIndex, loadCity, cacheKey});
})();
