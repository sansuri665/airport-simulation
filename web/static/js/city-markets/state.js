(() => {
  window.AirportCityMarketState = {
    index: null,
    selectedCityId: null,
    selectedCity: null,
    selectedYear: null,
    marketScope: "total",
    sortKey: "serviceable",
    search: "",
    loadToken: 0,
    cityCache: new Map(),
  };
})();
