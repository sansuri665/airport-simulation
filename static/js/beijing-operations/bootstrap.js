(() => {
  const releaseScript = window.AIRPORT_VIEWER_MANIFEST?.scripts?.beijing_airport_operations_viewer;
  const fallbackCheck = '<script>if (!window.AIRPORT_OPERATIONS_VIEWER_LAZY_INDEX && !window.CITY_AIRPORT_VALUATION_FORECAST_DATA) { document.write(document.getElementById("legacyBeijingOperationsDataScripts").innerHTML); }</script>';
  if (releaseScript) {
    document.write("<script src=" + JSON.stringify(releaseScript) + "></script>" + fallbackCheck);
  } else {
    document.write(
      '<script src="./output/city_airport_quarterly_operations/china_mainland/beijing_airport_system_quarterly_operations_viewer_data.js"></script>'
      + '<script src="./output/city_airport_financial_state/china_mainland/beijing_airport_system_financial_state_viewer_data.js"></script>'
      + '<script src="./output/city_airport_quarterly_operations/china_mainland/beijing_airport_system_operations_index.js"></script>'
      + fallbackCheck
    );
  }
})();
