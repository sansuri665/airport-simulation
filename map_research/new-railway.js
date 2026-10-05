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
    天津南: "天津",
    北京西: "北京",
    北京丰台: "北京",
    北京大兴: "北京",
    大兴机场: "北京",
    固安东: "固安",
    霸州北: "霸州",
    双辛: "高碑店",
    雄安: "雄安",
    涿州东: "涿州",
    高碑店东: "高碑店",
    保定东: "保定",
    定州东: "定州",
    正定机场: "正定",
    石家庄: "石家庄",
    北京通州: "北京",
    燕郊: "三河",
    大厂: "大厂",
    香河: "香河",
    宝坻: "天津",
    玉田南: "玉田",
    唐山西: "唐山",
    唐山: "唐山",
    北京北: "北京",
    清河: "北京",
    沙河: "北京",
    昌平: "北京",
    八达岭长城: "北京",
    东花园北: "怀来",
    怀来: "怀来",
    下花园北: "张家口",
    宣化北: "张家口",
    张家口: "张家口",
    北京站: "北京",
    北京朝阳: "北京",
    顺义西: "北京",
    怀柔南: "北京",
    密云: "北京",
    兴隆县西: "兴隆",
    安匠: "承德",
    承德南: "承德",
    承德县北: "承德县",
    平泉北: "平泉",
    牛河梁: "凌源",
    喀左: "喀左",
    奈林皋: "朝阳",
    辽宁朝阳: "朝阳",
    北票: "北票",
    乌兰木图: "阜新",
    阜新: "阜新",
    黑山北: "黑山",
    新民北: "新民",
    沈阳西: "沈阳",
    沈阳: "沈阳",
    建平: "建平",
    宁城: "宁城",
    平庄: "赤峰",
    赤峰: "赤峰",
    昌平北: "北京",
    怀柔北: "北京",
    古北口: "北京",
    滦平: "滦平",
    隆化: "隆化",
    四合永: "隆化",
    朝阳地: "赤峰",
    五十家子: "赤峰",
    三把火: "赤峰",
    赤峰南: "赤峰",
    军粮城北: "天津",
    塘沽: "天津",
    滨海: "天津",
    滨海西: "天津",
    滨海北: "天津",
    天津西: "天津",
    胜芳: "霸州",
    安次: "廊坊",
    永清东: "永清",
    团泊北: "天津",
    文安北: "文安",
    沧州西: "沧州",
    德州东: "德州",
    济南西: "济南",
    滨海东: "天津",
    滨海南: "天津",
    黄骅北: "黄骅",
    海兴西: "海兴",
    无棣: "无棣",
    滨州: "滨州",
    惠民: "惠民",
    商河: "商河",
    济阳: "济阳",
    遥墙机场: "济南",
    济南东: "济南",
    东营南: "东营",
    寿光东: "寿光",
    潍坊北: "潍坊"
  };
  const ORDER_NAME_ALIAS = {
    北京通州: "北京城市副中心",
    辽宁朝阳: "朝阳"
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
        ["tianjin", "天津", 39.13575, 117.20368]
      ]
    },
    {
      id: "beijingnan_tianjinnan",
      name: "北京南—天津南通道",
      stations: [
        ["jinghu_01", "北京南", 39.8636, 116.3728],
        ["langfang", "廊坊", 39.5058, 116.7011],
        ["tianjinnan", "天津南", 39.05583, 117.05500]
      ]
    },
    {
      id: "beijingxi_xiongan",
      name: "北京西—雄安通道",
      stations: [
        ["jingguang_01", "北京西", 39.893564, 116.315697],
        ["jingxiong_02", "北京大兴", 39.719390, 116.322540],
        ["jingxiong_03", "大兴机场", 39.513921, 116.409934],
        ["jingxiong_04", "固安东", 39.370919, 116.399011],
        ["jingxiong_05", "霸州北", 39.185308, 116.320453],
        ["jingxiongshang_02", "雄安", 39.055749, 116.153230]
      ]
    },
    {
      id: "beijingfengtai_xiongan",
      name: "北京丰台—雄安通道",
      stations: [
        ["jingguang_fengtai", "北京丰台", 39.849772, 116.294567],
        ["jingxiongshang_shuangxin", "双辛", 39.2940, 116.19],
        ["jingxiongshang_02", "雄安", 39.055749, 116.153230]
      ]
    },
    {
      id: "beijingfengtai_shijiazhuang",
      name: "北京丰台—石家庄通道",
      stations: [
        ["jingguang_fengtai", "北京丰台", 39.849772, 116.294567],
        ["jingguang_zhuozhoudong", "涿州东", 39.45864, 116.04739],
        ["jingguang_gaobeidiandong", "高碑店东", 39.28787, 115.94067],
        ["jingguang_02", "保定东", 38.86346, 115.59573],
        ["jingguang_dingzhoudong", "定州东", 38.50777, 115.06906],
        ["jingguang_zhengdingairport", "正定机场", 38.25131, 114.70333],
        ["jingguang_03", "石家庄", 38.01111, 114.47722]
      ]
    },
    {
      id: "beijingtongzhou_tangshan",
      name: "北京通州—唐山通道",
      stations: [
        ["jingtang_01", "北京通州", 39.90797, 116.70015],
        ["jingtang_02", "燕郊", 39.94167, 116.82583],
        ["jingtang_03", "大厂", 39.8886, 116.8976],
        ["jingtang_04", "香河", 39.71883, 117.02767],
        ["jingtang_05", "宝坻", 39.66050, 117.29900],
        ["jingtang_06", "玉田南", 39.69639, 117.80874],
        ["jingtang_07", "唐山西", 39.69528, 118.01709],
        ["jinqinshen_02", "唐山", 39.62424, 118.11170]
      ]
    },
    {
      id: "beijingbei_zhangjiakou",
      name: "北京北—张家口通道",
      stations: [
        ["jingbao_01", "北京北", 39.945280, 116.347220],
        ["jingbao_qinghe", "清河", 40.039864, 116.309173],
        ["jingbao_shahe", "沙河", 40.123890, 116.258890],
        ["jingbao_changping", "昌平", 40.188847, 116.187314],
        ["jingbao_badaling", "八达岭长城", 40.357941, 116.004759],
        ["jingbao_donghuayuanbei", "东花园北", 40.341786, 115.788172],
        ["jingbao_huailai", "怀来", 40.376689, 115.558223],
        ["jingbao_xiahuayuanbei", "下花园北", 40.502046, 115.295259],
        ["jingbao_xuanhuabei", "宣化北", 40.631230, 115.042504],
        ["jingbao_02", "张家口", 40.750675, 114.876969]
      ]
    },
    {
      id: "beijingchaoyang_shenyang",
      name: "北京站—沈阳通道",
      stations: [
        ["jingha_beijing", "北京站", 39.901, 116.4206],
        ["jingha_01", "北京朝阳", 39.943180, 116.502120],
        ["jingha_shunyixi", "顺义西", 40.177832, 116.484982],
        ["jingha_huairounan", "怀柔南", 40.277160, 116.698821],
        ["jingha_miyun", "密云", 40.350811, 116.844702],
        ["jingha_xinglongxianxi", "兴隆县西", 40.412549, 117.475721],
        ["jingha_anjiang", "安匠", 40.762119, 117.722803],
        ["jingha_02", "承德南", 40.882322, 117.957486],
        ["jingha_chengdexianbei", "承德县北", 40.934700, 118.284239],
        ["jingha_pingquanbei", "平泉北", 41.037158, 118.705056],
        ["jingha_niuheliang", "牛河梁", 41.194239, 119.392261],
        ["jingha_kazuo", "喀左", 41.222547, 119.799700],
        ["jingha_nailingao", "奈林皋", 41.399988, 120.062090],
        ["jingha_03", "辽宁朝阳", 41.597986, 120.403819],
        ["jingha_beipiao", "北票", 41.766689, 120.782853],
        ["jingha_wulanmutu", "乌兰木图", 41.962704, 121.287304],
        ["jingha_04", "阜新", 42.055969, 121.654200],
        ["jingha_heishanbei", "黑山北", 42.043894, 122.294425],
        ["jingha_xinminbei", "新民北", 42.022786, 122.799950],
        ["jingha_shenyangxi", "沈阳西", 41.916594, 123.229206],
        ["jingha_shenyang", "沈阳", 41.791714, 123.386817]
      ]
    },
    {
      id: "beijingchaoyang_chifeng",
      name: "北京朝阳—赤峰通道",
      stations: [
        ["jingha_01", "北京朝阳", 39.943180, 116.502120],
        ["jingha_shunyixi", "顺义西", 40.177832, 116.484982],
        ["jingha_huairounan", "怀柔南", 40.277160, 116.698821],
        ["jingha_miyun", "密云", 40.350811, 116.844702],
        ["jingha_xinglongxianxi", "兴隆县西", 40.412549, 117.475721],
        ["jingha_anjiang", "安匠", 40.762119, 117.722803],
        ["jingha_02", "承德南", 40.882322, 117.957486],
        ["jingha_chengdexianbei", "承德县北", 40.934700, 118.284239],
        ["jingha_pingquanbei", "平泉北", 41.037158, 118.705056],
        ["jingha_niuheliang", "牛河梁", 41.194239, 119.392261],
        ["jingha_jianping", "建平", 41.378100, 119.556360],
        ["jingha_ningcheng", "宁城", 41.58, 119.31],
        ["jingha_pingzhuang", "平庄", 41.988100, 119.289318],
        ["jingha_chifeng_02", "赤峰", 42.273599, 118.895648]
      ]
    },
    {
      id: "changping_chifengnan",
      name: "昌平—赤峰南通道",
      type: "conventional",
      stations: [
        ["jingbao_changping", "昌平", 40.1888, 116.1873],
        ["jingtong_changpingbei", "昌平北", 40.2300, 116.2270],
        ["jingtong_huairoubei", "怀柔北", 40.4079, 116.6871],
        ["jingtong_gubeikou", "古北口", 40.6906, 117.1353],
        ["zhangtang_luanping", "滦平", 40.9217, 117.3098],
        ["jingtong_longhua", "隆化", 41.3264, 117.7450],
        ["jingtong_siheyong", "四合永", 41.7992, 117.8224],
        ["jingtong_chaoyangdi", "朝阳地", 42.0224, 118.2206],
        ["jingtong_wushijiazi", "五十家子", 42.0925, 118.1651],
        ["jingtong_sanbahuo", "三把火", 42.2946, 118.6723],
        ["jingtong_chifengnan", "赤峰南", 42.2547, 118.9536]
      ]
    },
    {
      id: "tianjin_binhai",
      name: "天津—滨海通道",
      stations: [
        ["tianjin", "天津", 39.13575, 117.20368],
        ["junliangchengbei", "军粮城北", 39.0645, 117.4210],
        ["tanggu", "塘沽", 39.02833, 117.64028],
        ["jinwei_01", "滨海", 39.0035, 117.6788]
      ]
    },
    {
      id: "tianjin_tangshan",
      name: "天津—唐山通道",
      stations: [
        ["tianjin", "天津", 39.13575, 117.20368],
        ["junliangchengbei", "军粮城北", 39.0645, 117.4210],
        ["jingbin_binhaixi", "滨海西", 39.08003, 117.60568],
        ["jingbin_binhaibei", "滨海北", 39.23512, 117.75577],
        ["jinqinshen_02", "唐山", 39.62424, 118.11170]
      ]
    },
    {
      id: "tianjinxi_xiongan",
      name: "天津西—雄安通道",
      stations: [
        ["jinxing_01", "天津西", 39.15736, 117.15712],
        ["jinxing_shengfang", "胜芳", 39.13765, 116.75350],
        ["jinxing_02", "安次", 39.2356, 116.6756],
        ["jinxing_03", "永清东", 39.30431, 116.50526],
        ["jingxiong_04", "固安东", 39.37092, 116.39901],
        ["jingxiong_05", "霸州北", 39.18531, 116.32045],
        ["jingxiongshang_02", "雄安", 39.05575, 116.15323]
      ]
    },
    {
      id: "tianjinnan_xiongan",
      name: "天津南—雄安通道",
      stations: [
        ["tianjinnan", "天津南", 39.05583, 117.05500],
        ["tuanpobei", "团泊北", 38.99, 117.08],
        ["wenanbei", "文安北", 39.0050, 116.6263],
        ["jingxiongshang_02", "雄安", 39.05575, 116.15323]
      ]
    },
    {
      id: "tianjinnan_jinanxi",
      name: "天津南—济南西通道",
      stations: [
        ["tianjinnan", "天津南", 39.05583, 117.05500],
        ["jinghu_04", "沧州西", 38.30602, 116.76211],
        ["jinghu_05", "德州东", 37.41089, 116.45493],
        ["jinghu_06", "济南西", 36.66889, 116.88694]
      ]
    },
    {
      id: "tianjin_jinandong",
      name: "天津—济南东通道",
      stations: [
        ["tianjin", "天津", 39.13575, 117.20368],
        ["junliangchengbei", "军粮城北", 39.0645, 117.4210],
        ["tanggu", "塘沽", 39.02833, 117.64028],
        ["jinwei_01", "滨海", 39.0035, 117.6788],
        ["jinwei_binhaidong", "滨海东", 38.85, 117.57],
        ["jinwei_binhainan", "滨海南", 38.70943, 117.43954],
        ["jinwei_huanghuabei", "黄骅北", 38.401, 117.385],
        ["jinwei_haixingxi", "海兴西", 38.115, 117.450],
        ["jinwei_wudi", "无棣", 37.752, 117.725],
        ["jinwei_02", "滨州", 37.4532, 118.0122],
        ["jinwei_huimin", "惠民", 37.49, 117.50],
        ["jinwei_shanghe", "商河", 37.31, 117.16],
        ["jinwei_jiyang", "济阳", 36.99, 117.12],
        ["jinwei_yaoqiang", "遥墙机场", 36.86, 117.22],
        ["jiqing_01", "济南东", 36.7484, 117.1541]
      ]
    },
    {
      id: "binzhou_weifangbei",
      name: "滨州—潍坊北通道",
      stations: [
        ["jinwei_02", "滨州", 37.4532, 118.0122],
        ["jinwei_03", "东营南", 37.3560, 118.5450],
        ["jinwei_shouguangdong", "寿光东", 36.905, 118.865],
        ["jiqing_03", "潍坊北", 36.7954, 119.1894]
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
    type: corridor.type || "high_speed",
    stations: corridor.stations.map(([id, name, lat, lon]) => {
      if (stationById.has(id)) return stationById.get(id);
      const station = { id, name, city: CITY_BY_NAME[name] || "", lat, lon };
      stationById.set(id, station);
      return station;
    })
  }));
  const beijingListIds = new Set(BEIJING_STATION_IDS);
  const replacementAnchors = [...stationById.values()].filter((station) => !beijingListIds.has(station.id));
  collectBeijingStations().forEach((station) => {
    if (stationById.has(station.id)) return;
    const nearestKm = replacementAnchors.length
      ? Math.min(...replacementAnchors.map((anchor) => distanceKm(station, anchor)))
      : Infinity;
    if (nearestKm <= CLOSE_REPLACE_KM && !KEPT_NEAR_IDS.has(station.id)) return;
    stationById.set(station.id, station);
  });
  const highSpeedIds = new Set();
  const conventionalIds = new Set();
  corridors.forEach((corridor) => {
    corridor.stations.forEach((station) => {
      if (corridor.type === "conventional") conventionalIds.add(station.id);
      else highSpeedIds.add(station.id);
    });
  });
  stationById.forEach((station) => {
    station.type = conventionalIds.has(station.id) && !highSpeedIds.has(station.id) ? "conventional" : "high_speed";
  });
  const beijingStations = [...stationById.values()]
    .filter((station) => station.city === "北京")
    .sort((a, b) => a.name.localeCompare(b.name, "zh-CN"));
  const beijingIds = new Set(beijingStations.map((station) => station.id));
  const seenHops = new Set();
  const segments = corridors.flatMap((corridor) => corridor.stations.slice(0, -1).flatMap((station, index) => {
    const hop = `${station.id}>${corridor.stations[index + 1].id}`;
    if (seenHops.has(hop)) return [];
    seenHops.add(hop);
    return [{
      id: `${corridor.id}__${index}`,
      corridorId: corridor.id,
      corridorName: corridor.name,
      type: corridor.type,
      from: station,
      to: corridor.stations[index + 1]
    }];
  }));
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
    const orderName = ORDER_NAME_ALIAS[station.name] || station.name;
    const ownIndex = originalNameOrder.indexOf(orderName);
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
      const route = svgNode("polyline", { points, class: `railway-route ${segment.type}`, "data-id": segment.id });
      routeNodes.set(segment.id, route);
      routeLayer.appendChild(route);
    });
    stations.forEach((station) => {
      const { x, y } = project(station);
      const group = svgNode("g", { class: `railway-station ${station.type}`, "data-id": station.id });
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
    row.className = `airport-row railway-row railway-station-row${station.type === "conventional" ? " railway-row-conventional" : ""}`;
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
