(() => {
  "use strict";

  const SVG_NS = "http://www.w3.org/2000/svg";
  const VIEW = { left: 40, right: 146, bottom: -10, top: 56 };
  const MAP_LAYOUT_SCALE = 52;
  const MAP_FOCUS = { lon: 112, lat: 31 };
  const MIN_ZOOM = 0.04;
  const MAX_ZOOM = 48;
  const SEGMENT_FOCUS_MAX_ZOOM = 4;
  const STATION_LABEL_MIN_ZOOM = 0.22;
  const STATION_RADII = { ".railway-hit": 18, ".railway-halo": 9, ".railway-core": 4 };
  const LABEL_DENSE_KM = 7;
  const CLOSE_REPLACE_KM = 8;
  const KEPT_NEAR_IDS = new Set(["jingguang_01", "jingha_beijing", "jingguang_fengtai"]);
  const CITY_BY_NAME = {
    北京南: "北京",
    亦庄: "北京",
    武清: "天津",
    天津: "天津",
    廊坊: "廊坊",
    天津南: "天津"
  };
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
    "jingjin_yizhuang",
    "jingxiong_02"
  ];
  const CORRIDOR_DEFS = [
    {
      id: "beijingnan_tianjin",
      name: "北京南—天津通道",
      stations: [
        ["jinghu_01", "北京南", 39.8636, 116.3728],
        ["jingjin_yizhuang", "亦庄", 39.8119, 116.5962],
        ["wuqing", "武清", 39.3714, 117.0101],
        ["tianjin", "天津", 39.1420, 117.1760]
      ]
    },
    {
      id: "beijingnan_tianjinnan",
      name: "北京南—天津南通道",
      stations: [
        ["jinghu_01", "北京南", 39.8636, 116.3728],
        ["langfang", "廊坊", 39.5058, 116.7011],
        ["tianjinnan", "天津南", 39.0558, 117.0550]
      ]
    }
  ];

  const viewport = document.getElementById("viewport");
  const gridLayer = document.getElementById("gridLayer");
  const railwayLayer = document.getElementById("railwayLayer");
  const mapStage = document.getElementById("mapStage");
  const mapSvg = document.getElementById("mapSvg");
  const entryList = document.getElementById("entryList");
  const searchInput = document.getElementById("searchInput");
  const pageNote = document.getElementById("pageNote");
  const selectionReadout = document.getElementById("selectionReadout");
  const stationById = new Map();
  const corridors = CORRIDOR_DEFS.map((corridor) => ({
    id: corridor.id,
    name: corridor.name,
    stations: corridor.stations.map(([id, name, lat, lon]) => {
      if (stationById.has(id)) return stationById.get(id);
      const station = { id, name, city: CITY_BY_NAME[name] || "", lat, lon };
      stationById.set(id, station);
      return station;
    })
  }));
  const anchoredStations = [...stationById.values()];
  collectBeijingStations().forEach((station) => {
    if (stationById.has(station.id)) return;
    const nearestKm = Math.min(...anchoredStations.map((anchor) => distanceKm(station, anchor)));
    if (nearestKm <= CLOSE_REPLACE_KM && !KEPT_NEAR_IDS.has(station.id)) return;
    stationById.set(station.id, station);
  });
  const beijingStations = [...stationById.values()]
    .filter((station) => station.city === "北京")
    .sort((a, b) => a.name.localeCompare(b.name, "zh-CN"));
  const beijingIds = new Set(beijingStations.map((station) => station.id));
  const segments = corridors.flatMap((corridor) => corridor.stations.slice(0, -1).map((station, index) => ({
    id: `${corridor.id}__${index}`,
    corridorId: corridor.id,
    corridorName: corridor.name,
    from: station,
    to: corridor.stations[index + 1]
  })));
  const originalNameOrder = buildOriginalNameOrder();
  const stations = [...stationById.values()].sort((a, b) => stationOrderKey(a) - stationOrderKey(b) || a.name.localeCompare(b.name, "zh-CN"));
  const state = {
    x: 0,
    y: 0,
    scale: 1,
    searchQuery: "",
    selectedSegmentId: null,
    selectedStationId: null,
    dragging: false,
    pointer: null,
    dragMoved: false
  };
  const stationNodes = new Map();
  const stationGeo = new Map();
  const routeNodes = new Map();
  let routeLayer = null;
  let denseStationIds = new Set();
  let stationMarkerScale = null;
  let searchFrame = 0;
  let skipClearOnPointerUp = false;

  function buildOriginalNameOrder() {
    const lineIds = new Set(RAILWAYS.map((line) => line.id));
    const children = new Map();
    RAILWAYS.forEach((line) => {
      if (!line.parentLineId || !lineIds.has(line.parentLineId)) return;
      const siblings = children.get(line.parentLineId) || [];
      siblings.push(line);
      children.set(line.parentLineId, siblings);
    });
    const ordered = [];
    const visited = new Set();
    const append = (line) => {
      if (visited.has(line.id)) return;
      visited.add(line.id);
      ordered.push(line);
      (children.get(line.id) || []).forEach(append);
    };
    RAILWAYS.forEach((line) => {
      if (!line.parentLineId || !lineIds.has(line.parentLineId)) append(line);
    });
    RAILWAYS.forEach(append);
    const names = [];
    const seen = new Set();
    ordered.forEach((line) => line.stations.forEach((station) => {
      if (seen.has(station.id)) return;
      seen.add(station.id);
      names.push(station.name);
    }));
    return names;
  }

  function stationOrderKey(station) {
    const ownIndex = originalNameOrder.indexOf(station.name);
    return ownIndex >= 0 ? ownIndex : originalNameOrder.length + 1;
  }

  function collectBeijingStations() {
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

  function selectedSegment() {
    return segments.find((segment) => segment.id === state.selectedSegmentId) || null;
  }

  function corridorById(corridorId) {
    return corridors.find((corridor) => corridor.id === corridorId) || null;
  }

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

  function litStationIds() {
    const segment = selectedSegment();
    if (segment) return new Set([segment.from.id, segment.to.id]);
    return state.selectedStationId ? new Set([state.selectedStationId]) : new Set();
  }

  function updateDenseLabels() {
    const lit = litStationIds();
    stationNodes.forEach((group, stationId) => {
      const label = group.querySelector(".railway-label");
      const suppress = denseStationIds.has(stationId) && !lit.has(stationId);
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
    const hitLayer = svgNode("g", { class: "railway-hit-layer" });
    routeLayer = svgNode("g", { class: "railway-route-visual-layer" });
    routeNodes.clear();
    const stationVisualLayer = svgNode("g", { class: "railway-station-visual-layer" });
    segments.forEach((segment) => {
      const from = project(segment.from);
      const to = project(segment.to);
      const points = `${from.x},${from.y} ${to.x},${to.y}`;
      hitLayer.appendChild(svgNode("polyline", { points, class: "railway-route-hit", "data-id": segment.id }));
      const route = svgNode("polyline", { points, class: "railway-route high_speed", "data-id": segment.id });
      routeNodes.set(segment.id, route);
      routeLayer.appendChild(route);
    });
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
    railwayLayer.append(hitLayer, routeLayer, stationVisualLayer);
    stationMarkerScale = null;
    rebuildDenseStationIds();
    updateSegmentLine();
    updateTransform();
  }

  function updateSegmentLine() {
    routeNodes.forEach((route, segmentId) => {
      const selected = segmentId === state.selectedSegmentId;
      route.classList.toggle("selected", selected);
      if (selected && routeLayer) routeLayer.appendChild(route);
    });
  }

  function updateMapSelection() {
    const segment = selectedSegment();
    const lit = litStationIds();
    stationNodes.forEach((group, stationId) => {
      group.classList.toggle("selected", lit.has(stationId));
      group.classList.remove("dimmed");
    });
    const stationVisualLayer = railwayLayer.querySelector(".railway-station-visual-layer");
    lit.forEach((stationId) => {
      const node = stationNodes.get(stationId);
      if (node && stationVisualLayer) stationVisualLayer.appendChild(node);
    });
    updateDenseLabels();
    if (segment) selectionReadout.textContent = `${segment.from.name} — ${segment.to.name}`;
    else if (state.selectedStationId) selectionReadout.textContent = stationById.get(state.selectedStationId)?.name || "未选择";
    else selectionReadout.textContent = "未选择";
  }

  function updateListSelection() {
    entryList.querySelectorAll(".railway-row").forEach((row) => {
      row.classList.toggle("active", row.dataset.stationId === state.selectedStationId);
    });
    entryList.querySelector(".railway-row.active")?.scrollIntoView({ block: "nearest" });
  }

  function queryMatches(values) {
    return values.some((value) => String(value || "").toLowerCase().includes(state.searchQuery));
  }

  function visibleStations() {
    if (!state.searchQuery) return stations;
    return stations.filter((station) => queryMatches([station.name, station.city]));
  }

  function renderList() {
    entryList.replaceChildren();
    const stationRows = visibleStations();
    document.getElementById("entryCount").textContent = stationRows.length;
    pageNote.textContent = state.searchQuery
      ? `匹配到 ${stationRows.length} 个铁路站点，地图仍显示全部站点。`
      : `当前显示 ${stations.length} 个铁路站点。`;
    if (!stationRows.length) {
      const empty = document.createElement("div");
      empty.className = "empty-list";
      empty.textContent = "没有匹配的铁路站点";
      entryList.appendChild(empty);
      return;
    }
    const fragment = document.createDocumentFragment();
    stationRows.forEach((station) => fragment.appendChild(stationRow(station)));
    entryList.appendChild(fragment);
    updateListSelection();
  }

  function stationRow(station) {
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
    return row;
  }

  function segmentRow(segment) {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "airport-row railway-row railway-station-row";
    row.dataset.segmentId = segment.id;
    const dot = document.createElement("i");
    dot.className = "row-dot railway-row-dot";
    const main = document.createElement("span");
    main.className = "row-main";
    const name = document.createElement("span");
    name.className = "row-name";
    name.textContent = `${segment.from.name} — ${segment.to.name}`;
    const detail = document.createElement("span");
    detail.className = "row-city";
    detail.textContent = "相邻段";
    main.append(name, detail);
    row.append(dot, main);
    return row;
  }

  function fitStations(items, maxScale = MAX_ZOOM) {
    if (!items.length) return;
    const points = items.map(project);
    const minX = Math.min(...points.map((point) => point.x));
    const maxX = Math.max(...points.map((point) => point.x));
    const minY = Math.min(...points.map((point) => point.y));
    const maxY = Math.max(...points.map((point) => point.y));
    const spanX = Math.max(maxX - minX, 120);
    const spanY = Math.max(maxY - minY, 120);
    state.scale = Math.max(MIN_ZOOM, Math.min(maxScale, Math.min(1040 / spanX, 600 / spanY)));
    state.x = 600 - ((minX + maxX) / 2) * state.scale;
    state.y = 380 - ((minY + maxY) / 2) * state.scale;
    updateTransform();
  }

  function selectSegment(segmentId) {
    state.selectedSegmentId = segmentId;
    state.selectedStationId = null;
    updateSegmentLine();
    updateMapSelection();
    updateListSelection();
  }

  function focusBeijing() {
    state.selectedSegmentId = null;
    state.selectedStationId = null;
    updateSegmentLine();
    updateMapSelection();
    updateListSelection();
    fitStations(beijingStations);
  }

  function centerOnStation(station) {
    const point = project(station);
    state.scale = 1;
    state.x = 600 - point.x;
    state.y = 380 - point.y;
    updateTransform();
  }

  function selectStation(stationId, center) {
    state.selectedSegmentId = null;
    state.selectedStationId = stationId;
    updateSegmentLine();
    updateMapSelection();
    updateListSelection();
    const station = stationById.get(stationId);
    if (station && center) centerOnStation(station);
  }

  function clearSelection() {
    state.selectedSegmentId = null;
    state.selectedStationId = null;
    updateSegmentLine();
    updateMapSelection();
    updateListSelection();
  }

  function preferredSegmentForStation(stationId) {
    if (beijingIds.has(stationId)) return null;
    const outgoing = segments.filter((segment) => segment.from.id === stationId);
    if (outgoing.length === 1) return outgoing[0];
    if (outgoing.length > 1) return null;
    const incoming = segments.filter((segment) => segment.to.id === stationId);
    return incoming.length === 1 ? incoming[0] : null;
  }

  function resetView() {
    searchInput.value = "";
    state.searchQuery = "";
    clearSelection();
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
    const route = event.target.closest(".railway-route-hit");
    if (!station && !route) return;
    event.preventDefault();
    event.stopPropagation();
    skipClearOnPointerUp = true;
    if (station) selectStation(station.dataset.id, false);
    else selectSegment(route.dataset.id);
  });

  entryList.addEventListener("click", (event) => {
    const row = event.target.closest(".railway-row");
    if (!row?.dataset.stationId) return;
    selectStation(row.dataset.stationId, true);
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
