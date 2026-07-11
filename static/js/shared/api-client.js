(() => {
  async function requestJson(resource, options) {
    const response = await fetch(resource, options);
    return response.json();
  }

  window.AirportApiClient = Object.freeze({ requestJson });
})();
