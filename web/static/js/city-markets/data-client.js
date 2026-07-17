(() => {
  const EXPECTED_INDEX = "airport-city-market-viewer-lazy-index-v2";
  const EXPECTED_CHUNK = "airport-city-market-viewer-chunk-v2";

  function getIndex() {
    const index = window.AIRPORT_CITY_MARKET_VIEWER_INDEX;
    if (!index || index.schemaVersion !== EXPECTED_INDEX || !Array.isArray(index.cities)) {
      throw new Error("当前 Viewer 发布缺少城市市场数据，请重新发布 60 年 Viewer。");
    }
    return index;
  }

  async function loadCity(index, cityMeta) {
    const baseUrl = String(index.baseUrl || "");
    if (!baseUrl || !cityMeta?.file) throw new Error("城市数据分块地址无效。");
    const response = await fetch(new URL(cityMeta.file, baseUrl).href, { cache: "no-store" });
    if (!response.ok) throw new Error(`城市数据读取失败（HTTP ${response.status}）。`);
    const payload = await response.json();
    if (
      payload?.schemaVersion !== EXPECTED_CHUNK
      || payload?.marketId !== cityMeta.id
      || payload?.city?.id !== cityMeta.id
      || !Array.isArray(payload?.city?.points)
    ) {
      throw new Error("城市数据分块与当前发布不匹配。");
    }
    return payload.city;
  }

  window.AirportCityMarketData = { getIndex, loadCity };
})();
