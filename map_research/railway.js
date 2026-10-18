(() => {
  'use strict';
  const { stations, connections } = window.RAILWAY_DATA;
  const $ = id => document.getElementById(id);
  const NS = 'http://www.w3.org/2000/svg';
  const byStation = new Map(stations.map(s => [s.id, s]));
  const edgesByStation = new Map(stations.map(s => [s.id, []]));
  const typeName = type => type === 'conventional' ? '普速' : '高速';
  const divisionMileage = d => `高速约 ${Math.round(d.lengthKm.high_speed).toLocaleString('zh-CN')} 公里 · 普速约 ${Math.round(d.lengthKm.conventional).toLocaleString('zh-CN')} 公里`;
  const edges = connections.map(e => ({ ...e, from: byStation.get(e.from), to: byStation.get(e.to) }));
  const edgeMap = new Map(edges.map(e => [e.id, e]));
  const displayName = e => `${e.from.name} — ${e.to.name}`;
  edges.forEach(e => { edgesByStation.get(e.from.id).push(e); edgesByStation.get(e.to.id).push(e); });
  const divisions = window.resolveRailwayDivisions(window.RAILWAY_DATA,window.RAILWAY_DIVISIONS);
  const byDivision = new Map(divisions.map(d=>[d.id,d]));
  const validDivisions = divisions.filter(d=>!d.errors.length);
  const typesByStation = new Map(stations.map(s => [s.id, new Set(edgesByStation.get(s.id).map(e => e.type))]));
  const divisionSearch = new Map(divisions.map(d => [d.id,
    [d.name, ...[...d.stationIds].map(id => byStation.get(id).name)].join('\n').toLowerCase()
  ]));
  const hubs = new Set(['北京西','上海虹桥','广州南','武汉','成都东','重庆北','郑州东','西安北','昆明南','兰州西','乌鲁木齐','拉萨','哈尔滨','沈阳','长春','满洲里','漠河','海口','福州','南昌西','台北','高雄','香港西九龙','南宁东','杭州东','济南西','太原南','银川','西宁','喀什','抚远','格尔木','齐齐哈尔']);
  const state = { type: 'all', query: '', selected: null, labels: true, scale: 1, x: 0, y: 0, width: 1000, height: 700 };
  const returnView=readReturnView();
  if(returnView) {
    state.type=['all','high_speed','conventional'].includes(returnView.type)?returnView.type:'all';
    state.query=typeof returnView.query==='string'?returnView.query:'';
    state.labels=returnView.labels!==false;
  }

  function readReturnView() {
    if(new URLSearchParams(location.search).get('restore')!=='1') return null;
    try {
      const saved=JSON.parse(sessionStorage.getItem('railwayMapReturnView'));
      sessionStorage.removeItem('railwayMapReturnView');
      if(!saved || !Number.isFinite(saved.scale) || !Number.isFinite(saved.centerX) || !Number.isFinite(saved.centerY)) return null;
      return saved;
    } catch { return null; }
  }

  document.addEventListener('click',event=>{
    const link=event.target.closest('a.economy-link');
    if(!link) return;
    if(link.id==='economyLink') link.href=activeDivision()?`./economy.html?division=${encodeURIComponent(activeDivision().id)}`:'./economy.html';
    try {
      sessionStorage.setItem('railwayMapReturnView',JSON.stringify({
        type:state.type,query:state.query,labels:state.labels,selected:state.selected,
        scale:state.scale,centerX:(state.width/2-state.x)/state.scale,centerY:(state.height/2-state.y)/state.scale,
        listScrollTop:document.getElementById('entryList').scrollTop
      }));
    } catch { /* 存储不可用时仍可正常打开经济页面。 */ }
  });
  const divisionNodes = [];
  let shownStations = new Set();
  let shownEdges = new Set();
  let drag = null;
  let renderFrame = 0;
  const routeNodes = new Map();
  const stationNodes = new Map();
  const svg = $('mapSvg');
  const stage = $('mapStage');
  const viewport = $('viewport');
  const svgNode = (name, attrs = {}) => {
    const node = document.createElementNS(NS, name);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    return node;
  };
  const element = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };
  const project = ({ lat, lon }) => ({ x: lon * 20, y: -Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360)) * 180 / Math.PI * 20 });
  const projected = new Map(stations.map(s => [s.id, project(s)]));
  const typeMatches = c => state.type === 'all' || c.type === state.type;

  function buildMap() {
    for (let lon = 70; lon <= 140; lon += 5) {
      const a = project({ lat: 15, lon }), b = project({ lat: 56, lon });
      $('gridLayer').append(svgNode('line', { x1:a.x,y1:a.y,x2:b.x,y2:b.y,class:'grid-line' }));
    }
    for (let lat = 15; lat <= 55; lat += 5) {
      const a = project({ lat, lon: 70 }), b = project({ lat, lon: 140 });
      $('gridLayer').append(svgNode('line', { x1:a.x,y1:a.y,x2:b.x,y2:b.y,class:'grid-line' }));
    }
    const routes = document.createDocumentFragment(), hits = document.createDocumentFragment();
    for (const edge of edges) {
      const a = projected.get(edge.from.id), b = projected.get(edge.to.id);
      const attrs = { d:`M${a.x},${a.y}L${b.x},${b.y}`, 'data-edge-id':edge.id };
      const path = svgNode('path', { ...attrs, class:`railway-route ${edge.type}` });
      const hit = svgNode('path', { ...attrs, class:'railway-route-hit' });
      const title = svgNode('title'); title.textContent = `${edge.from.name} — ${edge.to.name} · ${typeName(edge.type)}`; hit.append(title);
      routes.append(path); hits.append(hit); routeNodes.set(edge.id, { path, hit });
    }
    $('routeLayer').append(routes); $('hitLayer').append(hits);
    const points = document.createDocumentFragment();
    for (const s of stations) {
      const types = typesByStation.get(s.id);
      const kind = types.size > 1 ? 'shared' : types.has('conventional') ? 'conventional' : 'high_speed';
      const group = svgNode('g', { class:`railway-station ${kind}`, 'data-station-id':s.id });
      const title = svgNode('title'); title.textContent = s.name;
      const hit = svgNode('circle', { r:9, class:'station-hit' });
      const core = svgNode('circle', { r:2.5, class:'station-core' });
      const label = svgNode('text', { x:7, y:3.5, class:'station-label' }); label.textContent = s.name;
      group.append(title, hit, core, label); points.append(group);
      stationNodes.set(s.id, { group, core, label });
    }
    $('stationLayer').append(points);
    for(const d of validDivisions) {
      const segments=d.boundaries.map(b=>({edgeId:b.edgeId,from:projected.get(b.insideId),to:project(b)}));
      for(const segment of segments) {
        const path=svgNode('path',{d:`M${segment.from.x},${segment.from.y}L${segment.to.x},${segment.to.y}`,class:`division-half ${edgeMap.get(segment.edgeId).type}`,'data-division-id':d.id,'data-edge-id':segment.edgeId});
        $('divisionLayer').append(path); divisionNodes.push({path,divisionId:d.id,edgeId:segment.edgeId});
      }
    }
  }

  function updateDivisions() {
    const d=activeDivision();
    for(const node of divisionNodes) node.path.style.display=d?.id===node.divisionId&&shownEdges.has(node.edgeId)?'':'none';
  }
  function activeDivision() { return byDivision.get(state.selected?.kind==='division'?state.selected.id:state.selected?.divisionId); }

  function applyFilters(fit = false) {
    shownStations = new Set(stations.filter(s => state.type === 'all' || typesByStation.get(s.id).has(state.type)).map(s => s.id));
    shownEdges = new Set(edges.filter(e => typeMatches(e) && shownStations.has(e.from.id) && shownStations.has(e.to.id)).map(e => e.id));
    for (const [id, nodes] of routeNodes) { nodes.path.style.display = nodes.hit.style.display = shownEdges.has(id) ? '' : 'none'; }
    for (const [id, node] of stationNodes) node.group.style.display = shownStations.has(id) ? '' : 'none';
    if(state.selected?.kind!=='division') state.selected = null;
    updateSelection();
    $('mapTitle').textContent = `泛中国${state.type === 'all' ? '铁路' : typeName(state.type)}网络`;
    $('mapSummary').textContent = `${shownEdges.size.toLocaleString('zh-CN')} 条连接 / ${shownStations.size.toLocaleString('zh-CN')} 个站点`;
    if (fit) fitPoints([...shownStations]); else scheduleTransform();
  }

  function renderList() {
    const fragment = document.createDocumentFragment();
    const items=divisions.filter(d=>!state.query || divisionSearch.get(d.id).includes(state.query));
    $('entryCount').textContent=`${items.length} 家`;
    $('pageNote').textContent='点击分局内的站点或连接，整体高亮管辖网';
    for(const d of items) {
      const row=element('button','entry-row division-row');row.type='button';row.dataset.divisionId=d.id;row.disabled=!!d.errors.length;
      const main=element('span','entry-main');main.append(element('span','entry-name',d.name));
      main.append(element('span','entry-description',d.errors.length?'边界待检查：'+d.errors.join('；'):`${d.stationIds.size} 个站点`));
      if(!d.errors.length) {
        const mileage=element('span','entry-description',divisionMileage(d));mileage.title='按站点坐标连线估算，跨界连接仅计分局内半段';main.append(mileage);
      }
      row.append(main);fragment.append(row);
    }
    if(!items.length) fragment.append(element('div','empty-list','没有匹配的分局。'));
    $('entryList').replaceChildren(fragment); updateActiveRows();
  }

  function selectionIds() {
    const litStations = new Set(), litEdges = new Set();
    const selected = state.selected;
    const d=activeDivision();
    if (d) {
      d.stationIds.forEach(id=>{if(shownStations.has(id))litStations.add(id);});
      d.edgeIds.forEach(id=>{if(shownEdges.has(id))litEdges.add(id);});
    } else if (selected?.kind === 'station') {
      litStations.add(selected.id);
      edgesByStation.get(selected.id).forEach(e => { if(shownEdges.has(e.id)) { litEdges.add(e.id); litStations.add(e.from.id); litStations.add(e.to.id); } });
    } else if (selected?.kind === 'edge') {
      const e = edgeMap.get(selected.id); litStations.add(e.from.id); litStations.add(e.to.id); litEdges.add(e.id);
    }
    return { litStations, litEdges };
  }

  function updateSelection() {
    const {litStations,litEdges} = selectionIds();
    const selecting = !!state.selected;
    routeNodes.forEach(({path,hit},id) => {
      const lit = litEdges.has(id);
      path.classList.toggle('selected',lit); path.classList.toggle('dimmed',selecting&&!lit);
      if (lit) { $('routeLayer').append(path); $('hitLayer').append(hit); }
    });
    stationNodes.forEach(({group},id) => {
      group.classList.toggle('selected',litStations.has(id));
      group.classList.toggle('dimmed',selecting&&!litStations.has(id));
      if (litStations.has(id)) $('stationLayer').append(group);
    });
    updateDivisions(); updateActiveRows(); renderDetail(); scheduleTransform();
  }

  function updateActiveRows() {
    const divisionId=activeDivision()?.id;
    $('entryList').querySelectorAll('.entry-row').forEach(row => {
      const active = row.dataset.divisionId===divisionId;
      row.classList.toggle('active',!!active); row.setAttribute('aria-pressed',String(!!active));
    });
  }

  function focusDivisionInList(id) {
    if(!byDivision.has(id)) return;
    if(state.query) {
      state.query=''; $('searchInput').value=''; renderList();
    }
    const row=$('entryList').querySelector(`[data-division-id="${id}"]`);
    row?.scrollIntoView({block:'nearest',behavior:'smooth'});
  }

  function focusMapSelectionDivision() {
    const d=activeDivision();
    if(d) focusDivisionInList(d.id);
  }

  function select(kind,id,center=false,divisionOverride=undefined) {
    const owner=validDivisions.find(d=>kind==='station'?d.stationIds.has(id):kind==='edge'&&(d.edgeIds.has(id)||d.boundaries.some(b=>b.edgeId===id)));
    state.selected = {kind,id,divisionId:divisionOverride===undefined?owner?.id:divisionOverride}; updateSelection();
    if (center) {
      if(activeDivision()) {fitDivision(activeDivision());return;}
      if (kind === 'edge') { const e=edgeMap.get(id); fitPoints([e.from.id,e.to.id],true); }
      if (kind === 'station') {
        const p = projected.get(id); state.scale = Math.max(state.scale,4);
        const usable = usableWidth(true); state.x = usable/2-p.x*state.scale; state.y = state.height/2-p.y*state.scale; scheduleTransform();
      }
    }
  }

  function connectionLink(e,stationId) {
    const other=e.from.id===stationId ? e.to : e.from;
    const button = element('button','detail-link',other.name); button.type='button'; button.dataset.edgeId=e.id;
    button.append(element('small','',`${typeName(e.type)} · 查看连接`)); return button;
  }

  function renderDivisionOverview(d) {
    $('divisionTitle').textContent=d.name;
    const stats=element('div','division-stats');
    stats.title='完整分局统计；里程按站点连线估算，交界仅计本局半段。';
    for(const [label,value] of [
      ['管辖站点',`${d.stationIds.size} 个`],
      ['政策票',`${d.policyVotes} 票`],
      ['高速里程',`约 ${Math.round(d.lengthKm.high_speed).toLocaleString('zh-CN')} 公里`],
      ['普速里程',`约 ${Math.round(d.lengthKm.conventional).toLocaleString('zh-CN')} 公里`]
    ]) {
      const metric=element('div','division-stat');
      if(label==='政策票') metric.title='初版固定票权 · 全国共 1000 票';
      metric.append(element('span','',label),element('strong','',value));stats.append(metric);
    }
    $('divisionBody').append(stats);
    const economyLink=element('a','page-link economy-link division-economy-link','查看经济环境 ↗');
    economyLink.href=`./economy.html?division=${encodeURIComponent(d.id)}`;
    $('divisionBody').append(economyLink);
    const ids=d.commercialStationIds;
    if(ids?.length) {
      const label='可开放车站商业';
      const section=element('section','station-commerce');
      section.setAttribute('aria-label',label);
      const heading=element('div','commerce-heading');
      heading.append(element('h3','',label),element('span','',`${ids.length} 座 · 第一版`));
      const list=element('ul','commerce-stations');
      for(const id of ids) list.append(element('li','commerce-station',byStation.get(id).name));
      section.append(heading,list);$('divisionBody').append(section);
    }
    const investmentIds=d.stationCityInvestmentIds;
    if(investmentIds?.length) {
      const section=element('section','station-commerce station-city-investment');
      section.setAttribute('aria-label','可开放站城资产投资');
      const heading=element('div','commerce-heading');
      heading.append(element('h3','','可开放站城资产投资'),element('span','',`${investmentIds.length} 座`));
      const list=element('ul','commerce-stations investment-stations');
      for(const id of investmentIds) list.append(element('li','commerce-station',byStation.get(id).name));
      section.append(heading,list);
      $('divisionBody').append(section);
    }
  }

  function renderDetail() {
    const selected = state.selected;
    const isDivision=selected?.kind==='division';
    $('divisionPanel').hidden = !isDivision;
    $('detailPanel').hidden = !selected || isDivision;
    $('divisionBody').replaceChildren();
    $('detailBody').replaceChildren();
    if (!selected) { $('selectionReadout').textContent='全网视图'; return; }
    if(isDivision) {
      const d=byDivision.get(selected.id);
      renderDivisionOverview(d);
      $('selectionReadout').textContent=d.name;
      return;
    }
    const body = $('detailBody');
    if (selected.kind === 'station') {
      const s = byStation.get(selected.id);
      $('detailKind').textContent='站点详情 / STATION'; $('detailTitle').textContent=s.name;
      $('detailMeta').textContent=`${s.city || '铁路站点'} · ${s.lat.toFixed(5)}°N, ${s.lon.toFixed(5)}°E`;
      body.append(element('p','detail-subtitle','所属分局 · 查看概览'));
      for(const d of validDivisions.filter(d=>d.stationIds.has(s.id))) body.append(divisionLink(d));
      body.append(element('p','detail-subtitle','直接相连的站点'));
      const adjacent=edgesByStation.get(s.id).filter(e=>shownEdges.has(e.id));
      adjacent.forEach(e=>body.append(connectionLink(e,s.id)));
      if(!adjacent.length) body.append(element('p','detail-meta','当前筛选下没有连接'));
    } else {
      const e=edgeMap.get(selected.id);
      $('detailKind').textContent='连接详情 / CONNECTION';
      $('detailTitle').textContent=displayName(e);
      $('detailMeta').textContent=`${typeName(e.type)} · 2 个端点 · 直接连接`;
      body.append(element('p','detail-subtitle','所属分局 · 查看概览'));
      for(const d of validDivisions) {
        if(d.edgeIds.has(e.id)) body.append(divisionLink(d));
        const b=d.boundaries.find(b=>b.edgeId===e.id);
        if(b) { body.append(divisionLink(d));body.append(element('p','division-note',`${byStation.get(b.insideId).name}至交界中点归该分局。`)); }
      }
      body.append(element('p','detail-subtitle','连接端点'));
      for(const s of [e.from,e.to]) {
        const button=element('button','detail-link',s.name); button.type='button'; button.dataset.stationId=s.id;
        button.append(element('small','',`${s.lat.toFixed(5)}°N, ${s.lon.toFixed(5)}°E`)); body.append(button);
      }
    }
    $('selectionReadout').textContent=$('detailTitle').textContent;
  }

  function usableWidth(detail=false) { return detail && state.width>620 ? state.width-340 : state.width; }
  function divisionLink(d) {
    const button=element('button','detail-link division-link',d.name);button.type='button';button.dataset.divisionId=d.id;return button;
  }
  function fitDivision(d) { fitCoordinates([...d.stationIds].filter(id=>shownStations.has(id)).map(id=>projected.get(id)).concat(d.boundaries.filter(b=>shownEdges.has(b.edgeId)).map(project)),true); }
  function fitPoints(ids,detail=false) { fitCoordinates(ids.map(id=>projected.get(id)),detail); }
  function fitCoordinates(points,detail=false) {
    if (!points.length) return;
    const xs=points.map(p=>p.x), ys=points.map(p=>p.y);
    const left=Math.min(...xs),right=Math.max(...xs),top=Math.min(...ys),bottom=Math.max(...ys);
    const width=usableWidth(detail);
    state.scale=Math.min(16,Math.max(.15,Math.min(Math.max(100,width-110)/Math.max(20,right-left),Math.max(100,state.height-170)/Math.max(20,bottom-top))));
    state.x=width/2-(left+right)/2*state.scale; state.y=(state.height+20)/2-(top+bottom)/2*state.scale;
    scheduleTransform();
  }
  function scheduleTransform() { cancelAnimationFrame(renderFrame); renderFrame=requestAnimationFrame(updateTransform); }
  function updateTransform() {
    viewport.setAttribute('transform',`translate(${state.x} ${state.y}) scale(${state.scale})`);
    const {litStations}=selectionIds();
    const selectedStation=state.selected?.kind==='station' ? state.selected.id : null;
    const candidates=[];
    for (const [id,node] of stationNodes) {
      if(!shownStations.has(id)) continue;
      const p=projected.get(id),sx=p.x*state.scale+state.x,sy=p.y*state.scale+state.y;
      const onscreen=sx>-30&&sx<state.width+30&&sy>-30&&sy<state.height+30;
      node.group.style.display=onscreen?'':'none';
      if(!onscreen) continue;
      node.group.setAttribute('transform',`translate(${p.x} ${p.y}) scale(${1/state.scale})`);
      node.core.setAttribute('r',(state.scale<1.2?1.65:2.5)+(litStations.has(id)?.3:0));
      node.label.style.display='none';
      const s=byStation.get(id),lit=litStations.has(id),hub=hubs.has(s.name);
      if(state.labels && (lit || hub || state.scale>2.2) && (!state.selected||lit)) candidates.push({node,sx,sy,name:s.name,priority:id===selectedStation?0:lit?1:hub?2:3});
    }
    candidates.sort((a,b)=>a.priority-b.priority);
    const cells=new Map();
    for(const c of candidates) {
      const box={x:c.sx+6,y:c.sy-6,w:c.name.length*10+6,h:14};
      if(box.x<0||box.x+box.w>state.width||box.y<0||box.y+box.h>state.height) continue;
      const keys=[]; for(let x=Math.floor(box.x/70);x<=Math.floor((box.x+box.w)/70);x++) for(let y=Math.floor(box.y/20);y<=Math.floor((box.y+box.h)/20);y++) keys.push(`${x}:${y}`);
      const overlaps=keys.some(key=>(cells.get(key)||[]).some(b=>box.x<b.x+b.w&&box.x+box.w>b.x&&box.y<b.y+b.h&&box.y+box.h>b.y));
      if(overlaps && c.priority!==0) continue;
      c.node.label.style.display=''; keys.forEach(key=>{if(!cells.has(key))cells.set(key,[]);cells.get(key).push(box);});
    }
    $('zoomReadout').value=`${Math.round(state.scale*100)}%`;
  }
  function zoomAt(scale,x=state.width/2,y=state.height/2) {
    const old=state.scale; state.scale=Math.max(.15,Math.min(40,scale));
    state.x=x-(x-state.x)/old*state.scale; state.y=y-(y-state.y)/old*state.scale; scheduleTransform();
  }
  function resetView() {
    const hadQuery=!!state.query;
    state.type='all'; state.query=''; state.selected=null;
    $('searchInput').value='';
    document.querySelectorAll('[data-type]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.type==='all')));
    applyFilters(true);
    if(hadQuery) renderList();
  }

  $('searchInput').addEventListener('input',()=>{state.query=$('searchInput').value.trim().toLowerCase();renderList();});
  document.querySelectorAll('[data-type]').forEach(button=>button.addEventListener('click',()=>{
    state.type=button.dataset.type;
    document.querySelectorAll('[data-type]').forEach(b=>b.setAttribute('aria-pressed',String(b===button))); applyFilters();
  }));
  function handleItemClick(event) {
    const division=event.target.closest('[data-division-id]');
    if(division){select('division',division.dataset.divisionId,true);return;}
    const edge=event.target.closest('[data-edge-id]'),station=event.target.closest('[data-station-id]');
    if(edge) select('edge',edge.dataset.edgeId,true);
    else if(station) select('station',station.dataset.stationId,true);
  }
  $('entryList').addEventListener('click',handleItemClick); $('detailBody').addEventListener('click',handleItemClick);
  $('closeDivision').addEventListener('click',()=>{state.selected=null;updateSelection();});
  $('closeDetail').addEventListener('click',()=>{state.selected=null;updateSelection();});
  $('fitButton').addEventListener('click',()=>activeDivision()?fitDivision(activeDivision()):fitPoints([...shownStations]));
  $('resetButton').addEventListener('click',resetView);
  $('zoomInButton').addEventListener('click',()=>zoomAt(state.scale*1.35));
  $('zoomOutButton').addEventListener('click',()=>zoomAt(state.scale/1.35));
  $('labelButton').addEventListener('click',()=>{state.labels=!state.labels;$('labelButton').setAttribute('aria-pressed',String(state.labels));scheduleTransform();});
  stage.addEventListener('wheel',event=>{
    event.preventDefault(); const rect=svg.getBoundingClientRect();zoomAt(state.scale*Math.exp(-event.deltaY*.0012),event.clientX-rect.left,event.clientY-rect.top);
  },{passive:false});
  stage.addEventListener('pointerdown',event=>{
    if(event.button!==0||event.target.closest('.map-controls'))return;
    stage.focus({preventScroll:true}); drag={id:event.pointerId,x:event.clientX,y:event.clientY,startX:event.clientX,startY:event.clientY,moved:false,target:event.target};stage.setPointerCapture(event.pointerId);
  });
  stage.addEventListener('pointermove',event=>{
    if(!drag||event.pointerId!==drag.id)return;
    if(Math.hypot(event.clientX-drag.startX,event.clientY-drag.startY)>4)drag.moved=true;
    if(drag.moved){stage.classList.add('dragging');state.x+=event.clientX-drag.x;state.y+=event.clientY-drag.y;scheduleTransform();}
    drag.x=event.clientX;drag.y=event.clientY;
  });
  function endDrag(event) {
    if(!drag||event.pointerId!==drag.id)return;
    const previous=drag;drag=null;stage.classList.remove('dragging');
    if(stage.hasPointerCapture(event.pointerId))stage.releasePointerCapture(event.pointerId);
    if(event.type==='pointercancel'||previous.moved)return;
    const division=previous.target.closest('[data-division-id]'),station=previous.target.closest('[data-station-id]'),edge=previous.target.closest('[data-edge-id]');
    if(division){select('division',division.dataset.divisionId);focusDivisionInList(division.dataset.divisionId);}
    else if(station){select('station',station.dataset.stationId);focusMapSelectionDivision();}
    else if(edge) {
      const id=edge.dataset.edgeId,e=edgeMap.get(id),a=projected.get(e.from.id),b=projected.get(e.to.id),rect=svg.getBoundingClientRect();
      const x=(event.clientX-rect.left-state.x)/state.scale,y=(event.clientY-rect.top-state.y)/state.scale;
      const t=((x-a.x)*(b.x-a.x)+(y-a.y)*(b.y-a.y))/((b.x-a.x)**2+(b.y-a.y)**2);
      const owner=validDivisions.find(d=>d.edgeIds.has(id)||d.boundaries.some(c=>c.edgeId===id&&(c.insideId===e.from.id?t<=.5:t>=.5)));
      select('edge',id,false,owner?.id||null);
      focusMapSelectionDivision();
    } else{state.selected=null;updateSelection();}
  }
  stage.addEventListener('pointerup',endDrag);stage.addEventListener('pointercancel',endDrag);
  stage.addEventListener('keydown',event=>{
    if(event.target!==stage)return;
    const moves={w:[0,50],ArrowUp:[0,50],s:[0,-50],ArrowDown:[0,-50],a:[50,0],ArrowLeft:[50,0],d:[-50,0],ArrowRight:[-50,0]};
    const move=moves[event.key];
    if(move){event.preventDefault();state.x+=move[0];state.y+=move[1];scheduleTransform();}
    else if(['+','=','-'].includes(event.key)){event.preventDefault();zoomAt(state.scale*(event.key==='-'?1/1.3:1.3));}
    else if(event.key==='Escape'){state.selected=null;updateSelection();}
  });
  let initialized=false;
  new ResizeObserver(()=>{
    const rect=stage.getBoundingClientRect(); if(!rect.width||!rect.height)return;
    const previousWidth=state.width,previousHeight=state.height;
    state.width=rect.width;state.height=rect.height;svg.setAttribute('viewBox',`0 0 ${state.width} ${state.height}`);
    if(!initialized){
      initialized=true;
      if(returnView) {
        state.scale=Math.max(.15,Math.min(40,returnView.scale));
        state.x=state.width/2-returnView.centerX*state.scale;state.y=state.height/2-returnView.centerY*state.scale;scheduleTransform();
      } else fitPoints([...shownStations]);
    }
    else {state.x+=(state.width-previousWidth)/2;state.y+=(state.height-previousHeight)/2;scheduleTransform();}
  }).observe(stage);
  $('totalConnections').textContent=edges.length.toLocaleString('zh-CN');
  $('totalStations').textContent=stations.length.toLocaleString('zh-CN');
  $('searchInput').value=state.query;
  document.querySelectorAll('[data-type]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.type===state.type)));
  $('labelButton').setAttribute('aria-pressed',String(state.labels));
  buildMap(); renderList(); applyFilters();
  const savedSelection=returnView?.selected;
  if(savedSelection && (savedSelection.kind==='division'?byDivision.has(savedSelection.id):savedSelection.kind==='station'?byStation.has(savedSelection.id):savedSelection.kind==='edge'&&edgeMap.has(savedSelection.id))) {
    state.selected=savedSelection;updateSelection();
  }
  if(returnView) $('entryList').scrollTop=Number(returnView.listScrollTop)||0;
})();
