(() => {
  "use strict";

  const SVG_NS = "http://www.w3.org/2000/svg";
  const VIEW = { left: 40, right: 146, bottom: -10, top: 56 };
  const MAP_LAYOUT_SCALE = 52;
  const MAP_FOCUS = { lon: 112, lat: 31 };
  const MIN_ZOOM = 0.04;
  const MAX_ZOOM = 48;
  const STATION_LABEL_MIN_ZOOM = 0.22;
  const STATION_RADII = { ".railway-hit": 18, ".railway-halo": 9, ".railway-core": 4 };
  const LABEL_DENSE_KM = 7;
  const BEIJING_STATION_IDS = [
    "jingguang_01",
    "jingguang_fengtai",
    "jinghu_01",
    "jingha_beijing",
    "jingha_01",
    "jingha_shunyixi",
    "jingha_huairounan",
    "jingha_miyun",
    "jingbao_01",
    "jingbao_qinghe",
    "jingbao_changping",
    "jingbao_yanqing",
    "jingtang_01",
    "jingjin_yizhuang",
    "jingxiong_02",
    "jingxiong_03",
    "huaixing_capital_airport"
  ];

  const viewport = document.getElementById("viewport");
  const gridLayer = document.getElementById("gridLayer");
  const railwayLayer = document.getElementById("railwayLayer");
  const mapStage = document.getElementById("mapStage");
  const mapSvg = document.getElementById("mapSvg");
  const stationList = document.getElementById("stationList");
  const searchInput = document.getElementById("searchInput");
  const stationNote = document.getElementById("stationNote");
  const stations = collectStations();
  const state = {
    x: 0,
    y: 0,
    scale: 1,
    searchQuery: "",
    selectedStation: null,
    dragging: false,
    pointer: null,
    dragMoved: false
  };
  const stationNodes = new Map();
  const stationGeo = new Map();
  let denseStationIds = new Set();
  let stationMarkerScale = null;
  let searchFrame = 0;
  let skipClearOnPointerUp = false;

  function collectStations() {
    const wanted = new Set(BEIJING_STATION_IDS);
    const byId = new Map();
    RAILWAYS.forEach((line) => {
      if (line.type !== "high_speed") return;
      line.stations.forEach((station) => {
        if (!wanted.has(station.id) || byId.has(station.id)) return;
        byId.set(station.id, {
          id: station.id,
          name: station.name,
          city: station.city,
          lat: station.lat,
          lon: station.lon
        });
      });
    });
    return [...byId.values()].sort((a, b) => a.name.localeCompare(b.name, "zh-CN"));
  }

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

  function updateTransform() {
    viewport.setAttribute("transform", `translate(${state.x} ${state.y}) scale(${state.scale})`);
    railwayLayer.classList.toggle("hide-station-labels", state.scale < STATION_LABEL_MIN_ZOOM);
    const nextMarkerScale = state.scale < STATION_LABEL_MIN_ZOOM ? STATION_LABEL_MIN_ZOOM / state.scale : 1;
    if (nextMarkerScale !== stationMarkerScale) {
      stationMarkerScale = nextMarkerScale;
      stationNodes.forEach((group) => {
        Object.entries(STATION_RADII).forEach(([selector, radius]) => {
          group.querySelector(selector)?.setAttribute("r", String(radius * stationMarkerScale));
        });
      });
    }
    document.getElementById("zoomReadout").textContent = `${Math.round(state.scale * 100)}%`;
  }

  function distanceKm(a, b) {
    const toRad = Math.PI / 180;
    const dLat = (b.lat - a.lat) * toRad;
    const dLon = (b.lon - a.lon) * toRad;
    const lat1 = a.lat * toRad;
    const lat2 = b.lat * toRad;
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
    return 6371 * 2 * Math.asin(Math.min(1, Math.sqrt(h)));
  }

  function rebuildDenseStationIds() {
    const ids = [...stationGeo.keys()];
    const dense = new Set();
    for (let i = 0; i < ids.length; i += 1) {
      const a = stationGeo.get(ids[i]);
      for (let j = i + 1; j < ids.length; j += 1) {
        const b = stationGeo.get(ids[j]);
        if (distanceKm(a, b) <= LABEL_DENSE_KM) {
          dense.add(ids[i]);
          dense.add(ids[j]);
        }
      }
    }
    denseStationIds = dense;
  }

  function updateDenseLabels() {
    stationNodes.forEach((group, stationId) => {
      const label = group.querySelector(".railway-label");
      const suppress = denseStationIds.has(stationId) && state.selectedStation !== stationId;
      group.classList.toggle("label-suppressed", suppress);
      if (label) {
        if (suppress) label.setAttribute("display", "none");
        else label.removeAttribute("display");
      }
    });
  }

  function renderStations() {
    railwayLayer.replaceChildren();
    stationNodes.clear();
    stationGeo.clear();
    denseStationIds = new Set();
    const stationVisualLayer = svgNode("g", { class: "railway-station-visual-layer" });
    stations.forEach((station) => {
      const { x, y } = project(station);
      const group = svgNode("g", { class: "railway-station high_speed", "data-id": station.id });
      group.appendChild(svgNode("circle", { cx: x, cy: y, r: STATION_RADII[".railway-hit"], class: "railway-hit" }));
      group.appendChild(svgNode("circle", { cx: x, cy: y, r: STATION_RADII[".railway-halo"], class: "railway-halo" }));
      group.appendChild(svgNode("circle", { cx: x, cy: y, r: STATION_RADII[".railway-core"], class: "railway-core" }));
      const label = svgNode("text", { x, y: y + 32, class: "railway-label" });
      label.textContent = station.name;
      group.appendChild(label);
      stationNodes.set(station.id, group);
      stationGeo.set(station.id, { lat: station.lat, lon: station.lon });
      stationVisualLayer.appendChild(group);
    });
    railwayLayer.appendChild(stationVisualLayer);
    stationMarkerScale = null;
    rebuildDenseStationIds();
    updateMapSelection();
    updateTransform();
  }

  function updateMapSelection() {
    stationNodes.forEach((group, stationId) => {
      group.classList.toggle("selected", state.selectedStation === stationId);
    });
    updateDenseLabels();
  }

  function updateListSelection() {
    stationList.querySelectorAll(".railway-row").forEach((row) => {
      row.classList.toggle("active", row.dataset.stationId === state.selectedStation);
    });
    stationList.querySelector(".railway-row.active")?.scrollIntoView({ block: "nearest" });
  }

  function selectStation(stationId) {
    state.selectedStation = stationId;
    updateMapSelection();
    updateListSelection();
  }

  function clearSelection() {
    state.selectedStation = null;
    updateMapSelection();
    updateListSelection();
  }

  function visibleStations() {
    if (!state.searchQuery) return stations;
    return stations.filter((station) => [station.name, station.city].some((value) => String(value || "").toLowerCase().includes(state.searchQuery)));
  }

  function renderList() {
    stationList.replaceChildren();
    const matched = visibleStations();
    document.getElementById("stationCount").textContent = matched.length;
    stationNote.textContent = state.searchQuery
      ? `匹配到 ${matched.length} 个北京高速铁路站点，地图仍显示全部站点。`
      : `当前显示 ${stations.length} 个北京高速铁路站点。`;
    if (!matched.length) {
      const empty = document.createElement("div");
      empty.className = "empty-list";
      empty.textContent = "没有匹配的铁路站点";
      stationList.appendChild(empty);
      return;
    }
    const fragment = document.createDocumentFragment();
    matched.forEach((station) => {
      const row = document.createElement("button");
      row.type = "button";
      row.className = "airport-row railway-row railway-station-row";
      row.dataset.stationId = station.id;
      const dot = document.createElement("i");
      dot.className = "row-dot railway-row-dot";
      const main = document.createElement("span");
      main.className = "row-main";
      const name = document.createElement("span");
      name.className = "row-name";
      name.textContent = station.name;
      const detail = document.createElement("span");
      detail.className = "row-city";
      detail.textContent = station.city;
      main.append(name, detail);
      row.append(dot, main);
      fragment.appendChild(row);
    });
    stationList.appendChild(fragment);
    updateListSelection();
  }

  function fitStations(items, scaleOverride) {
    if (!items.length) return;
    const points = items.map(project);
    const minX = Math.min(...points.map((point) => point.x));
    const maxX = Math.max(...points.map((point) => point.x));
    const minY = Math.min(...points.map((point) => point.y));
    const maxY = Math.max(...points.map((point) => point.y));
    const spanX = Math.max(maxX - minX, 1);
    const spanY = Math.max(maxY - minY, 1);
    state.scale = scaleOverride ?? Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, Math.min(1040 / spanX, 600 / spanY)));
    state.x = 600 - ((minX + maxX) / 2) * state.scale;
    state.y = 380 - ((minY + maxY) / 2) * state.scale;
    updateTransform();
  }

  function resetView() {
    searchInput.value = "";
    state.searchQuery = "";
    state.selectedStation = null;
    renderStations();
    renderList();
    fitStations(stations);
  }

  function zoomAt(nextScale, clientX, clientY) {
    const rect = mapSvg.getBoundingClientRect();
    const pointX = ((clientX - rect.left) / rect.width) * 1200;
    const pointY = ((clientY - rect.top) / rect.height) * 760;
    const oldScale = state.scale;
    state.scale = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, nextScale));
    state.x = pointX - ((pointX - state.x) / oldScale) * state.scale;
    state.y = pointY - ((pointY - state.y) / oldScale) * state.scale;
    updateTransform();
  }

  mapStage.addEventListener("wheel", (event) => {
    event.preventDefault();
    zoomAt(state.scale * Math.exp(-event.deltaY * 0.001), event.clientX, event.clientY);
  }, { passive: false });

  railwayLayer.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
    const station = event.target.closest(".railway-station");
    if (!station) return;
    event.preventDefault();
    event.stopPropagation();
    skipClearOnPointerUp = true;
    selectStation(station.dataset.id);
  });

  stationList.addEventListener("click", (event) => {
    const row = event.target.closest(".railway-row");
    if (!row?.dataset.stationId) return;
    const station = stations.find((item) => item.id === row.dataset.stationId);
    selectStation(row.dataset.stationId);
    if (station) fitStations([station], 1);
  });

  mapStage.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
    skipClearOnPointerUp = false;
    mapStage.focus();
    state.dragging = true;
    state.dragMoved = false;
    state.pointer = { x: event.clientX, y: event.clientY };
    mapStage.classList.add("dragging");
    mapStage.setPointerCapture(event.pointerId);
  });
  mapStage.addEventListener("pointermove", (event) => {
    if (!state.dragging || !state.pointer) return;
    state.x += event.clientX - state.pointer.x;
    state.y += event.clientY - state.pointer.y;
    if (Math.abs(event.clientX - state.pointer.x) > 3 || Math.abs(event.clientY - state.pointer.y) > 3) state.dragMoved = true;
    state.pointer = { x: event.clientX, y: event.clientY };
    updateTransform();
  });
  const endDrag = (event) => {
    if (!state.dragging) return;
    state.dragging = false;
    state.pointer = null;
    mapStage.classList.remove("dragging");
    if (event.pointerId !== undefined && mapStage.hasPointerCapture(event.pointerId)) mapStage.releasePointerCapture(event.pointerId);
    if (!state.dragMoved && !skipClearOnPointerUp) clearSelection();
    skipClearOnPointerUp = false;
  };
  mapStage.addEventListener("pointerup", endDrag);
  mapStage.addEventListener("pointercancel", endDrag);

  mapStage.addEventListener("keydown", (event) => {
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
    state.searchQuery = searchInput.value.trim().toLowerCase();
    cancelAnimationFrame(searchFrame);
    searchFrame = requestAnimationFrame(renderList);
  });
  document.getElementById("resetButton").addEventListener("click", resetView);
  document.getElementById("zoomInButton").addEventListener("click", () => zoomAt(state.scale * 1.2, mapStage.getBoundingClientRect().left + mapStage.clientWidth / 2, mapStage.getBoundingClientRect().top + mapStage.clientHeight / 2));
  document.getElementById("zoomOutButton").addEventListener("click", () => zoomAt(state.scale / 1.2, mapStage.getBoundingClientRect().left + mapStage.clientWidth / 2, mapStage.getBoundingClientRect().top + mapStage.clientHeight / 2));

  renderGrid();
  renderStations();
  renderList();
  fitStations(stations);
})();
