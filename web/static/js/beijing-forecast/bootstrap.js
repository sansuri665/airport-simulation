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
  const legacyData = "./output/city_airport_potential_passenger_forecast/china_mainland/beijing_airport_system_potential_passenger_forecast_viewer_data.js";
  return (async () => {
    try {
      await loadScript(releaseScript || canonicalIndex);
    } catch (error) {
      window.AIRPORT_FORECAST_LAZY_INDEX = null;
      await loadScript(legacyData);
    }
  })();
})();
