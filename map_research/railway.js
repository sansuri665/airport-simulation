(() => {
  "use strict";

  const SVG_NS = "http://www.w3.org/2000/svg";
  const VIEW = { left: 40, right: 146, bottom: -10, top: 56 };
  const MAP_LAYOUT_SCALE = 9.9;
  const MAP_FOCUS = { lon: 112, lat: 31 };
  const MIN_ZOOM = 0.2;
  const STATION_LABEL_MIN_ZOOM = 0.6;
  const STATION_RADII = { ".railway-hit": 18, ".railway-halo": 9, ".railway-core": 4 };
  const viewport = document.getElementById("viewport");
  const gridLayer = document.getElementById("gridLayer");
  const railwayLayer = document.getElementById("railwayLayer");
  const mapStage = document.getElementById("mapStage");
  const mapSvg = document.getElementById("mapSvg");
  const regionSelect = document.getElementById("regionSelect");
  const regionReadout = document.getElementById("regionReadout");
  const railwayList = document.getElementById("railwayList");
  const searchInput = document.getElementById("searchInput");
  const lineModeButton = document.getElementById("lineModeButton");
  const stationModeButton = document.getElementById("stationModeButton");
  const railwayNote = document.getElementById("railwayNote");
  const DEFAULT_VIEW = { x: -197.2, y: 77.6, scale: 1 };
  const state = { ...DEFAULT_VIEW, filtered: RAILWAYS, searchQuery: "", regionScope: "global", dataMode: "lines", selectedLine: null, selectedStation: null, dragging: false, pointer: null, dragMoved: false };
  let displayedLinesCache = null;
  let stationRecordsCache = null;
  let routeVisualLayer = null;
  let stationVisualLayer = null;
  const routeNodes = new Map();
  const stationNodes = new Map();
  const stationLineIds = new Map();
  let stationMarkerScale = null;
  let searchFrame = 0;

  const regionLabels = Object.fromEntries([...regionSelect.options].map((option) => [option.value, option.textContent]));
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

  function getDisplayedStations(line) {
    if (state.regionScope === "global" || !line.regions) return line.stations;
    if (!line.regions.includes(state.regionScope)) return [];

    const displayed = [];
    line.stations.forEach((station, index) => {
      const next = line.stations[index + 1];
      const stationRegion = station.region || line.region;
      const nextRegion = next && (next.region || line.region);
      if (stationRegion === state.regionScope) displayed.push(station);
      if (next && stationRegion !== nextRegion && (stationRegion === state.regionScope || nextRegion === state.regionScope)) {
        displayed.push({
          id: `${line.id}__boundary__${state.regionScope}`,
          name: line.boundaryLabel || "区域交界中点",
          city: "区域交界点",
          city_id: null,
          region: state.regionScope,
          isBoundary: true,
          lat: (station.lat + next.lat) / 2,
          lon: (station.lon + next.lon) / 2
        });
      }
    });
    return displayed;
  }

  function getDisplayedLines() {
    if (displayedLinesCache) return displayedLinesCache;
    displayedLinesCache = orderLines(state.filtered)
      .map((line) => ({ ...line, stations: getDisplayedStations(line) }))
      .filter((line) => line.stations.length > 0);
    return displayedLinesCache;
  }

  function getStationRecords(lines = getDisplayedLines()) {
    if (lines === displayedLinesCache && stationRecordsCache) return stationRecordsCache;
    const records = new Map();
    lines.forEach((line) => line.stations.filter((station) => !station.isBoundary).forEach((station) => {
      const record = records.get(station.id) || { station, lines: [], lineIds: [], types: [] };
      if (!record.lines.includes(line.name)) record.lines.push(line.name);
      if (!record.lineIds.includes(line.id)) record.lineIds.push(line.id);
      if (!record.types.includes(line.type)) record.types.push(line.type);
      records.set(station.id, record);
    }));
    const values = [...records.values()];
    if (lines === displayedLinesCache) stationRecordsCache = values;
    return values;
  }

  function invalidateDisplayedData() {
    displayedLinesCache = null;
    stationRecordsCache = null;
  }

  function orderLines(lines) {
    const lineIds = new Set(lines.map((line) => line.id));
    const children = new Map();
    lines.forEach((line) => {
      if (!line.parentLineId || !lineIds.has(line.parentLineId)) return;
      const siblings = children.get(line.parentLineId) || [];
      siblings.push(line);
      children.set(line.parentLineId, siblings);
    });

    const ordered = [];
    const visited = new Set();
    const appendTree = (line) => {
      if (visited.has(line.id)) return;
      visited.add(line.id);
      ordered.push(line);
      (children.get(line.id) || []).forEach(appendTree);
    };

    lines.forEach((line) => {
      if (!line.parentLineId || !lineIds.has(line.parentLineId)) appendTree(line);
    });
    lines.forEach(appendTree);
    return ordered;
  }

  function textMatches(values) {
    return values.some((value) => String(value || "").toLowerCase().includes(state.searchQuery));
  }

  function getSearchMatchedLines() {
    const lines = getDisplayedLines();
    if (!state.searchQuery) return lines;
    return lines.filter((line) => textMatches([
      line.id,
      line.name,
      line.shortName,
      line.type,
      line.typeLabel,
      ...line.stations.filter((station) => !station.isBoundary).flatMap((station) => [station.id, station.name, station.city, station.city_id])
    ]));
  }

  function getSearchStationRecords() {
    const records = getStationRecords(getDisplayedLines());
    if (!state.searchQuery) return records;
    return records.filter(({ station, lines }) => textMatches([
      station.id,
      station.name,
      station.city,
      station.city_id,
      ...lines
    ]));
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

  function renderRailways() {
    railwayLayer.replaceChildren();
    routeNodes.clear();
    stationNodes.clear();
    stationLineIds.clear();
    const displayedLines = getDisplayedLines();
    const stationRecords = getStationRecords(displayedLines);
    const hitLayer = svgNode("g", { class: "railway-hit-layer" });
    routeVisualLayer = svgNode("g", { class: "railway-route-visual-layer" });
    stationVisualLayer = svgNode("g", { class: "railway-station-visual-layer" });
    displayedLines.forEach((line) => {
      const routeStations = line.closed ? [...line.stations, line.stations[0]] : line.stations;
      const points = routeStations.map((station) => {
        const point = project(station);
        return `${point.x},${point.y}`;
      }).join(" ");
      const hitRoute = svgNode("polyline", { points, class: "railway-route-hit", "data-id": line.id });
      hitLayer.appendChild(hitRoute);
      const route = svgNode("polyline", { points, class: `railway-route ${line.type}`, "data-id": line.id });
      routeNodes.set(line.id, route);
      routeVisualLayer.appendChild(route);
    });

    stationRecords.forEach(({ station, lineIds, types }) => {
      const { x, y } = project(station);
      const typeClass = types.length === 1 ? ` ${types[0]}` : "";
      const group = svgNode("g", { class: `railway-station${typeClass}`, "data-id": station.id });
      group.appendChild(svgNode("circle", { cx: x, cy: y, r: 18, class: "railway-hit" }));
      group.appendChild(svgNode("circle", { cx: x, cy: y, r: 9, class: "railway-halo" }));
      group.appendChild(svgNode("circle", { cx: x, cy: y, r: 4, class: "railway-core" }));
      const label = svgNode("text", { x, y: y + 32, class: "railway-label" });
      label.textContent = station.name;
      group.appendChild(label);
      stationNodes.set(station.id, group);
      stationLineIds.set(station.id, lineIds);
      stationVisualLayer.appendChild(group);
    });
    railwayLayer.append(hitLayer, routeVisualLayer, stationVisualLayer);
    updateMapSelection();
  }

  function updateMapSelection() {
    routeNodes.forEach((route, lineId) => {
      route.classList.toggle("selected", state.selectedLine === lineId);
    });
    const selectedRoute = state.selectedLine && routeNodes.get(state.selectedLine);
    if (selectedRoute && routeVisualLayer) routeVisualLayer.appendChild(selectedRoute);

    stationNodes.forEach((group, stationId) => {
      group.classList.toggle("selected", state.selectedStation === stationId);
      group.classList.toggle("selected-line", Boolean(state.selectedLine && stationLineIds.get(stationId)?.includes(state.selectedLine)));
    });
    const selectedStation = state.selectedStation && stationNodes.get(state.selectedStation);
    if (selectedStation && stationVisualLayer) stationVisualLayer.appendChild(selectedStation);
  }

  function updateListSelection() {
    railwayList.querySelectorAll(".railway-row").forEach((row) => {
      const active = row.dataset.lineId
        ? row.dataset.lineId === state.selectedLine
        : row.dataset.stationId === state.selectedStation;
      row.classList.toggle("active", active);
    });
    railwayList.querySelector(".railway-row.active")?.scrollIntoView({ block: "nearest" });
  }

  function selectLine(lineId) {
    state.selectedLine = lineId;
    state.selectedStation = null;
    updateMapSelection();
    updateListSelection();
  }

  function selectStation(stationId) {
    state.selectedLine = null;
    state.selectedStation = stationId;
    updateMapSelection();
    updateListSelection();
  }

  function clearSelection() {
    state.selectedLine = null;
    state.selectedStation = null;
    updateMapSelection();
    updateListSelection();
  }

  function renderList() {
    railwayList.replaceChildren();
    const matchedLines = state.dataMode === "lines" ? getSearchMatchedLines() : null;
    const matchedStations = state.dataMode === "stations" ? getSearchStationRecords() : null;
    const resultCount = state.dataMode === "lines" ? matchedLines.length : matchedStations.length;
    document.getElementById("railwayCount").textContent = resultCount;
    const typeSummary = [...new Set(state.filtered.map((line) => line.typeLabel))].join(" / ");
    railwayNote.textContent = state.dataMode === "lines"
      ? (state.searchQuery ? `匹配到 ${resultCount} 条铁路线路，地图仍显示当前区域全部线路。` : `当前显示 ${state.filtered.length} 条${typeSummary}铁路预研线路。`)
      : (state.searchQuery ? `匹配到 ${resultCount} 个铁路站点，地图仍显示当前区域全部站点。` : `当前显示 ${resultCount} 个铁路站点，线路与站点均保留在地图上。`);
    if (!resultCount) {
      const empty = document.createElement("div");
      empty.className = "empty-list";
      empty.textContent = state.searchQuery ? "没有匹配的铁路线路或站点" : "当前区域暂无铁路线路数据";
      railwayList.appendChild(empty);
      return;
    }
    const fragment = document.createDocumentFragment();
    if (state.dataMode === "lines") {
      matchedLines.forEach((line) => {
        const row = document.createElement("button");
        row.type = "button";
        row.className = `airport-row railway-row railway-row-${line.type}`;
        row.dataset.lineId = line.id;
        const dot = document.createElement("i");
        dot.className = "row-dot railway-row-dot";
        const main = document.createElement("span");
        main.className = "row-main";
        const name = document.createElement("span");
        name.className = "row-name";
        name.textContent = line.name;
        const detail = document.createElement("span");
        detail.className = "row-city";
        const stationCount = line.stations.filter((station) => !station.isBoundary).length;
        detail.textContent = `${line.typeLabel} · ${stationCount} 个站点`;
        main.append(name, detail);
        const code = document.createElement("span");
        code.className = "row-code";
        code.textContent = line.shortName;
        row.append(dot, main, code);
        fragment.appendChild(row);
      });
      railwayList.appendChild(fragment);
      updateListSelection();
      return;
    }

    matchedStations.forEach(({ station, lines }) => {
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
      detail.textContent = `${station.city} · ${lines.join(" / ")}`;
      main.append(name, detail);
      row.append(dot, main);
      fragment.appendChild(row);
    });
    railwayList.appendChild(fragment);
    updateListSelection();
  }

  function centerOnItems(lines) {
    const stations = lines.flatMap((line) => line.stations);
    if (!stations.length) return;
    const points = stations.map(project);
    const minX = Math.min(...points.map((point) => point.x));
    const maxX = Math.max(...points.map((point) => point.x));
    const minY = Math.min(...points.map((point) => point.y));
    const maxY = Math.max(...points.map((point) => point.y));
    state.scale = 1;
    state.x = 600 - (minX + maxX) / 2;
    state.y = 380 - (minY + maxY) / 2;
    updateTransform();
  }

  function applyRegion() {
    const region = state.regionScope;
    state.filtered = region === "global"
      ? RAILWAYS
      : RAILWAYS.filter((line) => line.region === region || (line.regions || []).includes(region));
    invalidateDisplayedData();
    const displayedLines = getDisplayedLines();
    if (state.selectedLine && !displayedLines.some((line) => line.id === state.selectedLine)) state.selectedLine = null;
    if (state.selectedStation && !getStationRecords(displayedLines).some(({ station }) => station.id === state.selectedStation)) state.selectedStation = null;
    regionReadout.textContent = regionLabels[region];
    renderRailways();
    renderList();
    if (region === "global") {
      Object.assign(state, DEFAULT_VIEW);
      updateTransform();
    } else if (displayedLines.length) {
      centerOnItems(displayedLines);
    }
  }

  function resetView() {
    searchInput.value = "";
    state.regionScope = "global";
    state.searchQuery = "";
    state.selectedLine = null;
    state.selectedStation = null;
    state.filtered = RAILWAYS;
    invalidateDisplayedData();
    regionSelect.value = "global";
    regionReadout.textContent = regionLabels.global;
    Object.assign(state, DEFAULT_VIEW);
    updateTransform();
    renderRailways();
    renderList();
  }

  function setDataMode(mode) {
    state.dataMode = mode;
    state.selectedStation = null;
    lineModeButton.classList.toggle("active", mode === "lines");
    stationModeButton.classList.toggle("active", mode === "stations");
    lineModeButton.setAttribute("aria-pressed", String(mode === "lines"));
    stationModeButton.setAttribute("aria-pressed", String(mode === "stations"));
    updateMapSelection();
    renderList();
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

  mapStage.addEventListener("wheel", (event) => {
    event.preventDefault();
    zoomAt(state.scale * Math.exp(-event.deltaY * 0.001), event.clientX, event.clientY);
  }, { passive: false });

  railwayLayer.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
    const station = event.target.closest(".railway-station");
    const route = event.target.closest(".railway-route-hit");
    if (!station && !route) return;
    event.preventDefault();
    event.stopPropagation();
    if (station) selectStation(station.dataset.id);
    else selectLine(route.dataset.id);
  });

  railwayList.addEventListener("click", (event) => {
    const row = event.target.closest(".railway-row");
    if (!row) return;
    if (row.dataset.lineId) {
      const line = getDisplayedLines().find((item) => item.id === row.dataset.lineId);
      selectLine(row.dataset.lineId);
      if (line) centerOnItems([line]);
      return;
    }
    if (row.dataset.stationId) {
      const record = getStationRecords().find(({ station }) => station.id === row.dataset.stationId);
      selectStation(row.dataset.stationId);
      if (record) centerOnItems([{ stations: [record.station] }]);
    }
  });

  mapStage.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
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
    if (!state.dragMoved) clearSelection();
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

  regionSelect.addEventListener("change", () => {
    state.regionScope = regionSelect.value;
    applyRegion();
  });
  searchInput.addEventListener("input", () => {
    state.searchQuery = searchInput.value.trim().toLowerCase();
    cancelAnimationFrame(searchFrame);
    searchFrame = requestAnimationFrame(renderList);
  });
  lineModeButton.addEventListener("click", () => setDataMode("lines"));
  stationModeButton.addEventListener("click", () => setDataMode("stations"));
  document.getElementById("resetButton").addEventListener("click", resetView);
  document.getElementById("zoomInButton").addEventListener("click", () => zoomAt(state.scale * 1.2, mapStage.getBoundingClientRect().left + mapStage.clientWidth / 2, mapStage.getBoundingClientRect().top + mapStage.clientHeight / 2));
  document.getElementById("zoomOutButton").addEventListener("click", () => zoomAt(state.scale / 1.2, mapStage.getBoundingClientRect().left + mapStage.clientWidth / 2, mapStage.getBoundingClientRect().top + mapStage.clientHeight / 2));

  renderGrid();
  renderRailways();
  renderList();
  updateTransform();
})();
