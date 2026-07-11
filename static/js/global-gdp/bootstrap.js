(() => {
  const releaseScript = window.AIRPORT_VIEWER_MANIFEST?.scripts?.global_gdp_viewer;
  const fallbackCheck = '<script>if (!window.AIRPORT_GLOBAL_VIEWER_LAZY_INDEX && !Object.keys(window.REGIONAL_MACRO_DATASETS || {}).length) { document.write(document.getElementById("legacyGlobalViewerDataScripts").innerHTML); }</script>';
  if (releaseScript) {
    document.write("<script src=" + JSON.stringify(releaseScript) + "></script>" + fallbackCheck);
  } else {
    document.write(
      '<script src="./output/global_macro/global_macro_feedback_viewer_data.js"></script>'
      + '<script src="./output/regional_macro_reconciled/regional_macro_reconciled_viewer_data.js"></script>'
      + '<script src="./output/global_macro/global_viewer_index.js"></script>'
      + fallbackCheck
    );
  }
})();
