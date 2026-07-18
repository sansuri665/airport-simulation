(() => {
  window.AIRPORT_GLOBAL_VIEWER_LOAD_ERROR = "";
  const releaseScript = window.AIRPORT_VIEWER_MANIFEST?.scripts?.global_gdp_viewer;
  const sources = releaseScript
    ? [releaseScript]
    : [
        "./output/global_macro/global_macro_feedback_viewer_data.js",
        "./output/regional_macro_reconciled/regional_macro_reconciled_viewer_data.js",
        "./output/global_macro/global_viewer_index.js",
      ];
  const errorMessage = "全球 Viewer 数据加载失败，请重新发布 Viewer。";
  const scriptTag = (source) => (
    `<script src=${JSON.stringify(source)} onerror="window.AIRPORT_GLOBAL_VIEWER_LOAD_ERROR='${errorMessage}'"></script>`
  );
  document.write(sources.map(scriptTag).join(""));
})();
