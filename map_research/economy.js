(() => {
  'use strict';
  let data=window.RAILWAY_ECONOMY;
  const $=id=>document.getElementById(id);
  const params=new URLSearchParams(location.search);
  const regionByDivision=new Map(data.regions.flatMap(r=>r.divisions.map(id=>[id,r.id])));
  const division=window.RAILWAY_DIVISIONS.find(d=>d.id===params.get('division'));
  let rows=data.values.map(values=>Object.fromEntries(data.columns.map((key,i)=>[key,values[i]])));
  let loading=false;
  const forecasts=new Map();
  let forecastPanelOpen=false,forecastDraftKey=null;
  const metrics=[['energy_real_index','电力实际价格指数'],['wage_real_index','实际工资指数'],['materials_real_index','材料实际价格指数'],['passenger_demand_index','客运需求指数'],['freight_demand_index','货运需求指数']];
  const colors=['#83c6dc','#dda979','#b8a0d1','#93d2c6','#d4c37f','#92b0df','#d398ad','#a7bd94'];
  const ns='http://www.w3.org/2000/svg';
  const make=(name,attrs={},text)=>{const node=document.createElementNS(ns,name);for(const [key,value] of Object.entries(attrs))node.setAttribute(key,value);if(text!==undefined)node.textContent=text;return node;};
  for(const region of data.regions) {const option=document.createElement('option');option.value=region.id;option.textContent=region.name;$('economyRegion').append(option);}
  const initialRegion=params.get('region')||regionByDivision.get(division?.id)||'all';
  $('economyRegion').value=data.regions.some(r=>r.id===initialRegion)?initialRegion:'all';
  const initialYear=Number(params.get('year'));
  if(params.has('year')&&Number.isInteger(initialYear)&&initialYear>=2025&&initialYear<=2085)$('economyYear').value=initialYear;
  if(metrics.some(([id])=>id===params.get('metric')))$('economyMetric').value=params.get('metric');

  function forecastKey() {return `${$('economyRegion').value}|${$('economyMetric').value}`;}
  function currentForecast() {return forecasts.get(forecastKey());}
  function updateForecastLimit() {
    const max=data.baseYear+rows.length-1-Number($('forecastHorizon').value);
    $('forecastStart').min=data.baseYear;$('forecastStart').max=max;
    if(Number($('forecastStart').value)>max)$('forecastStart').value=max;
    updateForecastHint();
  }
  function updateForecastHint() {
    const score=Number($('forecastScore').value),horizon=Number($('forecastHorizon').value);
    $('forecastErrorHint').textContent=$('forecastScore').value!==''&&Number.isFinite(score)&&score>=0&&score<=100
      ?score===100?'100 分：每个预测年份与实际值完全一致。':`期望 ${score} 分 · ${horizon} 年预测：目标平均年度偏差约 ${window.RAILWAY_FORECAST.errorForScore(score,horizon).toFixed(2)}%，本次生成会有浮动。`
      :'';
  }
  function updateForecastControls(year,metric,regions) {
    const single=regions.length===1,forecast=single?currentForecast():null;
    $('openForecast').hidden=!single;$('clearForecast').hidden=!forecast;
    $('openForecast').textContent=forecast?'预测设置':'开始预测';
    $('openForecast').setAttribute('aria-expanded',String(single&&forecastPanelOpen));
    $('forecastForm').hidden=!single||!forecastPanelOpen;
    $('forecastContext').textContent=single?`${regions[0].name} · ${metrics.find(([id])=>id===metric)[1]}`:'';
    $('forecastSummary').textContent=forecast?`${forecast.startYear}—${forecast.startYear+forecast.horizon} · 期望 ${forecast.expectedScore} 分${year<forecast.startYear?' · 尚未到预测起点':''}`:'';
    const reviewed=forecast&&year>=forecast.startYear+forecast.horizon;
    $('forecastReview').hidden=!reviewed;
    if(reviewed)$('forecastReview').textContent=`本次预测实际得分 ${forecast.actualScore.toFixed(1)} 分 · 平均年度偏差 ${forecast.meanErrorPct.toFixed(2)}%。按 ${forecast.horizon} 年期误差尺度折算，不计已知起点。`;
    if(single&&forecastDraftKey!==forecastKey()) {
      forecastDraftKey=forecastKey();$('forecastStart').value=year;$('forecastStatus').textContent='';
    }
    updateForecastLimit();
  }

  function addChartInspection(chart,series,metric,x,y,plot) {
    const tooltip=$('chartTooltip'),last=plot.last;
    tooltip.hidden=true;
    const marker=make('g',{'pointer-events':'none','aria-hidden':'true',visibility:'hidden'});
    const guide=make('line',{y1:plot.top,y2:plot.bottom,stroke:'#8ba6ac','stroke-width':1,'stroke-dasharray':'3 4'});
    const inspectedSeries=series.map(item=>({...item,values:new Map(item.points.map(point=>[point.t,point.value]))}));
    const dots=series.map(item=>make('circle',{r:4,fill:item.color,stroke:'#10191e','stroke-width':1.5}));
    marker.append(guide,...dots);
    const target=make('rect',{x:plot.left,y:plot.top,width:plot.right-plot.left,height:plot.bottom-plot.top,fill:'transparent',tabindex:0,role:'slider',class:'chart-inspection-target','aria-label':'图表查看年份','aria-valuemin':data.baseYear,'aria-valuemax':data.baseYear+last,'aria-valuenow':data.baseYear+plot.current});
    let inspected=plot.current;
    function show(t) {
      inspected=Math.max(0,Math.min(last,t));
      const year=data.baseYear+inspected,px=x(inspected);
      guide.setAttribute('x1',px);guide.setAttribute('x2',px);
      const title=document.createElement('strong'),label=document.createElement('span');
      title.textContent=`${year} 年`;label.textContent=metrics.find(([id])=>id===metric)[1];
      const content=[title,label],readout=[];
      inspectedSeries.forEach((item,i)=>{
        const value=item.values.get(inspected);
        dots[i].setAttribute('visibility',value===undefined?'hidden':'visible');
        if(value===undefined)return;
        dots[i].setAttribute('cx',px);dots[i].setAttribute('cy',y(value));
        const entry=document.createElement('div'),swatch=document.createElement('i'),number=document.createElement('b');
        entry.className='chart-tooltip-row';swatch.style.background=item.color;number.textContent=value.toFixed(2);
        entry.append(swatch,document.createTextNode(item.name),number);content.push(entry);readout.push(`${item.name} ${value.toFixed(2)}`);
      });
      tooltip.replaceChildren(...content);tooltip.hidden=false;marker.setAttribute('visibility','visible');
      target.setAttribute('aria-valuenow',year);target.setAttribute('aria-valuetext',`${year} 年，${label.textContent}，${readout.join('，')}`);
      const box=chart.getBoundingClientRect(),anchor=px/plot.width*box.width;
      const preferred=anchor+12+tooltip.offsetWidth<=box.width?anchor+12:anchor-tooltip.offsetWidth-12;
      tooltip.style.left=`${Math.max(4,Math.min(box.width-tooltip.offsetWidth-4,preferred))}px`;
      tooltip.style.top=`${plot.top/plot.height*box.height}px`;
    }
    function hide() {tooltip.hidden=true;marker.setAttribute('visibility','hidden');}
    function inspectPointer(event) {
      const box=chart.getBoundingClientRect(),px=(event.clientX-box.left)/box.width*plot.width;
      const t=last===0?0:Math.max(0,Math.min(last,Math.round((px-plot.left)/(plot.right-plot.left)*last)));
      if(t!==inspected||tooltip.hidden)show(t);
    }
    target.addEventListener('pointermove',inspectPointer);
    target.addEventListener('pointerdown',inspectPointer);
    target.addEventListener('pointerleave',hide);
    target.addEventListener('focus',()=>show(inspected));
    target.addEventListener('blur',hide);
    target.addEventListener('keydown',event=>{
      const next={ArrowLeft:inspected-1,ArrowRight:inspected+1,Home:0,End:last}[event.key];
      if(next!==undefined){event.preventDefault();show(next);}
      else if(event.key==='Escape')hide();
    });
    chart.append(marker,target);
  }

  function draw() {
    const year=Number($('economyYear').value),index=year-data.baseYear;
    const metric=$('economyMetric').value,regionId=$('economyRegion').value;
    $('bureauLink').href=`./bureau.html?region=${regionId==='all'?'northeast':encodeURIComponent(regionId)}&seed=${data.seed}&year=${year}${division?`&bureau=${encodeURIComponent(division.id)}`:''}`;
    $('wageNote').hidden=metric!=='wage_real_index';
    const regions=data.regions.filter(r=>regionId==='all'||r.id===regionId);
    const history=rows.slice(0,index+1),current=rows[index];
    updateForecastControls(year,metric,regions);
    const savedForecast=regions.length===1?currentForecast():null;
    const forecast=savedForecast&&year>=savedForecast.startYear?savedForecast:null;
    const lastIndex=Math.max(index,forecast?forecast.startYear+forecast.horizon-data.baseYear:index);
    const series=regions.map(region=>({name:`${region.name}${forecast?' · 实际':''}`,color:colors[data.regions.indexOf(region)],points:history.map(row=>({t:row.year_index,value:row[`${region.id}__${metric}`]}))}));
    if(forecast)series.push({name:'预测中位数',color:'#e1bc83',forecast:true,points:forecast.points});
    const national=data.national[index];
    $('yearLabel').textContent=year;$('previousYear').disabled=index===0;$('nextYear').disabled=index===rows.length-1;
    $('divisionContext').textContent=division?`${division.name} · 所属经济区：${data.regions.find(r=>r.id===regionByDivision.get(division.id)).name}`:'八个经济区 · 年度价格与运输需求';
    $('chartTitle').textContent=metrics.find(([id])=>id===metric)[1];$('chartPeriod').textContent=`2025—${data.baseYear+lastIndex}${forecast?' · 含预测':''}`;
    $('snapshotTitle').textContent=`${year} 年经济区指标`;
    $('realRate').textContent=`${national.rate.toFixed(2)}%`;$('rateYear').textContent=`${year} 年 · 全国共同基准`;
    $('industryPe').textContent=`${national.pe.toFixed(2)} 倍`;$('valuationIndex').textContent=national.valuation.toFixed(2);
    const scenario=data.scenario;
    $('scenarioBadge').textContent='研究情景 V0.5 · 合成数据';
    $('scenarioProfile').textContent=scenario?.name||'基准情景';
    $('scenarioDescription').textContent=scenario?.description||'请重新生成情景以加载情景类型。';
    const phase=data.phases?.[index]?.name||'—';
    $('scenarioPhase').textContent=`${year} · ${phase}`;
    $('scenarioPhase').dataset.tone=/危机|压力|放缓/.test(phase)?'stress':'normal';
    $('scenarioPeriod').textContent=scenario?`约 ${scenario.cyclePeriodYears.toFixed(1)} 年`:'—';
    $('scenarioGrowth').textContent=scenario?`${scenario.growthMultiplier.toFixed(2)} × 基准`:'—';
    $('scenarioPersistence').textContent=scenario?scenario.cyclePersistence.toFixed(3):'—';
    const values=series.flatMap(item=>item.points.map(point=>point.value));
    const min=Math.min(100,...values),max=Math.max(100,...values),pad=Math.max(3,(max-min)*.12);
    const chart=$('economyChart'),width=Math.max(320,Math.round(chart.getBoundingClientRect().width)),height=Math.min(420,Math.max(260,Math.round(width*.44)));
    chart.setAttribute('viewBox',`0 0 ${width} ${height}`);
    const lo=min-pad,hi=max+pad,left=width<500?48:66,right=width-14,top=25,bottom=height-50;
    const x=t=>left+(right-left)*t/Math.max(1,lastIndex),y=v=>bottom-(v-lo)/(hi-lo)*(bottom-top);
    const fragment=document.createDocumentFragment();
    if(forecast&&lastIndex>index)fragment.append(make('rect',{x:x(index),y:top,width:right-x(index),height:bottom-top,fill:'#e1bc83','fill-opacity':.045}));
    for(let i=0;i<=4;i++) {const value=lo+(hi-lo)*i/4,py=y(value);fragment.append(make('line',{x1:left,x2:right,y1:py,y2:py,stroke:'#283a42'}),make('text',{x:left-12,y:py+4,fill:'#81979e','font-size':12,'text-anchor':'end'},value.toFixed(1)));}
    fragment.append(make('line',{x1:left,x2:right,y1:y(100),y2:y(100),stroke:'#55716c','stroke-dasharray':'4 6'}));
    const ticks=lastIndex===0?[0]:Array.from(new Set([0,Math.round(lastIndex/4),Math.round(lastIndex/2),Math.round(lastIndex*3/4),lastIndex]));
    for(const t of ticks) fragment.append(make('text',{x:x(t),y:height-19,fill:'#81979e','font-size':12,'text-anchor':'middle'},2025+t));
    const legend=document.createDocumentFragment();
    if(forecast) {
      const start=x(forecast.startYear-data.baseYear);
      fragment.append(make('line',{x1:start,x2:start,y1:top,y2:bottom,stroke:'#b59d77','stroke-dasharray':'3 5'}),make('text',{x:Math.min(start+5,right-60),y:top-9,fill:'#cbbd9c','font-size':10},'预测起点'));
    }
    for(const item of series) {
      const line=make('polyline',{points:item.points.map(point=>`${x(point.t)},${y(point.value)}`).join(' '),fill:'none',stroke:item.color,'stroke-width':2.3,'stroke-linejoin':'round',...(item.forecast?{'stroke-dasharray':'6 5'}:{})});
      fragment.append(line);
      item.points.forEach(point=>fragment.append(make('circle',{cx:x(point.t),cy:y(point.value),r:point.t===index?3:1.8,fill:item.color,'fill-opacity':point.t===index?1:.65,'aria-hidden':'true'})));
      const entry=document.createElement('span'),swatch=document.createElement('i');
      if(item.forecast)swatch.className='forecast-swatch';else swatch.style.background=item.color;
      entry.append(swatch,document.createTextNode(item.name));legend.append(entry);
    }
    chart.replaceChildren(fragment);chart.setAttribute('aria-label',`${$('chartTitle').textContent}，实际数据 2025 至 ${year} 年，${regions.map(r=>r.name).join('、')}${forecast?`，预测 ${forecast.startYear} 至 ${forecast.startYear+forecast.horizon} 年`:''}`);
    addChartInspection(chart,series,metric,x,y,{left,right,top,bottom,width,height,last:lastIndex,current:index});
    $('chartLegend').replaceChildren(legend);
    const table=document.createDocumentFragment();
    for(const region of regions) {
      const tr=document.createElement('tr'),name=document.createElement('th');name.scope='row';name.textContent=region.name;tr.append(name);
      const development=document.createElement('td');development.className='region-development';development.textContent=data.regionalPhases?.[index]?.regions[region.id]||'—';tr.append(development);
      for(const [id] of metrics) {const td=document.createElement('td');td.textContent=current[`${region.id}__${id}`].toFixed(2);tr.append(td);}table.append(tr);
    }
    $('economyTable').replaceChildren(table);
    $('scenarioReadout').textContent=`独立铁路情景 V0.5 · 种子 ${data.seed} · ${scenario?.name||'基准情景'} · 2025 年不变价口径`;
    const url=new URL(location.href);url.searchParams.set('region',regionId);url.searchParams.set('year',year);url.searchParams.set('metric',metric);url.searchParams.set('seed',String(data.seed));historyReplace(url);
  }
  async function generateScenario(seed) {
    if(loading) return;
    if(seed===data.seed && data.scenario && data.modelVersion==='railway-real-macro-v0.5.0') {
      $('scenarioSeed').value=String(seed);$('seedStatus').classList.remove('error');$('seedStatus').textContent=`当前种子：${seed} · 与现有情景一致`;return;
    }
    loading=true;
    for(const id of ['scenarioSeed','generateSeed','randomSeed']) $(id).disabled=true;
    document.querySelectorAll('[data-scenario-seed]').forEach(button=>button.disabled=true);
    $('seedStatus').classList.remove('error');$('seedStatus').textContent=`正在生成种子 ${seed} 的经济情景…`;
    const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),20000);
    try {
      const response=await fetch(`./api/economy?seed=${seed}`,{cache:'no-store',signal:controller.signal});
      if(!response.ok) throw new Error('情景生成服务不可用');
      const next=await response.json();
      if(next.seed!==seed || next.modelVersion!=='railway-real-macro-v0.5.0' || !next.scenario || next.phases?.length!==61 || next.values?.length!==61 || next.national?.length!==61 || !Array.isArray(next.columns) || next.regionalPhases?.length!==61 || !next.regionalPhases.every(phase=>data.regions.every(region=>typeof phase.regions?.[region.id]==='string'))) throw new Error('情景数据不完整');
      const nextRows=next.values.map(values=>Object.fromEntries(next.columns.map((key,i)=>[key,values[i]])));
      if(nextRows.some(row=>!Number.isFinite(row.northeast__passenger_demand_index))) throw new Error('情景数据格式不正确');
      data={...data,...next};rows=nextRows;forecasts.clear();forecastPanelOpen=false;
      $('scenarioSeed').value=String(seed);$('seedStatus').textContent=`当前种子：${seed} · 已生成`;
      draw();
    } catch {
      $('seedStatus').classList.add('error');
      $('seedStatus').textContent=`生成失败，当前仍显示种子 ${data.seed}。请使用 py map_research/serve.py 启动本地服务后重试。`;
    } finally {
      clearTimeout(timeout);loading=false;
      for(const id of ['scenarioSeed','generateSeed','randomSeed']) $(id).disabled=false;
      document.querySelectorAll('[data-scenario-seed]').forEach(button=>button.disabled=false);
    }
  }
  function readSeed() {
    const value=$('scenarioSeed').value.trim();
    const seed=/^\d{1,16}$/.test(value)?Number(value):NaN;
    if(!Number.isSafeInteger(seed)||seed<0) {
      $('seedStatus').classList.add('error');$('seedStatus').textContent='请输入 0—9,007,199,254,740,991 之间的整数。';return null;
    }
    return seed;
  }
  $('seedForm').addEventListener('submit',event=>{event.preventDefault();const seed=readSeed();if(seed!==null)generateScenario(seed);});
  $('randomSeed').addEventListener('click',()=>{
    const bits=crypto.getRandomValues(new Uint32Array(2));
    let seed=(bits[0]&0x1fffff)*4294967296+bits[1];
    if(seed===data.seed)seed=seed===Number.MAX_SAFE_INTEGER?0:seed+1;
    $('scenarioSeed').value=String(seed);generateScenario(seed);
  });
  $('scenarioExamples').addEventListener('click',event=>{
    const button=event.target.closest('[data-scenario-seed]');if(!button||loading)return;
    const seed=Number(button.dataset.scenarioSeed);$('scenarioSeed').value=String(seed);generateScenario(seed);
  });
  function historyReplace(url) { window.history.replaceState(null,'',url); }
  $('openForecast').addEventListener('click',()=>{
    if(loading)return;
    forecastPanelOpen=!forecastPanelOpen;
    if(forecastPanelOpen){$('forecastStart').value=Number($('economyYear').value);updateForecastLimit();$('forecastStatus').textContent='';}
    draw();
  });
  $('closeForecast').addEventListener('click',()=>{forecastPanelOpen=false;draw();});
  $('clearForecast').addEventListener('click',()=>{forecasts.delete(forecastKey());$('forecastStatus').textContent='';draw();});
  $('forecastHorizon').addEventListener('change',updateForecastLimit);
  $('forecastScore').addEventListener('input',updateForecastHint);
  $('forecastForm').addEventListener('submit',event=>{
    event.preventDefault();if(loading||$('economyRegion').value==='all')return;
    const startYear=Number($('forecastStart').value),horizon=Number($('forecastHorizon').value),expectedScore=Number($('forecastScore').value);
    const start=startYear-data.baseYear,metric=$('economyMetric').value,regionId=$('economyRegion').value,key=`${regionId}__${metric}`;
    try {
      if(!Number.isInteger(start)||start<0||start+horizon>=rows.length)throw new Error('起始年份与预测年限超出样本范围');
      const result=window.RAILWAY_FORECAST.generate({history:rows.slice(0,start+1).map(row=>row[key]),future:rows.slice(start+1,start+horizon+1).map(row=>row[key]),expectedScore});
      forecasts.set(forecastKey(),{...result,startYear,horizon,points:[{t:start,value:rows[start][key]},...result.values.map((value,i)=>({t:start+i+1,value}))]});
      $('economyYear').value=startYear;forecastPanelOpen=false;
      $('forecastStatus').textContent='';draw();
    } catch(error) {$('forecastStatus').textContent=error.message;$('forecastStatus').classList.add('forecast-status-error');}
  });
  $('economyRegion').addEventListener('change',draw);$('economyMetric').addEventListener('change',draw);$('economyYear').addEventListener('input',draw);
  $('previousYear').addEventListener('click',()=>{$('economyYear').value=Number($('economyYear').value)-1;draw();});
  $('nextYear').addEventListener('click',()=>{$('economyYear').value=Number($('economyYear').value)+1;draw();});
  let previousWidth=0;
  new ResizeObserver(entries=>{const width=Math.round(entries[0].contentRect.width);if(width!==previousWidth){previousWidth=width;draw();}}).observe(document.querySelector('.chart-wrap'));
  draw();
  const requestedSeed=params.get('seed');
  if(requestedSeed!==null) {
    $('scenarioSeed').value=requestedSeed;
    const seed=readSeed();if(seed!==null && seed!==data.seed)generateScenario(seed);
  }
})();
