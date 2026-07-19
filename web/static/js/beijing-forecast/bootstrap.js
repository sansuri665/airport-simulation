(() => {
  let playerPromise = null;
  let auditPromise = null;

  const loadScript = (source) => new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = source;
    script.async = true;
    script.addEventListener("load", () => resolve(source));
    script.addEventListener("error", () => reject(new Error(`无法加载 ${source}`)));
    document.head.appendChild(script);
  });

  function loadPlayerIndex() {
    if (playerPromise) return playerPromise;
    playerPromise = (async () => {
      const releaseScript = window.AIRPORT_VIEWER_MANIFEST?.scripts?.beijing_potential_passenger_forecast_viewer;
      if (!releaseScript) throw new Error("当前 Viewer Release 缺少预测入口");
      window.AIRPORT_FORECAST_LAZY_INDEX = null;
      await loadScript(new URL(releaseScript, window.location.href).href);
      if (!window.AIRPORT_FORECAST_LAZY_INDEX) {
        throw new Error("预测 Release 未注册玩家索引");
      }
      return window.AIRPORT_FORECAST_LAZY_INDEX;
    })();
    return playerPromise;
  }

  function loadAuditIndex(playerIndex) {
    if (auditPromise) return auditPromise;
    auditPromise = (async () => {
      const index = playerIndex || await loadPlayerIndex();
      if (window.AIRPORT_FORECAST_AUDIT_LAZY_INDEX) {
        return window.AIRPORT_FORECAST_AUDIT_LAZY_INDEX;
      }
      if (!index?.auditIndexUrl) {
        throw new Error("当前 Viewer Release 未提供独立开发审计入口");
      }
      await loadScript(index.auditIndexUrl);
      if (!window.AIRPORT_FORECAST_AUDIT_LAZY_INDEX) {
        throw new Error("开发审计索引没有正确注册");
      }
      return window.AIRPORT_FORECAST_AUDIT_LAZY_INDEX;
    })();
    return auditPromise;
  }

  window.AirportForecastBootstrap = Object.freeze({loadPlayerIndex, loadAuditIndex});
})();
