// 分局按连接边界划分，归属随站点连接网络计算；不切断实际铁路。
window.RAILWAY_DIVISIONS = [
  {
    id: 'jiamusi', name: '佳木斯铁路分局公司', seedStationId: 'hamujia_06',
    boundaryEdgeIds: [
      'high_speed:hamujia_03|hamujia_04',
      'high_speed:ha_jm_demoli|ha_jm_fangzheng',
      'conventional:ha_yc_tieli|suihua_jiamusi_taoshan'
    ]
  },
  {
    id: 'mudanjiang', name: '牡丹江铁路分局公司', seedStationId: 'hamujia_02',
    boundaryEdgeIds: [
      'high_speed:hamu_hengdaohezi_dong|hamu_yabulixi',
      'high_speed:hamujia_03|hamujia_04',
      'conventional:mudanjiang_tumen_dongjingcheng|mudanjiang_tumen_ludao'
    ]
  },
  {
    id: 'qiqihar', name: '齐齐哈尔铁路分局公司', seedStationId: 'binzhou_03',
    boundaryEdgeIds: [
      'high_speed:haqi_anda|haqi_daqingdong',
      'conventional:siping_qiqihar_tailai|siping_qiqihar_zhenlai',
      'conventional:tongliao_daqing_daanbei|tongliao_daqing_xinzhao',
      'conventional:harbin_heihe_beian|qiqi_beian_kedong'
    ]
  },
  {
    id: 'harbin', name: '哈尔滨铁路分局公司', seedStationId: 'harbin',
    boundaryEdgeIds: [
      'high_speed:hada_fuyubei|hada_shuangchengbei',
      'high_speed:haqi_anda|haqi_daqingdong',
      'high_speed:hamu_hengdaohezi_dong|hamu_yabulixi',
      'high_speed:ha_jm_demoli|ha_jm_fangzheng',
      'conventional:ha_yc_tieli|suihua_jiamusi_taoshan',
      'conventional:harbin_heihe_beian|qiqi_beian_kedong'
    ]
  },
  {
    id: 'meihekou', name: '梅河口铁路分局公司', seedStationId: 'shenyangjilin_meihekou',
    boundaryEdgeIds: [
      'conventional:changtongbai_02|siping_meihekou_shiling',
      'conventional:shenyangjilin_caoshi|shenyangjilin_shanchengzhen',
      'conventional:shenyangjilin_chaoyangzhen|shenyangjilin_panshi',
      'high_speed:shenbai_tonghua|shenbai_xinbin',
      'high_speed:shenbai_changbaishan|shenbai_changbaishanxi'
    ]
  },
  {
    id: 'changchun', name: '长春铁路分局公司', seedStationId: 'changchun',
    boundaryEdgeIds: [
      'high_speed:hada_fuyubei|hada_shuangchengbei',
      'high_speed:hada_gongzhulingnan|jingha_07',
      'conventional:shenyangjilin_chaoyangzhen|shenyangjilin_panshi',
      'high_speed:shenbai_changbaishan|shenbai_changbaishanxi',
      'conventional:siping_qiqihar_tailai|siping_qiqihar_zhenlai',
      'conventional:tongliao_daqing_daanbei|tongliao_daqing_xinzhao',
      'conventional:tongliao_daqing_baolongshan|tongliao_daqing_taipingchuan',
      'conventional:siping_qiqihar_baokang|siping_qiqihar_maolin'
    ]
  },
  {
    id: 'siping', name: '四平铁路分局公司', seedStationIds: ['siping', 'jingha_07'],
    boundaryEdgeIds: [
      'high_speed:hada_gongzhulingnan|jingha_07',
      'high_speed:hada_changtuxi|jingha_07',
      'conventional:changtongbai_02|siping_meihekou_shiling',
      'conventional:siping_qiqihar_baokang|siping_qiqihar_maolin',
      'conventional:dahushan_ouli|dahushan_shuangliao'
    ]
  },
  {
    id: 'tongliao', name: '通辽铁路分局公司', seedStationId: 'jingha_chifeng_03',
    boundaryEdgeIds: [
      'conventional:tongliao_daqing_baolongshan|tongliao_daqing_taipingchuan',
      'conventional:dahushan_ouli|dahushan_shuangliao',
      'conventional:jingha_ganqika|jingha_zhangwu',
      'high_speed:jingha_ganqika|jingha_zhanggutai',
      'conventional:daban|kailu',
      'conventional:jingtong_aohan|jingtong_naiman'
    ]
  },
  {
    id: 'shenyang', name: '沈阳铁路分局公司', seedStationId: 'jingha_shenyang',
    boundaryEdgeIds: [
      'high_speed:hada_changtuxi|jingha_07',
      'conventional:shenyangjilin_caoshi|shenyangjilin_shanchengzhen',
      'high_speed:shenbai_tonghua|shenbai_xinbin',
      'high_speed:jingha_ganqika|jingha_zhanggutai',
      'conventional:jingha_ganqika|jingha_zhangwu',
      'high_speed:jingha_heishanbei|jingha_xinminbei',
      'high_speed:jingha_panjinbei|jingha_taian',
      'conventional:jingha_zhangwu|jinzhou_xinlitun_xinlitun',
      'high_speed:hada_haichengxi|shenda_branch_02',
      'high_speed:hada_haichengxi|shenda_04',
      'high_speed:danda_01|danda_dandongxi'
    ]
  }
];

window.resolveRailwayDivisions = function(data, definitions) {
  const distanceKm = (a,b) => {
    const radians=Math.PI/180;
    const h=Math.sin((b.lat-a.lat)*radians/2)**2+Math.cos(a.lat*radians)*Math.cos(b.lat*radians)*Math.sin((b.lon-a.lon)*radians/2)**2;
    return 6371.0088*2*Math.asin(Math.sqrt(Math.min(1,Math.max(0,h))));
  };
  const stations = new Map(data.stations.map(s=>[s.id,s]));
  const edges = new Map(data.connections.map(e=>[e.id,e]));
  const adjacent = new Map(data.stations.map(s=>[s.id,[]]));
  data.connections.forEach(e=>{ adjacent.get(e.from).push(e); adjacent.get(e.to).push(e); });
  const results = definitions.map(def=>{
    const blocked = new Set(def.boundaryEdgeIds), errors=[];
    const seedStationIds = def.seedStationIds || [def.seedStationId];
    if(!seedStationIds.length || seedStationIds.some(id=>!stations.has(id))) errors.push('中心站不存在');
    for(const id of blocked) if(!edges.has(id)) errors.push(`交界连接不存在：${id}`);
    const stationIds = new Set(), queue=[];
    if(!errors.length) { for(const id of seedStationIds) { stationIds.add(id); queue.push(id); } }
    for(const id of queue) for(const e of adjacent.get(id)) {
      if(blocked.has(e.id)) continue;
      const next=e.from===id?e.to:e.from;
      if(!stationIds.has(next)) { stationIds.add(next); queue.push(next); }
    }
    const boundaries=[];
    for(const id of blocked) {
      const e=edges.get(id); if(!e) continue;
      if(stationIds.has(e.from)===stationIds.has(e.to)) { errors.push('交界未能隔开内外两侧，请检查绕行连接'); continue; }
      const from=stations.get(e.from),to=stations.get(e.to);
      boundaries.push({edgeId:id,insideId:stationIds.has(e.from)?e.from:e.to,outsideId:stationIds.has(e.from)?e.to:e.from,
        lat:(from.lat+to.lat)/2,lon:(from.lon+to.lon)/2});
    }
    const edgeIds=new Set(data.connections.filter(e=>!blocked.has(e.id)&&stationIds.has(e.from)&&stationIds.has(e.to)).map(e=>e.id));
    const lengthKm={high_speed:0,conventional:0};
    for(const id of edgeIds) {
      const e=edges.get(id);lengthKm[e.type]+=distanceKm(stations.get(e.from),stations.get(e.to));
    }
    for(const b of boundaries) lengthKm[edges.get(b.edgeId).type]+=distanceKm(stations.get(b.insideId),b);
    return {...def,stationIds,edgeIds,boundaries,lengthKm,errors};
  });
  // 后续划分多家分局时，不允许重复归属悄悄覆盖。
  for(let i=0;i<results.length;i++) for(let j=i+1;j<results.length;j++) {
    if([...results[i].stationIds].some(id=>results[j].stationIds.has(id))) {
      results[i].errors.push(`与${results[j].name}的站点归属重叠`);
      results[j].errors.push(`与${results[i].name}的站点归属重叠`);
    }
  }
  return results;
};
