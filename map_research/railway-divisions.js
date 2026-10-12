// 分局按连接边界划分，归属随站点连接网络计算；不切断实际铁路。
window.RAILWAY_DIVISIONS = [
  {
    id: 'jiamusi', name: '佳木斯铁路分局公司', seedStationId: 'hamujia_06',
    boundaryEdgeIds: [
      'high_speed:hamujia_03|hamujia_04',
      'high_speed:ha_jm_demoli|ha_jm_fangzheng',
      'conventional:ha_yc_tieli|suihua_jiamusi_taoshan'
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
    if(!stations.has(def.seedStationId)) errors.push('中心站不存在');
    for(const id of blocked) if(!edges.has(id)) errors.push(`交界连接不存在：${id}`);
    const stationIds = new Set(), queue=[];
    if(!errors.length) { stationIds.add(def.seedStationId); queue.push(def.seedStationId); }
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
