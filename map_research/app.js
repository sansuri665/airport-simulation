(() => {
  "use strict";

  const SVG_NS = "http://www.w3.org/2000/svg";
  const VIEW = { width: 1200, height: 760, left: 40, right: 146, bottom: -10, top: 56 };
  const MAP_LAYOUT_SCALE = 9.9;
  const MAP_FOCUS = { lon: 112, lat: 31 };
  const MIN_ZOOM = 0.2;
  const POINT_LABEL_MIN_ZOOM = 0.6;
  const AIRPORT_MARKER_SIZE = 0.82;
  const AIRPORT_RADII = { ".point-hit": 18, ".point-halo": 11, ".point-core": 4.5 };
  const viewport = document.getElementById("viewport");
  const gridLayer = document.getElementById("gridLayer");
  const airportLayer = document.getElementById("airportLayer");
  const mapStage = document.getElementById("mapStage");
  const mapSvg = document.getElementById("mapSvg");
  const list = document.getElementById("airportList");
  const searchInput = document.getElementById("searchInput");
  const regionSelect = document.getElementById("regionSelect");
  const detailCard = document.getElementById("detailCard");
  const airportDetail = document.getElementById("airportDetail");
  const emptyDetail = document.getElementById("emptyDetail");
  const DEFAULT_VIEW = { x: -197.2, y: 77.6, scale: 1 };
  const state = { ...DEFAULT_VIEW, selected: null, filtered: AIRPORTS, regionScope: "global", dragging: false, pointer: null };
  const airportNodes = new Map();
  let airportMarkerScale = null;
  let selectedAirportNode = null;
  let regionAirportsCache = { scope: null, items: null };
  let searchFrame = 0;

  const byId = (id) => document.getElementById(id);
  const svgNode = (tag, attrs = {}) => {
    const node = document.createElementNS(SVG_NS, tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, String(value)));
    return node;
  };

  function rawProject({ lat, lon }) {
    const x = 50 + ((lon - VIEW.left) / (VIEW.right - VIEW.left)) * 1100;
    const y = 700 - ((lat - VIEW.bottom) / (VIEW.top - VIEW.bottom)) * 640;
    return { x, y };
  }

  function project(point) {
    const raw = rawProject(point);
    const focus = rawProject(MAP_FOCUS);
    return {
      x: focus.x + (raw.x - focus.x) * MAP_LAYOUT_SCALE,
      y: focus.y + (raw.y - focus.y) * MAP_LAYOUT_SCALE
    };
  }

  function renderGrid() {
    gridLayer.replaceChildren();
    for (let lon = 40; lon <= 150; lon += 10) {
      const x = project({ lat: VIEW.bottom, lon }).x;
      gridLayer.appendChild(svgNode("line", { x1: x, y1: 60, x2: x, y2: 700, class: "grid-line" }));
      const label = svgNode("text", { x: x + 4, y: 718, class: "grid-label" });
      label.textContent = `${lon}°E`;
      gridLayer.appendChild(label);
    }
    for (let lat = -10; lat <= 60; lat += 5) {
      const y = project({ lat, lon: VIEW.left }).y;
      gridLayer.appendChild(svgNode("line", { x1: 50, y1: y, x2: 1150, y2: y, class: "grid-line" }));
      const label = svgNode("text", { x: 26, y: y + 4, class: "grid-label" });
      label.textContent = `${lat}°N`;
      gridLayer.appendChild(label);
    }
  }

  function labelOffset(airport, index) {
    return [0, 28];
  }

  function renderAirports() {
    airportLayer.replaceChildren();
    airportNodes.clear();
    const fragment = document.createDocumentFragment();
    AIRPORTS.forEach((airport, index) => {
      const { x, y } = project(airport);
      const [dx, dy] = labelOffset(airport, index);
      const group = svgNode("g", { class: `airport-point${airport.reference ? " reference" : ""}`, "data-id": airport.id });
      group.appendChild(svgNode("circle", { cx: x, cy: y, r: 18 * AIRPORT_MARKER_SIZE, class: "point-hit" }));
      group.appendChild(svgNode("circle", { cx: x, cy: y, r: 11 * AIRPORT_MARKER_SIZE, class: "point-halo" }));
      group.appendChild(svgNode("circle", { cx: x, cy: y, r: 4.5 * AIRPORT_MARKER_SIZE, class: "point-core" }));
      const name = svgNode("text", { x: x + dx, y: y + dy, class: "point-label", style: `font-size:${12 * AIRPORT_MARKER_SIZE}px` });
      name.textContent = airport.name;
      group.appendChild(name);
      const code = svgNode("text", { x: x + dx, y: y + dy + 12, class: "point-code", style: `font-size:${9 * AIRPORT_MARKER_SIZE}px` });
      code.textContent = airport.code;
      group.appendChild(code);
      airportNodes.set(airport.id, group);
      fragment.appendChild(group);
    });
    airportLayer.appendChild(fragment);
    updateAirportMap();
  }

  function updateAirportMap() {
    const visibleIds = new Set(state.filtered.map((airport) => airport.id));
    airportNodes.forEach((node, airportId) => {
      node.style.display = visibleIds.has(airportId) ? "" : "none";
    });
    byId("visibleCount").textContent = `${state.filtered.length} / ${AIRPORTS.length} 个点位`;
    byId("airportCount").textContent = state.filtered.length;
  }

  function updateAirportSelection() {
    const nextNode = state.selected && airportNodes.get(state.selected);
    if (selectedAirportNode === nextNode) return;
    selectedAirportNode?.classList.remove("selected");
    selectedAirportNode = nextNode || null;
    if (selectedAirportNode) {
      selectedAirportNode.classList.add("selected");
      airportLayer.appendChild(selectedAirportNode);
    }
  }

  function updateListSelection() {
    list.querySelector(".airport-row.active")?.classList.remove("active");
    if (!state.selected) return;
    list.querySelector(`.airport-row[data-airport-id="${CSS.escape(state.selected)}"]`)?.classList.add("active");
  }

  function renderList() {
    list.replaceChildren();
    if (!state.filtered.length) {
      const empty = document.createElement("div");
      empty.className = "empty-list";
      empty.textContent = "没有匹配的机场";
      list.appendChild(empty);
      return;
    }
    const fragment = document.createDocumentFragment();
    state.filtered.forEach((airport) => {
      const row = document.createElement("button");
      row.type = "button";
      row.className = `airport-row${airport.reference ? " reference" : ""}`;
      row.dataset.airportId = airport.id;
      const dot = document.createElement("i");
      dot.className = "row-dot";
      const main = document.createElement("span");
      main.className = "row-main";
      const name = document.createElement("span");
      name.className = "row-name";
      name.textContent = airport.name;
      const city = document.createElement("span");
      city.className = "row-city";
      city.textContent = `${airport.city} · ${airport.status}`;
      main.append(name, city);
      const code = document.createElement("span");
      code.className = "row-code";
      code.textContent = airport.code;
      row.append(dot, main, code);
      fragment.appendChild(row);
    });
    list.appendChild(fragment);
    updateListSelection();
  }

  function updateDetail(airport) {
    if (!airport) {
      airportDetail.hidden = true;
      emptyDetail.hidden = false;
      return;
    }
    emptyDetail.hidden = true;
    airportDetail.hidden = false;
    byId("detailName").textContent = airport.name;
    byId("detailCity").textContent = airport.city;
    byId("detailCode").textContent = airport.code;
    byId("detailLat").textContent = airport.lat.toFixed(6);
    byId("detailLon").textContent = airport.lon.toFixed(6);
    byId("detailStatus").textContent = airport.status;
    byId("detailSource").textContent = `坐标来源：${airport.source}`;
  }

  function selectAirport(id, focus) {
    const airport = AIRPORTS.find((item) => item.id === id);
    if (!airport) return;
    state.selected = id;
    if (focus) focusAirport(airport);
    updateDetail(airport);
    updateAirportSelection();
    updateListSelection();
    detailCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function updateTransform() {
    viewport.setAttribute("transform", `translate(${state.x} ${state.y}) scale(${state.scale})`);
    airportLayer.classList.toggle("hide-point-labels", state.scale < POINT_LABEL_MIN_ZOOM);
    const nextMarkerScale = state.scale < POINT_LABEL_MIN_ZOOM ? POINT_LABEL_MIN_ZOOM / state.scale : 1;
    if (nextMarkerScale !== airportMarkerScale) {
      airportMarkerScale = nextMarkerScale;
      airportNodes.forEach((group) => {
        Object.entries(AIRPORT_RADII).forEach(([selector, radius]) => {
          group.querySelector(selector)?.setAttribute("r", String(radius * AIRPORT_MARKER_SIZE * airportMarkerScale));
        });
      });
    }
    byId("zoomReadout").textContent = `${Math.round(state.scale * 100)}%`;
  }

  function focusAirport(airport) {
    const point = project(airport);
    state.x = 600 - point.x * state.scale;
    state.y = 380 - point.y * state.scale;
    updateTransform();
  }

  function zoomAt(nextScale, clientX, clientY) {
    const rect = mapSvg.getBoundingClientRect();
    const pointX = ((clientX - rect.left) / rect.width) * 1200;
    const pointY = ((clientY - rect.top) / rect.height) * 760;
    const oldScale = state.scale;
    state.scale = Math.max(MIN_ZOOM, Math.min(12, nextScale));
    state.x = pointX - ((pointX - state.x) / oldScale) * state.scale;
    state.y = pointY - ((pointY - state.y) / oldScale) * state.scale;
    updateTransform();
  }

  function applySearch() {
    const query = searchInput.value.trim().toLowerCase();
    if (regionAirportsCache.scope !== state.regionScope) {
      regionAirportsCache = {
        scope: state.regionScope,
        items: state.regionScope === "global"
          ? AIRPORTS
          : AIRPORTS.filter((airport) => (airport.region || "china_mainland") === state.regionScope)
      };
    }
    const regionFiltered = regionAirportsCache.items;
    state.filtered = query
      ? regionFiltered.filter((airport) => [airport.id, airport.code, airport.name, airport.city].some((value) => value.toLowerCase().includes(query)))
      : regionFiltered;
    updateAirportMap();
    renderList();
  }

  function setRegion(region) {
    state.regionScope = region;
    regionSelect.value = region;
    applySearch();
    if (region === "global") {
      state.x = DEFAULT_VIEW.x;
      state.y = DEFAULT_VIEW.y;
      state.scale = DEFAULT_VIEW.scale;
      updateTransform();
    } else {
      centerOnItems(state.filtered);
    }
  }

  function centerOnItems(items) {
    if (!items.length) return;
    const points = items.map(project);
    const minX = Math.min(...points.map((point) => point.x));
    const maxX = Math.max(...points.map((point) => point.x));
    const minY = Math.min(...points.map((point) => point.y));
    const maxY = Math.max(...points.map((point) => point.y));
    state.scale = 1;
    state.x = 600 - (minX + maxX) / 2;
    state.y = 380 - (minY + maxY) / 2;
    updateTransform();
  }

  function resetView() {
    searchInput.value = "";
    state.regionScope = "global";
    regionSelect.value = "global";
    state.filtered = AIRPORTS;
    state.x = DEFAULT_VIEW.x;
    state.y = DEFAULT_VIEW.y;
    state.scale = DEFAULT_VIEW.scale;
    state.selected = null;
    updateDetail(null);
    updateTransform();
    updateAirportSelection();
    updateAirportMap();
    renderList();
  }

  mapStage.addEventListener("wheel", (event) => {
    event.preventDefault();
    zoomAt(state.scale * Math.exp(-event.deltaY * 0.001), event.clientX, event.clientY);
  }, { passive: false });

  airportLayer.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
    const airport = event.target.closest(".airport-point");
    if (!airport) return;
    event.preventDefault();
    event.stopPropagation();
    mapStage.focus();
    selectAirport(airport.dataset.id, true);
  });

  list.addEventListener("click", (event) => {
    const row = event.target.closest(".airport-row");
    if (row?.dataset.airportId) selectAirport(row.dataset.airportId, true);
  });

  mapStage.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
    mapStage.focus();
    state.dragging = true;
    state.pointer = { x: event.clientX, y: event.clientY };
    mapStage.classList.add("dragging");
    mapStage.setPointerCapture(event.pointerId);
  });
  mapStage.addEventListener("pointermove", (event) => {
    if (!state.dragging || !state.pointer) return;
    state.x += event.clientX - state.pointer.x;
    state.y += event.clientY - state.pointer.y;
    state.pointer = { x: event.clientX, y: event.clientY };
    updateTransform();
  });
  const endDrag = (event) => {
    if (!state.dragging) return;
    state.dragging = false;
    state.pointer = null;
    mapStage.classList.remove("dragging");
    if (event.pointerId !== undefined && mapStage.hasPointerCapture(event.pointerId)) mapStage.releasePointerCapture(event.pointerId);
  };
  mapStage.addEventListener("pointerup", endDrag);
  mapStage.addEventListener("pointercancel", endDrag);

  mapStage.addEventListener("keydown", (event) => {
    if (["INPUT", "TEXTAREA", "BUTTON"].includes(document.activeElement?.tagName)) return;
    const key = event.key.toLowerCase();
    const step = event.shiftKey ? 100 : 48;
    const moves = { w: [0, step], a: [step, 0], s: [0, -step], d: [-step, 0] };
    if (!moves[key]) return;
    event.preventDefault();
    state.x += moves[key][0];
    state.y += moves[key][1];
    updateTransform();
  });

  searchInput.addEventListener("input", () => {
    cancelAnimationFrame(searchFrame);
    searchFrame = requestAnimationFrame(applySearch);
  });
  regionSelect.addEventListener("change", () => setRegion(regionSelect.value));
  byId("resetButton").addEventListener("click", resetView);
  byId("zoomInButton").addEventListener("click", () => zoomAt(state.scale * 1.2, mapStage.getBoundingClientRect().left + mapStage.clientWidth / 2, mapStage.getBoundingClientRect().top + mapStage.clientHeight / 2));
  byId("zoomOutButton").addEventListener("click", () => zoomAt(state.scale / 1.2, mapStage.getBoundingClientRect().left + mapStage.clientWidth / 2, mapStage.getBoundingClientRect().top + mapStage.clientHeight / 2));

  renderGrid();
  updateTransform();
  renderAirports();
  renderList();
})();
