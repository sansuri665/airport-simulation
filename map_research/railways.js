const RAILWAYS = [
  {
    id: "jingguang_high_speed",
    name: "京广高铁",
    shortName: "京广",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "运营线路",
    source: "用户提供参考坐标；县级／中间站坐标参考维基百科车站条目",
    stations: [
      { id: "jingguang_01", name: "北京西", city: "北京", lat: 39.8936, lon: 116.3157 },
      { id: "jingguang_fengtai", name: "北京丰台", city: "北京", lat: 39.8498, lon: 116.2946 },
      { id: "jingguang_zhuozhoudong", name: "涿州东", city: "涿州", lat: 39.4588, lon: 116.0481 },
      { id: "jingguang_gaobeidiandong", name: "高碑店东", city: "高碑店", lat: 39.2875, lon: 115.9411 },
      { id: "jingguang_02", name: "保定东", city: "保定", lat: 39.087, lon: 115.57 },
      { id: "jingguang_dingzhoudong", name: "定州东", city: "定州", lat: 38.5072, lon: 115.0693 },
      { id: "jingguang_zhengdingairport", name: "正定机场", city: "正定", lat: 38.2507, lon: 114.7035 },
      { id: "jingguang_03", name: "石家庄", city: "石家庄", lat: 38.0225, lon: 114.484 },
      { id: "jingguang_gaoyixi", name: "高邑西", city: "高邑", lat: 37.629, lon: 114.5238 },
      { id: "jingguang_04", name: "邢台东", city: "邢台", lat: 37.07, lon: 114.57 },
      { id: "jingguang_05", name: "邯郸东", city: "邯郸", lat: 36.615, lon: 114.565 },
      { id: "jingguang_06", name: "安阳东", city: "安阳", lat: 36.08, lon: 114.4 },
      { id: "jingguang_07", name: "鹤壁东", city: "鹤壁", lat: 35.76, lon: 114.32 },
      { id: "jingguang_08", name: "新乡东", city: "新乡", lat: 35.302, lon: 113.94 },
      { id: "jingguang_09", name: "郑州东", city: "郑州", lat: 34.758, lon: 113.769 },
      { id: "jingguang_10", name: "许昌东", city: "许昌", lat: 34.02, lon: 113.87 },
      { id: "jingguang_11", name: "漯河西", city: "漯河", lat: 33.57, lon: 113.92 },
      { id: "jingguang_12", name: "驻马店西", city: "驻马店", lat: 32.98, lon: 114.02 },
      { id: "jingguang_minggangdong", name: "明港东", city: "明港", lat: 32.4886, lon: 114.0585 },
      { id: "jingguang_13", name: "信阳东", city: "信阳", lat: 32.15, lon: 114.12 },
      { id: "jingguang_14", name: "孝感北", city: "孝感", lat: 31.45, lon: 113.9 },
      { id: "jingguang_15", name: "武汉", city: "武汉", lat: 30.61, lon: 114.43 },
      { id: "jingguang_16", name: "咸宁北", city: "咸宁", lat: 29.86, lon: 114.33 },
      { id: "jingguang_chibibei", name: "赤壁北", city: "赤壁", lat: 29.7397, lon: 113.8948 },
      { id: "jingguang_17", name: "岳阳东", city: "岳阳", lat: 29.38, lon: 113.16 },
      { id: "jingguang_miluodong", name: "汨罗东", city: "汨罗", lat: 28.7488, lon: 113.1377 },
      { id: "jingguang_18", name: "长沙南", city: "长沙", lat: 28.15, lon: 113.08 },
      { id: "jingguang_19", name: "株洲西", city: "株洲", lat: 27.85, lon: 113.08 },
      { id: "jingguang_hengshanxi", name: "衡山西", city: "衡山", lat: 27.2515, lon: 112.7836 },
      { id: "jingguang_20", name: "衡阳东", city: "衡阳", lat: 26.85, lon: 112.62 },
      { id: "jingguang_leiyangxi", name: "耒阳西", city: "耒阳", lat: 26.4173, lon: 112.7826 },
      { id: "jingguang_21", name: "郴州西", city: "郴州", lat: 25.76, lon: 113.02 },
      { id: "jingguang_lechangdong", name: "乐昌东", city: "乐昌", lat: 25.1166, lon: 113.3909 },
      { id: "jingguang_22", name: "韶关", city: "韶关", lat: 24.8, lon: 113.61 },
      { id: "jingguang_yingdexi", name: "英德西", city: "英德", lat: 24.1614, lon: 113.3444 },
      { id: "jingguang_23", name: "清远", city: "清远", lat: 23.7, lon: 113.06 },
      { id: "jingguang_guangzhoubei", name: "广州北", city: "广州", lat: 23.3796, lon: 113.1991 },
      { id: "jingguang_24", name: "广州南", city: "广州", lat: 22.99, lon: 113.27 }
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
      { id: "jingguang_09", name: "郑州东", city: "郑州", lat: 34.758, lon: 113.769 },
      { id: "jingguang_zhoukou_02", name: "周口东", city: "周口", lat: 33.642, lon: 114.728 },
      { id: "shanghehang_03", name: "阜阳西", city: "阜阳", lat: 32.89, lon: 115.8 }
    ]
  },
  {
    id: "wujiu_high_speed",
    name: "京广高铁武九支线",
    shortName: "京广武九支线",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "支线预研线路",
    parentLineId: "jingguang_high_speed",
    networkRole: "branch",
    source: "用户提供参考坐标；武汉、九江复用既有站点身份",
    stations: [
      { id: "jingguang_15", name: "武汉", city: "武汉", lat: 30.61, lon: 114.43 },
      { id: "jingguang_wujiu_02", name: "鄂州站", city: "鄂州", lat: 30.396, lon: 114.901 },
      { id: "jingguang_wujiu_03", name: "黄石北站", city: "黄石", lat: 30.216, lon: 115.029 },
      { id: "heshen_03", name: "九江", city: "九江", lat: 29.72, lon: 115.98 }
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
    source: "用户提供参考坐标；北端改接北京丰台（与京雄城际区分）；丰台复用京广既有站点身份",
    stations: [
      { id: "jingguang_fengtai", name: "北京丰台", city: "北京", lat: 39.8498, lon: 116.2946 },
      { id: "jingxiongshang_02", name: "雄安", city: "雄安", lat: 39.001, lon: 116.1 },
      { id: "jingxiongshang_03", name: "衡水", city: "衡水", lat: 37.738, lon: 115.7 },
      { id: "jingxiongshang_04", name: "聊城西", city: "聊城", lat: 36.43, lon: 115.92 },
      { id: "jingxiongshang_05", name: "濮阳东", city: "濮阳", lat: 35.77, lon: 115.06 },
      { id: "jingxiongshang_06", name: "菏泽东", city: "菏泽", lat: 35.245, lon: 115.52 },
      { id: "jingxiongshang_07", name: "商丘", city: "商丘", lat: 34.44, lon: 115.65 }
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
      { id: "jingxiongshang_07", name: "商丘", city: "商丘", lat: 34.44, lon: 115.65 },
      { id: "shanghehang_02", name: "亳州南", city: "亳州", lat: 33.87, lon: 115.78 },
      { id: "shanghehang_03", name: "阜阳西", city: "阜阳", lat: 32.89, lon: 115.8 },
      { id: "shanghehang_04", name: "淮南南", city: "淮南", lat: 32.58, lon: 116.93 },
      { id: "shanghehang_05", name: "合肥南", city: "合肥", lat: 31.78, lon: 117.3 },
      { id: "shanghehang_06", name: "芜湖", city: "芜湖", lat: 31.34, lon: 118.39 },
      { id: "shanghehang_07", name: "宣城", city: "宣城", lat: 30.95, lon: 118.75 },
      { id: "shanghehang_08", name: "湖州", city: "湖州", lat: 30.87, lon: 120.09 },
      { id: "shanghehang_09", name: "杭州东", city: "杭州", lat: 30.315, lon: 120.21 }
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
      { id: "shanghehang_05", name: "合肥南", city: "合肥", lat: 31.78, lon: 117.3 },
      { id: "heshen_02", name: "六安", city: "六安", lat: 31.75, lon: 116.5 },
      { id: "heshen_03", name: "九江", city: "九江", lat: 29.72, lon: 115.98 },
      { id: "heshen_04", name: "南昌西", city: "南昌", lat: 28.61, lon: 115.82 },
      { id: "heshen_05", name: "吉安西", city: "吉安", lat: 27.1, lon: 114.98 },
      { id: "heshen_06", name: "赣州西", city: "赣州", lat: 25.82, lon: 114.92 },
      { id: "heshen_07", name: "河源东", city: "河源", lat: 23.74, lon: 114.7 },
      { id: "heshen_08", name: "惠州北", city: "惠州", lat: 23.12, lon: 114.42 },
      { id: "heshen_09", name: "东莞南", city: "东莞", lat: 22.91, lon: 114.14 },
      { id: "heshen_10", name: "深圳北", city: "深圳", lat: 22.61, lon: 114.03 }
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
      { id: "heshen_07", name: "河源东", city: "河源", lat: 23.74, lon: 114.7 },
      { id: "heshen_meizhou_02", name: "梅州西", city: "梅州市", lat: 24.292, lon: 116.099 },
      { id: "yuxia_10", name: "龙岩", city: "龙岩", lat: 25.095, lon: 117.015 }
    ]
  },
  {
    id: "guangzhuanao_high_speed",
    name: "广珠澳高铁",
    shortName: "广珠澳",
    type: "high_speed",
    typeLabel: "高速",
    region: "cross_region",
    regions: [
      "china_mainland",
      "hk_macao_taiwan"
    ],
    boundaryLabel: "珠澳交界中点",
    status: "跨区域预研线路",
    source: "用户提供参考坐标；广州南沙复用广深港高铁既有站点身份",
    stations: [
      { id: "guangshen_02", name: "广州南沙", city: "广州南沙", region: "china_mainland", lat: 22.866, lon: 113.672 },
      { id: "guangzhuanao_02", name: "中山", city: "中山", region: "china_mainland", lat: 22.53, lon: 113.392 },
      { id: "guangzhuanao_03", name: "珠海", city: "珠海", region: "china_mainland", lat: 22.2167, lon: 113.553 },
      { id: "guangzhuanao_04", name: "澳门南", city: "澳门", region: "hk_macao_taiwan", lat: 22, lon: 113.65 }
    ]
  },
  {
    id: "futai_cross_region_high_speed",
    name: "福台跨海高铁",
    shortName: "福台跨海",
    type: "high_speed",
    typeLabel: "高速",
    region: "cross_region",
    regions: [
      "china_mainland",
      "hk_macao_taiwan"
    ],
    boundaryLabel: "台湾海峡中点",
    status: "跨区域预研线路",
    source: "用户指定跨海方案；福州南、台北复用既有站点身份；不设中间虚构站点",
    stations: [
      { id: "hangshen_07", name: "福州南", city: "福州", region: "china_mainland", lat: 25.985, lon: 119.39 },
      { id: "taiwan_01", name: "台北", city: "台北", region: "hk_macao_taiwan", lat: 25.0478, lon: 121.517 }
    ]
  },
  {
    id: "xiagao_cross_region_high_speed",
    name: "厦高跨海高铁",
    shortName: "厦高跨海",
    type: "high_speed",
    typeLabel: "高速",
    region: "cross_region",
    regions: [
      "china_mainland",
      "hk_macao_taiwan"
    ],
    boundaryLabel: "台湾海峡中点",
    status: "跨区域预研线路",
    source: "用户指定跨海方案；厦门北、高雄复用既有站点身份；不设中间虚构站点",
    stations: [
      { id: "hangshen_10", name: "厦门北", city: "厦门", region: "china_mainland", lat: 24.637, lon: 118.074 },
      { id: "taiwan_07", name: "高雄", city: "高雄", region: "hk_macao_taiwan", lat: 22.687, lon: 120.307 }
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
      { id: "heshen_10", name: "深圳北", city: "深圳", lat: 22.61, lon: 114.03 },
      { id: "guangzhuanao_02", name: "中山", city: "中山", lat: 22.53, lon: 113.392 },
      { id: "shenjiang_03", name: "江门", city: "江门", lat: 22.582, lon: 113.094 },
      { id: "nanguang_03", name: "肇庆东", city: "肇庆", lat: 23.11, lon: 112.61 }
    ]
  },
  {
    id: "jinghu_high_speed",
    name: "京沪高铁",
    shortName: "京沪",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "运营线路",
    source: "县级挂名站补入；坐标参考维基百科车站条目",
    stations: [
      { id: "jinghu_01", name: "北京南", city: "北京", lat: 39.8636, lon: 116.3728 },
      { id: "jinghu_02", name: "廊坊", city: "廊坊", lat: 39.52, lon: 116.69 },
      { id: "jinghu_03", name: "天津南", city: "天津", lat: 39.02, lon: 117.06 },
      { id: "jinghu_04", name: "沧州西", city: "沧州", lat: 38.31, lon: 116.82 },
      { id: "jinghu_05", name: "德州东", city: "德州", lat: 37.44, lon: 116.36 },
      { id: "jinghu_06", name: "济南西", city: "济南", lat: 36.67, lon: 116.9 },
      { id: "jinghu_07", name: "泰安", city: "泰安", lat: 36.2, lon: 117.09 },
      { id: "jinghu_qufudong", name: "曲阜东", city: "曲阜", lat: 35.5565, lon: 117.0638 },
      { id: "jinghu_tengzhoudong", name: "滕州东", city: "滕州", lat: 35.091, lon: 117.2524 },
      { id: "jinghu_08", name: "枣庄", city: "枣庄", lat: 34.788, lon: 117.263 },
      { id: "jinghu_09", name: "徐州东", city: "徐州", lat: 34.265, lon: 117.28 },
      { id: "jinghu_10", name: "宿州东", city: "宿州", lat: 33.66, lon: 117.15 },
      { id: "jinghu_11", name: "蚌埠南", city: "蚌埠", lat: 32.94, lon: 117.39 },
      { id: "jinghu_dingyuan", name: "定远", city: "定远", lat: 32.5774, lon: 117.8373 },
      { id: "jinghu_12", name: "滁州", city: "滁州", lat: 32.26, lon: 118.33 },
      { id: "jinghu_13", name: "南京南", city: "南京", lat: 31.97, lon: 118.8 },
      { id: "jinghu_14", name: "镇江南", city: "镇江", lat: 32.14, lon: 119.42 },
      { id: "jinghu_danyangbei", name: "丹阳北", city: "丹阳", lat: 32.017, lon: 119.6666 },
      { id: "jinghu_15", name: "常州北", city: "常州", lat: 31.84, lon: 119.97 },
      { id: "jinghu_16", name: "无锡东", city: "无锡", lat: 31.59, lon: 120.43 },
      { id: "jinghu_17", name: "苏州北", city: "苏州", lat: 31.43, lon: 120.65 },
      { id: "jinghu_kunshannan", name: "昆山南", city: "昆山", lat: 31.355, lon: 120.9467 },
      { id: "jinghu_18", name: "上海虹桥", city: "上海", lat: 31.197, lon: 121.33 }
    ]
  },
  {
    id: "jinghu_tianjinxi_branch_high_speed",
    name: "京沪高铁天津西联络线",
    shortName: "京沪天津西联络",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "运营线路",
    parentLineId: "jinghu_high_speed",
    networkRole: "branch",
    source: "京沪正线不停天津西；经天津南—天津西联络引入枢纽始发；两端复用京沪／津兴既有站点身份",
    stations: [
      { id: "jinghu_03", name: "天津南", city: "天津", lat: 39.02, lon: 117.06 },
      { id: "jinxing_01", name: "天津西", city: "天津", lat: 39.157, lon: 117.161 }
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
      { id: "jinghu_18", name: "上海虹桥", city: "上海", lat: 31.197, lon: 121.33 },
      { id: "hukun_02", name: "嘉兴南", city: "嘉兴", lat: 30.75, lon: 120.76 },
      { id: "shanghehang_09", name: "杭州东", city: "杭州", lat: 30.315, lon: 120.21 },
      { id: "hukun_04", name: "金华", city: "金华", lat: 29.1, lon: 119.65 },
      { id: "hukun_05", name: "衢州", city: "衢州", lat: 28.97, lon: 118.87 },
      { id: "hukun_06", name: "上饶", city: "上饶", lat: 28.45, lon: 117.97 },
      { id: "hukun_07", name: "鹰潭北", city: "鹰潭", lat: 28.23, lon: 116.97 },
      { id: "hukun_08", name: "抚州东", city: "抚州", lat: 28, lon: 116.61 },
      { id: "heshen_04", name: "南昌西", city: "南昌", lat: 28.61, lon: 115.82 },
      { id: "hukun_10", name: "宜春", city: "宜春", lat: 27.8, lon: 114.39 },
      { id: "hukun_11", name: "萍乡北", city: "萍乡", lat: 27.62, lon: 113.9 },
      { id: "jingguang_19", name: "株洲西", city: "株洲", lat: 27.85, lon: 113.08 },
      { id: "jingguang_18", name: "长沙南", city: "长沙", lat: 28.15, lon: 113.08 },
      { id: "hukun_14", name: "湘潭北", city: "湘潭", lat: 27.95, lon: 112.95 },
      { id: "hukun_15", name: "娄底南", city: "娄底", lat: 27.7, lon: 112 },
      { id: "hukun_16", name: "怀化南", city: "怀化", lat: 27.55, lon: 109.96 },
      { id: "hukun_17", name: "凯里南", city: "凯里", lat: 26.58, lon: 107.98 },
      { id: "hukun_18", name: "贵阳北", city: "贵阳", lat: 26.65, lon: 106.63 },
      { id: "hukun_19", name: "安顺西", city: "安顺", lat: 26.25, lon: 105.93 },
      { id: "hukun_20", name: "曲靖北", city: "曲靖", lat: 25.52, lon: 103.8 },
      { id: "hukun_21", name: "昆明南", city: "昆明", lat: 24.874, lon: 102.862 }
    ]
  },
  {
    id: "changjinghuang_high_speed",
    name: "合深高铁景德镇支线",
    shortName: "合深景德镇支线",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "支线预研线路",
    parentLineId: "heshen_high_speed",
    networkRole: "branch",
    source: "用户提供参考坐标；南昌西、黄山北复用既有站点身份",
    stations: [
      { id: "heshen_04", name: "南昌西", city: "南昌", lat: 28.61, lon: 115.82 },
      { id: "changjinghuang_02", name: "景德镇北站", city: "景德镇", lat: 29.342, lon: 117.176 },
      { id: "hefu_04", name: "黄山北", city: "黄山", lat: 29.815, lon: 118.295 }
    ]
  },
  {
    id: "changfu_high_speed",
    name: "昌福高铁",
    shortName: "昌福",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；南昌西、抚州东、福州南复用既有站点身份",
    stations: [
      { id: "heshen_04", name: "南昌西", city: "南昌", lat: 28.61, lon: 115.82 },
      { id: "hukun_08", name: "抚州东", city: "抚州", lat: 28, lon: 116.61 },
      { id: "changfu_03", name: "三明北", city: "三明", lat: 26.369, lon: 117.631 },
      { id: "hangshen_07", name: "福州南", city: "福州", lat: 25.985, lon: 119.39 }
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
      { id: "huyurong_01", name: "上海东", city: "上海", lat: 31.25, lon: 121.68 },
      { id: "huyurong_02", name: "南通", city: "南通", lat: 31.98, lon: 120.9 },
      { id: "huyurong_03", name: "泰州", city: "泰州", lat: 32.46, lon: 119.92 },
      { id: "huyurong_04", name: "扬州东", city: "扬州", lat: 32.39, lon: 119.47 },
      { id: "huyurong_05", name: "南京北", city: "南京", lat: 32.16, lon: 118.73 },
      { id: "shanghehang_05", name: "合肥南", city: "合肥", lat: 31.78, lon: 117.3 },
      { id: "heshen_02", name: "六安", city: "六安", lat: 31.75, lon: 116.5 },
      { id: "huyurong_08", name: "汉口", city: "武汉", lat: 30.62, lon: 114.27 },
      { id: "huyurong_09", name: "江汉", city: "江汉", lat: 30.65, lon: 113.16 },
      { id: "huyurong_10", name: "荆门西", city: "荆门", lat: 31.05, lon: 112.16 },
      { id: "huyurong_11", name: "宜昌北", city: "宜昌", lat: 30.76, lon: 111.3 },
      { id: "huyurong_12", name: "恩施南", city: "恩施", lat: 30.27, lon: 109.47 },
      { id: "huyurong_13", name: "涪陵北", city: "涪陵", lat: 29.72, lon: 107.39 },
      { id: "huyurong_14", name: "重庆北", city: "重庆", lat: 29.61, lon: 106.55 },
      { id: "huyurong_15", name: "成都", city: "成都", sourceLat: 30.66, sourceLon: 104.07, lat: 30.72, lon: 103.98 }
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
      { id: "lianxulan_01", name: "连云港", city: "连云港", lat: 34.6, lon: 119.22 },
      { id: "jinghu_09", name: "徐州东", city: "徐州", lat: 34.265, lon: 117.28 },
      { id: "jingxiongshang_07", name: "商丘", city: "商丘", lat: 34.44, lon: 115.65 },
      { id: "lianxulan_04", name: "开封北", city: "开封", lat: 34.82, lon: 114.35 },
      { id: "jingguang_09", name: "郑州东", city: "郑州", lat: 34.758, lon: 113.769 },
      { id: "lianxulan_06", name: "洛阳龙门", city: "洛阳", lat: 34.61, lon: 112.39 },
      { id: "lianxulan_07", name: "三门峡南", city: "三门峡", lat: 34.74, lon: 111.19 },
      { id: "lianxulan_08", name: "渭南北", city: "渭南", lat: 34.52, lon: 109.48 },
      { id: "lianxulan_09", name: "西安北", city: "西安", lat: 34.38, lon: 108.94 },
      { id: "lianxulan_10", name: "咸阳西", city: "咸阳", lat: 34.33, lon: 108.65 },
      { id: "lianxulan_11", name: "宝鸡南", city: "宝鸡", lat: 34.35, lon: 107.15 },
      { id: "lianxulan_12", name: "天水南", city: "天水", lat: 34.56, lon: 105.87 },
      { id: "lianxulan_13", name: "定西北", city: "定西", lat: 35.58, lon: 104.63 },
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
      { id: "jingguang_09", name: "郑州东", city: "郑州", lat: 34.758, lon: 113.769 },
      { id: "zhengyu_02", name: "平顶山西", city: "平顶山", lat: 33.74, lon: 113.3 },
      { id: "zhengyu_03", name: "南阳东", city: "南阳", lat: 32.98, lon: 112.6 },
      { id: "zhengyu_04", name: "襄阳东", city: "襄阳", lat: 32.04, lon: 112.2 },
      { id: "zhengyu_05", name: "神农架", city: "神农架", lat: 31.74, lon: 110.68 },
      { id: "zhengyu_06", name: "万州北", city: "万州", lat: 30.82, lon: 108.39 },
      { id: "huyurong_13", name: "涪陵北", city: "涪陵", lat: 29.72, lon: 107.39 },
      { id: "huyurong_14", name: "重庆北", city: "重庆", lat: 29.61, lon: 106.55 }
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
      { id: "lianxulan_09", name: "西安北", city: "西安", lat: 34.38, lon: 108.94 },
      { id: "xicheng_02", name: "汉中", city: "汉中", lat: 33.063, lon: 107.023 },
      { id: "xicheng_03", name: "广元", city: "广元", lat: 32.44, lon: 105.828 },
      { id: "xicheng_04", name: "绵阳", city: "绵阳", lat: 31.459, lon: 104.741 },
      { id: "xicheng_05", name: "德阳", city: "德阳", lat: 31.13, lon: 104.397 },
      { id: "xicheng_06", name: "成都东", city: "成都", lat: 30.632, lon: 104.141 }
    ]
  },
  {
    id: "hanbanan_high_speed",
    name: "成达万高铁巴中支线",
    shortName: "成达万巴中支线",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "支线预研线路",
    parentLineId: "chengdawan_high_speed",
    networkRole: "branch",
    source: "用户提供参考站序；汉中、南充复用既有站点身份",
    stations: [
      { id: "xicheng_02", name: "汉中", city: "汉中", lat: 33.063, lon: 107.023 },
      { id: "bazhong_01", name: "巴中", city: "巴中", lat: 31.8762, lon: 106.7612 },
      { id: "langyu_04", name: "南充北", city: "南充", lat: 30.856, lon: 106.071 }
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
      { id: "xicheng_06", name: "成都东", city: "成都", lat: 30.632, lon: 104.141 },
      { id: "chenggui_02", name: "眉山东", city: "眉山", lat: 30.05, lon: 103.87 },
      { id: "chenggui_03", name: "乐山", city: "乐山", lat: 29.57, lon: 103.76 },
      { id: "yukun_03", name: "宜宾西", city: "宜宾", lat: 28.751, lon: 104.62 },
      { id: "chenggui_05", name: "毕节", city: "毕节", lat: 27.3, lon: 105.28 },
      { id: "hukun_18", name: "贵阳北", city: "贵阳", lat: 26.65, lon: 106.63 }
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
    source: "用户提供参考坐标；北京站／朝阳及顺义西／怀柔南／密云坐标参考维基百科",
    stations: [
      { id: "jingha_beijing", name: "北京站", city: "北京", lat: 39.901, lon: 116.4206 },
      { id: "jingha_01", name: "北京朝阳", city: "北京", lat: 39.9432, lon: 116.5021 },
      { id: "jingha_shunyixi", name: "顺义西", city: "北京", lat: 40.1778, lon: 116.485 },
      { id: "jingha_huairounan", name: "怀柔南", city: "北京", lat: 40.2772, lon: 116.6988 },
      { id: "jingha_miyun", name: "密云", city: "北京", lat: 40.3508, lon: 116.8447 },
      { id: "jingha_02", name: "承德南", city: "承德", lat: 40.885, lon: 117.965 },
      { id: "jingha_03", name: "朝阳", city: "朝阳", lat: 41.598, lon: 120.404 },
      { id: "jingha_04", name: "阜新", city: "阜新", lat: 42.05, lon: 121.67 },
      { id: "jingha_05", name: "沈阳北", city: "沈阳", lat: 41.817, lon: 123.436 },
      { id: "jingha_06", name: "铁岭西", city: "铁岭", lat: 42.233, lon: 123.673 },
      { id: "jingha_07", name: "四平东", city: "四平", lat: 43.139, lon: 124.438 },
      { id: "jingha_08", name: "长春西", city: "长春", lat: 43.877, lon: 125.201 },
      { id: "jingha_09", name: "哈尔滨西", city: "哈尔滨", lat: 45.707, lon: 126.577 }
    ]
  },
  {
    id: "jingha_chifeng_branch_high_speed",
    name: "京哈高铁赤峰支线",
    shortName: "京哈赤峰支线",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "支线预研线路",
    parentLineId: "jingha_high_speed",
    networkRole: "branch",
    source: "用户提供参考坐标；朝阳复用京哈高铁既有站点身份",
    stations: [
      { id: "jingha_03", name: "朝阳", city: "朝阳", lat: 41.598, lon: 120.404 },
      { id: "jingha_chifeng_02", name: "赤峰", city: "赤峰", lat: 42.258, lon: 118.888 },
      { id: "jingha_chifeng_03", name: "通辽", city: "通辽", lat: 43.617, lon: 122.265 }
    ]
  },
  {
    id: "guangshenhongkong_high_speed",
    name: "广深港高铁",
    shortName: "广深港",
    type: "high_speed",
    typeLabel: "高速",
    region: "cross_region",
    regions: [
      "china_mainland",
      "hk_macao_taiwan"
    ],
    boundaryLabel: "深港交界中点",
    status: "跨区域预研线路",
    source: "用户提供参考坐标；复用既有站点身份",
    stations: [
      { id: "jingguang_24", name: "广州南", city: "广州", region: "china_mainland", lat: 22.99, lon: 113.27 },
      { id: "guangshen_02", name: "广州南沙", city: "广州南沙", region: "china_mainland", lat: 22.866, lon: 113.672 },
      { id: "heshen_10", name: "深圳北", city: "深圳", region: "china_mainland", lat: 22.61, lon: 114.03 },
      { id: "shenzhen_hongkong_02", name: "香港西九龙", city: "香港", region: "hk_macao_taiwan", lat: 22.303, lon: 114.161 }
    ]
  },
  {
    id: "taiwan_west_high_speed",
    name: "台湾西部高铁",
    shortName: "台湾西高铁",
    type: "high_speed",
    typeLabel: "高速",
    region: "hk_macao_taiwan",
    status: "预研线路",
    source: "用户提供参考坐标；台湾节点统一归入港澳台区域",
    stations: [
      { id: "taiwan_01", name: "台北", city: "台北", region: "hk_macao_taiwan", lat: 25.0478, lon: 121.517 },
      { id: "taiwan_02", name: "桃园", city: "桃园", region: "hk_macao_taiwan", lat: 25.013, lon: 121.214 },
      { id: "taiwan_03", name: "新竹", city: "新竹", region: "hk_macao_taiwan", lat: 24.808, lon: 120.972 },
      { id: "taiwan_04", name: "台中", city: "台中", region: "hk_macao_taiwan", lat: 24.1368, lon: 120.685 },
      { id: "taiwan_05", name: "嘉义", city: "嘉义", region: "hk_macao_taiwan", lat: 23.479, lon: 120.441 },
      { id: "taiwan_06", name: "台南", city: "台南", region: "hk_macao_taiwan", lat: 22.997, lon: 120.213 },
      { id: "taiwan_07", name: "高雄", city: "高雄", region: "hk_macao_taiwan", lat: 22.687, lon: 120.307 }
    ]
  },
  {
    id: "huadong_conventional",
    name: "花东铁路",
    shortName: "花东",
    type: "conventional",
    typeLabel: "普速",
    region: "hk_macao_taiwan",
    status: "普速预研线路",
    source: "用户提供参考坐标；台湾节点统一归入港澳台区域",
    stations: [
      { id: "taiwan_01", name: "台北", city: "台北", region: "hk_macao_taiwan", lat: 25.0478, lon: 121.517 },
      { id: "taiwan_08", name: "花莲", city: "花莲", region: "hk_macao_taiwan", lat: 23.992, lon: 121.614 },
      { id: "taiwan_09", name: "台东", city: "台东", region: "hk_macao_taiwan", lat: 22.793, lon: 121.124 }
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
      { id: "langyu_02", name: "陇南", city: "陇南", lat: 33.3803, lon: 104.96 },
      { id: "xicheng_03", name: "广元", city: "广元", lat: 32.44, lon: 105.828 },
      { id: "langyu_04", name: "南充北", city: "南充", lat: 30.856, lon: 106.071 },
      { id: "langyu_05", name: "广安南", city: "广安", lat: 30.47, lon: 106.63 }
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
    parentLineId: "langyu_conventional",
    networkRole: "branch",
    source: "用户提供参考站序；广元复用既有站点身份",
    stations: [
      { id: "xicheng_03", name: "广元", city: "广元", lat: 32.44, lon: 105.828 },
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
    source: "原京包银拆分；北京段清河／昌平／延庆及枢纽坐标参考维基百科",
    stations: [
      { id: "jingbao_01", name: "北京北", city: "北京", lat: 39.9453, lon: 116.3472 },
      { id: "jingbao_qinghe", name: "清河", city: "北京", lat: 40.0399, lon: 116.3092 },
      { id: "jingbao_changping", name: "昌平", city: "北京", lat: 40.1888, lon: 116.1873 },
      { id: "jingbao_yanqing", name: "延庆", city: "北京", lat: 40.4347, lon: 115.9781 },
      { id: "jingbao_02", name: "张家口", city: "张家口", lat: 40.752, lon: 114.8828 },
      { id: "jingbao_03", name: "乌兰察布", city: "乌兰察布", lat: 40.9642, lon: 113.1633 },
      { id: "jingbao_04", name: "呼和浩特东", city: "呼和浩特", lat: 40.8511, lon: 111.7653 },
      { id: "jingbao_05", name: "包头", city: "包头", lat: 40.6039, lon: 109.8312 }
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
    source: "原京包银拆分；包头复用京包高铁既有站点身份",
    stations: [
      { id: "jingbao_05", name: "包头", city: "包头", lat: 40.6039, lon: 109.8312 },
      { id: "baoyin_02", name: "巴彦淖尔", city: "巴彦淖尔", note: "河套平原中心", lat: 40.7336, lon: 107.4048 },
      { id: "baoyin_04", name: "乌海", city: "乌海", note: "内蒙古西部节点", lat: 39.6689, lon: 106.801 },
      { id: "baoyin_05", name: "石嘴山", city: "石嘴山", note: "宁夏北部地级市", lat: 38.9575, lon: 106.377 },
      { id: "baoyin_06", name: "银川", city: "银川", note: "宁夏首府、线路终点", lat: 38.4915, lon: 106.1669 }
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
      { id: "jingbao_02", name: "张家口", city: "张家口", lat: 40.752, lon: 114.8828 },
      { id: "zhangdaxi_02", name: "大同南", city: "大同", lat: 40.02, lon: 113.15 },
      { id: "zhangdaxi_03", name: "朔州东", city: "朔州", lat: 39.32, lon: 112.43 },
      { id: "zhangdaxi_04", name: "忻州西", city: "忻州", lat: 38.42, lon: 112.73 },
      { id: "zhangdaxi_05", name: "太原南", city: "太原", lat: 37.78, lon: 112.56 },
      { id: "zhangdaxi_06", name: "晋中", city: "晋中", lat: 37.68, lon: 112.73 },
      { id: "zhangdaxi_07", name: "临汾西", city: "临汾", lat: 36.09, lon: 111.5 },
      { id: "zhangdaxi_08", name: "运城北", city: "运城", lat: 35.07, lon: 110.99 },
      { id: "lianxulan_08", name: "渭南北", city: "渭南", lat: 34.52, lon: 109.48 },
      { id: "lianxulan_09", name: "西安北", city: "西安", lat: 34.38, lon: 108.94 }
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
      { id: "rila_01", name: "日照西", city: "日照", lat: 35.416, lon: 119.354 },
      { id: "rila_02", name: "临沂北", city: "临沂", lat: 35.124, lon: 118.378 },
      { id: "rila_03", name: "济宁北", city: "济宁", lat: 35.5, lon: 116.58 },
      { id: "jingxiongshang_06", name: "菏泽东", city: "菏泽", lat: 35.245, lon: 115.52 },
      { id: "lianxulan_04", name: "开封北", city: "开封", lat: 34.82, lon: 114.35 }
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
      { id: "jingguang_03", name: "石家庄", city: "石家庄", lat: 38.0225, lon: 114.484 },
      { id: "shita_02", name: "阳泉北", city: "阳泉", lat: 38.06, lon: 113.63 },
      { id: "zhangdaxi_05", name: "太原南", city: "太原", lat: 37.78, lon: 112.56 },
      { id: "taiyin_02", name: "吕梁", city: "吕梁", lat: 37.5675, lon: 111.1311 },
      { id: "xiyubao_04", name: "榆林南", city: "榆林", lat: 38.219, lon: 109.734 },
      { id: "baoyin_06", name: "银川", city: "银川", lat: 38.4915, lon: 106.1669 },
      { id: "taiyin_04", name: "巴彦浩特", city: "巴彦浩特", lat: 38.839, lon: 105.668 }
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
      { id: "xicheng_06", name: "成都东", city: "成都", lat: 30.632, lon: 104.141 },
      { id: "chengyu_02", name: "资阳北", city: "资阳", lat: 30.136, lon: 104.616 },
      { id: "chengyu_03", name: "内江北", city: "内江", lat: 29.6126, lon: 105.0817 },
      { id: "chengyu_04", name: "重庆西", city: "重庆", lat: 29.502, lon: 106.438 }
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
      { id: "jinghu_06", name: "济南西", city: "济南", lat: 36.67, lon: 116.9 },
      { id: "jingxiongshang_04", name: "聊城西", city: "聊城", lat: 36.43, lon: 115.92 },
      { id: "jingxiongshang_05", name: "濮阳东", city: "濮阳", lat: 35.77, lon: 115.06 },
      { id: "jingguang_09", name: "郑州东", city: "郑州", lat: 34.758, lon: 113.769 }
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
      { id: "jingguang_24", name: "广州南", city: "广州", lat: 22.99, lon: 113.27 },
      { id: "nanguang_02", name: "佛山西", city: "佛山", lat: 23.09, lon: 112.9 },
      { id: "nanguang_03", name: "肇庆东", city: "肇庆", lat: 23.11, lon: 112.61 },
      { id: "nanguang_04", name: "云浮东", city: "云浮", lat: 22.93, lon: 112.05 },
      { id: "nanguang_05", name: "梧州南", city: "梧州", lat: 23.5, lon: 111.25 },
      { id: "nanguang_06", name: "贵港", city: "贵港", lat: 23.09, lon: 109.61 },
      { id: "nanguang_07", name: "南宁东", city: "南宁", lat: 22.84, lon: 108.37 }
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
      { id: "nanguang_04", name: "云浮东", city: "云浮", lat: 22.93, lon: 112.05 },
      { id: "yuegui_02", name: "茂名", city: "茂名", lat: 21.66, lon: 110.92 },
      { id: "yuegui_03", name: "玉林", city: "玉林", lat: 22.63, lon: 110.15 },
      { id: "nanguang_06", name: "贵港", city: "贵港", lat: 23.09, lon: 109.61 }
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
      { id: "nanguang_02", name: "佛山西", city: "佛山", lat: 23.09, lon: 112.9 },
      { id: "nanguang_03", name: "肇庆东", city: "肇庆", lat: 23.11, lon: 112.61 },
      { id: "nanguang_04", name: "云浮东", city: "云浮", lat: 22.93, lon: 112.05 },
      { id: "guangzhan_03", name: "阳江", city: "阳江", lat: 21.87, lon: 111.98 },
      { id: "yuegui_02", name: "茂名", city: "茂名", lat: 21.66, lon: 110.92 },
      { id: "guangzhan_05", name: "湛江北", city: "湛江", lat: 21.27, lon: 110.35 }
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
      { id: "nanguang_07", name: "南宁东", city: "南宁", lat: 22.84, lon: 108.37 },
      { id: "nankun_02", name: "百色", city: "百色", lat: 23.9, lon: 106.61 },
      { id: "nankun_03", name: "文山", city: "文山", lat: 23.37, lon: 104.24 },
      { id: "nankun_04", name: "蒙自", city: "蒙自", lat: 23.37, lon: 103.38 },
      { id: "hukun_21", name: "昆明南", city: "昆明", lat: 24.874, lon: 102.862 }
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
      { id: "nankun_02", name: "百色", city: "百色", lat: 23.9, lon: 106.61 },
      { id: "nankun_railway_03", name: "兴义", city: "兴义", lat: 25.09, lon: 104.9 },
      { id: "hukun_21", name: "昆明南", city: "昆明", lat: 24.874, lon: 102.862 }
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
      { id: "chengyu_04", name: "重庆西", city: "重庆", lat: 29.502, lon: 106.438 },
      { id: "yunan_02", name: "遵义", city: "遵义", lat: 27.7254, lon: 106.9272 },
      { id: "hukun_18", name: "贵阳北", city: "贵阳", lat: 26.65, lon: 106.63 },
      { id: "yunan_04", name: "都匀东", city: "都匀", lat: 26.26, lon: 107.52 },
      { id: "yunan_05", name: "河池西", city: "河池", lat: 24.69, lon: 108.02 },
      { id: "nanguang_07", name: "南宁东", city: "南宁", lat: 22.84, lon: 108.37 }
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
      { id: "shanghehang_09", name: "杭州东", city: "杭州", lat: 30.315, lon: 120.21 },
      { id: "hangshen_02", name: "绍兴北", city: "绍兴", lat: 30.109, lon: 120.536 },
      { id: "hangshen_03", name: "宁波", city: "宁波", lat: 29.862, lon: 121.536 },
      { id: "hangshen_04", name: "台州西", city: "台州", lat: 28.657, lon: 121.304 },
      { id: "hangshen_05", name: "温州南", city: "温州", lat: 27.972, lon: 120.585 },
      { id: "hangshen_06", name: "宁德", city: "宁德", lat: 26.665, lon: 119.588 },
      { id: "hangshen_07", name: "福州南", city: "福州", lat: 25.985, lon: 119.39 },
      { id: "hangshen_08", name: "莆田", city: "莆田", lat: 25.355, lon: 119.063 },
      { id: "hangshen_09", name: "泉州东", city: "泉州", lat: 24.9247, lon: 118.7658 },
      { id: "hangshen_10", name: "厦门北", city: "厦门", lat: 24.637, lon: 118.074 },
      { id: "hangshen_11", name: "漳州", city: "漳州", lat: 24.503, lon: 117.664 },
      { id: "hangshen_12", name: "潮汕", city: "揭阳/潮汕", lat: 23.54, lon: 116.59 },
      { id: "hangshen_13", name: "汕尾", city: "汕尾", lat: 22.786, lon: 115.382 },
      { id: "heshen_08", name: "惠州北", city: "惠州", lat: 23.12, lon: 114.42 }
    ]
  },
  {
    id: "hangshen_lishui_branch_high_speed",
    name: "杭深高铁丽水支线",
    shortName: "杭深丽水支线",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "支线预研线路",
    parentLineId: "hangshen_high_speed",
    networkRole: "branch",
    source: "用户提供参考坐标；温州南、金华复用既有站点身份",
    stations: [
      { id: "hangshen_05", name: "温州南", city: "温州", lat: 27.972, lon: 120.585 },
      { id: "hangshen_lishui_02", name: "丽水站", city: "丽水", lat: 28.45, lon: 119.919 },
      { id: "hukun_04", name: "金华", city: "金华", lat: 29.1, lon: 119.65 }
    ]
  },
  {
    id: "hangshen_zhoushan_branch_high_speed",
    name: "杭深高铁舟山支线",
    shortName: "杭深舟山支线",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "支线预研线路",
    parentLineId: "hangshen_high_speed",
    networkRole: "branch",
    source: "用户提供参考坐标；宁波复用既有站点身份",
    stations: [
      { id: "hangshen_03", name: "宁波", city: "宁波", lat: 29.862, lon: 121.536 },
      { id: "hangshen_zhoushan_02", name: "舟山", city: "舟山", lat: 30.016, lon: 122.107 }
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
    source: "用户提供线路方向；兰州西、乌鲁木齐和伊宁复用既有站点身份；乌伊段并入兰新高铁",
    stations: [
      { id: "lianxulan_14", name: "兰州西", city: "兰州", lat: 36.0675, lon: 103.7492 },
      { id: "lanxin_02", name: "海东西", city: "海东", lat: 36.5095, lon: 102.0535 },
      { id: "lanxin_03", name: "西宁", city: "西宁", lat: 36.6217, lon: 101.8067 },
      { id: "lanxin_04", name: "张掖西", city: "张掖", lat: 38.925, lon: 100.421 },
      { id: "lanxin_05", name: "酒泉南", city: "酒泉", lat: 39.7037, lon: 98.5362 },
      { id: "lanxin_06", name: "嘉峪关南", city: "嘉峪关", lat: 39.687, lon: 98.29 },
      { id: "lanxin_07", name: "哈密", city: "哈密", lat: 42.82, lon: 93.515 },
      { id: "lanxin_08", name: "吐鲁番北", city: "吐鲁番", lat: 43.016, lon: 89.183 },
      { id: "lanxin_09", name: "乌鲁木齐", city: "乌鲁木齐", lat: 43.831, lon: 87.535 },
      { id: "yiku_01", name: "伊宁", city: "伊宁", lat: 43.977, lon: 81.273 }
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
      { id: "lianxulan_14", name: "兰州西", city: "兰州", lat: 36.0675, lon: 103.7492 },
      { id: "lanzhang_02", name: "武威东", city: "武威", lat: 37.92, lon: 102.71 },
      { id: "lanzhang_03", name: "金昌南", city: "金昌", lat: 38.43, lon: 102.18 },
      { id: "lanxin_04", name: "张掖西", city: "张掖", lat: 38.925, lon: 100.421 }
    ]
  },
  {
    id: "jiqing_high_speed",
    name: "济青威高铁",
    shortName: "济青威",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标",
    stations: [
      { id: "jiqing_01", name: "济南东", city: "济南", lat: 36.767, lon: 117.209 },
      { id: "jiqing_02", name: "淄博北", city: "淄博", lat: 36.875, lon: 118.103 },
      { id: "jiqing_03", name: "潍坊北", city: "潍坊", lat: 36.78, lon: 119.155 },
      { id: "jiqing_04", name: "青岛北", city: "青岛", lat: 36.169, lon: 120.376 },
      { id: "qingwei_02", name: "烟台南", city: "烟台", lat: 37.431, lon: 121.383 },
      { id: "qingwei_03", name: "威海", city: "威海", lat: 37.424, lon: 122.109 }
    ]
  },
  {
    id: "jiqing_binlin_branch_high_speed",
    name: "济青威高铁滨临支线",
    shortName: "济青威滨临支线",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "支线预研线路",
    parentLineId: "jiqing_high_speed",
    networkRole: "branch",
    source: "用户指定站序；滨州、淄博、临沂复用既有站点身份",
    stations: [
      { id: "jinwei_02", name: "滨州", city: "滨州", lat: 37.38, lon: 118.017 },
      { id: "jiqing_02", name: "淄博北", city: "淄博", lat: 36.875, lon: 118.103 },
      { id: "rila_02", name: "临沂北", city: "临沂", lat: 35.124, lon: 118.378 }
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
      { id: "lianxulan_11", name: "宝鸡南", city: "宝鸡", lat: 34.35, lon: 107.15 },
      { id: "baozhong_02", name: "平凉", city: "平凉", lat: 35.5506, lon: 106.7079 },
      { id: "baozhong_03", name: "固原", city: "固原", lat: 36.011, lon: 106.285 },
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
      { id: "chenggui_03", name: "乐山", city: "乐山", lat: 29.57, lon: 103.76 },
      { id: "chengkun_02", name: "西昌西", city: "西昌", lat: 27.8718, lon: 102.1591 },
      { id: "chengkun_03", name: "攀枝花南", city: "攀枝花", lat: 26.4714, lon: 101.7463 },
      { id: "chengkun_04", name: "楚雄", city: "楚雄", lat: 25.036, lon: 101.546 },
      { id: "hukun_21", name: "昆明南", city: "昆明", lat: 24.874, lon: 102.862 }
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
      { id: "hukun_21", name: "昆明南", city: "昆明", lat: 24.874, lon: 102.862 },
      { id: "kunmo_02", name: "玉溪", city: "玉溪", lat: 24.351, lon: 102.542 },
      { id: "kunmo_03", name: "普洱", city: "普洱", lat: 22.789, lon: 100.981 },
      { id: "kunmo_04", name: "景洪", city: "景洪", lat: 22.006, lon: 100.797 }
    ]
  },
  {
    id: "darui_lushui_branch_conventional",
    name: "保山—泸水铁路",
    shortName: "保泸",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "原中缅泸水支线；父线海外段已移除，暂作独立境内预研线",
    stations: [
      { id: "darui_02", name: "保山", city: "保山", lat: 25.127, lon: 99.177 },
      { id: "darui_lushui_02", name: "泸水", city: "泸水", lat: 25.851, lon: 98.857 }
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
      { id: "kunmo_03", name: "普洱", city: "普洱", lat: 22.789, lon: 100.981 },
      { id: "dalin_02", name: "临沧", city: "临沧", lat: 23.886, lon: 100.088 },
      { id: "diancang_03", name: "大理", city: "大理", lat: 25.592, lon: 100.2485 }
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
    source: "用户提供参考坐标；哈尔滨复用既有站点身份；鹤岗为延伸终点",
    stations: [
      { id: "jingha_09", name: "哈尔滨西", city: "哈尔滨", lat: 45.707, lon: 126.577 },
      { id: "hamujia_02", name: "牡丹江", city: "牡丹江", lat: 44.5877, lon: 129.6065 },
      { id: "hamujia_03", name: "鸡西西", city: "鸡西", lat: 45.3088, lon: 130.8148 },
      { id: "hamujia_04", name: "七台河西", city: "七台河", lat: 45.7423, lon: 130.7737 },
      { id: "hamujia_05", name: "双鸭山西", city: "双鸭山", lat: 46.7054, lon: 131.0846 },
      { id: "hamujia_06", name: "佳木斯", city: "佳木斯", lat: 46.804, lon: 130.3836 },
      { id: "hamujia_07", name: "鹤岗市", city: "鹤岗", lat: 47.35, lon: 130.297 }
    ]
  },
  {
    id: "hayi_high_speed",
    name: "哈伊高铁",
    shortName: "哈伊",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；哈尔滨复用既有站点身份；黑河为哈伊黑通道终点",
    stations: [
      { id: "jingha_09", name: "哈尔滨西", city: "哈尔滨", lat: 45.707, lon: 126.577 },
      { id: "hayi_02", name: "绥化", city: "绥化", lat: 46.646, lon: 126.99 },
      { id: "hayi_03", name: "伊春", city: "伊春", lat: 47.728, lon: 128.84 },
      { id: "hayi_04", name: "黑河", city: "黑河", lat: 50.245, lon: 127.528 }
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
      { id: "yuxia_01", name: "重庆东", city: "重庆", lat: 29.5, lon: 106.65 },
      { id: "yuxia_02", name: "黔江", city: "黔江", lat: 29.475, lon: 108.77 },
      { id: "yuxia_03", name: "张家界西", city: "张家界", lat: 29.13, lon: 110.45 },
      { id: "yuxia_04", name: "常德", city: "常德", lat: 29.055, lon: 111.7 },
      { id: "yuxia_05", name: "益阳南", city: "益阳", lat: 28.525, lon: 112.355 },
      { id: "yuxia_06", name: "长沙西", city: "长沙", lat: 28.32, lon: 112.805 },
      { id: "hukun_11", name: "萍乡北", city: "萍乡", lat: 27.62, lon: 113.9 },
      { id: "heshen_05", name: "吉安西", city: "吉安", lat: 27.1, lon: 114.98 },
      { id: "heshen_06", name: "赣州西", city: "赣州", lat: 25.82, lon: 114.92 },
      { id: "yuxia_10", name: "龙岩", city: "龙岩", lat: 25.095, lon: 117.015 },
      { id: "hangshen_11", name: "漳州", city: "漳州", lat: 24.503, lon: 117.664 },
      { id: "hangshen_10", name: "厦门北", city: "厦门", lat: 24.637, lon: 118.074 }
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
      { id: "shanghehang_05", name: "合肥南", city: "合肥", lat: 31.78, lon: 117.3 },
      { id: "shanghehang_06", name: "芜湖", city: "芜湖", lat: 31.34, lon: 118.39 },
      { id: "hefu_03", name: "铜陵北", city: "铜陵", lat: 30.945, lon: 117.84 },
      { id: "hefu_04", name: "黄山北", city: "黄山", lat: 29.815, lon: 118.295 },
      { id: "hukun_06", name: "上饶", city: "上饶", lat: 28.45, lon: 117.97 },
      { id: "hefu_06", name: "南平", city: "南平", lat: 27.655, lon: 118.08 },
      { id: "hangshen_07", name: "福州南", city: "福州", lat: 25.985, lon: 119.39 }
    ]
  },
  {
    id: "heanqihuang_high_speed",
    name: "合福高铁安池支线",
    shortName: "合福安池支线",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "支线预研线路",
    parentLineId: "hefu_high_speed",
    networkRole: "branch",
    source: "用户提供参考坐标；合肥南、黄山北复用既有站点身份",
    stations: [
      { id: "shanghehang_05", name: "合肥南", city: "合肥", lat: 31.78, lon: 117.3 },
      { id: "heanqihuang_02", name: "安庆站", city: "安庆", lat: 30.543, lon: 117.063 },
      { id: "heanqihuang_03", name: "池州站", city: "池州", lat: 30.664, lon: 117.491 },
      { id: "hefu_04", name: "黄山北", city: "黄山", lat: 29.815, lon: 118.295 }
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
      { id: "xiwu_01", name: "西安东", city: "西安", lat: 34.249, lon: 109.137 },
      { id: "xiwu_02", name: "商洛西", city: "商洛", lat: 33.872, lon: 109.834 },
      { id: "xiwu_03", name: "十堰东", city: "十堰", lat: 32.646, lon: 110.854 },
      { id: "zhengyu_04", name: "襄阳东", city: "襄阳", lat: 32.04, lon: 112.2 },
      { id: "xiwu_05", name: "随州南", city: "随州", lat: 31.635, lon: 113.382 },
      { id: "huyurong_08", name: "汉口", city: "武汉", lat: 30.62, lon: 114.27 }
    ]
  },
  {
    id: "hannanxinhe_high_speed",
    name: "汉南信合高铁",
    shortName: "汉南信合",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户指定线路合并；汉中、安康、十堰、南阳、信阳、六安复用既有站点身份",
    stations: [
      { id: "xicheng_02", name: "汉中", city: "汉中", lat: 33.063, lon: 107.023 },
      { id: "xiyu_02", name: "安康西", city: "安康", lat: 32.733, lon: 108.9464 },
      { id: "xiwu_03", name: "十堰东", city: "十堰", lat: 32.646, lon: 110.854 },
      { id: "zhengyu_03", name: "南阳东", city: "南阳", lat: 32.98, lon: 112.6 },
      { id: "jingguang_13", name: "信阳东", city: "信阳", lat: 32.15, lon: 114.12 },
      { id: "heshen_02", name: "六安", city: "六安", lat: 31.75, lon: 116.5 }
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
      { id: "jingha_05", name: "沈阳北", city: "沈阳", lat: 41.817, lon: 123.436 },
      { id: "shenda_02", name: "辽阳", city: "辽阳", lat: 41.27, lon: 123.174 },
      { id: "shenda_03", name: "鞍山西", city: "鞍山", lat: 41.108, lon: 122.922 },
      { id: "shenda_04", name: "营口东", city: "营口", lat: 40.625, lon: 122.358 },
      { id: "shenda_05", name: "大连北", city: "大连", lat: 39.014, lon: 121.615 }
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
      { id: "jinqinshen_05", name: "锦州南", city: "锦州", sourceLat: 41.0172, sourceLon: 121.1254, lat: 41.06, lon: 121.151 },
      { id: "shenda_branch_02", name: "盘锦", city: "盘锦", lat: 41.124, lon: 122.07 },
      { id: "shenda_04", name: "营口东", city: "营口", sourceLat: 40.6195, sourceLon: 122.426, lat: 40.625, lon: 122.358 }
    ]
  },
  {
    id: "jingha_futong_branch_high_speed",
    name: "京哈高铁抚通支线",
    shortName: "京哈抚通支线",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "支线预研线路",
    parentLineId: "jingha_high_speed",
    networkRole: "branch",
    source: "用户提供参考坐标；沈阳北复用既有站点身份",
    stations: [
      { id: "jingha_05", name: "沈阳北", city: "沈阳", lat: 41.817, lon: 123.436 },
      { id: "shenfu_02", name: "抚顺", city: "抚顺", lat: 41.88, lon: 123.957 },
      { id: "changtongbai_03", name: "通化站", city: "通化", lat: 41.728, lon: 125.939 }
    ]
  },
  {
    id: "changtongbai_high_speed",
    name: "长通白高铁",
    shortName: "长通白",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；长春复用既有站点身份",
    stations: [
      { id: "jingha_08", name: "长春西", city: "长春", lat: 43.877, lon: 125.201 },
      { id: "changtongbai_02", name: "辽源站", city: "辽源", lat: 42.902, lon: 125.145 },
      { id: "changtongbai_03", name: "通化站", city: "通化", lat: 41.728, lon: 125.939 },
      { id: "changtongbai_04", name: "白山站", city: "白山", lat: 41.944, lon: 126.418 }
    ]
  },
  {
    id: "changjisui_high_speed",
    name: "长吉珲高铁",
    shortName: "长吉珲",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；长春复用既有站点身份；本线暂到延吉",
    stations: [
      { id: "jingha_08", name: "长春西", city: "长春", lat: 43.877, lon: 125.201 },
      { id: "changjisui_02", name: "吉林市", city: "吉林市", lat: 43.837, lon: 126.55 },
      { id: "changjisui_03", name: "延吉", city: "延吉", lat: 42.906, lon: 129.515 }
    ]
  },
  {
    id: "changsongbai_high_speed",
    name: "长松白高铁",
    shortName: "长松白",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；长春复用既有站点身份；乌兰浩特复用通海铁路节点",
    stations: [
      { id: "jingha_08", name: "长春西", city: "长春", lat: 43.877, lon: 125.201 },
      { id: "changsongbai_02", name: "松原", city: "松原", lat: 45.141, lon: 124.825 },
      { id: "changsongbai_03", name: "白城", city: "白城", lat: 45.619, lon: 122.838 },
      { id: "tonghai_02", name: "乌兰浩特", city: "乌兰浩特", lat: 46.072, lon: 122.093 }
    ]
  },
  {
    id: "shendan_high_speed",
    name: "沈丹高铁",
    shortName: "沈丹",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；沈阳北、丹东复用既有站点身份",
    stations: [
      { id: "jingha_05", name: "沈阳北", city: "沈阳", lat: 41.817, lon: 123.436 },
      { id: "shendan_02", name: "本溪", city: "本溪", lat: 41.294, lon: 123.766 },
      { id: "danda_01", name: "丹东", city: "丹东", lat: 40.129, lon: 124.397 }
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
      { id: "danda_01", name: "丹东", city: "丹东", lat: 40.129, lon: 124.397 },
      { id: "shenda_05", name: "大连北", city: "大连", lat: 39.014, lon: 121.615 }
    ]
  },
  {
    id: "jinqin_high_speed",
    name: "津秦高铁",
    shortName: "津秦",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "运营线路",
    source: "用户指定站序；天津／唐山／秦皇岛／滨海西复用既有站点身份；宁河按服务该区的滨海北一带落点；滦河／北戴河坐标参考维基百科",
    stations: [
      { id: "jinqinshen_01", name: "天津", city: "天津", lat: 39.142, lon: 117.176 },
      { id: "jingbin_binhaixi", name: "滨海西", city: "天津", lat: 39.0801, lon: 117.6051 },
      { id: "jinqin_ninghe", name: "宁河", city: "天津", lat: 39.2348, lon: 117.7562 },
      { id: "jinqinshen_02", name: "唐山", city: "唐山", lat: 39.632, lon: 118.18 },
      { id: "jinqin_luanhe", name: "滦河", city: "滦州", lat: 39.8528, lon: 118.6665 },
      { id: "jinqin_beidaihe", name: "北戴河", city: "秦皇岛", lat: 39.8502, lon: 119.4132 },
      { id: "jinqinshen_03", name: "秦皇岛", city: "秦皇岛", lat: 39.949, lon: 119.604 }
    ]
  },
  {
    id: "qinshen_high_speed",
    name: "秦沈高铁",
    shortName: "秦沈",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "运营线路",
    source: "由原津秦沈拆出；秦皇岛／葫芦岛北／锦州南／沈阳北复用既有站点身份",
    stations: [
      { id: "jinqinshen_03", name: "秦皇岛", city: "秦皇岛", lat: 39.949, lon: 119.604 },
      { id: "jinqinshen_04", name: "葫芦岛北", city: "葫芦岛", lat: 40.756, lon: 120.84 },
      { id: "jinqinshen_05", name: "锦州南", city: "锦州", lat: 41.06, lon: 121.151 },
      { id: "jingha_05", name: "沈阳北", city: "沈阳", lat: 41.817, lon: 123.436 }
    ]
  },
  {
    id: "jinwei_high_speed",
    name: "津潍高铁",
    shortName: "津潍",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "运营线路",
    source: "区县级挂名精简；滨海／滨州／东营南／潍坊北复用既有站点身份；黄骅北／海兴西／无棣／寿光东按公开选址落点",
    stations: [
      { id: "jinwei_01", name: "滨海", city: "天津", lat: 39.032, lon: 117.71 },
      { id: "jinwei_huanghuabei", name: "黄骅北", city: "黄骅", lat: 38.401, lon: 117.385 },
      { id: "jinwei_haixingxi", name: "海兴西", city: "海兴", lat: 38.115, lon: 117.45 },
      { id: "jinwei_wudi", name: "无棣", city: "无棣", lat: 37.752, lon: 117.725 },
      { id: "jinwei_02", name: "滨州", city: "滨州", lat: 37.38, lon: 118.017 },
      { id: "jinwei_03", name: "东营南", city: "东营", lat: 37.387, lon: 118.673 },
      { id: "jinwei_shouguangdong", name: "寿光东", city: "寿光", lat: 36.905, lon: 118.865 },
      { id: "jiqing_03", name: "潍坊北", city: "潍坊", lat: 36.78, lon: 119.155 }
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
      { id: "lianxulan_01", name: "连云港", city: "连云港", lat: 34.6, lon: 119.22 },
      { id: "liuyantong_02", name: "盐城", city: "盐城", lat: 33.347, lon: 120.161 },
      { id: "huyurong_02", name: "南通", city: "南通", lat: 31.98, lon: 120.9 }
    ]
  },
  {
    id: "xuyan_high_speed",
    name: "徐盐高铁",
    shortName: "徐盐",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "预研线路",
    source: "用户提供参考坐标；徐州东、盐城复用既有站点身份",
    stations: [
      { id: "jinghu_09", name: "徐州东", city: "徐州", lat: 34.265, lon: 117.28 },
      { id: "xuyan_02", name: "宿迁站", city: "宿迁", lat: 33.94, lon: 118.296 },
      { id: "xuyan_03", name: "淮安东站", city: "淮安", lat: 33.627, lon: 119.104 },
      { id: "liuyantong_02", name: "盐城", city: "盐城", lat: 33.347, lon: 120.161 }
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
      { id: "nanguang_07", name: "南宁东", city: "南宁", lat: 22.84, lon: 108.37 },
      { id: "nanzhan_02", name: "钦州东", city: "钦州", lat: 21.96, lon: 108.65 },
      { id: "nanzhan_03", name: "北海", city: "北海", lat: 21.48, lon: 109.12 },
      { id: "guangzhan_05", name: "湛江北", city: "湛江", lat: 21.27, lon: 110.35 }
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
      { id: "nanzhan_02", name: "钦州东", city: "钦州", lat: 21.96, lon: 108.65 },
      { id: "nanzhan_fangchenggang_02", name: "防城港北", city: "防城港", lat: 21.687, lon: 108.354 }
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
      { id: "zhengyu_04", name: "襄阳东", city: "襄阳", lat: 32.04, lon: 112.2 },
      { id: "huyurong_10", name: "荆门西", city: "荆门", lat: 31.05, lon: 112.16 },
      { id: "huyurong_11", name: "宜昌北", city: "宜昌", lat: 30.76, lon: 111.3 },
      { id: "yuxia_04", name: "常德", city: "常德", lat: 29.055, lon: 111.7 }
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
      { id: "jingguang_20", name: "衡阳东", city: "衡阳", sourceLat: 26.8997, sourceLon: 112.7045, lat: 26.85, lon: 112.62 },
      { id: "nanheng_02", name: "永州", city: "永州", lat: 26.4577, lon: 111.5655 },
      { id: "guigang_03", name: "桂林西", city: "桂林", sourceLat: 25.3315, sourceLon: 110.2982, lat: 25.3575, lon: 110.2625 },
      { id: "nanheng_04", name: "柳州", city: "柳州", lat: 24.3105, lon: 109.3834 },
      { id: "nanheng_05", name: "来宾北", city: "来宾", lat: 23.733, lon: 109.229 },
      { id: "nanguang_07", name: "南宁东", city: "南宁", sourceLat: 22.8446, sourceLon: 108.41, lat: 22.84, lon: 108.37 }
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
      { id: "yuxia_05", name: "益阳南", city: "益阳", lat: 28.525, lon: 112.355 },
      { id: "hukun_15", name: "娄底南", city: "娄底", lat: 27.7, lon: 112 },
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
      { id: "hukun_16", name: "怀化南", city: "怀化", lat: 27.55, lon: 109.96 },
      { id: "guigang_03", name: "桂林西", city: "桂林", lat: 25.3575, lon: 110.2625 }
    ]
  },
  {
    id: "changjiu_high_speed",
    name: "渝厦高铁常九支线",
    shortName: "渝厦常九支线",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "支线预研线路",
    parentLineId: "yuxia_high_speed",
    networkRole: "branch",
    source: "用户指定线路调整；复用渝厦高铁常德站与既有岳阳、九江站点身份",
    stations: [
      { id: "yuxia_04", name: "常德", city: "常德", lat: 29.055, lon: 111.7 },
      { id: "jingguang_17", name: "岳阳东", city: "岳阳", lat: 29.38, lon: 113.16 },
      { id: "heshen_03", name: "九江", city: "九江", lat: 29.72, lon: 115.98 }
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
      { id: "guangzhan_05", name: "湛江北", city: "湛江", sourceLat: 21.273, sourceLon: 110.357, lat: 21.27, lon: 110.35 },
      { id: "zhanhai_02", name: "海口北", city: "海口", lat: 20.05, lon: 110.16 }
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
      { id: "zhanhai_02", name: "海口北", city: "海口", lat: 20.05, lon: 110.16 },
      { id: "hainanring_02", name: "琼海", city: "琼海", lat: 19.258, lon: 110.474 },
      { id: "hainanring_03", name: "三亚", city: "三亚", lat: 18.252, lon: 109.512 },
      { id: "hainanring_04", name: "儋州", city: "儋州", lat: 19.709, lon: 109.2 }
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
      { id: "jingguang_09", name: "郑州东", city: "郑州", lat: 34.758, lon: 113.769 },
      { id: "zhengtai_02", name: "焦作", city: "焦作", lat: 35.214, lon: 113.24 },
      { id: "zhengtai_03", name: "晋城东", city: "晋城", lat: 35.509, lon: 112.927 },
      { id: "zhengtai_04", name: "长治东", city: "长治", lat: 36.196, lon: 113.173 },
      { id: "zhangdaxi_06", name: "晋中", city: "晋中", lat: 37.68, lon: 112.73 },
      { id: "zhangdaxi_05", name: "太原南", city: "太原", lat: 37.78, lon: 112.56 }
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
      { id: "lianxulan_09", name: "西安北", city: "西安", lat: 34.38, lon: 108.94 },
      { id: "lianxulan_10", name: "咸阳西", city: "咸阳", lat: 34.33, lon: 108.65 },
      { id: "xiyin_03", name: "庆阳", city: "庆阳", lat: 35.713, lon: 107.677 },
      { id: "xiyin_04", name: "吴忠", city: "吴忠", lat: 37.9875, lon: 106.1919 },
      { id: "baoyin_06", name: "银川", city: "银川", lat: 38.4915, lon: 106.1669 }
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
      { id: "xiwu_01", name: "西安东", city: "西安", lat: 34.249, lon: 109.137 },
      { id: "xiyu_02", name: "安康西", city: "安康", lat: 32.733, lon: 108.9464 },
      { id: "xiyu_03", name: "达州南", city: "达州", lat: 31.102, lon: 107.48 },
      { id: "langyu_05", name: "广安南", city: "广安", lat: 30.47, lon: 106.63 },
      { id: "huyurong_14", name: "重庆北", city: "重庆", lat: 29.61, lon: 106.55 }
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
      { id: "huyurong_15", name: "成都", city: "成都", lat: 30.72, lon: 103.98 },
      { id: "chengdawan_03", name: "遂宁", city: "遂宁", lat: 30.548, lon: 105.57 },
      { id: "langyu_04", name: "南充北", city: "南充", lat: 30.856, lon: 106.071 },
      { id: "xiyu_03", name: "达州南", city: "达州", lat: 31.102, lon: 107.48 },
      { id: "zhengyu_06", name: "万州北", city: "万州", lat: 30.82, lon: 108.39 }
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
      { id: "hukun_18", name: "贵阳北", city: "贵阳", lat: 26.65, lon: 106.63 },
      { id: "yunan_04", name: "都匀东", city: "都匀", lat: 26.26, lon: 107.52 },
      { id: "guigang_03", name: "桂林西", city: "桂林", lat: 25.3575, lon: 110.2625 },
      { id: "guigang_04", name: "贺州", city: "贺州", lat: 24.413, lon: 111.566 },
      { id: "nanguang_03", name: "肇庆东", city: "肇庆", lat: 23.11, lon: 112.61 },
      { id: "nanguang_02", name: "佛山西", city: "佛山", lat: 23.09, lon: 112.9 },
      { id: "jingguang_24", name: "广州南", city: "广州", lat: 22.99, lon: 113.27 }
    ]
  },
  {
    id: "jinxiongxin_high_speed",
    name: "津雄忻高铁",
    shortName: "津雄忻",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "运营线路",
    source: "津雄段天津南—静海北—文安北—雄安；文安北按京九文安站以北约10公里落点；其后接白洋淀／雄忻县级站",
    stations: [
      { id: "jinghu_03", name: "天津南", city: "天津", lat: 39.02, lon: 117.06 },
      { id: "jinxiongxin_jinghaibei", name: "静海北", city: "天津", lat: 38.99, lon: 116.95 },
      { id: "jinxiongxin_wenanbei", name: "文安北", city: "文安", lat: 38.973, lon: 116.3 },
      { id: "jingxiongshang_02", name: "雄安", city: "雄安", lat: 39.001, lon: 116.1 },
      { id: "jinxiongxin_baiyangdian", name: "白洋淀", city: "容城", lat: 39.069, lon: 115.8686 },
      { id: "jingguang_02", name: "保定东", city: "保定", lat: 39.087, lon: 115.57 },
      { id: "jinxiongxin_wangdoubei", name: "望都北", city: "望都", lat: 38.85, lon: 115.15 },
      { id: "jinxiongxin_tangxian", name: "唐县", city: "唐县", lat: 38.748, lon: 114.981 },
      { id: "jinxiongxin_quyang", name: "曲阳", city: "曲阳", lat: 38.622, lon: 114.745 },
      { id: "jinxiongxin_fuping", name: "阜平", city: "阜平", lat: 38.849, lon: 114.195 },
      { id: "jinxiongxin_wutaixian", name: "五台县", city: "五台", lat: 38.728, lon: 113.255 },
      { id: "jinxiongxin_dingxiangbei", name: "定襄北", city: "定襄", lat: 38.54, lon: 112.96 },
      { id: "zhangdaxi_04", name: "忻州西", city: "忻州", lat: 38.42, lon: 112.73 }
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
      { id: "jingguang_03", name: "石家庄", city: "石家庄", lat: 38.0225, lon: 114.484 },
      { id: "jingxiongshang_03", name: "衡水", city: "衡水", lat: 37.738, lon: 115.7 },
      { id: "jinghu_05", name: "德州东", city: "德州", lat: 37.44, lon: 116.36 }
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
      { id: "yuxia_03", name: "张家界西", city: "张家界", lat: 29.13, lon: 110.45 },
      { id: "zhangjihua_02", name: "吉首东", city: "吉首", lat: 28.314, lon: 109.775 },
      { id: "hukun_16", name: "怀化南", city: "怀化", lat: 27.55, lon: 109.96 }
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
      { id: "zhangjihua_02", name: "吉首东", city: "吉首", lat: 28.314, lon: 109.775 },
      { id: "zhangjihua_branch_01", name: "铜仁凤凰", city: "铜仁", lat: 27.87, lon: 109.25 }
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
    parentLineId: "hukun_high_speed",
    networkRole: "branch",
    source: "国家铁路局站点名单；公开地图参考坐标；安顺西、昭通东复用既有站点身份",
    stations: [
      { id: "hukun_19", name: "安顺西", city: "安顺", lat: 26.25, lon: 105.93 },
      { id: "anliu_05", name: "六盘水", city: "六盘水", lat: 26.5941, lon: 104.8501 },
      { id: "yukun_04", name: "昭通东", city: "昭通", lat: 27.321, lon: 103.784 }
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
      { id: "yukun_04", name: "昭通东", city: "昭通", lat: 27.321, lon: 103.784 },
      { id: "chenggui_05", name: "毕节", city: "毕节", lat: 27.3, lon: 105.28 },
      { id: "yunan_02", name: "遵义", city: "遵义", lat: 27.7254, lon: 106.9272 },
      { id: "yuxia_02", name: "黔江", city: "黔江", lat: 29.475, lon: 108.77 }
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
      { id: "lianxulan_09", name: "西安北", city: "西安", lat: 34.38, lon: 108.94 },
      { id: "xiyubao_02", name: "铜川", city: "铜川", lat: 34.898, lon: 108.966 },
      { id: "xiyubao_03", name: "延安", city: "延安", lat: 36.585, lon: 109.49 },
      { id: "xiyubao_04", name: "榆林南", city: "榆林", lat: 38.219, lon: 109.734 },
      { id: "xiyubao_05", name: "鄂尔多斯", city: "鄂尔多斯", lat: 39.608, lon: 109.99 },
      { id: "jingbao_05", name: "包头", city: "包头", lat: 40.6039, lon: 109.8312 }
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
      { id: "qinghaihu_02", name: "青海湖", city: "青海湖", lat: 36.96, lon: 100.9 },
      { id: "qinghaihu_03", name: "共和", city: "共和", lat: 36.284, lon: 100.62 },
      { id: "qingchang_02", name: "玛沁", city: "玛沁", lat: 34.477, lon: 100.239 },
      { id: "qingchang_03", name: "玉树", city: "玉树", lat: 33.004, lon: 96.978 },
      { id: "chuanzang_04", name: "昌都", city: "昌都", lat: 31.14, lon: 97.172 }
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
      { id: "lanxin_09", name: "乌鲁木齐", city: "乌鲁木齐", lat: 43.831, lon: 87.535 },
      { id: "beijiang_04", name: "昌吉", city: "昌吉", lat: 43.9464, lon: 87.1911 },
      { id: "wubo_03", name: "石河子", city: "石河子", lat: 44.2675, lon: 86.0605 },
      { id: "beijiang_01", name: "奎屯", city: "奎屯", lat: 44.426, lon: 84.902 },
      { id: "wubo_04", name: "博乐", city: "博乐", lat: 44.906, lon: 82.066 }
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
      { id: "beijiang_02", name: "克拉玛依", city: "克拉玛依", lat: 45.58, lon: 84.87 },
      { id: "beijiang_tacheng_02", name: "塔城", city: "塔城", lat: 46.748, lon: 82.986 }
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
      { id: "beijiang_01", name: "奎屯", city: "奎屯", lat: 44.426, lon: 84.902 },
      { id: "beijiang_02", name: "克拉玛依", city: "克拉玛依", lat: 45.58, lon: 84.87 },
      { id: "beijiang_03", name: "阿勒泰", city: "阿勒泰", lat: 47.847, lon: 88.133 },
      { id: "beijiang_04", name: "昌吉", city: "昌吉", lat: 43.9464, lon: 87.1911 },
      { id: "lanxin_09", name: "乌鲁木齐", city: "乌鲁木齐", lat: 43.831, lon: 87.535 }
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
      { id: "yiku_01", name: "伊宁", city: "伊宁", lat: 43.977, lon: 81.273 },
      { id: "nanjiang_01", name: "库尔勒", city: "库尔勒", lat: 41.726, lon: 86.174 }
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
      { id: "qingzang_03", name: "格尔木", city: "格尔木", lat: 36.3829, lon: 94.9061 },
      { id: "heruo_03", name: "若羌", city: "若羌", lat: 39.025, lon: 88.168 },
      { id: "nanjiang_01", name: "库尔勒", city: "库尔勒", lat: 41.726, lon: 86.174 }
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
      { id: "xinzang_01", name: "和田", city: "和田", lat: 37.111, lon: 79.922 },
      { id: "heruo_02", name: "且末", city: "且末", lat: 38.145, lon: 85.529 },
      { id: "heruo_03", name: "若羌", city: "若羌", lat: 39.025, lon: 88.168 }
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
      { id: "nanjiang_01", name: "库尔勒", city: "库尔勒", lat: 41.726, lon: 86.174 },
      { id: "nanjiang_02", name: "库车", city: "库车", lat: 41.706, lon: 82.963 },
      { id: "nanjiang_03", name: "阿克苏", city: "阿克苏", lat: 41.124, lon: 80.263 },
      { id: "nanjiang_05", name: "阿图什", city: "阿图什", lat: 39.7197, lon: 76.2164 },
      { id: "nanjiang_04", name: "喀什", city: "喀什", lat: 39.515, lon: 76.063 },
      { id: "nanjiang_06", name: "莎车", city: "莎车县", lat: 38.3742, lon: 77.2297 },
      { id: "nanjiang_07", name: "叶城", city: "叶城县", lat: 37.8932, lon: 77.4708 },
      { id: "xinzang_01", name: "和田", city: "和田", lat: 37.111, lon: 79.922 }
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
      { id: "xinzang_01", name: "和田", city: "和田", lat: 37.111, lon: 79.922 },
      { id: "xinzang_02", name: "阿里", city: "阿里", lat: 32.501, lon: 80.105 },
      { id: "xinzang_03", name: "日喀则", city: "日喀则", lat: 29.267, lon: 88.88 },
      { id: "chuanzang_07", name: "拉萨", city: "拉萨", lat: 29.625, lon: 91.0686 }
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
      { id: "hukun_21", name: "昆明南", city: "昆明", lat: 24.874, lon: 102.862 },
      { id: "chengkun_04", name: "楚雄", city: "楚雄", lat: 25.036, lon: 101.546 },
      { id: "diancang_03", name: "大理", city: "大理", lat: 25.592, lon: 100.2485 },
      { id: "diancang_04", name: "丽江", city: "丽江", lat: 26.8138, lon: 100.2512 },
      { id: "diancang_05", name: "香格里拉", city: "香格里拉", lat: 27.814, lon: 99.6889 },
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
      { id: "qinghaihu_02", name: "青海湖", city: "青海湖", lat: 36.96, lon: 100.9 },
      { id: "qingzang_02", name: "德令哈", city: "德令哈", lat: 37.3148, lon: 97.383 },
      { id: "qingzang_03", name: "格尔木", city: "格尔木", lat: 36.3829, lon: 94.9061 },
      { id: "qingzang_04", name: "那曲", city: "那曲", lat: 31.4454, lon: 91.9896 },
      { id: "chuanzang_07", name: "拉萨", city: "拉萨", lat: 29.625, lon: 91.0686 }
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
      { id: "huyurong_15", name: "成都", city: "成都", lat: 30.72, lon: 103.98 },
      { id: "chuanzang_02", name: "雅安", city: "雅安", lat: 30.031, lon: 103.055 },
      { id: "chuanzang_03", name: "康定", city: "康定", lat: 30.05, lon: 101.965 },
      { id: "chuanzang_04", name: "昌都", city: "昌都", lat: 31.14, lon: 97.172 },
      { id: "chuanzang_05", name: "林芝", city: "林芝", lat: 29.5296, lon: 94.4373 },
      { id: "chuanzang_06", name: "山南", city: "山南", lat: 29.24, lon: 91.77 },
      { id: "chuanzang_07", name: "拉萨", city: "拉萨", lat: 29.625, lon: 91.0686 }
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
      { id: "xicheng_06", name: "成都东", city: "成都", lat: 30.632, lon: 104.141 },
      { id: "chengyu_02", name: "资阳北", city: "资阳", lat: 30.136, lon: 104.616 },
      { id: "chengziyi_03", name: "自贡", city: "自贡", lat: 29.327, lon: 104.835 },
      { id: "yukun_03", name: "宜宾西", city: "宜宾", lat: 28.751, lon: 104.62 }
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
      { id: "chengyu_04", name: "重庆西", city: "重庆", lat: 29.502, lon: 106.438 },
      { id: "yukun_02", name: "泸州", city: "泸州", lat: 28.947, lon: 105.414 },
      { id: "yukun_03", name: "宜宾西", city: "宜宾", lat: 28.751, lon: 104.62 },
      { id: "yukun_04", name: "昭通东", city: "昭通", lat: 27.321, lon: 103.784 },
      { id: "hukun_21", name: "昆明南", city: "昆明", lat: 24.874, lon: 102.862 }
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
      { id: "baoyin_06", name: "银川", city: "银川", lat: 38.4915, lon: 106.1669 },
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
      { id: "xicheng_06", name: "成都东", city: "成都", lat: 30.632, lon: 104.141 },
      { id: "chuanqing_02", name: "马尔康", city: "马尔康", lat: 31.905, lon: 102.228 },
      { id: "chuanqing_03", name: "合作", city: "合作", lat: 34.985, lon: 102.911 },
      { id: "chuanqing_04", name: "同仁", city: "同仁", lat: 35.665, lon: 102.078 },
      { id: "lanxin_02", name: "海东西", city: "海东", lat: 36.5095, lon: 102.0535 }
    ]
  },
  {
    id: "lanhe_conventional",
    name: "川青铁路兰合支线",
    shortName: "川青兰合支线",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速支线预研线路",
    parentLineId: "chuanqing_conventional",
    networkRole: "branch",
    source: "用户提供参考坐标；兰州西、合作复用既有站点身份",
    stations: [
      { id: "lianxulan_14", name: "兰州西", city: "兰州", lat: 36.0675, lon: 103.7492 },
      { id: "lanhe_02", name: "临夏", city: "临夏", lat: 35.601, lon: 103.21 },
      { id: "chuanqing_03", name: "合作", city: "合作", lat: 34.985, lon: 102.911 }
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
      { id: "jingha_09", name: "哈尔滨西", city: "哈尔滨", lat: 45.707, lon: 126.577 },
      { id: "binzhou_02", name: "大庆西", city: "大庆", lat: 46.628, lon: 124.873 },
      { id: "binzhou_03", name: "齐齐哈尔", city: "齐齐哈尔", lat: 47.354, lon: 123.918 },
      { id: "binzhou_04", name: "海拉尔", city: "呼伦贝尔", lat: 49.212, lon: 119.758 }
    ]
  },
  {
    id: "binzhou_linbranch_conventional",
    name: "滨洲铁路林区支线",
    shortName: "滨洲林区支线",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "支线预研线路",
    parentLineId: "binzhou_conventional",
    networkRole: "branch",
    source: "用户提供参考坐标；齐齐哈尔复用滨洲铁路既有站点身份",
    stations: [
      { id: "binzhou_03", name: "齐齐哈尔", city: "齐齐哈尔", lat: 47.354, lon: 123.918 },
      { id: "binzhou_linbranch_02", name: "加格达奇", city: "加格达奇", lat: 50.415, lon: 124.117 }
    ]
  },
  {
    id: "tonghai_conventional",
    name: "通海铁路",
    shortName: "通海",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "普速预研线路",
    source: "用户提供参考坐标；通辽、海拉尔复用既有站点身份",
    stations: [
      { id: "jingha_chifeng_03", name: "通辽", city: "通辽", lat: 43.617, lon: 122.265 },
      { id: "tonghai_02", name: "乌兰浩特", city: "乌兰浩特", lat: 46.072, lon: 122.093 },
      { id: "binzhou_04", name: "海拉尔", city: "呼伦贝尔", lat: 49.212, lon: 119.758 }
    ]
  },
  {
    id: "wuxi_high_speed",
    name: "京包高铁乌锡支线",
    shortName: "京包乌锡支线",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "支线预研线路",
    parentLineId: "jingbao_high_speed",
    networkRole: "branch",
    source: "用户指定线路调整；乌兰察布复用京包高铁既有站点身份",
    stations: [
      { id: "jingbao_03", name: "乌兰察布", city: "乌兰察布", lat: 40.9642, lon: 113.1633 },
      { id: "wuxi_02", name: "锡林浩特", city: "锡林浩特", lat: 43.933, lon: 116.087 }
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
      { id: "zhangdaxi_02", name: "大同南", city: "大同", lat: 40.02, lon: 113.15 }
    ]
  },
  {
    id: "jingtang_intercity_high_speed",
    name: "京唐城际",
    shortName: "京唐",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "运营线路",
    source: "县级／市级挂名站原则；坐标参考维基百科与 OSM；唐山复用津秦既有站点身份",
    stations: [
      { id: "jingtang_01", name: "北京城市副中心", city: "北京", lat: 39.9021, lon: 116.7021 },
      { id: "jingtang_02", name: "燕郊", city: "三河", lat: 39.941, lon: 116.8257 },
      { id: "jingtang_03", name: "大厂", city: "大厂", lat: 39.8886, lon: 116.8976 },
      { id: "jingtang_04", name: "香河", city: "香河", lat: 39.7188, lon: 117.0277 },
      { id: "jingtang_05", name: "宝坻", city: "天津", lat: 39.6605, lon: 117.299 },
      { id: "jingtang_06", name: "玉田南", city: "玉田", lat: 39.6964, lon: 117.8087 },
      { id: "jingtang_07", name: "唐山西", city: "唐山", lat: 39.6953, lon: 118.0171 },
      { id: "jinqinshen_02", name: "唐山", city: "唐山", lat: 39.632, lon: 118.18 }
    ]
  },
  {
    id: "jingjin_intercity_high_speed",
    name: "京津城际",
    shortName: "京津",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "运营线路",
    source: "县级挂名站原则；亦庄按同类中间站补入；坐标参考维基百科与 OSM；北京南、天津复用既有站点身份",
    stations: [
      { id: "jinghu_01", name: "北京南", city: "北京", lat: 39.8636, lon: 116.3728 },
      { id: "jingjin_yizhuang", name: "亦庄", city: "北京", lat: 39.8119, lon: 116.5962 },
      { id: "jingjin_02", name: "武清", city: "天津", lat: 39.371, lon: 117.01 },
      { id: "jinqinshen_01", name: "天津", city: "天津", lat: 39.142, lon: 117.176 }
    ]
  },
  {
    id: "jingxiong_intercity_high_speed",
    name: "京雄城际",
    shortName: "京雄",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "运营线路",
    source: "县级挂名站原则；坐标参考维基百科与 OSM；北京西、雄安复用既有站点身份",
    stations: [
      { id: "jingguang_01", name: "北京西", city: "北京", lat: 39.8936, lon: 116.3157 },
      { id: "jingxiong_02", name: "北京大兴", city: "北京", lat: 39.7194, lon: 116.3225 },
      { id: "jingxiong_03", name: "大兴机场", city: "北京", lat: 39.5139, lon: 116.4099 },
      { id: "jingxiong_04", name: "固安东", city: "固安", lat: 39.3709, lon: 116.399 },
      { id: "jingxiong_05", name: "霸州北", city: "霸州", lat: 39.1853, lon: 116.3205 },
      { id: "jingxiongshang_02", name: "雄安", city: "雄安", lat: 39.001, lon: 116.1 }
    ]
  },
  {
    id: "jinxing_intercity_high_speed",
    name: "津兴城际",
    shortName: "津兴",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "运营线路",
    source: "区县级挂名精简；去掉胜芳；固安东、大兴机场复用京雄城际既有站点身份",
    stations: [
      { id: "jinxing_01", name: "天津西", city: "天津", lat: 39.157, lon: 117.161 },
      { id: "jinxing_02", name: "安次", city: "廊坊", lat: 39.2356, lon: 116.6756 },
      { id: "jinxing_03", name: "永清东", city: "永清", lat: 39.3043, lon: 116.5053 },
      { id: "jingxiong_04", name: "固安东", city: "固安", lat: 39.3709, lon: 116.399 },
      { id: "jingxiong_03", name: "大兴机场", city: "北京", lat: 39.5139, lon: 116.4099 }
    ]
  },
  {
    id: "huaixing_intercity_high_speed",
    name: "怀兴城际",
    shortName: "怀兴",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "运营线路",
    source: "区县级／枢纽精简；亦庄复用京津城际站点身份；怀柔南、副中心、大兴机场复用既有站点身份",
    stations: [
      { id: "jingha_huairounan", name: "怀柔南", city: "北京", lat: 40.2772, lon: 116.6988 },
      { id: "huaixing_capital_airport", name: "首都机场", city: "北京", lat: 40.0515, lon: 116.6098 },
      { id: "jingtang_01", name: "北京城市副中心", city: "北京", lat: 39.9021, lon: 116.7021 },
      { id: "jingjin_yizhuang", name: "亦庄", city: "北京", lat: 39.8119, lon: 116.5962 },
      { id: "huaixing_langfangbei", name: "廊坊北", city: "廊坊", lat: 39.5771, lon: 116.667 },
      { id: "huaixing_langfangxi", name: "廊坊西", city: "廊坊", lat: 39.5476, lon: 116.5674 },
      { id: "jingxiong_03", name: "大兴机场", city: "北京", lat: 39.5139, lon: 116.4099 }
    ]
  },
  {
    id: "pinggu_suburban_conventional",
    name: "平谷市郊线",
    shortName: "平谷市郊",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "运营线路",
    source: "用户指定站序；燕郊复用京唐；三河参考三河县站；平谷参考维基百科平谷站",
    stations: [
      { id: "jingtang_02", name: "燕郊", city: "三河", lat: 39.941, lon: 116.8257 },
      { id: "pinggu_suburban_sanhe", name: "三河", city: "三河", lat: 39.9711, lon: 117.0828 },
      { id: "pinggu_suburban_pinggu", name: "平谷", city: "北京", lat: 40.1544, lon: 117.1112 }
    ]
  },
  {
    id: "jingbin_intercity_high_speed",
    name: "京滨城际",
    shortName: "京滨",
    type: "high_speed",
    typeLabel: "高速",
    region: "china_mainland",
    status: "运营线路",
    source: "用户指定站序；宝坻复用京唐；北辰／天津机场／滨海西坐标参考维基百科",
    stations: [
      { id: "jingtang_05", name: "宝坻", city: "天津", lat: 39.6605, lon: 117.299 },
      { id: "jingbin_beichen", name: "北辰", city: "天津", lat: 39.2709, lon: 117.2704 },
      { id: "jingbin_tianjin_airport", name: "天津机场", city: "天津", lat: 39.1336, lon: 117.3621 },
      { id: "jingbin_binhaixi", name: "滨海西", city: "天津", lat: 39.0801, lon: 117.6051 }
    ]
  },
  {
    id: "beijing_subcenter_suburban_conventional",
    name: "城市副中心市郊线",
    shortName: "副中心市郊",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "运营线路",
    source: "取代原房山市郊线，形成东西大轴；房山东／石景山东沿用既有身份；北京西／北京／副中心复用既有站点身份",
    stations: [
      { id: "fangshan_suburban_01", name: "房山东", city: "北京", lat: 39.7647, lon: 116.1704 },
      { id: "fangshan_suburban_02", name: "石景山东", city: "北京", lat: 39.8945, lon: 116.2146 },
      { id: "jingguang_01", name: "北京西", city: "北京", lat: 39.8936, lon: 116.3157 },
      { id: "jingha_beijing", name: "北京", city: "北京", lat: 39.901, lon: 116.4206 },
      { id: "jingtang_01", name: "北京城市副中心", city: "北京", lat: 39.9021, lon: 116.7021 }
    ]
  },
  {
    id: "jingyuan_conventional",
    name: "京原铁路",
    shortName: "京原",
    type: "conventional",
    typeLabel: "普速",
    region: "china_mainland",
    status: "运营线路",
    source: "用户指定站序；房山东复用副中心市郊既有站点身份；涞源／灵丘／繁峙／代县／原平坐标参考维基百科",
    stations: [
      { id: "fangshan_suburban_01", name: "房山东", city: "北京", lat: 39.7647, lon: 116.1704 },
      { id: "jingyuan_laiyuan", name: "涞源", city: "涞源", lat: 39.3709, lon: 114.706 },
      { id: "jingyuan_lingqiu", name: "灵丘", city: "灵丘", lat: 39.4622, lon: 114.2225 },
      { id: "jingyuan_fanshi", name: "繁峙", city: "繁峙", lat: 39.1647, lon: 113.2671 },
      { id: "jingyuan_daixian", name: "代县", city: "代县", lat: 39.0761, lon: 112.9778 },
      { id: "jingyuan_yuanping", name: "原平", city: "原平", lat: 38.7194, lon: 112.7278 }
    ]
  }
];
