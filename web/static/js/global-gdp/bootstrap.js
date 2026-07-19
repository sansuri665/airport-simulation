(() => {
  window.AIRPORT_GLOBAL_VIEWER_LOAD_ERROR = "";
  const releaseScript = window.AIRPORT_VIEWER_MANIFEST?.scripts?.global_gdp_viewer;
  const errorMessage = "全球 Viewer 数据加载失败，请重新发布 Viewer。";
  if (!releaseScript) {
    window.AIRPORT_GLOBAL_VIEWER_LOAD_ERROR = "当前 Viewer Manifest 没有全球 Viewer Release。";
    return;
  }
  window.addEventListener("error", (event) => {
    if (event.target?.dataset?.airportGlobalRelease === "true") {
      window.AIRPORT_GLOBAL_VIEWER_LOAD_ERROR = errorMessage;
    }
  }, true);
  document.write(
    `<script data-airport-global-release="true" src=${JSON.stringify(releaseScript)}><\/script>`
  );
})();
