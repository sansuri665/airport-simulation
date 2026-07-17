window.AIRPORT_FORECAST_DATA_READY = (() => {
  const loadScript = (source) => new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = source;
    script.onload = () => resolve(source);
    script.onerror = () => reject(new Error(`无法加载 ${source}`));
    document.head.appendChild(script);
  });
  const releaseScript = window.AIRPORT_VIEWER_MANIFEST?.scripts?.beijing_potential_passenger_forecast_viewer;
  const canonicalIndex = "./output/city_airport_potential_passenger_forecast/china_mainland/beijing_airport_system_forecast_index.js";
  return (async () => {
    await loadScript(releaseScript || canonicalIndex);
    if (!window.AIRPORT_FORECAST_LAZY_INDEX) {
      throw new Error("预测发布未注册轻量索引");
    }
  })();
})();
