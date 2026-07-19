(() => {
  let releasePromise = null;

  function loadReleaseData() {
    if (releasePromise) return releasePromise;
    releasePromise = new Promise((resolve, reject) => {
      const releaseScript = window.AIRPORT_VIEWER_MANIFEST?.scripts?.global_gdp_viewer;
      if (!releaseScript) {
        reject(new Error("当前 Viewer Manifest 没有全球 Viewer Release。"));
        return;
      }
      const script = document.createElement("script");
      script.src = new URL(releaseScript, window.location.href).href;
      script.async = true;
      script.addEventListener("load", resolve);
      script.addEventListener("error", () => reject(new Error("全球 Viewer Release 加载失败。")));
      document.head.append(script);
    });
    return releasePromise;
  }

  window.AirportGlobalViewerBootstrap = Object.freeze({loadReleaseData});
})();
