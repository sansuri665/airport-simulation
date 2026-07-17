(() => {
  const releaseScript = window.AIRPORT_VIEWER_MANIFEST?.scripts?.city_market_viewer;
  if (releaseScript) {
    document.write("<script src=" + JSON.stringify(releaseScript) + "></script>");
  } else {
    window.AIRPORT_CITY_MARKET_VIEWER_INDEX = null;
  }
})();
