const RAILWAYS = [
  {
    id: "jingguang_high_speed",
    name: "京广高铁",
    shortName: "京广",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "运营线路",
    source: "用户提供参考坐标",
    stations: [
      { id: "jingguang_01", name: "北京西", city: "北京", sourceLat: 39.8947, sourceLon: 116.3220, lat: 39.8947, lon: 116.2620 },
      { id: "jingguang_02", name: "保定东", city: "保定", lat: 39.0870, lon: 115.5700 },
      { id: "jingguang_03", name: "石家庄", city: "石家庄", lat: 38.0225, lon: 114.4840 },
      { id: "jingguang_04", name: "邢台东", city: "邢台", lat: 37.0700, lon: 114.5700 },
      { id: "jingguang_05", name: "邯郸东", city: "邯郸", lat: 36.6150, lon: 114.5650 },
      { id: "jingguang_06", name: "安阳东", city: "安阳", lat: 36.0800, lon: 114.4000 },
      { id: "jingguang_07", name: "鹤壁东", city: "鹤壁", lat: 35.7600, lon: 114.3200 },
      { id: "jingguang_08", name: "新乡东", city: "新乡", lat: 35.3020, lon: 113.9400 },
      { id: "jingguang_09", name: "郑州东", city: "郑州", lat: 34.7580, lon: 113.7690 },
      { id: "jingguang_10", name: "许昌东", city: "许昌", lat: 34.0200, lon: 113.8700 },
      { id: "jingguang_11", name: "漯河西", city: "漯河", lat: 33.5700, lon: 113.9200 },
      { id: "jingguang_12", name: "驻马店西", city: "驻马店", lat: 32.9800, lon: 114.0200 },
      { id: "jingguang_13", name: "信阳东", city: "信阳", lat: 32.1500, lon: 114.1200 },
      { id: "jingguang_14", name: "孝感北", city: "孝感", lat: 31.4500, lon: 113.9000 },
      { id: "jingguang_15", name: "武汉", city: "武汉", lat: 30.6100, lon: 114.4300 },
      { id: "jingguang_16", name: "咸宁北", city: "咸宁", lat: 29.8600, lon: 114.3300 },
      { id: "jingguang_17", name: "岳阳东", city: "岳阳", lat: 29.3800, lon: 113.1600 },
      { id: "jingguang_18", name: "长沙南", city: "长沙", lat: 28.1500, lon: 113.0800 },
      { id: "jingguang_19", name: "株洲西", city: "株洲", lat: 27.8500, lon: 113.0800 },
      { id: "jingguang_20", name: "衡阳东", city: "衡阳", lat: 26.8500, lon: 112.6200 },
      { id: "jingguang_21", name: "郴州西", city: "郴州", lat: 25.7600, lon: 113.0200 },
      { id: "jingguang_22", name: "韶关", city: "韶关", lat: 24.8000, lon: 113.6100 },
      { id: "jingguang_23", name: "清远", city: "清远", lat: 23.7000, lon: 113.0600 },
      { id: "jingguang_24", name: "广州南", city: "广州", lat: 22.9900, lon: 113.2700 }
    ]
  },
  {
    id: "jingguang_zhoukou_branch_high_speed",
    name: "京广高铁周口支线",
    shortName: "京广周口支线",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "支线预研线路",
    parentLineId: "jingguang_high_speed",
    networkRole: "branch",
    source: "用户提供参考坐标；郑州东、阜阳西复用既有站点身份",
    stations: [
      { id: "jingguang_09", name: "郑州东", city: "郑州", lat: 34.7600, lon: 113.7700 },
      { id: "jingguang_zhoukou_02", name: "周口东", city: "周口", lat: 33.6420, lon: 114.7280 },
      { id: "shanghehang_03", name: "阜阳西", city: "阜阳", lat: 32.8900, lon: 115.8000 }
    ]
  },
  {
    id: "wujiu_high_speed",
    name: "武九高铁",
    shortName: "武九",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；武汉、九江复用既有站点身份",
    stations: [
      { id: "jingguang_15", name: "武汉", city: "武汉", lat: 30.6100, lon: 114.4300 },
      { id: "jingguang_wujiu_02", name: "鄂州站", city: "鄂州", lat: 30.3960, lon: 114.9010 },
      { id: "jingguang_wujiu_03", name: "黄石北站", city: "黄石", lat: 30.2160, lon: 115.0290 },
      { id: "heshen_03", name: "九江", city: "九江", lat: 29.7200, lon: 115.9800 }
    ]
  },
  {
    id: "jingxiongshang_high_speed",
    name: "京雄商高铁",
    shortName: "京雄商",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标",
    stations: [
      { id: "jingguang_01", name: "北京西", city: "北京", sourceLat: 39.8947, sourceLon: 116.3220, lat: 39.8947, lon: 116.2620 },
      { id: "jingxiongshang_02", name: "雄安", city: "雄安", lat: 39.0010, lon: 116.1000 },
      { id: "jingxiongshang_03", name: "衡水", city: "衡水", lat: 37.7380, lon: 115.7000 },
      { id: "jingxiongshang_04", name: "聊城西", city: "聊城", lat: 36.4300, lon: 115.9200 },
      { id: "jingxiongshang_05", name: "濮阳东", city: "濮阳", lat: 35.7700, lon: 115.0600 },
      { id: "jingxiongshang_06", name: "菏泽东", city: "菏泽", lat: 35.2450, lon: 115.5200 },
      { id: "jingxiongshang_07", name: "商丘", city: "商丘", lat: 34.4400, lon: 115.6500 }
    ]
  },
  {
    id: "shanghehang_high_speed",
    name: "商合杭高铁",
    shortName: "商合杭",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标",
    stations: [
      { id: "jingxiongshang_07", name: "商丘", city: "商丘", lat: 34.4400, lon: 115.6500 },
      { id: "shanghehang_02", name: "亳州南", city: "亳州", lat: 33.8700, lon: 115.7800 },
      { id: "shanghehang_03", name: "阜阳西", city: "阜阳", lat: 32.8900, lon: 115.8000 },
      { id: "shanghehang_04", name: "淮南南", city: "淮南", lat: 32.5800, lon: 116.9300 },
      { id: "shanghehang_05", name: "合肥南", city: "合肥", lat: 31.7800, lon: 117.3000 },
      { id: "shanghehang_06", name: "芜湖", city: "芜湖", lat: 31.3400, lon: 118.3900 },
      { id: "shanghehang_07", name: "宣城", city: "宣城", lat: 30.9500, lon: 118.7500 },
      { id: "shanghehang_08", name: "湖州", city: "湖州", lat: 30.8700, lon: 120.0900 },
      { id: "shanghehang_09", name: "杭州东", city: "杭州", lat: 30.3150, lon: 120.2100 }
    ]
  },
  {
    id: "heshen_high_speed",
    name: "合深高铁",
    shortName: "合深",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标",
    stations: [
      { id: "shanghehang_05", name: "合肥南", city: "合肥", lat: 31.7800, lon: 117.3000 },
      { id: "heshen_02", name: "六安", city: "六安", lat: 31.7500, lon: 116.5000 },
      { id: "heshen_03", name: "九江", city: "九江", lat: 29.7200, lon: 115.9800 },
      { id: "heshen_04", name: "南昌西", city: "南昌", lat: 28.6100, lon: 115.8200 },
      { id: "heshen_05", name: "吉安西", city: "吉安", lat: 27.1000, lon: 114.9800 },
      { id: "heshen_06", name: "赣州西", city: "赣州", lat: 25.8200, lon: 114.9200 },
      { id: "heshen_07", name: "河源东", city: "河源", lat: 23.7400, lon: 114.7000 },
      { id: "heshen_08", name: "惠州北", city: "惠州", lat: 23.1200, lon: 114.4200 },
      { id: "heshen_09", name: "东莞南", city: "东莞", lat: 22.9100, lon: 114.1400 },
      { id: "heshen_10", name: "深圳北", city: "深圳", lat: 22.6100, lon: 114.0300 }
    ]
  },
  {
    id: "heshen_meizhou_branch_high_speed",
    name: "合深高铁梅州支线",
    shortName: "合深梅州支线",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "支线预研线路",
    parentLineId: "heshen_high_speed",
    networkRole: "branch",
    source: "用户提供参考坐标；河源东、龙岩复用既有站点身份",
    stations: [
      { id: "heshen_07", name: "河源东", city: "河源", lat: 23.7400, lon: 114.7000 },
      { id: "heshen_meizhou_02", name: "梅州西", city: "梅州市", lat: 24.2920, lon: 116.0990 },
      { id: "yuxia_10", name: "龙岩", city: "龙岩", lat: 25.0950, lon: 117.0150 }
    ]
  },
  {
    id: "shenzhen_hongkong_high_speed",
    name: "深港高铁",
    shortName: "深港",
    type: "high_speed",
    typeLabel: "高速",
    region: "cross_region",
    regions: ["china_mainland", "hk_macao_taiwan"],
    boundaryLabel: "深港交界中点",
    status: "跨区域预研线路",
    source: "用户提供参考坐标",
    stations: [
      { id: "heshen_10", name: "深圳北", city: "深圳", region: "china_mainland", lat: 22.6100, lon: 114.0300 },
      { id: "shenzhen_hongkong_02", name: "香港西九龙", city: "香港", region: "hk_macao_taiwan", lat: 22.3030, lon: 114.1610 }
    ]
  },
  {
    id: "guangzhuanao_high_speed",
    name: "广珠澳高铁",
    shortName: "广珠澳",
    type: "high_speed",
    typeLabel: "高速",
    region: "cross_region",
    regions: ["china_mainland", "hk_macao_taiwan"],
    boundaryLabel: "珠澳交界中点",
    status: "跨区域预研线路",
    source: "用户提供参考坐标；广州南沙复用广深港高铁既有站点身份",
    stations: [
      { id: "guangshen_02", name: "广州南沙", city: "广州南沙", region: "china_mainland", lat: 22.8660, lon: 113.6720 },
      { id: "guangzhuanao_02", name: "中山", city: "中山", region: "china_mainland", lat: 22.5300, lon: 113.3920 },
      { id: "guangzhuanao_03", name: "珠海", city: "珠海", region: "china_mainland", lat: 22.2167, lon: 113.5530 },
      { id: "guangzhuanao_04", name: "澳门南", city: "澳门", region: "hk_macao_taiwan", lat: 22.0000, lon: 113.6500 }
    ]
  },
  {
    id: "shenjiang_high_speed",
    name: "深江高铁",
    shortName: "深江",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考站序；深圳北、中山、肇庆东复用既有站点身份",
    stations: [
      { id: "heshen_10", name: "深圳北", city: "深圳", lat: 22.6100, lon: 114.0300 },
      { id: "guangzhuanao_02", name: "中山", city: "中山", lat: 22.5300, lon: 113.3920 },
      { id: "shenjiang_03", name: "江门", city: "江门", lat: 22.5820, lon: 113.0940 },
      { id: "nanguang_03", name: "肇庆东", city: "肇庆", lat: 23.1100, lon: 112.6100 }
    ]
  },
  {
    id: "jinghu_high_speed",
    name: "京沪高铁",
    shortName: "京沪",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标",
    stations: [
      { id: "jinghu_01", name: "北京南", city: "北京", sourceLat: 39.8650, sourceLon: 116.3780, lat: 39.8650, lon: 116.4380 },
      { id: "jinghu_02", name: "廊坊", city: "廊坊", lat: 39.5200, lon: 116.6900 },
      { id: "jinghu_03", name: "天津南", city: "天津", lat: 39.0200, lon: 117.0600 },
      { id: "jinghu_04", name: "沧州西", city: "沧州", lat: 38.3100, lon: 116.8200 },
      { id: "jinghu_05", name: "德州东", city: "德州", lat: 37.4400, lon: 116.3600 },
      { id: "jinghu_06", name: "济南西", city: "济南", lat: 36.6700, lon: 116.9000 },
      { id: "jinghu_07", name: "泰安", city: "泰安", lat: 36.2000, lon: 117.0900 },
      { id: "jinghu_08", name: "枣庄站", city: "枣庄", lat: 34.7880, lon: 117.2630 },
      { id: "jinghu_09", name: "徐州东", city: "徐州", lat: 34.2650, lon: 117.2800 },
      { id: "jinghu_10", name: "宿州东", city: "宿州", lat: 33.6600, lon: 117.1500 },
      { id: "jinghu_11", name: "蚌埠南", city: "蚌埠", lat: 32.9400, lon: 117.3900 },
      { id: "jinghu_12", name: "滁州", city: "滁州", lat: 32.2600, lon: 118.3300 },
      { id: "jinghu_13", name: "南京南", city: "南京", lat: 31.9700, lon: 118.8000 },
      { id: "jinghu_14", name: "镇江南", city: "镇江", lat: 32.1400, lon: 119.4200 },
      { id: "jinghu_15", name: "常州北", city: "常州", lat: 31.8400, lon: 119.9700 },
      { id: "jinghu_16", name: "无锡东", city: "无锡", lat: 31.5900, lon: 120.4300 },
      { id: "jinghu_17", name: "苏州北", city: "苏州", lat: 31.4300, lon: 120.6500 },
      { id: "jinghu_18", name: "上海虹桥", city: "上海", lat: 31.1970, lon: 121.3300 }
    ]
  },
  {
    id: "jinghu_ningma_branch_high_speed",
    name: "京沪高铁宁马支线",
    shortName: "京沪宁马支线",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "支线预研线路",
    parentLineId: "jinghu_high_speed",
    networkRole: "branch",
    source: "用户提供参考坐标；南京南复用既有站点身份",
    stations: [
      { id: "jinghu_13", name: "南京南", city: "南京", lat: 31.9700, lon: 118.8000 },
      { id: "jinghu_ningma_02", name: "马鞍山站", city: "马鞍山", lat: 31.6700, lon: 118.5070 }
    ]
  },
  {
    id: "hukun_high_speed",
    name: "沪昆高铁",
    shortName: "沪昆",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标",
    stations: [
      { id: "jinghu_18", name: "上海虹桥", city: "上海", lat: 31.1970, lon: 121.3300 },
      { id: "hukun_02", name: "嘉兴南", city: "嘉兴", lat: 30.7500, lon: 120.7600 },
      { id: "shanghehang_09", name: "杭州东", city: "杭州", lat: 30.3150, lon: 120.2100 },
      { id: "hukun_04", name: "金华", city: "金华", lat: 29.1000, lon: 119.6500 },
      { id: "hukun_05", name: "衢州", city: "衢州", lat: 28.9700, lon: 118.8700 },
      { id: "hukun_06", name: "上饶", city: "上饶", lat: 28.4500, lon: 117.9700 },
      { id: "hukun_07", name: "鹰潭北", city: "鹰潭", lat: 28.2300, lon: 116.9700 },
      { id: "hukun_08", name: "抚州东", city: "抚州", lat: 28.0000, lon: 116.6100 },
      { id: "heshen_04", name: "南昌西", city: "南昌", lat: 28.6100, lon: 115.8200 },
      { id: "hukun_10", name: "宜春", city: "宜春", lat: 27.8000, lon: 114.3900 },
      { id: "hukun_11", name: "萍乡北", city: "萍乡", lat: 27.6200, lon: 113.9000 },
      { id: "jingguang_19", name: "株洲西", city: "株洲", lat: 27.8500, lon: 113.0800 },
      { id: "jingguang_18", name: "长沙南", city: "长沙", lat: 28.1500, lon: 113.0800 },
      { id: "hukun_14", name: "湘潭北", city: "湘潭", lat: 27.9500, lon: 112.9500 },
      { id: "hukun_15", name: "娄底南", city: "娄底", lat: 27.7000, lon: 112.0000 },
      { id: "hukun_16", name: "怀化南", city: "怀化", lat: 27.5500, lon: 109.9600 },
      { id: "hukun_17", name: "凯里南", city: "凯里", lat: 26.5800, lon: 107.9800 },
      { id: "hukun_18", name: "贵阳北", city: "贵阳", lat: 26.6500, lon: 106.6300 },
      { id: "hukun_19", name: "安顺西", city: "安顺", lat: 26.2500, lon: 105.9300 },
      { id: "hukun_20", name: "曲靖北", city: "曲靖", lat: 25.5200, lon: 103.8000 },
      { id: "hukun_21", name: "昆明南", city: "昆明", lat: 24.8740, lon: 102.8620 }
    ]
  },
  {
    id: "huyurong_high_speed",
    name: "沪渝蓉高铁",
    shortName: "沪渝蓉",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；六安复用既有站点坐标",
    stations: [
      { id: "huyurong_01", name: "上海东", city: "上海", lat: 31.2500, lon: 121.6800 },
      { id: "huyurong_02", name: "南通", city: "南通", lat: 31.9800, lon: 120.9000 },
      { id: "huyurong_03", name: "泰州", city: "泰州", lat: 32.4600, lon: 119.9200 },
      { id: "huyurong_04", name: "扬州东", city: "扬州", lat: 32.3900, lon: 119.4700 },
      { id: "huyurong_05", name: "南京北", city: "南京", lat: 32.1600, lon: 118.7300 },
      { id: "shanghehang_05", name: "合肥南", city: "合肥", lat: 31.7800, lon: 117.3000 },
      { id: "heshen_02", name: "六安", city: "六安", lat: 31.7500, lon: 116.5000 },
      { id: "huyurong_08", name: "汉口", city: "武汉", lat: 30.6200, lon: 114.2700 },
      { id: "huyurong_09", name: "江汉", city: "江汉", lat: 30.6500, lon: 113.1600 },
      { id: "huyurong_10", name: "荆门西", city: "荆门", lat: 31.0500, lon: 112.1600 },
      { id: "huyurong_11", name: "宜昌北", city: "宜昌", lat: 30.7600, lon: 111.3000 },
      { id: "huyurong_12", name: "恩施南", city: "恩施", lat: 30.2700, lon: 109.4700 },
      { id: "huyurong_13", name: "涪陵北", city: "涪陵", lat: 29.7200, lon: 107.3900 },
      { id: "huyurong_14", name: "重庆北", city: "重庆", lat: 29.6100, lon: 106.5500 },
      { id: "huyurong_15", name: "成都", city: "成都", sourceLat: 30.6600, sourceLon: 104.0700, lat: 30.7200, lon: 103.9800 }
    ]
  },
  {
    id: "lianxulan_high_speed",
    name: "连徐兰高铁",
    shortName: "连徐兰",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；复用既有站点身份",
    stations: [
      { id: "lianxulan_01", name: "连云港", city: "连云港", lat: 34.6000, lon: 119.2200 },
      { id: "jinghu_09", name: "徐州东", city: "徐州", lat: 34.2650, lon: 117.2800 },
      { id: "jingxiongshang_07", name: "商丘", city: "商丘", lat: 34.4400, lon: 115.6500 },
      { id: "lianxulan_04", name: "开封北", city: "开封", lat: 34.8200, lon: 114.3500 },
      { id: "jingguang_09", name: "郑州东", city: "郑州", lat: 34.7600, lon: 113.7700 },
      { id: "lianxulan_06", name: "洛阳龙门", city: "洛阳", lat: 34.6100, lon: 112.3900 },
      { id: "lianxulan_07", name: "三门峡南", city: "三门峡", lat: 34.7400, lon: 111.1900 },
      { id: "lianxulan_08", name: "渭南北", city: "渭南", lat: 34.5200, lon: 109.4800 },
      { id: "lianxulan_09", name: "西安北", city: "西安", lat: 34.3800, lon: 108.9400 },
      { id: "lianxulan_10", name: "咸阳西", city: "咸阳", lat: 34.3300, lon: 108.6500 },
      { id: "lianxulan_11", name: "宝鸡南", city: "宝鸡", lat: 34.3500, lon: 107.1500 },
      { id: "lianxulan_12", name: "天水南", city: "天水", lat: 34.5600, lon: 105.8700 },
      { id: "lianxulan_13", name: "定西北", city: "定西", lat: 35.5800, lon: 104.6300 },
      { id: "lianxulan_14", name: "兰州西", city: "兰州", lat: 36.0675, lon: 103.7492 }
    ]
  },
  {
    id: "zhengyu_high_speed",
    name: "郑渝高铁",
    shortName: "郑渝",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；复用既有站点身份",
    stations: [
      { id: "jingguang_09", name: "郑州东", city: "郑州", lat: 34.7600, lon: 113.7700 },
      { id: "zhengyu_02", name: "平顶山西", city: "平顶山", lat: 33.7400, lon: 113.3000 },
      { id: "zhengyu_03", name: "南阳东", city: "南阳", lat: 32.9800, lon: 112.6000 },
      { id: "zhengyu_04", name: "襄阳东", city: "襄阳", lat: 32.0400, lon: 112.2000 },
      { id: "zhengyu_05", name: "神农架", city: "神农架", lat: 31.7400, lon: 110.6800 },
      { id: "zhengyu_06", name: "万州北", city: "万州", lat: 30.8200, lon: 108.3900 },
      { id: "huyurong_13", name: "涪陵北", city: "涪陵", lat: 29.7200, lon: 107.3900 },
      { id: "huyurong_14", name: "重庆北", city: "重庆", lat: 29.6100, lon: 106.5500 }
    ]
  },
  {
    id: "nanxinhe_high_speed",
    name: "南信合高铁",
    shortName: "南信合",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户指定站序；南阳、信阳、六安复用既有站点身份",
    stations: [
      { id: "zhengyu_03", name: "南阳东", city: "南阳", lat: 32.9800, lon: 112.6000 },
      { id: "jingguang_13", name: "信阳东", city: "信阳", lat: 32.1500, lon: 114.1200 },
      { id: "heshen_02", name: "六安", city: "六安", lat: 31.7500, lon: 116.5000 }
    ]
  },
  {
    id: "xicheng_high_speed",
    name: "西成高铁",
    shortName: "西成",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；西安北复用既有站点身份",
    stations: [
      { id: "lianxulan_09", name: "西安北", city: "西安", lat: 34.3800, lon: 108.9400 },
      { id: "xicheng_02", name: "汉中", city: "汉中", lat: 33.0630, lon: 107.0230 },
      { id: "xicheng_03", name: "广元", city: "广元", lat: 32.4400, lon: 105.8280 },
      { id: "xicheng_04", name: "绵阳", city: "绵阳", lat: 31.4590, lon: 104.7410 },
      { id: "xicheng_05", name: "德阳", city: "德阳", lat: 31.1300, lon: 104.3970 },
      { id: "xicheng_06", name: "成都东", city: "成都", lat: 30.6320, lon: 104.1410 }
    ]
  },
  {
    id: "hanbanan_high_speed",
    name: "汉巴南铁路",
    shortName: "汉巴南",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考站序；汉中、南充复用既有站点身份",
    stations: [
      { id: "xicheng_02", name: "汉中", city: "汉中", lat: 33.0630, lon: 107.0230 },
      { id: "bazhong_01", name: "巴中", city: "巴中", lat: 31.8762, lon: 106.7612 },
      { id: "langyu_04", name: "南充北", city: "南充", lat: 30.8560, lon: 106.0710 }
    ]
  },
  {
    id: "chenggui_high_speed",
    name: "成贵高铁",
    shortName: "成贵",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；成都东、宜宾西复用既有站点身份",
    stations: [
      { id: "xicheng_06", name: "成都东", city: "成都", lat: 30.6320, lon: 104.1410 },
      { id: "chenggui_02", name: "眉山东", city: "眉山", lat: 30.0500, lon: 103.8700 },
      { id: "chenggui_03", name: "乐山", city: "乐山", lat: 29.5700, lon: 103.7600 },
      { id: "yukun_03", name: "宜宾西", city: "宜宾", lat: 28.7510, lon: 104.6200 },
      { id: "chenggui_05", name: "毕节", city: "毕节", lat: 27.3000, lon: 105.2800 },
      { id: "hukun_18", name: "贵阳北", city: "贵阳", lat: 26.6500, lon: 106.6300 }
    ]
  },
  {
    id: "jingha_high_speed",
    name: "京哈高铁",
    shortName: "京哈",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标",
    stations: [
      { id: "jingha_01", name: "北京朝阳", city: "北京", sourceLat: 39.9440, sourceLon: 116.5060, lat: 40.0350, lon: 116.5060 },
      { id: "jingha_02", name: "承德南", city: "承德", lat: 40.8850, lon: 117.9650 },
      { id: "jingha_03", name: "朝阳", city: "朝阳", lat: 41.5980, lon: 120.4040 },
      { id: "jingha_04", name: "阜新", city: "阜新", lat: 42.0500, lon: 121.6700 },
      { id: "jingha_05", name: "沈阳北", city: "沈阳", lat: 41.8170, lon: 123.4360 },
      { id: "jingha_06", name: "铁岭西", city: "铁岭", lat: 42.2330, lon: 123.6730 },
      { id: "jingha_07", name: "四平东", city: "四平", lat: 43.1390, lon: 124.4380 },
      { id: "jingha_08", name: "长春西", city: "长春", lat: 43.8770, lon: 125.2010 },
      { id: "jingha_09", name: "哈尔滨西", city: "哈尔滨", lat: 45.7070, lon: 126.5770 }
    ]
  },
  {
    id: "guangshenhongkong_high_speed",
    name: "广深港高铁",
    shortName: "广深港",
    type: "high_speed",
    typeLabel: "高速",
    region: "cross_region",
    regions: ["china_mainland", "hk_macao_taiwan"],
    boundaryLabel: "深港交界中点",
    status: "跨区域预研线路",
    source: "用户提供参考坐标；复用既有站点身份",
    stations: [
      { id: "jingguang_24", name: "广州南", city: "广州", region: "china_mainland", lat: 22.9900, lon: 113.2700 },
      { id: "guangshen_02", name: "广州南沙", city: "广州南沙", region: "china_mainland", lat: 22.8660, lon: 113.6720 },
      { id: "heshen_10", name: "深圳北", city: "深圳", region: "china_mainland", lat: 22.6100, lon: 114.0300 },
      { id: "shenzhen_hongkong_02", name: "香港西九龙", city: "香港", region: "hk_macao_taiwan", lat: 22.3030, lon: 114.1610 }
    ]
  },
  {
    id: "langyu_conventional",
    name: "兰渝铁路",
    shortName: "兰渝",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考坐标；广元、广安南复用既有站点身份",
    stations: [
      { id: "lianxulan_14", name: "兰州西", city: "兰州", lat: 36.0675, lon: 103.7492 },
      { id: "langyu_02", name: "陇南", city: "陇南", lat: 33.3803, lon: 104.9600 },
      { id: "xicheng_03", name: "广元", city: "广元", lat: 32.4400, lon: 105.8280 },
      { id: "langyu_04", name: "南充北", city: "南充", lat: 30.8560, lon: 106.0710 },
      { id: "langyu_05", name: "广安南", city: "广安", lat: 30.4700, lon: 106.6300 }
    ]
  },
  {
    id: "langyu_bazhong_branch_conventional",
    name: "兰渝铁路巴中支线",
    shortName: "兰渝巴中支线",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考站序；广元复用既有站点身份",
    stations: [
      { id: "xicheng_03", name: "广元", city: "广元", lat: 32.4400, lon: 105.8280 },
      { id: "bazhong_01", name: "巴中", city: "巴中", lat: 31.8762, lon: 106.7612 }
    ]
  },
  {
    id: "jingbao_high_speed",
    name: "京包高铁",
    shortName: "京包",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；北京北使用错开后的工作坐标",
    stations: [
      { id: "jingbao_01", name: "北京北", city: "北京", sourceLat: 39.9447, sourceLon: 116.3535, lat: 40.0800, lon: 116.2000 },
      { id: "jingbao_02", name: "张家口", city: "张家口", lat: 40.7520, lon: 114.8828 },
      { id: "jingbao_03", name: "乌兰察布", city: "乌兰察布", lat: 40.9642, lon: 113.1633 },
      { id: "jingbao_04", name: "呼和浩特东", city: "呼和浩特", lat: 40.8511, lon: 111.7653 },
      { id: "jingbao_05", name: "包头", city: "包头", lat: 40.6054, lon: 109.8366 }
    ]
  },
  {
    id: "zhangdaxi_high_speed",
    name: "张大西高铁",
    shortName: "张大西",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；复用既有站点身份",
    stations: [
      { id: "jingbao_02", name: "张家口", city: "张家口", lat: 40.7520, lon: 114.8828 },
      { id: "zhangdaxi_02", name: "大同南", city: "大同", lat: 40.0200, lon: 113.1500 },
      { id: "zhangdaxi_03", name: "朔州东", city: "朔州", lat: 39.3200, lon: 112.4300 },
      { id: "zhangdaxi_04", name: "忻州西", city: "忻州", lat: 38.4200, lon: 112.7300 },
      { id: "zhangdaxi_05", name: "太原南", city: "太原", lat: 37.7800, lon: 112.5600 },
      { id: "zhangdaxi_06", name: "晋中", city: "晋中", lat: 37.6800, lon: 112.7300 },
      { id: "zhangdaxi_07", name: "临汾西", city: "临汾", lat: 36.0900, lon: 111.5000 },
      { id: "zhangdaxi_08", name: "运城北", city: "运城", lat: 35.0700, lon: 110.9900 },
      { id: "lianxulan_08", name: "渭南北", city: "渭南", lat: 34.5200, lon: 109.4800 },
      { id: "lianxulan_09", name: "西安北", city: "西安", lat: 34.3800, lon: 108.9400 }
    ]
  },
  {
    id: "rila_high_speed",
    name: "日兰高铁",
    shortName: "日兰",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；菏泽东、开封北复用既有站点身份",
    stations: [
      { id: "rila_01", name: "日照西", city: "日照", lat: 35.4160, lon: 119.3540 },
      { id: "rila_02", name: "临沂北", city: "临沂", lat: 35.1240, lon: 118.3780 },
      { id: "rila_03", name: "济宁北", city: "济宁", lat: 35.5000, lon: 116.5800 },
      { id: "jingxiongshang_06", name: "菏泽东", city: "菏泽", lat: 35.2450, lon: 115.5200 },
      { id: "lianxulan_04", name: "开封北", city: "开封", lat: 34.8200, lon: 114.3500 }
    ]
  },
  {
    id: "shitaiyin_high_speed",
    name: "石太银高铁",
    shortName: "石太银",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户指定线路合并；石家庄、太原南、银川复用既有站点身份；巴彦浩特为新终点",
    stations: [
      { id: "jingguang_03", name: "石家庄", city: "石家庄", lat: 38.0225, lon: 114.4840 },
      { id: "shita_02", name: "阳泉北", city: "阳泉", lat: 38.0600, lon: 113.6300 },
      { id: "zhangdaxi_05", name: "太原南", city: "太原", lat: 37.7800, lon: 112.5600 },
      { id: "taiyin_02", name: "吕梁", city: "吕梁", lat: 37.5675, lon: 111.1311 },
      { id: "xiyubao_04", name: "榆林南", city: "榆林", lat: 38.2190, lon: 109.7340 },
      { id: "baoyin_06", name: "银川", city: "银川", lat: 38.4942, lon: 106.1633 },
      { id: "taiyin_04", name: "巴彦浩特", city: "阿拉善盟", lat: 38.8390, lon: 105.6680 }
    ]
  },
  {
    id: "chengyu_high_speed",
    name: "成渝高铁",
    shortName: "成渝",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；成都东复用既有站点身份",
    stations: [
      { id: "xicheng_06", name: "成都东", city: "成都", lat: 30.6320, lon: 104.1410 },
      { id: "chengyu_02", name: "资阳北", city: "资阳", lat: 30.1360, lon: 104.6160 },
      { id: "chengyu_03", name: "内江北", city: "内江", lat: 29.6126, lon: 105.0817 },
      { id: "chengyu_04", name: "重庆西", city: "重庆", lat: 29.5020, lon: 106.4380 }
    ]
  },
  {
    id: "jizheng_high_speed",
    name: "济郑高铁",
    shortName: "济郑",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；全线复用既有站点身份",
    stations: [
      { id: "jinghu_06", name: "济南西", city: "济南", lat: 36.6700, lon: 116.9000 },
      { id: "jingxiongshang_04", name: "聊城西", city: "聊城", lat: 36.4300, lon: 115.9200 },
      { id: "jingxiongshang_05", name: "濮阳东", city: "濮阳", lat: 35.7700, lon: 115.0600 },
      { id: "jingguang_09", name: "郑州东", city: "郑州", lat: 34.7600, lon: 113.7700 }
    ]
  },
  {
    id: "baoyin_high_speed",
    name: "包银高铁",
    shortName: "包银",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；包头复用既有站点身份",
    stations: [
      { id: "jingbao_05", name: "包头", city: "包头", note: "与京包高铁衔接", lat: 40.6054, lon: 109.8366 },
      { id: "baoyin_02", name: "巴彦淖尔", city: "巴彦淖尔", note: "河套平原中心", lat: 40.7336, lon: 107.4048 },
      { id: "baoyin_04", name: "乌海", city: "乌海", note: "内蒙古西部节点", lat: 39.6689, lon: 106.8010 },
      { id: "baoyin_05", name: "石嘴山", city: "石嘴山", note: "宁夏北部地级市", lat: 38.9575, lon: 106.3770 },
      { id: "baoyin_06", name: "银川", city: "银川", note: "宁夏首府、线路终点", lat: 38.4942, lon: 106.1633 }
    ]
  },
  {
    id: "nanguang_high_speed",
    name: "南广高铁",
    shortName: "南广",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；广州南复用既有站点身份",
    stations: [
      { id: "jingguang_24", name: "广州南", city: "广州", lat: 22.9900, lon: 113.2700 },
      { id: "nanguang_02", name: "佛山西", city: "佛山", lat: 23.0900, lon: 112.9000 },
      { id: "nanguang_03", name: "肇庆东", city: "肇庆", lat: 23.1100, lon: 112.6100 },
      { id: "nanguang_04", name: "云浮东", city: "云浮", lat: 22.9300, lon: 112.0500 },
      { id: "nanguang_05", name: "梧州南", city: "梧州", lat: 23.5000, lon: 111.2500 },
      { id: "nanguang_06", name: "贵港", city: "贵港", lat: 23.0900, lon: 109.6100 },
      { id: "nanguang_07", name: "南宁东", city: "南宁", lat: 22.8400, lon: 108.3700 }
    ]
  },
  {
    id: "yuegui_conventional",
    name: "粤桂铁路",
    shortName: "粤桂",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考坐标；云浮东、贵港复用既有站点身份",
    stations: [
      { id: "nanguang_04", name: "云浮东", city: "云浮", lat: 22.9300, lon: 112.0500 },
      { id: "yuegui_02", name: "茂名", city: "茂名", lat: 21.6600, lon: 110.9200 },
      { id: "yuegui_03", name: "玉林", city: "玉林", lat: 22.6300, lon: 110.1500 },
      { id: "nanguang_06", name: "贵港", city: "贵港", lat: 23.0900, lon: 109.6100 }
    ]
  },
  {
    id: "guangzhan_high_speed",
    name: "广湛高铁",
    shortName: "广湛",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；佛山西、云浮东、茂名复用既有站点身份",
    stations: [
      { id: "nanguang_02", name: "佛山西", city: "佛山", lat: 23.0900, lon: 112.9000 },
      { id: "nanguang_03", name: "肇庆东", city: "肇庆", lat: 23.1100, lon: 112.6100 },
      { id: "nanguang_04", name: "云浮东", city: "云浮", lat: 22.9300, lon: 112.0500 },
      { id: "guangzhan_03", name: "阳江", city: "阳江", lat: 21.8700, lon: 111.9800 },
      { id: "yuegui_02", name: "茂名", city: "茂名", lat: 21.6600, lon: 110.9200 },
      { id: "guangzhan_05", name: "湛江北", city: "湛江", lat: 21.2700, lon: 110.3500 }
    ]
  },
  {
    id: "nankun_high_speed",
    name: "南昆高铁",
    shortName: "南昆",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；南宁东、百色、昆明南复用既有站点身份",
    stations: [
      { id: "nanguang_07", name: "南宁东", city: "南宁", lat: 22.8400, lon: 108.3700 },
      { id: "nankun_02", name: "百色", city: "百色", lat: 23.9000, lon: 106.6100 },
      { id: "nankun_03", name: "文山", city: "文山", lat: 23.3700, lon: 104.2400 },
      { id: "nankun_04", name: "蒙自", city: "蒙自", lat: 23.3700, lon: 103.3800 },
      { id: "hukun_21", name: "昆明南", city: "昆明", lat: 24.8740, lon: 102.8620 }
    ]
  },
  {
    id: "nankun_conventional",
    name: "南昆铁路",
    shortName: "南昆",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考坐标；百色、昆明南复用既有站点身份",
    stations: [
      { id: "nankun_02", name: "百色", city: "百色", lat: 23.9000, lon: 106.6100 },
      { id: "nankun_railway_03", name: "兴义", city: "兴义", lat: 25.0900, lon: 104.9000 },
      { id: "hukun_21", name: "昆明南", city: "昆明", lat: 24.8740, lon: 102.8620 }
    ]
  },
  {
    id: "yunan_high_speed",
    name: "渝南高铁",
    shortName: "渝南",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户确认线路方案；重庆西、贵阳北、南宁东复用既有站点身份",
    stations: [
      { id: "chengyu_04", name: "重庆西", city: "重庆", lat: 29.5020, lon: 106.4380 },
      { id: "yunan_02", name: "遵义", city: "遵义", lat: 27.7254, lon: 106.9272 },
      { id: "hukun_18", name: "贵阳北", city: "贵阳", lat: 26.6500, lon: 106.6300 },
      { id: "yunan_04", name: "都匀东", city: "都匀", lat: 26.2600, lon: 107.5200 },
      { id: "yunan_05", name: "河池西", city: "河池", lat: 24.6900, lon: 108.0200 },
      { id: "nanguang_07", name: "南宁东", city: "南宁", lat: 22.8400, lon: 108.3700 }
    ]
  },
  {
    id: "hangshen_high_speed",
    name: "杭深高铁",
    shortName: "杭深",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；杭州东、惠州北、深圳北复用既有站点身份",
    stations: [
      { id: "shanghehang_09", name: "杭州东", city: "杭州", lat: 30.3150, lon: 120.2100 },
      { id: "hangshen_02", name: "绍兴北", city: "绍兴", lat: 30.1090, lon: 120.5360 },
      { id: "hangshen_03", name: "宁波", city: "宁波", lat: 29.8620, lon: 121.5360 },
      { id: "hangshen_04", name: "台州西", city: "台州", lat: 28.6570, lon: 121.3040 },
      { id: "hangshen_05", name: "温州南", city: "温州", lat: 27.9720, lon: 120.5850 },
      { id: "hangshen_06", name: "宁德", city: "宁德", lat: 26.6650, lon: 119.5880 },
      { id: "hangshen_07", name: "福州南", city: "福州", lat: 25.9850, lon: 119.3900 },
      { id: "hangshen_08", name: "莆田", city: "莆田", lat: 25.3550, lon: 119.0630 },
      { id: "hangshen_09", name: "泉州东", city: "泉州", lat: 24.9247, lon: 118.7658 },
      { id: "hangshen_10", name: "厦门北", city: "厦门", lat: 24.6370, lon: 118.0740 },
      { id: "hangshen_11", name: "漳州", city: "漳州", lat: 24.5030, lon: 117.6640 },
      { id: "hangshen_12", name: "潮汕", city: "潮州／汕头", lat: 23.5400, lon: 116.5900 },
      { id: "hangshen_13", name: "汕尾", city: "汕尾", lat: 22.7860, lon: 115.3820 },
      { id: "heshen_08", name: "惠州北", city: "惠州", lat: 23.1200, lon: 114.4200 }
    ]
  },
  {
    id: "lanxin_high_speed",
    name: "兰新高铁",
    shortName: "兰新",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；兰州西复用既有站点身份",
    stations: [
      { id: "lianxulan_14", name: "兰州西", city: "兰州", lat: 36.0675, lon: 103.7492 },
      { id: "lanxin_02", name: "海东西", city: "海东", lat: 36.5095, lon: 102.0535 },
      { id: "lanxin_03", name: "西宁", city: "西宁", lat: 36.6217, lon: 101.8067 },
      { id: "lanxin_04", name: "张掖西", city: "张掖", lat: 38.9250, lon: 100.4210 },
      { id: "lanxin_05", name: "酒泉南", city: "酒泉", lat: 39.7037, lon: 98.5362 },
      { id: "lanxin_06", name: "嘉峪关南", city: "嘉峪关", lat: 39.6870, lon: 98.2900 },
      { id: "lanxin_07", name: "哈密", city: "哈密", lat: 42.8200, lon: 93.5150 },
      { id: "lanxin_08", name: "吐鲁番北", city: "吐鲁番", lat: 43.0160, lon: 89.1830 },
      { id: "lanxin_09", name: "乌鲁木齐", city: "乌鲁木齐", lat: 43.8310, lon: 87.5350 }
    ]
  },
  {
    id: "lanzhang_high_speed",
    name: "兰张高铁",
    shortName: "兰张",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；兰州西、张掖西复用既有站点身份",
    stations: [
      { id: "lianxulan_14", name: "兰州西", city: "兰州", lat: 36.0670, lon: 103.7490 },
      { id: "lanzhang_02", name: "武威东", city: "武威", lat: 37.9200, lon: 102.7100 },
      { id: "lanzhang_03", name: "金昌南", city: "金昌", lat: 38.4300, lon: 102.1800 },
      { id: "lanxin_04", name: "张掖西", city: "张掖", lat: 38.9250, lon: 100.4130 }
    ]
  },
  {
    id: "jiqing_high_speed",
    name: "济青高铁",
    shortName: "济青",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标",
    stations: [
      { id: "jiqing_01", name: "济南东", city: "济南", lat: 36.7670, lon: 117.2090 },
      { id: "jiqing_02", name: "淄博北", city: "淄博", lat: 36.8750, lon: 118.1030 },
      { id: "jiqing_03", name: "潍坊北", city: "潍坊", lat: 36.7800, lon: 119.1550 },
      { id: "jiqing_04", name: "青岛北", city: "青岛", lat: 36.1690, lon: 120.3760 }
    ]
  },
  {
    id: "jiqing_binlin_branch_high_speed",
    name: "济青高铁滨临支线",
    shortName: "济青滨临支线",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "支线预研线路",
    parentLineId: "jiqing_high_speed",
    networkRole: "branch",
    source: "用户指定站序；滨州、淄博、临沂复用既有站点身份",
    stations: [
      { id: "jinwei_02", name: "滨州", city: "滨州", lat: 37.3800, lon: 118.0170 },
      { id: "jiqing_02", name: "淄博北", city: "淄博", lat: 36.8750, lon: 118.1030 },
      { id: "rila_02", name: "临沂北", city: "临沂", lat: 35.1240, lon: 118.3780 }
    ]
  },
  {
    id: "baozhong_conventional",
    name: "宝中铁路",
    shortName: "宝中",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考坐标；宝鸡、固原、中卫复用既有站点身份",
    stations: [
      { id: "lianxulan_11", name: "宝鸡南", city: "宝鸡", lat: 34.3500, lon: 107.1500 },
      { id: "baozhong_02", name: "平凉", city: "平凉", lat: 35.5506, lon: 106.7079 },
      { id: "baozhong_03", name: "固原", city: "固原", lat: 36.0110, lon: 106.2850 },
      { id: "yinlan_03", name: "中卫南", city: "中卫", lat: 37.4767, lon: 105.1744 }
    ]
  },
  {
    id: "chengkun_conventional",
    name: "成昆铁路",
    shortName: "成昆",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考坐标；乐山、昆明南复用既有站点身份",
    stations: [
      { id: "chenggui_03", name: "乐山", city: "乐山", lat: 29.5700, lon: 103.7600 },
      { id: "chengkun_02", name: "西昌西", city: "凉山州", lat: 27.8718, lon: 102.1591 },
      { id: "chengkun_03", name: "攀枝花南", city: "攀枝花", lat: 26.4714, lon: 101.7463 },
      { id: "chengkun_04", name: "楚雄", city: "楚雄州", lat: 25.0360, lon: 101.5460 },
      { id: "hukun_21", name: "昆明南", city: "昆明", lat: 24.8740, lon: 102.8620 }
    ]
  },
  {
    id: "kunmo_conventional",
    name: "昆磨铁路",
    shortName: "昆磨",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考坐标；昆明南复用既有站点身份",
    stations: [
      { id: "hukun_21", name: "昆明南", city: "昆明", lat: 24.8740, lon: 102.8620 },
      { id: "kunmo_02", name: "玉溪", city: "玉溪", lat: 24.3510, lon: 102.5420 },
      { id: "kunmo_03", name: "普洱", city: "普洱", lat: 22.7890, lon: 100.9810 },
      { id: "kunmo_04", name: "景洪", city: "西双版纳州", lat: 22.0060, lon: 100.7970 }
    ]
  },
  {
    id: "darui_conventional",
    name: "大瑞铁路",
    shortName: "大瑞",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考坐标；大理复用既有站点身份",
    stations: [
      { id: "diancang_03", name: "大理", city: "大理州", lat: 25.5920, lon: 100.2485 },
      { id: "darui_02", name: "保山", city: "保山", lat: 25.1270, lon: 99.1770 },
      { id: "darui_03", name: "芒市", city: "德宏州", lat: 24.4340, lon: 98.5840 }
    ]
  },
  {
    id: "darui_lushui_branch_conventional",
    name: "大瑞铁路泸水支线",
    shortName: "大瑞泸水支线",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "支线预研线路",
    parentLineId: "darui_conventional",
    networkRole: "branch",
    source: "用户提供参考坐标；保山复用大瑞铁路既有站点身份",
    stations: [
      { id: "darui_02", name: "保山", city: "保山", lat: 25.1270, lon: 99.1770 },
      { id: "darui_lushui_02", name: "泸水", city: "怒江州", lat: 25.8510, lon: 98.8570 }
    ]
  },
  {
    id: "kunmo_lincang_branch_conventional",
    name: "昆磨铁路临沧支线",
    shortName: "昆磨临沧支线",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "支线预研线路",
    parentLineId: "kunmo_conventional",
    networkRole: "branch",
    source: "用户指定站序；普洱、临沧、大理复用既有站点身份",
    stations: [
      { id: "kunmo_03", name: "普洱", city: "普洱", lat: 22.7890, lon: 100.9810 },
      { id: "dalin_02", name: "临沧", city: "临沧", lat: 23.8860, lon: 100.0880 },
      { id: "diancang_03", name: "大理", city: "大理州", lat: 25.5920, lon: 100.2485 }
    ]
  },
  {
    id: "hamu_jia_high_speed",
    name: "哈牡佳高铁",
    shortName: "哈牡佳",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；哈尔滨复用既有站点身份",
    stations: [
      { id: "jingha_09", name: "哈尔滨西", city: "哈尔滨", lat: 45.7070, lon: 126.5770 },
      { id: "hamujia_02", name: "牡丹江", city: "牡丹江", lat: 44.5877, lon: 129.6065 },
      { id: "hamujia_03", name: "鸡西西", city: "鸡西", lat: 45.3088, lon: 130.8148 },
      { id: "hamujia_04", name: "七台河西", city: "七台河", lat: 45.7423, lon: 130.7737 },
      { id: "hamujia_05", name: "双鸭山西", city: "双鸭山", lat: 46.7054, lon: 131.0846 },
      { id: "hamujia_06", name: "佳木斯", city: "佳木斯", lat: 46.8040, lon: 130.3836 }
    ]
  },
  {
    id: "yuxia_high_speed",
    name: "渝厦高铁",
    shortName: "渝厦",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；萍乡北、吉安西、赣州西、漳州、厦门北复用既有站点身份",
    stations: [
      { id: "yuxia_01", name: "重庆东", city: "重庆", lat: 29.5000, lon: 106.6500 },
      { id: "yuxia_02", name: "黔江", city: "重庆黔江", lat: 29.4750, lon: 108.7700 },
      { id: "yuxia_03", name: "张家界西", city: "张家界", lat: 29.1300, lon: 110.4500 },
      { id: "yuxia_04", name: "常德", city: "常德", lat: 29.0550, lon: 111.7000 },
      { id: "yuxia_05", name: "益阳南", city: "益阳", lat: 28.5250, lon: 112.3550 },
      { id: "yuxia_06", name: "长沙西", city: "长沙", lat: 28.3200, lon: 112.8050 },
      { id: "hukun_11", name: "萍乡北", city: "萍乡", lat: 27.6200, lon: 113.9000 },
      { id: "heshen_05", name: "吉安西", city: "吉安", lat: 27.1000, lon: 114.9800 },
      { id: "heshen_06", name: "赣州西", city: "赣州", lat: 25.8200, lon: 114.9200 },
      { id: "yuxia_10", name: "龙岩", city: "龙岩", lat: 25.0950, lon: 117.0150 },
      { id: "hangshen_11", name: "漳州", city: "漳州", lat: 24.5030, lon: 117.6640 },
      { id: "hangshen_10", name: "厦门北", city: "厦门", lat: 24.6370, lon: 118.0740 }
    ]
  },
  {
    id: "hefu_high_speed",
    name: "合福高铁",
    shortName: "合福",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；合肥南、芜湖、上饶、福州南复用既有站点身份",
    stations: [
      { id: "shanghehang_05", name: "合肥南", city: "合肥", lat: 31.7800, lon: 117.3000 },
      { id: "shanghehang_06", name: "芜湖", city: "芜湖", lat: 31.3400, lon: 118.3900 },
      { id: "hefu_03", name: "铜陵北", city: "铜陵", lat: 30.9450, lon: 117.8400 },
      { id: "hefu_04", name: "黄山北", city: "黄山", lat: 29.8150, lon: 118.2950 },
      { id: "hukun_06", name: "上饶", city: "上饶", lat: 28.4500, lon: 117.9700 },
      { id: "hefu_06", name: "南平", city: "南平", lat: 27.6550, lon: 118.0800 },
      { id: "hangshen_07", name: "福州南", city: "福州", lat: 25.9850, lon: 119.3900 }
    ]
  },
  {
    id: "heanqihuang_high_speed",
    name: "合安池黄高铁",
    shortName: "合安池黄",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；合肥南、黄山北复用既有站点身份",
    stations: [
      { id: "shanghehang_05", name: "合肥南", city: "合肥", lat: 31.7800, lon: 117.3000 },
      { id: "heanqihuang_02", name: "安庆站", city: "安庆", lat: 30.5430, lon: 117.0630 },
      { id: "heanqihuang_03", name: "池州站", city: "池州", lat: 30.6640, lon: 117.4910 },
      { id: "hefu_04", name: "黄山北", city: "黄山", lat: 29.8150, lon: 118.2950 }
    ]
  },
  {
    id: "xiwu_high_speed",
    name: "西武高铁",
    shortName: "西武",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；襄阳东、汉口复用既有站点身份",
    stations: [
      { id: "xiwu_01", name: "西安东", city: "西安", lat: 34.2490, lon: 109.1370 },
      { id: "xiwu_02", name: "商洛西", city: "商洛", lat: 33.8720, lon: 109.8340 },
      { id: "xiwu_03", name: "十堰东", city: "十堰", lat: 32.6460, lon: 110.8540 },
      { id: "zhengyu_04", name: "襄阳东", city: "襄阳", lat: 32.0400, lon: 112.2000 },
      { id: "xiwu_05", name: "随州南", city: "随州", lat: 31.6350, lon: 113.3820 },
      { id: "huyurong_08", name: "汉口", city: "武汉", lat: 30.6200, lon: 114.2700 }
    ]
  },
  {
    id: "hanshi_high_speed",
    name: "汉十南高铁",
    shortName: "汉十南",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户指定站序；汉中、安康、十堰、南阳复用既有站点身份",
    stations: [
      { id: "xicheng_02", name: "汉中", city: "汉中", lat: 33.0630, lon: 107.0230 },
      { id: "xiyu_02", name: "安康西", city: "安康", lat: 32.7330, lon: 108.9464 },
      { id: "xiwu_03", name: "十堰东", city: "十堰", lat: 32.6460, lon: 110.8540 },
      { id: "zhengyu_03", name: "南阳东", city: "南阳", lat: 32.9800, lon: 112.6000 }
    ]
  },
  {
    id: "shenda_high_speed",
    name: "沈大高铁",
    shortName: "沈大",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；沈阳北复用既有站点身份",
    stations: [
      { id: "jingha_05", name: "沈阳北", city: "沈阳", lat: 41.8170, lon: 123.4360 },
      { id: "shenda_02", name: "辽阳", city: "辽阳", lat: 41.2700, lon: 123.1740 },
      { id: "shenda_03", name: "鞍山西", city: "鞍山", lat: 41.1080, lon: 122.9220 },
      { id: "shenda_04", name: "营口东", city: "营口", lat: 40.6250, lon: 122.3580 },
      { id: "shenda_05", name: "大连北", city: "大连", lat: 39.0140, lon: 121.6150 }
    ]
  },
  {
    id: "shenda_panjin_branch",
    name: "沈大高铁·盘锦支线",
    shortName: "盘锦支线",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "支线预研线路",
    parentLineId: "shenda_high_speed",
    networkRole: "branch",
    source: "用户提供参考坐标；营口东复用沈大高铁主线站点身份",
    stations: [
      { id: "jinqinshen_05", name: "锦州南", city: "锦州", sourceLat: 41.0172, sourceLon: 121.1254, lat: 41.0600, lon: 121.1510 },
      { id: "shenda_branch_02", name: "盘锦", city: "盘锦", lat: 41.1240, lon: 122.0700 },
      { id: "shenda_04", name: "营口东", city: "营口", sourceLat: 40.6195, sourceLon: 122.4260, lat: 40.6250, lon: 122.3580 }
    ]
  },
  {
    id: "danda_conventional",
    name: "丹大铁路",
    shortName: "丹大",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考坐标；大连北复用既有站点身份",
    stations: [
      { id: "danda_01", name: "丹东", city: "丹东", lat: 40.1290, lon: 124.3970 },
      { id: "shenda_05", name: "大连北", city: "大连", lat: 39.0140, lon: 121.6150 }
    ]
  },
  {
    id: "jinqinshen_high_speed",
    name: "津秦沈高铁",
    shortName: "津秦沈",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；沈阳北复用既有站点身份",
    stations: [
      { id: "jinqinshen_01", name: "天津", city: "天津", lat: 39.1420, lon: 117.1760 },
      { id: "jinqinshen_02", name: "唐山", city: "唐山", lat: 39.6320, lon: 118.1800 },
      { id: "jinqinshen_03", name: "秦皇岛", city: "秦皇岛", lat: 39.9490, lon: 119.6040 },
      { id: "jinqinshen_04", name: "葫芦岛北", city: "葫芦岛", lat: 40.7560, lon: 120.8400 },
      { id: "jinqinshen_05", name: "锦州南", city: "锦州", lat: 41.0600, lon: 121.1510 },
      { id: "jingha_05", name: "沈阳北", city: "沈阳", lat: 41.8170, lon: 123.4360 }
    ]
  },
  {
    id: "jinwei_high_speed",
    name: "津潍高铁",
    shortName: "津潍",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；潍坊北复用既有站点身份",
    stations: [
      { id: "jinwei_01", name: "滨海", city: "天津", lat: 39.0320, lon: 117.7100 },
      { id: "jinwei_02", name: "滨州", city: "滨州", lat: 37.3800, lon: 118.0170 },
      { id: "jinwei_03", name: "东营南", city: "东营", lat: 37.3870, lon: 118.6730 },
      { id: "jiqing_03", name: "潍坊北", city: "潍坊", lat: 36.7800, lon: 119.1550 }
    ]
  },
  {
    id: "liuyantong_high_speed",
    name: "连盐通高铁",
    shortName: "连盐通",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；连云港、南通复用既有站点身份",
    stations: [
      { id: "lianxulan_01", name: "连云港", city: "连云港", lat: 34.6000, lon: 119.2200 },
      { id: "liuyantong_02", name: "盐城", city: "盐城", lat: 33.3470, lon: 120.1610 },
      { id: "huyurong_02", name: "南通", city: "南通", lat: 31.9800, lon: 120.9000 }
    ]
  },
  {
    id: "nanping_high_speed",
    name: "南凭高铁",
    shortName: "南凭",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户指定先行建设南宁至崇左段；南宁东复用既有站点身份",
    stations: [
      { id: "nanguang_07", name: "南宁东", city: "南宁", lat: 22.8400, lon: 108.3700 },
      { id: "nanping_02", name: "崇左", city: "崇左", lat: 22.3830, lon: 107.3650 }
    ]
  },
  {
    id: "nanzhan_high_speed",
    name: "南湛高铁",
    shortName: "南湛",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；南宁东、湛江北复用既有站点身份",
    stations: [
      { id: "nanguang_07", name: "南宁东", city: "南宁", lat: 22.8400, lon: 108.3700 },
      { id: "nanzhan_02", name: "钦州东", city: "钦州", lat: 21.9600, lon: 108.6500 },
      { id: "nanzhan_03", name: "北海", city: "北海", lat: 21.4800, lon: 109.1200 },
      { id: "guangzhan_05", name: "湛江北", city: "湛江", lat: 21.2700, lon: 110.3500 }
    ]
  },
  {
    id: "nanzhan_fangchenggang_branch_high_speed",
    name: "南湛高铁·防城港支线",
    shortName: "南湛防城港支线",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "支线预研线路",
    parentLineId: "nanzhan_high_speed",
    networkRole: "branch",
    source: "用户指定支线；钦州东复用南湛高铁既有站点身份",
    stations: [
      { id: "nanzhan_02", name: "钦州东", city: "钦州", lat: 21.9600, lon: 108.6500 },
      { id: "nanzhan_fangchenggang_02", name: "防城港北", city: "防城港", lat: 21.6870, lon: 108.3540 }
    ]
  },
  {
    id: "xiangyichang_high_speed",
    name: "襄宜常高铁",
    shortName: "襄宜常",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户指定使用既有站点身份",
    stations: [
      { id: "zhengyu_04", name: "襄阳东", city: "襄阳", lat: 32.0400, lon: 112.2000 },
      { id: "huyurong_10", name: "荆门西", city: "荆门", lat: 31.0500, lon: 112.1600 },
      { id: "huyurong_11", name: "宜昌北", city: "宜昌", lat: 30.7600, lon: 111.3000 },
      { id: "yuxia_04", name: "常德", city: "常德", lat: 29.0550, lon: 111.7000 }
    ]
  },
  {
    id: "nanheng_high_speed",
    name: "南衡高铁",
    shortName: "南衡",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；衡阳东、桂林西、来宾北、南宁东复用既有站点身份",
    stations: [
      { id: "jingguang_20", name: "衡阳东", city: "衡阳", sourceLat: 26.8997, sourceLon: 112.7045, lat: 26.8500, lon: 112.6200 },
      { id: "nanheng_02", name: "永州", city: "永州", lat: 26.4577, lon: 111.5655 },
      { id: "guigang_03", name: "桂林西", city: "桂林", sourceLat: 25.3315, sourceLon: 110.2982, lat: 25.3575, lon: 110.2625 },
      { id: "nanheng_04", name: "柳州", city: "柳州", lat: 24.3105, lon: 109.3834 },
      { id: "nanheng_05", name: "来宾北", city: "来宾", lat: 23.7330, lon: 109.2290 },
      { id: "nanguang_07", name: "南宁东", city: "南宁", sourceLat: 22.8446, sourceLon: 108.4100, lat: 22.8400, lon: 108.3700 }
    ]
  },
  {
    id: "yishaoyong_high_speed",
    name: "益邵永高铁",
    shortName: "益邵永",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；益阳南、娄底南、永州复用既有站点身份",
    stations: [
      { id: "yuxia_05", name: "益阳南", city: "益阳", lat: 28.5250, lon: 112.3550 },
      { id: "hukun_15", name: "娄底南", city: "娄底", lat: 27.7000, lon: 112.0000 },
      { id: "yishaoyong_02", name: "邵阳", city: "邵阳", lat: 27.2136, lon: 111.4611 },
      { id: "nanheng_02", name: "永州", city: "永州", lat: 26.4577, lon: 111.5655 }
    ]
  },
  {
    id: "hukun_guilin_branch_high_speed",
    name: "沪昆高铁桂林支线",
    shortName: "沪昆桂林支线",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "支线预研线路",
    parentLineId: "hukun_high_speed",
    networkRole: "branch",
    source: "用户指定站序；怀化南、桂林西复用既有站点身份",
    stations: [
      { id: "hukun_16", name: "怀化南", city: "怀化", lat: 27.5500, lon: 109.9600 },
      { id: "guigang_03", name: "桂林西", city: "桂林", lat: 25.3575, lon: 110.2625 }
    ]
  },
  {
    id: "changjiu_high_speed",
    name: "常九高铁",
    shortName: "常九",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户指定站序；常德、岳阳、九江复用既有站点身份",
    stations: [
      { id: "yuxia_04", name: "常德", city: "常德", lat: 29.0550, lon: 111.7000 },
      { id: "jingguang_17", name: "岳阳东", city: "岳阳", lat: 29.3800, lon: 113.1600 },
      { id: "heshen_03", name: "九江", city: "九江", lat: 29.7200, lon: 115.9800 }
    ]
  },
  {
    id: "zhanhai_high_speed",
    name: "湛海高铁",
    shortName: "湛海",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；湛江北复用既有站点身份",
    stations: [
      { id: "guangzhan_05", name: "湛江北", city: "湛江", sourceLat: 21.2730, sourceLon: 110.3570, lat: 21.2700, lon: 110.3500 },
      { id: "zhanhai_02", name: "海口北", city: "海口", lat: 20.0500, lon: 110.1600 }
    ]
  },
  {
    id: "hainan_ring_high_speed",
    name: "海南环岛高铁",
    shortName: "海南环岛",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    closed: true,
    source: "用户提供参考坐标；海口北复用湛海高铁站点身份",
    stations: [
      { id: "zhanhai_02", name: "海口北", city: "海口", lat: 20.0500, lon: 110.1600 },
      { id: "hainanring_02", name: "琼海", city: "琼海", lat: 19.2580, lon: 110.4740 },
      { id: "hainanring_03", name: "三亚", city: "三亚", lat: 18.2520, lon: 109.5120 },
      { id: "hainanring_04", name: "儋州", city: "儋州", lat: 19.7090, lon: 109.2000 }
    ]
  },
  {
    id: "qingwei_high_speed",
    name: "青威城际",
    shortName: "青威",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；青岛北复用既有站点身份",
    stations: [
      { id: "jiqing_04", name: "青岛北", city: "青岛", lat: 36.1690, lon: 120.3760 },
      { id: "qingwei_02", name: "烟台南", city: "烟台", lat: 37.4310, lon: 121.3830 },
      { id: "qingwei_03", name: "威海", city: "威海", lat: 37.4240, lon: 122.1090 }
    ]
  },
  {
    id: "zhengtai_high_speed",
    name: "郑太高铁",
    shortName: "郑太",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；郑州东、晋中、太原南复用既有站点身份",
    stations: [
      { id: "jingguang_09", name: "郑州东", city: "郑州", lat: 34.7580, lon: 113.7690 },
      { id: "zhengtai_02", name: "焦作", city: "焦作", lat: 35.2140, lon: 113.2400 },
      { id: "zhengtai_03", name: "晋城东", city: "晋城", lat: 35.5090, lon: 112.9270 },
      { id: "zhengtai_04", name: "长治东", city: "长治", lat: 36.1960, lon: 113.1730 },
      { id: "zhangdaxi_06", name: "晋中", city: "晋中", lat: 37.6800, lon: 112.7300 },
      { id: "zhangdaxi_05", name: "太原南", city: "太原", lat: 37.7800, lon: 112.5600 }
    ]
  },
  {
    id: "xiyin_high_speed",
    name: "西银高铁",
    shortName: "西银",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；西安北、咸阳西、银川复用既有站点身份",
    stations: [
      { id: "lianxulan_09", name: "西安北", city: "西安", lat: 34.3769, lon: 108.9390 },
      { id: "lianxulan_10", name: "咸阳西", city: "咸阳", lat: 34.3300, lon: 108.6500 },
      { id: "xiyin_03", name: "庆阳", city: "庆阳", lat: 35.7130, lon: 107.6770 },
      { id: "xiyin_04", name: "吴忠", city: "吴忠", lat: 37.9875, lon: 106.1919 },
      { id: "baoyin_06", name: "银川", city: "银川", lat: 38.4942, lon: 106.1633 }
    ]
  },
  {
    id: "xiyu_high_speed",
    name: "西渝高铁",
    shortName: "西渝",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；西安东、广安南、重庆北复用既有站点身份",
    stations: [
      { id: "xiwu_01", name: "西安东", city: "西安", lat: 34.2490, lon: 109.1370 },
      { id: "xiyu_02", name: "安康西", city: "安康", lat: 32.7330, lon: 108.9464 },
      { id: "xiyu_03", name: "达州南", city: "达州", lat: 31.1020, lon: 107.4800 },
      { id: "langyu_05", name: "广安南", city: "广安", lat: 30.4700, lon: 106.6300 },
      { id: "huyurong_14", name: "重庆北", city: "重庆", lat: 29.6100, lon: 106.5500 }
    ]
  },
  {
    id: "chengdawan_high_speed",
    name: "成达万高铁",
    shortName: "成达万",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；成都、南充北、达州南、万州北复用既有站点身份",
    stations: [
      { id: "huyurong_15", name: "成都", city: "成都", lat: 30.7200, lon: 103.9800 },
      { id: "chengdawan_03", name: "遂宁", city: "遂宁", lat: 30.5480, lon: 105.5700 },
      { id: "langyu_04", name: "南充北", city: "南充", lat: 30.8560, lon: 106.0710 },
      { id: "xiyu_03", name: "达州南", city: "达州", lat: 31.1020, lon: 107.4800 },
      { id: "zhengyu_06", name: "万州北", city: "万州", lat: 30.8200, lon: 108.3900 }
    ]
  },
  {
    id: "guigang_high_speed",
    name: "贵广高铁",
    shortName: "贵广",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；贵阳北、都匀东、肇庆东、佛山西、广州南复用既有站点身份",
    stations: [
      { id: "hukun_18", name: "贵阳北", city: "贵阳", lat: 26.6500, lon: 106.6300 },
      { id: "yunan_04", name: "都匀东", city: "黔南州", lat: 26.2600, lon: 107.5200 },
      { id: "guigang_03", name: "桂林西", city: "桂林", lat: 25.3575, lon: 110.2625 },
      { id: "guigang_04", name: "贺州", city: "贺州", lat: 24.4130, lon: 111.5660 },
      { id: "nanguang_03", name: "肇庆东", city: "肇庆", lat: 23.1100, lon: 112.6100 },
      { id: "nanguang_02", name: "佛山西", city: "佛山", lat: 23.0900, lon: 112.9000 },
      { id: "jingguang_24", name: "广州南", city: "广州", lat: 22.9900, lon: 113.2700 }
    ]
  },
  {
    id: "jinxiongxin_high_speed",
    name: "津雄忻高铁",
    shortName: "津雄忻",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；天津南、雄安、保定东、忻州西复用既有站点身份",
    stations: [
      { id: "jinghu_03", name: "天津南", city: "天津", lat: 39.0200, lon: 117.0600 },
      { id: "jingxiongshang_02", name: "雄安", city: "雄安", lat: 39.0010, lon: 116.1000 },
      { id: "jingguang_02", name: "保定东", city: "保定", lat: 39.0870, lon: 115.5700 },
      { id: "zhangdaxi_04", name: "忻州西", city: "忻州", lat: 38.4200, lon: 112.7300 }
    ]
  },
  {
    id: "shide_high_speed",
    name: "石德高铁",
    shortName: "石德",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户指定使用既有站点身份",
    stations: [
      { id: "jingguang_03", name: "石家庄", city: "石家庄", lat: 38.0225, lon: 114.4840 },
      { id: "jingxiongshang_03", name: "衡水", city: "衡水", lat: 37.7380, lon: 115.7000 },
      { id: "jinghu_05", name: "德州东", city: "德州", lat: 37.4400, lon: 116.3600 }
    ]
  },
  {
    id: "zhangjihua_high_speed",
    name: "张吉怀高铁",
    shortName: "张吉怀",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；张家界西、怀化南复用既有站点身份",
    stations: [
      { id: "yuxia_03", name: "张家界西", city: "张家界", lat: 29.1300, lon: 110.4500 },
      { id: "zhangjihua_02", name: "吉首东", city: "湘西州", lat: 28.3140, lon: 109.7750 },
      { id: "hukun_16", name: "怀化南", city: "怀化", lat: 27.5500, lon: 109.9600 }
    ]
  },
  {
    id: "zhangjihua_tongren_branch",
    name: "张吉怀高铁·铜仁凤凰支线",
    shortName: "铜仁支线",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "支线预研线路",
    parentLineId: "zhangjihua_high_speed",
    networkRole: "branch",
    source: "用户提供参考坐标；吉首东接入张吉怀高铁主线",
    stations: [
      { id: "zhangjihua_02", name: "吉首东", city: "湘西州", lat: 28.3140, lon: 109.7750 },
      { id: "zhangjihua_branch_01", name: "铜仁凤凰", city: "铜仁", lat: 27.8700, lon: 109.2500 }
    ]
  },
  {
    id: "anliu_high_speed",
    name: "沪昆高铁六盘水支线",
    shortName: "六盘水支线",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "国家铁路局站点名单；公开地图参考坐标；安顺西、昭通东复用既有站点身份",
    stations: [
      { id: "hukun_19", name: "安顺西", city: "安顺", lat: 26.2500, lon: 105.9300 },
      { id: "anliu_05", name: "六盘水", city: "六盘水", lat: 26.5941, lon: 104.8501 },
      { id: "yukun_04", name: "昭通东", city: "昭通", lat: 27.3210, lon: 103.7840 }
    ]
  },
  {
    id: "zhaoqian_conventional",
    name: "昭黔铁路",
    shortName: "昭黔",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户指定站序；全线复用既有站点身份",
    stations: [
      { id: "yukun_04", name: "昭通东", city: "昭通", lat: 27.3210, lon: 103.7840 },
      { id: "chenggui_05", name: "毕节", city: "毕节", lat: 27.3000, lon: 105.2800 },
      { id: "yunan_02", name: "遵义", city: "遵义", lat: 27.7254, lon: 106.9272 },
      { id: "yuxia_02", name: "黔江", city: "重庆黔江", lat: 29.4750, lon: 108.7700 }
    ]
  },
  {
    id: "xiyubao_high_speed",
    name: "西榆包高铁",
    shortName: "西榆包",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；西安北、包头复用既有站点身份",
    stations: [
      { id: "lianxulan_09", name: "西安北", city: "西安", lat: 34.3769, lon: 108.9390 },
      { id: "xiyubao_02", name: "铜川", city: "铜川", lat: 34.8980, lon: 108.9660 },
      { id: "xiyubao_03", name: "延安", city: "延安", lat: 36.5850, lon: 109.4900 },
      { id: "xiyubao_04", name: "榆林南", city: "榆林", lat: 38.2190, lon: 109.7340 },
      { id: "xiyubao_05", name: "鄂尔多斯", city: "鄂尔多斯", lat: 39.6080, lon: 109.9900 },
      { id: "jingbao_05", name: "包头", city: "包头", lat: 40.6054, lon: 109.8366 }
    ]
  },
  {
    id: "qingchang_conventional",
    name: "青昌铁路",
    shortName: "青昌",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考坐标；青海湖、共和、昌都复用既有站点身份",
    stations: [
      { id: "qinghaihu_02", name: "青海湖", city: "海北州／青海湖景区", lat: 36.9600, lon: 100.9000 },
      { id: "qinghaihu_03", name: "共和", city: "海南州", lat: 36.2840, lon: 100.6200 },
      { id: "qingchang_02", name: "玛沁", city: "果洛州", lat: 34.4770, lon: 100.2390 },
      { id: "qingchang_03", name: "玉树", city: "玉树州", lat: 33.0040, lon: 96.9780 },
      { id: "chuanzang_04", name: "昌都", city: "昌都", lat: 31.1400, lon: 97.1720 }
    ]
  },
  {
    id: "wubo_conventional",
    name: "乌博铁路",
    shortName: "乌博",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考站序；乌鲁木齐、昌吉、奎屯复用既有站点身份",
    stations: [
      { id: "lanxin_09", name: "乌鲁木齐", city: "乌鲁木齐", lat: 43.8310, lon: 87.5350 },
      { id: "beijiang_04", name: "昌吉", city: "昌吉州", lat: 43.9464, lon: 87.1911 },
      { id: "wubo_03", name: "石河子", city: "石河子", lat: 44.2675, lon: 86.0605 },
      { id: "beijiang_01", name: "奎屯", city: "伊犁州东部", lat: 44.4260, lon: 84.9020 },
      { id: "wubo_04", name: "博乐", city: "博尔塔拉州", lat: 44.9060, lon: 82.0660 }
    ]
  },
  {
    id: "beijiang_tacheng_branch",
    name: "北疆铁路·塔城支线",
    shortName: "塔城支线",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速支线预研",
    parentLineId: "beijiang_conventional",
    networkRole: "branch",
    source: "用户提供参考坐标；克拉玛依复用北疆铁路站点身份",
    stations: [
      { id: "beijiang_02", name: "克拉玛依", city: "克拉玛依", lat: 45.5800, lon: 84.8700 },
      { id: "beijiang_tacheng_02", name: "塔城", city: "塔城地区", lat: 46.7480, lon: 82.9860 }
    ]
  },
  {
    id: "wuyi_high_speed",
    name: "乌伊高铁",
    shortName: "乌伊",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户指定复用既有乌鲁木齐、伊宁站点身份",
    stations: [
      { id: "lanxin_09", name: "乌鲁木齐", city: "乌鲁木齐", lat: 43.8310, lon: 87.5350 },
      { id: "yiku_01", name: "伊宁", city: "伊犁州", lat: 43.9770, lon: 81.2730 }
    ]
  },
  {
    id: "beijiang_conventional",
    name: "北疆铁路",
    shortName: "北疆",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考坐标；乌鲁木齐复用兰新铁路站点身份",
    stations: [
      { id: "beijiang_01", name: "奎屯", city: "伊犁州东部", lat: 44.4260, lon: 84.9020 },
      { id: "beijiang_02", name: "克拉玛依", city: "克拉玛依", lat: 45.5800, lon: 84.8700 },
      { id: "beijiang_03", name: "阿勒泰", city: "阿勒泰地区", lat: 47.8470, lon: 88.1330 },
      { id: "beijiang_04", name: "昌吉", city: "昌吉州", lat: 43.9464, lon: 87.1911 },
      { id: "lanxin_09", name: "乌鲁木齐", city: "乌鲁木齐", lat: 43.8310, lon: 87.5350 }
    ]
  },
  {
    id: "yiku_conventional",
    name: "伊库铁路",
    shortName: "伊库",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考坐标；库尔勒复用南疆铁路站点身份",
    stations: [
      { id: "yiku_01", name: "伊宁", city: "伊犁州", lat: 43.9770, lon: 81.2730 },
      { id: "nanjiang_01", name: "库尔勒", city: "巴音郭楞州", lat: 41.7260, lon: 86.1740 }
    ]
  },
  {
    id: "geku_conventional",
    name: "格库铁路",
    shortName: "格库",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考坐标；格尔木、若羌、库尔勒复用既有站点身份",
    stations: [
      { id: "qingzang_03", name: "格尔木", city: "海西州", lat: 36.3829, lon: 94.9061 },
      { id: "heruo_03", name: "若羌", city: "巴音郭楞州", lat: 39.0250, lon: 88.1680 },
      { id: "nanjiang_01", name: "库尔勒", city: "巴音郭楞州", lat: 41.7260, lon: 86.1740 }
    ]
  },
  {
    id: "heruo_conventional",
    name: "和若铁路",
    shortName: "和若",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考坐标；和田复用既有站点身份",
    stations: [
      { id: "xinzang_01", name: "和田", city: "和田地区", lat: 37.1110, lon: 79.9220 },
      { id: "heruo_02", name: "且末", city: "巴音郭楞州", lat: 38.1450, lon: 85.5290 },
      { id: "heruo_03", name: "若羌", city: "巴音郭楞州", lat: 39.0250, lon: 88.1680 }
    ]
  },
  {
    id: "nanjiang_conventional",
    name: "南疆铁路",
    shortName: "南疆",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考坐标；和田复用新藏铁路站点身份",
    stations: [
      { id: "nanjiang_01", name: "库尔勒", city: "巴音郭楞州", lat: 41.7260, lon: 86.1740 },
      { id: "nanjiang_02", name: "库车", city: "阿克苏地区", lat: 41.7060, lon: 82.9630 },
      { id: "nanjiang_03", name: "阿克苏", city: "阿克苏地区", lat: 41.1240, lon: 80.2630 },
      { id: "nanjiang_05", name: "阿图什", city: "克孜勒苏州", lat: 39.7197, lon: 76.2164 },
      { id: "nanjiang_04", name: "喀什", city: "喀什地区", lat: 39.5150, lon: 76.0630 },
      { id: "nanjiang_06", name: "莎车", city: "莎车县", lat: 38.3742, lon: 77.2297 },
      { id: "nanjiang_07", name: "叶城", city: "叶城县", lat: 37.8932, lon: 77.4708 },
      { id: "xinzang_01", name: "和田", city: "和田地区", lat: 37.1110, lon: 79.9220 }
    ]
  },
  {
    id: "xinzang_conventional",
    name: "新藏铁路",
    shortName: "新藏",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考坐标；拉萨复用既有站点身份",
    stations: [
      { id: "xinzang_01", name: "和田", city: "和田地区", lat: 37.1110, lon: 79.9220 },
      { id: "xinzang_02", name: "阿里", city: "阿里地区噶尔县", lat: 32.5010, lon: 80.1050 },
      { id: "xinzang_03", name: "日喀则", city: "日喀则", lat: 29.2670, lon: 88.8800 },
      { id: "chuanzang_07", name: "拉萨", city: "拉萨", lat: 29.6250, lon: 91.0686 }
    ]
  },
  {
    id: "diancang_conventional",
    name: "滇藏铁路",
    shortName: "滇藏",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考坐标；昆明南、楚雄、林芝复用既有站点身份",
    stations: [
      { id: "hukun_21", name: "昆明南", city: "昆明", lat: 24.8740, lon: 102.8620 },
      { id: "chengkun_04", name: "楚雄", city: "楚雄州", lat: 25.0360, lon: 101.5460 },
      { id: "diancang_03", name: "大理", city: "大理州", lat: 25.5920, lon: 100.2485 },
      { id: "diancang_04", name: "丽江", city: "丽江", lat: 26.8138, lon: 100.2512 },
      { id: "diancang_05", name: "香格里拉", city: "迪庆州", lat: 27.8140, lon: 99.6889 },
      { id: "chuanzang_05", name: "林芝", city: "林芝", lat: 29.5296, lon: 94.4373 }
    ]
  },
  {
    id: "qingzang_conventional",
    name: "青藏铁路",
    shortName: "青藏",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考坐标；西宁、拉萨复用既有站点身份",
    stations: [
      { id: "lanxin_03", name: "西宁", city: "西宁", lat: 36.6217, lon: 101.8067 },
      { id: "qinghaihu_02", name: "青海湖", city: "海北州／青海湖景区", lat: 36.9600, lon: 100.9000 },
      { id: "qingzang_02", name: "德令哈", city: "海西州", lat: 37.3148, lon: 97.3830 },
      { id: "qingzang_03", name: "格尔木", city: "海西州", lat: 36.3829, lon: 94.9061 },
      { id: "qingzang_04", name: "那曲", city: "那曲", lat: 31.4454, lon: 91.9896 },
      { id: "chuanzang_07", name: "拉萨", city: "拉萨", lat: 29.6250, lon: 91.0686 }
    ]
  },
  {
    id: "chuanzang_conventional",
    name: "川藏铁路",
    shortName: "川藏",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考坐标；成都复用既有站点身份",
    stations: [
      { id: "huyurong_15", name: "成都", city: "成都", lat: 30.7200, lon: 103.9800 },
      { id: "chuanzang_02", name: "雅安", city: "雅安", lat: 30.0310, lon: 103.0550 },
      { id: "chuanzang_03", name: "康定", city: "康定", lat: 30.0500, lon: 101.9650 },
      { id: "chuanzang_04", name: "昌都", city: "昌都", lat: 31.1400, lon: 97.1720 },
      { id: "chuanzang_05", name: "林芝", city: "林芝", lat: 29.5296, lon: 94.4373 },
      { id: "chuanzang_06", name: "山南", city: "山南", lat: 29.2400, lon: 91.7700 },
      { id: "chuanzang_07", name: "拉萨", city: "拉萨", lat: 29.6250, lon: 91.0686 }
    ]
  },
  {
    id: "chengziyi_high_speed",
    name: "成自宜高铁",
    shortName: "成自宜",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；成都东、资阳北、宜宾复用既有站点身份",
    stations: [
      { id: "xicheng_06", name: "成都东", city: "成都", lat: 30.6320, lon: 104.1410 },
      { id: "chengyu_02", name: "资阳北", city: "资阳", lat: 30.1360, lon: 104.6160 },
      { id: "chengziyi_03", name: "自贡", city: "自贡", lat: 29.3270, lon: 104.8350 },
      { id: "yukun_03", name: "宜宾西", city: "宜宾", lat: 28.7510, lon: 104.6200 }
    ]
  },
  {
    id: "yukun_high_speed",
    name: "渝昆高铁",
    shortName: "渝昆",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；重庆西、昆明南复用既有站点身份",
    stations: [
      { id: "chengyu_04", name: "重庆西", city: "重庆", lat: 29.5020, lon: 106.4380 },
      { id: "yukun_02", name: "泸州", city: "泸州", lat: 28.9470, lon: 105.4140 },
      { id: "yukun_03", name: "宜宾西", city: "宜宾", lat: 28.7510, lon: 104.6200 },
      { id: "yukun_04", name: "昭通东", city: "昭通", lat: 27.3210, lon: 103.7840 },
      { id: "hukun_21", name: "昆明南", city: "昆明", lat: 24.8740, lon: 102.8620 }
    ]
  },
  {
    id: "yinlan_high_speed",
    name: "银兰高铁",
    shortName: "银兰",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；银川、吴忠、兰州西复用既有站点身份",
    stations: [
      { id: "baoyin_06", name: "银川", city: "银川", lat: 38.4942, lon: 106.1633 },
      { id: "xiyin_04", name: "吴忠", city: "吴忠", lat: 37.9875, lon: 106.1919 },
      { id: "yinlan_03", name: "中卫南", city: "中卫", lat: 37.4767, lon: 105.1744 },
      { id: "yinlan_04", name: "白银南", city: "白银", lat: 36.4765, lon: 104.1804 },
      { id: "lianxulan_14", name: "兰州西", city: "兰州", lat: 36.0675, lon: 103.7492 }
    ]
  },
  {
    id: "chuanqing_conventional",
    name: "川青铁路",
    shortName: "川青",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考坐标；成都东、海东西复用既有站点身份",
    stations: [
      { id: "xicheng_06", name: "成都东", city: "成都", lat: 30.6320, lon: 104.1410 },
      { id: "chuanqing_02", name: "马尔康", city: "阿坝州", lat: 31.9050, lon: 102.2280 },
      { id: "chuanqing_03", name: "合作", city: "甘南州", lat: 34.9850, lon: 102.9110 },
      { id: "chuanqing_04", name: "同仁", city: "黄南州", lat: 35.6650, lon: 102.0780 },
      { id: "lanxin_02", name: "海东西", city: "海东", lat: 36.5095, lon: 102.0535 }
    ]
  },
  {
    id: "lanhe_conventional",
    name: "兰合铁路",
    shortName: "兰合",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考坐标；兰州西、合作复用既有站点身份",
    stations: [
      { id: "lianxulan_14", name: "兰州西", city: "兰州", lat: 36.0675, lon: 103.7492 },
      { id: "lanhe_02", name: "临夏", city: "临夏州", lat: 35.6010, lon: 103.2100 },
      { id: "chuanqing_03", name: "合作", city: "甘南州", lat: 34.9850, lon: 102.9110 }
    ]
  },
  {
    id: "binzhou_conventional",
    name: "滨洲铁路",
    shortName: "滨洲",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考坐标；哈尔滨西复用既有站点身份",
    stations: [
      { id: "jingha_09", name: "哈尔滨西", city: "哈尔滨", lat: 45.7070, lon: 126.5770 },
      { id: "binzhou_02", name: "大庆西", city: "大庆", lat: 46.6280, lon: 124.8730 },
      { id: "binzhou_03", name: "齐齐哈尔", city: "齐齐哈尔", lat: 47.3540, lon: 123.9180 },
      { id: "binzhou_04", name: "海拉尔", city: "呼伦贝尔", lat: 49.2120, lon: 119.7580 }
    ]
  },
  {
    id: "wuxi_high_speed",
    name: "乌锡高铁",
    shortName: "乌锡",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；乌兰察布复用既有站点身份",
    stations: [
      { id: "jingbao_03", name: "乌兰察布", city: "乌兰察布", lat: 40.9642, lon: 113.1633 },
      { id: "wuxi_02", name: "锡林浩特", city: "锡林郭勒盟", lat: 43.9330, lon: 116.0870 }
    ]
  },
  {
    id: "jida_high_speed",
    name: "张大西高铁集大支线",
    shortName: "张大西集大支线",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "支线预研线路",
    parentLineId: "zhangdaxi_high_speed",
    networkRole: "branch",
    source: "用户指定复用既有站点身份",
    stations: [
      { id: "jingbao_03", name: "乌兰察布", city: "乌兰察布", lat: 40.9642, lon: 113.1633 },
      { id: "zhangdaxi_02", name: "大同南", city: "大同", lat: 40.0200, lon: 113.1500 }
    ]
  }
];
