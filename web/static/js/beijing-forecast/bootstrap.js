window.AIRPORT_FORECAST_DATA_READY = (() => {
  const loadScript = (source) => new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = source;
    script.onload = () => resolve(source);
    script.onerror = () => reject(new Error(`无法加载 ${source}`));
    document.head.appendChild(script);
  });
  const releaseScript = window.AIRPORT_VIEWER_MANIFEST?.scripts?.beijing_potential_passenger_forecast_viewer;
  return (async () => {
    if (!releaseScript) {
      throw new Error("当前 Viewer Manifest 没有预测 Viewer Release");
    }
    await loadScript(releaseScript);
    if (!window.AIRPORT_FORECAST_LAZY_INDEX) {
      throw new Error("预测发布未注册轻量索引");
    }
  })();
})();
