(() => {
  let releasePromise = null;

  function loadReleaseIndex() {
    if (releasePromise) return releasePromise;
    releasePromise = new Promise((resolve, reject) => {
      const releaseScript = window.AIRPORT_VIEWER_MANIFEST?.scripts?.city_market_viewer;
      if (!releaseScript) {
        reject(new Error("当前 Viewer 发布缺少城市市场入口。"));
        return;
      }
      window.AIRPORT_CITY_MARKET_VIEWER_INDEX = null;
      const script = document.createElement("script");
      script.src = new URL(releaseScript, window.location.href).href;
      script.async = true;
      script.addEventListener("load", () => resolve(window.AIRPORT_CITY_MARKET_VIEWER_INDEX));
      script.addEventListener("error", () => reject(new Error("当前 Viewer 城市市场索引加载失败。")));
      document.head.append(script);
    });
    return releasePromise;
  }

  window.AirportCityMarketBootstrap = Object.freeze({loadReleaseIndex});
})();
