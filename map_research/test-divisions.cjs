const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const context={window:{}};
for(const file of ['railway-data.js','railway-divisions.js']) vm.runInNewContext(fs.readFileSync(path.join(__dirname,file),'utf8'),context);
const {RAILWAY_DATA:data,RAILWAY_DIVISIONS:defs,resolveRailwayDivisions:resolve}=context.window;
const before=JSON.stringify(data);
const connectionIds=new Set(data.connections.map(e=>e.id));
assert(connectionIds.has('high_speed:jingguang_05|liaohanchang_handannan'),'邯郸东—邯郸南 high-speed connection exists');
assert(connectionIds.has('conventional:houma_houma|zhangdaxi_houmaxi'),'侯马—侯马西 conventional connection exists');
assert(connectionIds.has('conventional:jingbao_03|jiningnan'),'乌兰察布—集宁南 conventional connection exists');
assert(connectionIds.has('conventional:baoyin_02|linha_linhe'),'巴彦淖尔—临河 conventional connection exists');
assert(connectionIds.has('conventional:baozhong_zhongwei|yinlan_03'),'中卫—中卫南 conventional connection exists');
assert(connectionIds.has('high_speed:lianxulan_09|xiping_xian'),'西安北—西安站 high_speed connection exists');
assert(connectionIds.has('high_speed:xiwu_01|xiping_xian'),'西安站—西安东 high_speed connection exists');
assert(connectionIds.has('conventional:baoji_baoji|lianxulan_11'),'宝鸡—宝鸡南 conventional connection exists');
assert(connectionIds.has('conventional:lianxulan_12|tianping_tianshui'),'天水南—天水 conventional connection exists');
const chongqingStation=data.stations.find(s=>s.id==='chongqing_caiyuanba');
assert(chongqingStation,'重庆站（菜园坝） must be registered');
assert.equal(chongqingStation.name,'重庆站');
assert.equal(chongqingStation.lat,29.54881);
assert.equal(chongqingStation.lon,106.54588);
for(const id of [
  'high_speed:chengyu_04|huyurong_14',
  'high_speed:chengyu_04|chongqing_caiyuanba',
  'high_speed:chongqing_caiyuanba|yuxia_01'
]) assert(connectionIds.has(id),`Chongqing station connection exists: ${id}`);
for(const id of [
  'conventional:yiwan_wanzhou|zhengyu_06',
  'conventional:yiwan_yichangdong|huyurong_11',
  'conventional:qiangui_guiyang|hukun_18',
  'conventional:nankun_railway_03|panxing_xingyinan',
  'conventional:chengkun_kunming|hukun_21',
  'conventional:liuwu_wuzhou|nanguang_05',
  'conventional:jingguang_22|ganshao_shaoguandong'
]) assert(connectionIds.has(id),`Conventional city connection exists: ${id}`);
for(const id of [
  'high_speed:chengyi_yibin|yukun_03',
  'high_speed:liuhe_liuzhoudong|nanheng_04',
  'high_speed:hengliu_guilin|nanheng_guilinbei',
  'high_speed:guigang_03|nanheng_guilinbei'
]) assert(connectionIds.has(id),`High-speed city connection exists: ${id}`);
for(const id of [
  'high_speed:langfang|jinxing_01',
  'high_speed:jinxing_01|tianjinnan',
  'high_speed:jinxing_01|tianjin'
]) assert(connectionIds.has(id),`Tianjin connection exists: ${id}`);
assert(!connectionIds.has('high_speed:langfang|tianjinnan'),'京沪高铁连接经过天津西');
assert(defs.find(def=>def.id==='beijing').boundaryEdgeIds.includes('high_speed:jingtang_04|jingtang_05'));
assert(defs.find(def=>def.id==='tangshan').boundaryEdgeIds.includes('high_speed:jingtang_04|jingtang_05'));
assert(!defs.find(def=>def.id==='tangshan').boundaryEdgeIds.includes('high_speed:jingtang_05|jingtang_06'));
const [d,m]=resolve(data,defs);
assert.equal(d.errors.length,0);
assert.equal(d.stationIds.size,33);
assert.equal(d.edgeIds.size,32);
assert.equal(d.boundaries.length,3);
const byName=name=>data.stations.find(s=>s.name===name).id;
for(const name of ['佳木斯','鹤岗','同江北','抚远','七台河西','得莫利','桃山']) assert(d.stationIds.has(byName(name)),name);
for(const name of ['鸡西西','方正','铁力','哈尔滨','牡丹江']) assert(!d.stationIds.has(byName(name)),name);
const exits=data.connections.filter(e=>d.stationIds.has(e.from)!==d.stationIds.has(e.to));
assert.deepEqual(new Set(exits.map(e=>e.id)),new Set(defs[0].boundaryEdgeIds));
for(const b of d.boundaries) { assert(d.stationIds.has(b.insideId)); assert(!d.stationIds.has(b.outsideId)); assert(!d.edgeIds.has(b.edgeId)); }
assert(Math.abs(d.boundaries[0].lat-45.525585)<1e-9);
assert(Math.abs(d.boundaries[0].lon-130.794315)<1e-9);
assert.equal(m.errors.length,0,`Mudanjiang division: ${m.errors.join('; ')}`);
assert.equal(m.stationIds.size,18);
assert.equal(m.edgeIds.size,17);
assert.equal(m.boundaries.length,3);
for(const name of ['牡丹江','横道河子东','鸡西西','东京城','绥芬河']) assert(m.stationIds.has(byName(name)),name);
for(const name of ['亚布力西','七台河西','鹿道','佳木斯','哈尔滨']) assert(!m.stationIds.has(byName(name)),name);
const mudExits=data.connections.filter(e=>m.stationIds.has(e.from)!==m.stationIds.has(e.to));
assert.deepEqual(new Set(mudExits.map(e=>e.id)),new Set(defs[1].boundaryEdgeIds));
for(const b of m.boundaries) { assert(m.stationIds.has(b.insideId)); assert(!m.stationIds.has(b.outsideId)); assert(!m.edgeIds.has(b.edgeId)); }
assert.equal([...d.stationIds].filter(id=>m.stationIds.has(id)).length,0,'the two divisions must not overlap');
assert(Math.abs(m.boundaries[0].lat-44.848645)<1e-9);
assert(Math.abs(m.boundaries[0].lon-128.839625)<1e-9);
const zhangjiakouDef=defs.find(def=>def.id==='zhangjiakou');
assert(zhangjiakouDef,'Zhangjiakou division must be configured');
const zhangjiakou=resolve(data,[zhangjiakouDef])[0];
assert.equal(zhangjiakou.errors.length,0,`Zhangjiakou division: ${zhangjiakou.errors.join('; ')}`);
assert.equal(zhangjiakou.stationIds.size,22);
assert.equal(zhangjiakou.edgeIds.size,20);
assert.equal(zhangjiakou.boundaries.length,7);
assert.deepEqual(new Set(zhangjiakouDef.seedStationIds),new Set([byName('张家口'),byName('张家口南')]));
const expectedZhangjiakouSides=new Map([
  ['high_speed:jingbao_badaling|jingbao_donghuayuanbei',['东花园北','八达岭长城']],
  ['conventional:zhangtang_chicheng|zhangtang_fengning',['赤城','丰宁']],
  ['high_speed:jingbao_huaian|zhanghu_xinghebei',['怀安','兴和北']],
  ['high_speed:jingbao_huaian|zhangdaxi_tianzhen',['怀安','天镇']],
  ['high_speed:dabao_laiyuan|shizhang_xiheying',['西合营','涞源']],
  ['conventional:huade|zhengxiangbaiqi',['正镶白旗','化德']],
  ['conventional:jingpeng|sanggendalai',['桑根达来','经棚']]
]);
for(const b of zhangjiakou.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedZhangjiakouSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedZhangjiakouSides.get(b.edgeId)[1]);
}
const chifengDef=defs.find(def=>def.id==='chifeng');
const [chifeng]=resolve(data,[chifengDef]);
assert.equal(chifeng.errors.length,0,`Chifeng division: ${chifeng.errors.join('; ')}`);
assert.equal(chifeng.stationIds.size,27);
assert.equal(chifeng.edgeIds.size,25);
const chifengSangganBoundary=chifeng.boundaries.find(b=>b.edgeId==='conventional:jingpeng|sanggendalai');
assert.equal(data.stations.find(s=>s.id===chifengSangganBoundary.insideId).name,'经棚');
assert.equal(data.stations.find(s=>s.id===chifengSangganBoundary.outsideId).name,'桑根达来');
const beijingDef=defs.find(def=>def.id==='beijing');
assert(beijingDef,'Beijing division must be configured');
const [beijing]=resolve(data,[beijingDef]);
assert.equal(beijing.errors.length,0,`Beijing division: ${beijing.errors.join('; ')}`);
assert.equal(beijing.stationIds.size,48);
assert.equal(beijing.edgeIds.size,45);
assert.equal(beijing.boundaries.length,13);
assert.deepEqual(new Set(beijingDef.seedStationIds),new Set(['北京西','北京北','北京通州'].map(byName)));
const expectedBeijingSides=new Map([
  ['high_speed:jingbao_badaling|jingbao_donghuayuanbei',['八达岭长城','东花园北']],
  ['conventional:zhangtang_chicheng|zhangtang_fengning',['丰宁','赤城']],
  ['high_speed:jingha_niuheliang|jingha_pingquanbei',['平泉北','牛河梁']],
  ['conventional:jinzhou_chengde_pingquan|jinzhou_chengde_sanshijia',['平泉','三十家']],
  ['conventional:jingtong_chaoyangdi|jingtong_siheyong',['四合永','朝阳地']],
  ['conventional:zhangtang_fengrunxi|zhangtang_tuanpiaozhuang',['团瓢庄','丰润西']],
  ['high_speed:jingjin_yizhuang|wuqing',['亦庄','武清']],
  ['high_speed:langfang|jinxing_01',['廊坊','天津西']],
  ['high_speed:jingtang_04|jingtang_05',['香河','宝坻']],
  ['high_speed:jinxing_02|jinxing_shengfang',['安次','胜芳']],
  ['high_speed:jingxiong_04|jingxiong_05',['固安东','霸州北']],
  ['high_speed:jingxiongshang_02|jingxiongshang_shuangxin',['双辛','雄安']],
  ['high_speed:jingguang_02|jingguang_gaobeidiandong',['高碑店东','保定东']]
]);
for(const b of beijing.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedBeijingSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedBeijingSides.get(b.edgeId)[1]);
}
const resolvedDivisions=resolve(data,defs);
const resolvedBeijing=resolvedDivisions.find(div=>div.id==='beijing');
assert.equal(resolvedBeijing.errors.length,0,`Beijing overlap check: ${resolvedBeijing.errors.join('; ')}`);
for(const other of resolvedDivisions.filter(div=>div.id!=='beijing')) {
  assert.equal([...beijing.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Beijing overlaps ${other.name}`);
}
const tangshanDef=defs.find(def=>def.id==='tangshan');
assert(tangshanDef,'Tangshan division must be configured');
const [tangshan]=resolve(data,[tangshanDef]);
assert.equal(tangshan.errors.length,0,`Tangshan division: ${tangshan.errors.join('; ')}`);
assert.equal(tangshan.stationIds.size,13);
assert.equal(tangshan.edgeIds.size,12);
assert.equal(tangshan.boundaries.length,4);
const expectedTangshanSides=new Map([
  ['high_speed:jingtang_04|jingtang_05',['宝坻','香河']],
  ['high_speed:jingbin_binhaibei|jinqinshen_02',['唐山','滨海北']],
  ['conventional:zhangtang_fengrunxi|zhangtang_tuanpiaozhuang',['丰润西','团瓢庄']],
  ['high_speed:qinshen_dongdaihe|qinshen_shanhaiguan',['山海关','东戴河']]
]);
for(const b of tangshan.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedTangshanSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedTangshanSides.get(b.edgeId)[1]);
}
const resolvedTangshan=resolve(data,defs).find(div=>div.id==='tangshan');
assert.equal(resolvedTangshan.errors.length,0,`Tangshan overlap check: ${resolvedTangshan.errors.join('; ')}`);
assert(tangshan.stationIds.has(byName('宝坻')),'Tangshan includes BaoDi up to the Xianghe-Baodi boundary');
assert(!tangshan.stationIds.has(byName('香河')),'Xianghe remains on the Beijing side');
for(const other of resolve(data,defs).filter(div=>div.id!=='tangshan')) {
  assert.equal([...tangshan.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Tangshan overlaps ${other.name}`);
}
const tianjinDef=defs.find(def=>def.id==='tianjin');
assert(tianjinDef,'Tianjin division must be configured');
assert.deepEqual(new Set(tianjinDef.boundaryEdgeIds),new Set([
  'high_speed:jingjin_yizhuang|wuqing',
  'high_speed:langfang|jinxing_01',
  'high_speed:jinxing_02|jinxing_shengfang',
  'high_speed:jingbin_binhaibei|jinqinshen_02',
  'high_speed:tuanpobei|wenanbei',
  'high_speed:hengcang_fuchengnan|shihuang_jiaohe',
  'high_speed:jinghu_04|jinghu_05',
  'high_speed:jinwei_haixingxi|jinwei_wudi'
]));
const [tianjin]=resolve(data,[tianjinDef]);
assert.equal(tianjin.errors.length,0,`Tianjin division: ${tianjin.errors.join('; ')}`);
assert.equal(tianjin.stationIds.size,23);
assert.equal(tianjin.edgeIds.size,23);
assert.equal(tianjin.boundaries.length,8);
const expectedTianjinSides=new Map([
  ['high_speed:jingjin_yizhuang|wuqing',['武清','亦庄']],
  ['high_speed:langfang|jinxing_01',['天津西','廊坊']],
  ['high_speed:jinxing_02|jinxing_shengfang',['胜芳','安次']],
  ['high_speed:jingbin_binhaibei|jinqinshen_02',['滨海北','唐山']],
  ['high_speed:tuanpobei|wenanbei',['团泊北','文安北']],
  ['high_speed:hengcang_fuchengnan|shihuang_jiaohe',['交河','阜城南']],
  ['high_speed:jinghu_04|jinghu_05',['沧州西','德州东']],
  ['high_speed:jinwei_haixingxi|jinwei_wudi',['海兴西','无棣']]
]);
for(const b of tianjin.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedTianjinSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedTianjinSides.get(b.edgeId)[1]);
}
const resolvedTianjin=resolve(data,defs).find(div=>div.id==='tianjin');
assert.equal(resolvedTianjin.errors.length,0,`Tianjin overlap check: ${resolvedTianjin.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='tianjin')) {
  assert.equal([...tianjin.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Tianjin overlaps ${other.name}`);
}
const xionganDef=defs.find(def=>def.id==='xiongan');
assert(xionganDef,'Xiong’an division must be configured');
const [xiongan]=resolve(data,[xionganDef]);
assert.equal(xiongan.errors.length,0,`Xiong’an division: ${xiongan.errors.join('; ')}`);
assert.equal(xiongan.stationIds.size,17);
assert.equal(xiongan.edgeIds.size,17);
assert.equal(xiongan.boundaries.length,11);
const expectedXionganSides=new Map([
  ['high_speed:jingxiong_04|jingxiong_05',['霸州北','固安东']],
  ['high_speed:jingxiongshang_02|jingxiongshang_shuangxin',['雄安','双辛']],
  ['high_speed:jingguang_02|jingguang_gaobeidiandong',['保定东','高碑店东']],
  ['high_speed:tuanpobei|wenanbei',['文安北','团泊北']],
  ['high_speed:jingguang_dingzhoudong|jingguang_zhengdingairport',['定州东','正定机场']],
  ['high_speed:shibao_anguodong|shibao_wuji',['安国东','无极']],
  ['high_speed:jinxiongxin_quyang|shizhang_xingtang',['曲阳','行唐']],
  ['high_speed:jingxiongshang_shenzhoudong|jingxiongshang_suninghejian',['肃宁河间','深州东']],
  ['high_speed:dabao_laiyuan|shizhang_xiheying',['涞源','西合营']],
  ['high_speed:dabao_laiyuan|dabao_lingqiu',['涞源','灵丘']],
  ['high_speed:jinxiongxin_fuping|jinxiongxin_wutaishan',['阜平','五台山']]
]);
for(const b of xiongan.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedXionganSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedXionganSides.get(b.edgeId)[1]);
}
const resolvedXiongan=resolve(data,defs).find(div=>div.id==='xiongan');
assert.equal(resolvedXiongan.errors.length,0,`Xiong’an overlap check: ${resolvedXiongan.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='xiongan')) {
  assert.equal([...xiongan.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Xiong’an overlaps ${other.name}`);
}
const shijiazhuangDef=defs.find(def=>def.id==='shijiazhuang');
assert(shijiazhuangDef,'Shijiazhuang division must be configured');
const [shijiazhuang]=resolve(data,[shijiazhuangDef]);
assert.equal(shijiazhuang.errors.length,0,`Shijiazhuang division: ${shijiazhuang.errors.join('; ')}`);
assert.equal(shijiazhuang.stationIds.size,29);
assert.equal(shijiazhuang.edgeIds.size,28);
assert.equal(shijiazhuang.boundaries.length,11);
const expectedShijiazhuangSides=new Map([
  ['high_speed:jingguang_dingzhoudong|jingguang_zhengdingairport',['正定机场','定州东']],
  ['high_speed:shibao_anguodong|shibao_wuji',['无极','安国东']],
  ['high_speed:jinxiongxin_quyang|shizhang_xingtang',['行唐','曲阳']],
  ['high_speed:jingxiongshang_shenzhoudong|jingxiongshang_suninghejian',['深州东','肃宁河间']],
  ['high_speed:hengcang_fuchengnan|shihuang_jiaohe',['阜城南','交河']],
  ['high_speed:shita_02|shita_jingxingbei',['井陉北','阳泉北']],
  ['high_speed:jinghu_05|shiji_jingzhou',['景州','德州东']],
  ['high_speed:jingxiongshang_linqingdong|jingxiongshang_qinghexi',['清河西','临清东']],
  ['high_speed:jingguang_05|jingguang_06',['邯郸东','安阳东']],
  ['high_speed:liaohanchang_lichengnan|liaohanchang_shexiannan',['涉县南','黎城南']],
  ['high_speed:liaohanchang_guantaonan|liaohanchang_guanxiannan',['馆陶南','冠县南']]
]);
for(const b of shijiazhuang.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedShijiazhuangSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedShijiazhuangSides.get(b.edgeId)[1]);
}
const resolvedShijiazhuang=resolve(data,defs).find(div=>div.id==='shijiazhuang');
assert.equal(resolvedShijiazhuang.errors.length,0,`Shijiazhuang overlap check: ${resolvedShijiazhuang.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='shijiazhuang')) {
  assert.equal([...shijiazhuang.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Shijiazhuang overlaps ${other.name}`);
}
const datongDef=defs.find(def=>def.id==='datong');
assert(datongDef,'Datong division must be configured');
assert.equal(data.stations.find(s=>s.id===datongDef.seedStationId).name,'大同南');
const [datong]=resolve(data,[datongDef]);
assert.equal(datong.errors.length,0,`Datong division: ${datong.errors.join('; ')}`);
assert.equal(datong.stationIds.size,12);
assert.equal(datong.edgeIds.size,11);
assert.equal(datong.boundaries.length,5);
const expectedDatongSides=new Map([
  ['high_speed:jingbao_huaian|zhangdaxi_tianzhen',['天镇','怀安']],
  ['high_speed:dabao_laiyuan|dabao_lingqiu',['灵丘','涞源']],
  ['high_speed:zhangdaxi_03|zhangdaxi_yanmenguan',['朔州东','雁门关']],
  ['high_speed:jida_fengzhenbei|jingbao_03',['丰镇北','乌兰察布']],
  ['high_speed:hushuo_helingeer|hushuo_youyu',['右玉','和林格尔']]
]);
for(const b of datong.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedDatongSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedDatongSides.get(b.edgeId)[1]);
}
const resolvedDatong=resolve(data,defs).find(div=>div.id==='datong');
assert.equal(resolvedDatong.errors.length,0,`Datong overlap check: ${resolvedDatong.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='datong')) {
  assert.equal([...datong.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Datong overlaps ${other.name}`);
}
const taiyuanDef=defs.find(def=>def.id==='taiyuan');
assert(taiyuanDef,'Taiyuan division must be configured');
assert.equal(data.stations.find(s=>s.id===taiyuanDef.seedStationId).name,'太原南');
const [taiyuan]=resolve(data,[taiyuanDef]);
assert.equal(taiyuan.errors.length,0,`Taiyuan division: ${taiyuan.errors.join('; ')}`);
assert.equal(taiyuan.stationIds.size,23);
assert.equal(taiyuan.edgeIds.size,22);
assert.equal(taiyuan.boundaries.length,6);
const expectedTaiyuanSides=new Map([
  ['high_speed:zhangdaxi_03|zhangdaxi_yanmenguan',['雁门关','朔州东']],
  ['high_speed:jinxiongxin_fuping|jinxiongxin_wutaishan',['五台山','阜平']],
  ['high_speed:shita_02|shita_jingxingbei',['阳泉北','井陉北']],
  ['high_speed:zhengtai_wuxiang|zhengtai_yushexi',['榆社西','武乡']],
  ['high_speed:zhangdaxi_huozhoudong|zhangdaxi_lingshidong',['灵石东','霍州东']],
  ['high_speed:taisui_liulinxi|yanyu_suidexi',['柳林西','绥德西']]
]);
for(const b of taiyuan.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedTaiyuanSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedTaiyuanSides.get(b.edgeId)[1]);
}
const resolvedTaiyuan=resolve(data,defs).find(div=>div.id==='taiyuan');
assert.equal(resolvedTaiyuan.errors.length,0,`Taiyuan overlap check: ${resolvedTaiyuan.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='taiyuan')) {
  assert.equal([...taiyuan.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Taiyuan overlaps ${other.name}`);
}
const changzhiDef=defs.find(def=>def.id==='changzhi');
assert(changzhiDef,'Changzhi division must be configured');
assert.equal(changzhiDef.seedStationIds.map(id=>data.stations.find(s=>s.id===id).name).join('、'),'长治东、沁水');
const [changzhi]=resolve(data,[changzhiDef]);
assert.equal(changzhi.errors.length,0,`Changzhi division: ${changzhi.errors.join('; ')}`);
assert.equal(changzhi.stationIds.size,11);
assert.equal(changzhi.edgeIds.size,9);
assert.equal(changzhi.boundaries.length,6);
const expectedChangzhiSides=new Map([
  ['high_speed:zhengtai_wuxiang|zhengtai_yushexi',['武乡','榆社西']],
  ['high_speed:liaohanchang_lichengnan|liaohanchang_shexiannan',['黎城南','涉县南']],
  ['high_speed:linchang_anze|linchang_fushan',['安泽','浮山']],
  ['high_speed:zhengtai_03|zhengtai_jiaozuoxi',['晋城东','焦作西']],
  ['conventional:houyue_qinshui|houyue_yicheng',['沁水','翼城']],
  ['conventional:houyue_jiyuan|houyue_yangcheng',['阳城','济源']]
]);
for(const b of changzhi.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedChangzhiSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedChangzhiSides.get(b.edgeId)[1]);
}
const resolvedChangzhi=resolve(data,defs).find(div=>div.id==='changzhi');
assert.equal(resolvedChangzhi.errors.length,0,`Changzhi overlap check: ${resolvedChangzhi.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='changzhi')) {
  assert.equal([...changzhi.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Changzhi overlaps ${other.name}`);
}
const houmaDef=defs.find(def=>def.id==='houma');
assert(houmaDef,'Houma division must be configured');
assert.equal(data.stations.find(s=>s.id===houmaDef.seedStationId).name,'侯马');
const [houma]=resolve(data,[houmaDef]);
assert.equal(houma.errors.length,0,`Houma division: ${houma.errors.join('; ')}`);
assert.equal(houma.stationIds.size,15);
assert.equal(houma.edgeIds.size,14);
assert.equal(houma.boundaries.length,6);
const expectedHoumaSides=new Map([
  ['high_speed:zhangdaxi_huozhoudong|zhangdaxi_lingshidong',['霍州东','灵石东']],
  ['high_speed:linchang_anze|linchang_fushan',['浮山','安泽']],
  ['conventional:houyue_qinshui|houyue_yicheng',['翼城','沁水']],
  ['high_speed:zhangdaxi_dali|zhangdaxi_yongjibei',['永济北','大荔']],
  ['high_speed:xihanhou_hejin|yunhan_hanchengdong',['河津','韩城东']],
  ['high_speed:lianxulan_07|zhangdaxi_08',['运城北','三门峡南']]
]);
for(const b of houma.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedHoumaSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedHoumaSides.get(b.edgeId)[1]);
}
const resolvedHouma=resolve(data,defs).find(div=>div.id==='houma');
assert.equal(resolvedHouma.errors.length,0,`Houma overlap check: ${resolvedHouma.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='houma')) {
  assert.equal([...houma.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Houma overlaps ${other.name}`);
}
const jiningDef=defs.find(def=>def.id==='jining');
assert(jiningDef,'Jining division must be configured');
assert.equal(data.stations.find(s=>s.id===jiningDef.seedStationId).name,'集宁南');
const [jining]=resolve(data,[jiningDef]);
assert.equal(jining.errors.length,0,`Jining division: ${jining.errors.join('; ')}`);
assert.equal(jining.stationIds.size,12);
assert.equal(jining.edgeIds.size,11);
assert.equal(jining.boundaries.length,4);
const expectedJiningSides=new Map([
  ['high_speed:jingbao_huaian|zhanghu_xinghebei',['兴和北','怀安']],
  ['high_speed:jida_fengzhenbei|jingbao_03',['乌兰察布','丰镇北']],
  ['high_speed:jingbao_qixianyingnan|jingbao_zhuozidong',['卓资东','旗下营南']],
  ['conventional:huade|zhengxiangbaiqi',['化德','正镶白旗']]
]);
for(const b of jining.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedJiningSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedJiningSides.get(b.edgeId)[1]);
}
const resolvedJining=resolve(data,defs).find(div=>div.id==='jining');
assert.equal(resolvedJining.errors.length,0,`Jining overlap check: ${resolvedJining.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='jining')) {
  assert.equal([...jining.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Jining overlaps ${other.name}`);
}
const hohhotDef=defs.find(def=>def.id==='hohhot');
assert(hohhotDef,'Hohhot division must be configured');
assert.equal(data.stations.find(s=>s.id===hohhotDef.seedStationId).name,'呼和浩特东');
const [hohhot]=resolve(data,[hohhotDef]);
assert.equal(hohhot.errors.length,0,`Hohhot division: ${hohhot.errors.join('; ')}`);
assert.equal(hohhot.stationIds.size,8);
assert.equal(hohhot.edgeIds.size,7);
assert.equal(hohhot.boundaries.length,4);
const expectedHohhotSides=new Map([
  ['high_speed:jingbao_qixianyingnan|jingbao_zhuozidong',['旗下营南','卓资东']],
  ['high_speed:jingbao_chasuqi|jingbao_salaqi',['察素齐','萨拉齐']],
  ['high_speed:hushuo_helingeer|hushuo_youyu',['和林格尔','右玉']],
  ['high_speed:baohu_dongshengdong|dae_zhungeer',['准格尔','东胜东']]
]);
for(const b of hohhot.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedHohhotSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedHohhotSides.get(b.edgeId)[1]);
}
const resolvedHohhot=resolve(data,defs).find(div=>div.id==='hohhot');
assert.equal(resolvedHohhot.errors.length,0,`Hohhot overlap check: ${resolvedHohhot.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='hohhot')) {
  assert.equal([...hohhot.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Hohhot overlaps ${other.name}`);
}
const baotouDef=defs.find(def=>def.id==='baotou');
assert(baotouDef,'Baotou division must be configured');
assert.equal(data.stations.find(s=>s.id===baotouDef.seedStationId).name,'包头');
const [baotou]=resolve(data,[baotouDef]);
assert.equal(baotou.errors.length,0,`Baotou division: ${baotou.errors.join('; ')}`);
assert.equal(baotou.stationIds.size,20);
assert.equal(baotou.edgeIds.size,19);
assert.equal(baotou.boundaries.length,5);
const expectedBaotouSides=new Map([
  ['high_speed:jingbao_chasuqi|jingbao_salaqi',['萨拉齐','察素齐']],
  ['high_speed:baohu_dongshengdong|dae_zhungeer',['东胜东','准格尔']],
  ['high_speed:xiyubao_04|xiyubao_05',['鄂尔多斯','榆林南']],
  ['high_speed:baoyin_huinongnan|baoyin_wuhainan',['乌海南','惠农南']],
  ['conventional:linha_ejina|linha_mazongshan',['额济纳','马鬃山']]
]);
for(const b of baotou.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedBaotouSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedBaotouSides.get(b.edgeId)[1]);
}
const resolvedBaotou=resolve(data,defs).find(div=>div.id==='baotou');
assert.equal(resolvedBaotou.errors.length,0,`Baotou overlap check: ${resolvedBaotou.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='baotou')) {
  assert.equal([...baotou.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Baotou overlaps ${other.name}`);
}
const yinchuanDef=defs.find(def=>def.id==='yinchuan');
assert(yinchuanDef,'Yinchuan division must be configured');
assert.equal(data.stations.find(s=>s.id===yinchuanDef.seedStationId).name,'银川');
const [yinchuan]=resolve(data,[yinchuanDef]);
assert.equal(yinchuan.errors.length,0,`Yinchuan division: ${yinchuan.errors.join('; ')}`);
assert.equal(yinchuan.stationIds.size,12);
assert.equal(yinchuan.edgeIds.size,11);
assert.equal(yinchuan.boundaries.length,5);
const expectedYinchuanSides=new Map([
  ['high_speed:baoyin_huinongnan|baoyin_wuhainan',['惠农南','乌海南']],
  ['high_speed:xiyin_04|yinlan_hongsibaobei',['吴忠','红寺堡北']],
  ['conventional:taiyin_yanchi|yanzhong_hongsibao',['盐池','红寺堡']],
  ['high_speed:taiyin_dingbian|taiyin_yanchi',['盐池','定边']],
  ['high_speed:xiyin_huanxian|xiyin_tianshuibu',['甜水堡','环县']]
]);
for(const b of yinchuan.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedYinchuanSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedYinchuanSides.get(b.edgeId)[1]);
}
const resolvedYinchuan=resolve(data,defs).find(div=>div.id==='yinchuan');
assert.equal(resolvedYinchuan.errors.length,0,`Yinchuan overlap check: ${resolvedYinchuan.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='yinchuan')) {
  assert.equal([...yinchuan.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Yinchuan overlaps ${other.name}`);
}
const zhongweiDef=defs.find(def=>def.id==='zhongwei');
assert(zhongweiDef,'Zhongwei division must be configured');
assert.equal(data.stations.find(s=>s.id===zhongweiDef.seedStationId).name,'中卫');
const [zhongwei]=resolve(data,[zhongweiDef]);
assert.equal(zhongwei.errors.length,0,`Zhongwei division: ${zhongwei.errors.join('; ')}`);
assert.equal(zhongwei.stationIds.size,11);
assert.equal(zhongwei.edgeIds.size,10);
assert.equal(zhongwei.boundaries.length,5);
const expectedZhongweiSides=new Map([
  ['high_speed:xiyin_04|yinlan_hongsibaobei',['红寺堡北','吴忠']],
  ['conventional:taiyin_yanchi|yanzhong_hongsibao',['红寺堡','盐池']],
  ['high_speed:yinlan_03|yinlan_beitan',['中卫南','北滩']],
  ['conventional:ganwu_gantang|ganwu_tanjiajing',['干塘','谭家井']],
  ['conventional:baozhong_02|baozhong_03',['固原','平凉']]
]);
for(const b of zhongwei.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedZhongweiSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedZhongweiSides.get(b.edgeId)[1]);
}
const resolvedZhongwei=resolve(data,defs).find(div=>div.id==='zhongwei');
assert.equal(resolvedZhongwei.errors.length,0,`Zhongwei overlap check: ${resolvedZhongwei.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='zhongwei')) {
  assert.equal([...zhongwei.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Zhongwei overlaps ${other.name}`);
}
const xianDef=defs.find(def=>def.id==='xian');
assert(xianDef,'Xi’an division must be configured');
assert.equal(data.stations.find(s=>s.id===xianDef.seedStationId).name,'西安站');
const [xian]=resolve(data,[xianDef]);
assert.equal(xian.errors.length,0,`Xi’an division: ${xian.errors.join('; ')}`);
assert.equal(xian.stationIds.size,48);
assert.equal(xian.edgeIds.size,48);
assert.equal(xian.boundaries.length,11);
const expectedXianSides=new Map([
  ['high_speed:lianxulan_qishan|lianxulan_yanglingnan',['杨陵南','岐山']],
  ['high_speed:xiyu_02|xiyu_zhenanxi',['镇安西','安康西']],
  ['high_speed:xicheng_foping|xicheng_yangxianxi',['佛坪','洋县西']],
  ['high_speed:yanyu_qingjianbei|yanyu_yanchuan',['延川','清涧北']],
  ['high_speed:zhangdaxi_dali|zhangdaxi_yongjibei',['大荔','永济北']],
  ['high_speed:xihanhou_hejin|yunhan_hanchengdong',['韩城东','河津']],
  ['high_speed:lianxulan_huashanbei|lianxulan_lingbaoxi',['华山北','灵宝西']],
  ['high_speed:shangnan_shangnandong|shangnan_xixiadong',['商南东','西峡东']],
  ['high_speed:xiwu_manchuanguan|xiwu_yunxi',['漫川关','郧西']],
  ['high_speed:xiyin_binzhoudong|xiyin_ningxian',['彬州东','宁县']],
  ['conventional:xiping_changqingqiao|xiping_changwu',['长武','长庆桥']]
]);
for(const b of xian.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedXianSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedXianSides.get(b.edgeId)[1]);
}
const resolvedXian=resolve(data,defs).find(div=>div.id==='xian');
assert.equal(resolvedXian.errors.length,0,`Xi’an overlap check: ${resolvedXian.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='xian')) {
  assert.equal([...xian.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Xi’an overlaps ${other.name}`);
}
const baojiDef=defs.find(def=>def.id==='baoji');
assert(baojiDef,'Baoji division must be configured');
assert.equal(data.stations.find(s=>s.id===baojiDef.seedStationId).name,'宝鸡');
const [baoji]=resolve(data,[baojiDef]);
assert.equal(baoji.errors.length,0,`Baoji division: ${baoji.errors.join('; ')}`);
assert.equal(baoji.stationIds.size,12);
assert.equal(baoji.edgeIds.size,11);
assert.equal(baoji.boundaries.length,4);
const expectedBaojiSides=new Map([
  ['high_speed:lianxulan_qishan|lianxulan_yanglingnan',['岐山','杨陵南']],
  ['high_speed:lianxulan_11|lianxulan_dongcha',['宝鸡南','东岔']],
  ['conventional:baozhong_ankouyao|baozhong_longxian',['陇县','安口窑']],
  ['conventional:baocheng_yangpingguan|baocheng_yanzibian',['阳平关','燕子砭']]
]);
for(const b of baoji.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedBaojiSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedBaojiSides.get(b.edgeId)[1]);
}
const resolvedBaoji=resolve(data,defs).find(div=>div.id==='baoji');
assert.equal(resolvedBaoji.errors.length,0,`Baoji overlap check: ${resolvedBaoji.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='baoji')) {
  assert.equal([...baoji.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Baoji overlaps ${other.name}`);
}
const ankangDef=defs.find(def=>def.id==='ankang');
assert(ankangDef,'Ankang division must be configured');
assert.equal(data.stations.find(s=>s.id===ankangDef.seedStationId).name,'安康西');
const [ankang]=resolve(data,[ankangDef]);
assert.equal(ankang.errors.length,0,`Ankang division: ${ankang.errors.join('; ')}`);
assert.equal(ankang.stationIds.size,12);
assert.equal(ankang.edgeIds.size,11);
assert.equal(ankang.boundaries.length,6);
const expectedAnkangSides=new Map([
  ['high_speed:xiyu_02|xiyu_zhenanxi',['安康西','镇安西']],
  ['high_speed:xicheng_foping|xicheng_yangxianxi',['洋县西','佛坪']],
  ['high_speed:hananshi_baihe|xiwu_03',['白河','十堰东']],
  ['high_speed:xicheng_chaotiannan|xicheng_ningqiangnan',['宁强南','朝天南']],
  ['high_speed:xiyu_chengkou|xiyu_langao',['岚皋','城口']],
  ['high_speed:chengbaan_wanyuanbei|chengbaan_ziyangnan',['紫阳南','万源北']]
]);
for(const b of ankang.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedAnkangSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedAnkangSides.get(b.edgeId)[1]);
}
const resolvedAnkang=resolve(data,defs).find(div=>div.id==='ankang');
assert.equal(resolvedAnkang.errors.length,0,`Ankang overlap check: ${resolvedAnkang.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='ankang')) {
  assert.equal([...ankang.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Ankang overlaps ${other.name}`);
}
const suideDef=defs.find(def=>def.id==='suidexi');
assert(suideDef,'Suide division must be configured');
assert.equal(data.stations.find(s=>s.id===suideDef.seedStationId).name,'绥德西');
const [suide]=resolve(data,[suideDef]);
assert.equal(suide.errors.length,0,`Suide division: ${suide.errors.join('; ')}`);
assert.equal(suide.stationIds.size,7);
assert.equal(suide.edgeIds.size,6);
assert.equal(suide.boundaries.length,4);
const expectedSuideSides=new Map([
  ['high_speed:xiyubao_04|xiyubao_05',['榆林南','鄂尔多斯']],
  ['high_speed:taisui_liulinxi|yanyu_suidexi',['绥德西','柳林西']],
  ['high_speed:taiyin_dingbian|taiyin_yanchi',['定边','盐池']],
  ['high_speed:yanyu_qingjianbei|yanyu_yanchuan',['清涧北','延川']]
]);
for(const b of suide.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedSuideSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedSuideSides.get(b.edgeId)[1]);
}
const resolvedSuide=resolve(data,defs).find(div=>div.id==='suidexi');
assert.equal(resolvedSuide.errors.length,0,`Suide overlap check: ${resolvedSuide.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='suidexi')) {
  assert.equal([...suide.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Suide overlaps ${other.name}`);
}
const lanzhouDef=defs.find(def=>def.id==='lanzhou');
assert(lanzhouDef,'Lanzhou division must be configured');
assert.equal(data.stations.find(s=>s.id===lanzhouDef.seedStationId).name,'兰州');
const [lanzhou]=resolve(data,[lanzhouDef]);
assert.equal(lanzhou.errors.length,0,`Lanzhou division: ${lanzhou.errors.join('; ')}`);
assert.equal(lanzhou.stationIds.size,38);
assert.equal(lanzhou.edgeIds.size,37);
assert.equal(lanzhou.boundaries.length,9);
const expectedLanzhouSides=new Map([
  ['high_speed:lianxulan_11|lianxulan_dongcha',['东岔','宝鸡南']],
  ['conventional:dingping_huining|dingping_jingning',['会宁','静宁']],
  ['conventional:baozhong_huating|tianping_zhangjiachuan',['张家川','华亭']],
  ['high_speed:lanzhang_tianzhuxi|lanzhang_yongdengbei',['永登北','天祝西']],
  ['high_speed:yinlan_03|yinlan_beitan',['北滩','中卫南']],
  ['high_speed:lanxin_haidong|lanxin_minhenan',['民和南','海东']],
  ['conventional:chuanqing_04|chuanqing_ganjia',['甘加','同仁']],
  ['conventional:langyu_02|langyu_yaodu',['陇南','姚渡']],
  ['conventional:chuanqing_huahu|chuanqing_langmusi',['郎木寺','花湖']]
]);
for(const b of lanzhou.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedLanzhouSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedLanzhouSides.get(b.edgeId)[1]);
}
const resolvedLanzhou=resolve(data,defs).find(div=>div.id==='lanzhou');
assert.equal(resolvedLanzhou.errors.length,0,`Lanzhou overlap check: ${resolvedLanzhou.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='lanzhou')) {
  assert.equal([...lanzhou.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Lanzhou overlaps ${other.name}`);
}
const pingliangDef=defs.find(def=>def.id==='pingliang');
assert(pingliangDef,'Pingliang division must be configured');
assert.equal(data.stations.find(s=>s.id===pingliangDef.seedStationId).name,'平凉');
const [pingliang]=resolve(data,[pingliangDef]);
assert.equal(pingliang.errors.length,0,`Pingliang division: ${pingliang.errors.join('; ')}`);
assert.equal(pingliang.stationIds.size,17);
assert.equal(pingliang.edgeIds.size,16);
assert.equal(pingliang.boundaries.length,7);
const expectedPingliangSides=new Map([
  ['conventional:dingping_huining|dingping_jingning',['静宁','会宁']],
  ['conventional:baozhong_huating|tianping_zhangjiachuan',['华亭','张家川']],
  ['conventional:baozhong_02|baozhong_03',['平凉','固原']],
  ['conventional:baozhong_ankouyao|baozhong_longxian',['安口窑','陇县']],
  ['conventional:xiping_changqingqiao|xiping_changwu',['长庆桥','长武']],
  ['high_speed:xiyin_binzhoudong|xiyin_ningxian',['宁县','彬州东']],
  ['high_speed:xiyin_huanxian|xiyin_tianshuibu',['环县','甜水堡']]
]);
for(const b of pingliang.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedPingliangSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedPingliangSides.get(b.edgeId)[1]);
}
const resolvedPingliang=resolve(data,defs).find(div=>div.id==='pingliang');
assert.equal(resolvedPingliang.errors.length,0,`Pingliang overlap check: ${resolvedPingliang.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='pingliang')) {
  assert.equal([...pingliang.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Pingliang overlaps ${other.name}`);
}
const wuweiDef=defs.find(def=>def.id==='wuwei');
assert(wuweiDef,'Wuwei division must be configured');
assert.equal(wuweiDef.seedStationIds.map(id=>data.stations.find(s=>s.id===id).name).join('、'),'武威东、武威南');
const [wuwei]=resolve(data,[wuweiDef]);
assert.equal(wuwei.errors.length,0,`Wuwei division: ${wuwei.errors.join('; ')}`);
assert.equal(wuwei.stationIds.size,9);
assert.equal(wuwei.edgeIds.size,7);
assert.equal(wuwei.boundaries.length,3);
const expectedWuweiSides=new Map([
  ['high_speed:lanzhang_tianzhuxi|lanzhang_yongdengbei',['天祝西','永登北']],
  ['high_speed:lanzhang_03|lanzhang_jilingxi',['金昌南','芨岭西']],
  ['conventional:ganwu_gantang|ganwu_tanjiajing',['谭家井','干塘']]
]);
for(const b of wuwei.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedWuweiSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedWuweiSides.get(b.edgeId)[1]);
}
const resolvedWuwei=resolve(data,defs).find(div=>div.id==='wuwei');
assert.equal(resolvedWuwei.errors.length,0,`Wuwei overlap check: ${resolvedWuwei.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='wuwei')) {
  assert.equal([...wuwei.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Wuwei overlaps ${other.name}`);
}
const zhangyeDef=defs.find(def=>def.id==='zhangye');
assert(zhangyeDef,'Zhangye division must be configured');
assert.equal(zhangyeDef.seedStationIds.map(id=>data.stations.find(s=>s.id===id).name).join('、'),'张掖西、马鬃山');
const [zhangye]=resolve(data,[zhangyeDef]);
assert.equal(zhangye.errors.length,0,`Zhangye division: ${zhangye.errors.join('; ')}`);
assert.equal(zhangye.stationIds.size,20);
assert.equal(zhangye.edgeIds.size,18);
assert.equal(zhangye.boundaries.length,6);
const expectedZhangyeSides=new Map([
  ['high_speed:lanzhang_03|lanzhang_jilingxi',['芨岭西','金昌南']],
  ['high_speed:lanxin_menyuan|lanxin_shandanmachang',['山丹马场','门源']],
  ['high_speed:lanxin_07|lanxin_liuyuannan',['柳园南','哈密']],
  ['conventional:dunge_dangjinshan|dunge_suganhu',['当金山','苏干湖']],
  ['conventional:linha_ejina|linha_mazongshan',['马鬃山','额济纳']],
  ['conventional:linha_mingshui|linha_wutongshui',['明水','梧桐水']]
]);
for(const b of zhangye.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedZhangyeSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedZhangyeSides.get(b.edgeId)[1]);
}
const resolvedZhangye=resolve(data,defs).find(div=>div.id==='zhangye');
assert.equal(resolvedZhangye.errors.length,0,`Zhangye overlap check: ${resolvedZhangye.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='zhangye')) {
  assert.equal([...zhangye.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Zhangye overlaps ${other.name}`);
}
const xiningDef=defs.find(def=>def.id==='xining');
assert(xiningDef,'Xining division must be configured');
assert.equal(data.stations.find(s=>s.id===xiningDef.seedStationId).name,'西宁');
const [xining]=resolve(data,[xiningDef]);
assert.equal(xining.errors.length,0,`Xining division: ${xining.errors.join('; ')}`);
assert.equal(xining.stationIds.size,12);
assert.equal(xining.edgeIds.size,11);
assert.equal(xining.boundaries.length,4);
const expectedXiningSides=new Map([
  ['high_speed:lanxin_haidong|lanxin_minhenan',['海东','民和南']],
  ['high_speed:lanxin_menyuan|lanxin_shandanmachang',['门源','山丹马场']],
  ['conventional:chuanqing_04|chuanqing_ganjia',['同仁','甘加']],
  ['conventional:qingzang_gangcha|qingzang_tianjun',['刚察','天峻']]
]);
for(const b of xining.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedXiningSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedXiningSides.get(b.edgeId)[1]);
}
const resolvedXining=resolve(data,defs).find(div=>div.id==='xining');
assert.equal(resolvedXining.errors.length,0,`Xining overlap check: ${resolvedXining.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='xining')) {
  assert.equal([...xining.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Xining overlaps ${other.name}`);
}
const golmudDef=defs.find(def=>def.id==='golmud');
assert(golmudDef,'Golmud division must be configured');
assert.equal(data.stations.find(s=>s.id===golmudDef.seedStationId).name,'格尔木');
const [golmud]=resolve(data,[golmudDef]);
assert.equal(golmud.errors.length,0,`Golmud division: ${golmud.errors.join('; ')}`);
assert.equal(golmud.stationIds.size,20);
assert.equal(golmud.edgeIds.size,19);
assert.equal(golmud.boundaries.length,4);
const expectedGolmudSides=new Map([
  ['conventional:qingzang_gangcha|qingzang_tianjun',['天峻','刚察']],
  ['conventional:dunge_dangjinshan|dunge_suganhu',['苏干湖','当金山']],
  ['conventional:geku_milan|geku_yitunbulake',['依吞布拉克','米兰']],
  ['conventional:qingzang_anduo|qingzang_tanggula',['唐古拉','安多']]
]);
for(const b of golmud.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedGolmudSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedGolmudSides.get(b.edgeId)[1]);
}
const resolvedGolmud=resolve(data,defs).find(div=>div.id==='golmud');
assert.equal(resolvedGolmud.errors.length,0,`Golmud overlap check: ${resolvedGolmud.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='golmud')) {
  assert.equal([...golmud.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Golmud overlaps ${other.name}`);
}
const hamiDef=defs.find(def=>def.id==='hami');
assert(hamiDef,'Hami division must be configured');
assert.equal(data.stations.find(s=>s.id===hamiDef.seedStationId).name,'哈密');
const [hami]=resolve(data,[hamiDef]);
assert.equal(hami.errors.length,0,`Hami division: ${hami.errors.join('; ')}`);
assert.equal(hami.stationIds.size,5);
assert.equal(hami.edgeIds.size,4);
assert.equal(hami.boundaries.length,4);
const expectedHamiSides=new Map([
  ['high_speed:lanxin_07|lanxin_liuyuannan',['哈密','柳园南']],
  ['conventional:linha_mingshui|linha_wutongshui',['梧桐水','明水']],
  ['high_speed:lanxin_shanshanbei|lanxin_tuha',['吐哈','鄯善北']],
  ['conventional:geku_milandong|hamimi_luozhong',['罗中','米兰东']]
]);
for(const b of hami.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedHamiSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedHamiSides.get(b.edgeId)[1]);
}
const resolvedHami=resolve(data,defs).find(div=>div.id==='hami');
assert.equal(resolvedHami.errors.length,0,`Hami overlap check: ${resolvedHami.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='hami')) {
  assert.equal([...hami.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Hami overlaps ${other.name}`);
}
const urumqiDef=defs.find(def=>def.id==='urumqi');
assert(urumqiDef,'Urumqi division must be configured');
assert.equal(urumqiDef.seedStationIds.map(id=>data.stations.find(s=>s.id===id).name).join('、'),'乌鲁木齐、托克逊');
const [urumqi]=resolve(data,[urumqiDef]);
assert.equal(urumqi.errors.length,0,`Urumqi division: ${urumqi.errors.join('; ')}`);
assert.equal(urumqi.stationIds.size,10);
assert.equal(urumqi.edgeIds.size,8);
assert.equal(urumqi.boundaries.length,4);
const expectedUrumqiSides=new Map([
  ['high_speed:lanxin_shanshanbei|lanxin_tuha',['鄯善北','吐哈']],
  ['conventional:beijiang_shawanshi|beijiang_shihezi',['石河子','沙湾市']],
  ['conventional:afuzhun_fuyun|beijiang_03',['富蕴','阿勒泰']],
  ['conventional:nanjiang_malan|nanjiang_tuokexun',['托克逊','马兰']]
]);
for(const b of urumqi.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedUrumqiSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedUrumqiSides.get(b.edgeId)[1]);
}
const resolvedUrumqi=resolve(data,defs).find(div=>div.id==='urumqi');
assert.equal(resolvedUrumqi.errors.length,0,`Urumqi overlap check: ${resolvedUrumqi.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='urumqi')) {
  assert.equal([...urumqi.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Urumqi overlaps ${other.name}`);
}
const kuitunDef=defs.find(def=>def.id==='kuitun');
assert(kuitunDef,'Kuitun division must be configured');
assert.equal(data.stations.find(s=>s.id===kuitunDef.seedStationId).name,'奎屯');
const [kuitun]=resolve(data,[kuitunDef]);
assert.equal(kuitun.errors.length,0,`Kuitun division: ${kuitun.errors.join('; ')}`);
assert.equal(kuitun.stationIds.size,19);
assert.equal(kuitun.edgeIds.size,18);
assert.equal(kuitun.boundaries.length,3);
const expectedKuitunSides=new Map([
  ['conventional:beijiang_shawanshi|beijiang_shihezi',['沙湾市','石河子']],
  ['conventional:afuzhun_fuyun|beijiang_03',['阿勒泰','富蕴']],
  ['conventional:kue_kutaikelike|yia_bayinbuluke',['巴音布鲁克','库台克力克']]
]);
for(const b of kuitun.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedKuitunSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedKuitunSides.get(b.edgeId)[1]);
}
const resolvedKuitun=resolve(data,defs).find(div=>div.id==='kuitun');
assert.equal(resolvedKuitun.errors.length,0,`Kuitun overlap check: ${resolvedKuitun.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='kuitun')) {
  assert.equal([...kuitun.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Kuitun overlaps ${other.name}`);
}
const korlaDef=defs.find(def=>def.id==='korla');
assert(korlaDef,'Korla division must be configured');
assert.equal(data.stations.find(s=>s.id===korlaDef.seedStationId).name,'库尔勒');
const [korla]=resolve(data,[korlaDef]);
assert.equal(korla.errors.length,0,`Korla division: ${korla.errors.join('; ')}`);
assert.equal(korla.stationIds.size,17);
assert.equal(korla.edgeIds.size,16);
assert.equal(korla.boundaries.length,6);
const expectedKorlaSides=new Map([
  ['conventional:geku_milandong|hamimi_luozhong',['米兰东','罗中']],
  ['conventional:kue_kutaikelike|yia_bayinbuluke',['库台克力克','巴音布鲁克']],
  ['conventional:geku_milan|geku_yitunbulake',['米兰','依吞布拉克']],
  ['conventional:nanjiang_03|nanjiang_bachu',['阿克苏','巴楚']],
  ['conventional:heruo_02|heruo_minfeng',['且末','民丰']],
  ['conventional:nanjiang_malan|nanjiang_tuokexun',['马兰','托克逊']]
]);
for(const b of korla.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedKorlaSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedKorlaSides.get(b.edgeId)[1]);
}
const resolvedKorla=resolve(data,defs).find(div=>div.id==='korla');
assert.equal(resolvedKorla.errors.length,0,`Korla overlap check: ${resolvedKorla.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='korla')) {
  assert.equal([...korla.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Korla overlaps ${other.name}`);
}
const kashgarDef=defs.find(def=>def.id==='kashgar');
assert(kashgarDef,'Kashgar division must be configured');
assert.equal(data.stations.find(s=>s.id===kashgarDef.seedStationId).name,'喀什');
const [kashgar]=resolve(data,[kashgarDef]);
assert.equal(kashgar.errors.length,0,`Kashgar division: ${kashgar.errors.join('; ')}`);
assert.equal(kashgar.stationIds.size,13);
assert.equal(kashgar.edgeIds.size,12);
assert.equal(kashgar.boundaries.length,2);
const expectedKashgarSides=new Map([
  ['conventional:nanjiang_03|nanjiang_bachu',['巴楚','阿克苏']],
  ['conventional:heruo_02|heruo_minfeng',['民丰','且末']]
]);
for(const b of kashgar.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedKashgarSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedKashgarSides.get(b.edgeId)[1]);
}
const resolvedKashgar=resolve(data,defs).find(div=>div.id==='kashgar');
assert.equal(resolvedKashgar.errors.length,0,`Kashgar overlap check: ${resolvedKashgar.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='kashgar')) {
  assert.equal([...kashgar.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Kashgar overlaps ${other.name}`);
}
const lhasaDef=defs.find(def=>def.id==='lhasa');
assert(lhasaDef,'Lhasa division must be configured');
assert.equal(data.stations.find(s=>s.id===lhasaDef.seedStationId).name,'拉萨');
const [lhasa]=resolve(data,[lhasaDef]);
assert.equal(lhasa.errors.length,0,`Lhasa division: ${lhasa.errors.join('; ')}`);
assert.equal(lhasa.stationIds.size,33);
assert.equal(lhasa.edgeIds.size,33);
assert.equal(lhasa.boundaries.length,3);
const expectedLhasaSides=new Map([
  ['conventional:qingzang_anduo|qingzang_tanggula',['安多','唐古拉']],
  ['conventional:chuanzang_baiyu|chuanzang_gongjue',['贡觉','白玉']],
  ['conventional:dianzang_deqin|dianzang_yanjing',['盐井','德钦']]
]);
for(const b of lhasa.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedLhasaSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedLhasaSides.get(b.edgeId)[1]);
}
const resolvedLhasa=resolve(data,defs).find(div=>div.id==='lhasa');
assert.equal(resolvedLhasa.errors.length,0,`Lhasa overlap check: ${resolvedLhasa.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='lhasa')) {
  assert.equal([...lhasa.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Lhasa overlaps ${other.name}`);
}
const chengduDef=defs.find(def=>def.id==='chengdu');
assert(chengduDef,'Chengdu division must be configured');
assert.equal(chengduDef.seedStationIds.map(id=>data.stations.find(s=>s.id===id).name).join('、'),'成都东、雷波');
const [chengdu]=resolve(data,[chengduDef]);
assert.equal(chengdu.errors.length,0,`Chengdu division: ${chengdu.errors.join('; ')}`);
assert.equal(chengdu.stationIds.size,86);
assert.equal(chengdu.edgeIds.size,89);
assert.equal(chengdu.boundaries.length,13);
const expectedChengduSides=new Map([
  ['high_speed:chengdawan_03|chengdawan_tongnan',['遂宁','潼南']],
  ['high_speed:chengyu_anyue|chengyu_dazushike',['安岳','大足石刻']],
  ['high_speed:chengyu_longchangbei|chengyu_rongchangbei',['隆昌北','荣昌北']],
  ['high_speed:xicheng_jiangyoubei|xicheng_qingchuan',['江油北','青川']],
  ['high_speed:chengbaan_yanting|miansuinei_santai',['三台','盐亭']],
  ['high_speed:chengdawan_pengxinan|langyu_04',['蓬溪南','南充北']],
  ['high_speed:chengyi_weiyuan|chengyi_zizhongxi',['资中西','威远']],
  ['high_speed:chengyu_03|chengziyi_03',['内江北','自贡']],
  ['high_speed:chenggui_nixi|chenggui_qianwei',['犍为','泥溪']],
  ['conventional:yixipan_leibo|yixipan_suijiang',['雷波','绥江']],
  ['conventional:chengkun_03|chengkun_yongren',['攀枝花南','永仁']],
  ['conventional:chuanzang_baiyu|chuanzang_gongjue',['白玉','贡觉']],
  ['conventional:chuanqing_huahu|chuanqing_langmusi',['花湖','郎木寺']]
]);
for(const b of chengdu.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedChengduSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedChengduSides.get(b.edgeId)[1]);
}
const resolvedChengdu=resolve(data,defs).find(div=>div.id==='chengdu');
assert.equal(resolvedChengdu.errors.length,0,`Chengdu overlap check: ${resolvedChengdu.errors.join('; ')}`);
for(const other of resolve(data,defs).filter(div=>div.id!=='chengdu')) {
  assert.equal([...chengdu.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Chengdu overlaps ${other.name}`);
}
const chongqingDef=defs.find(def=>def.id==='chongqing');
assert(chongqingDef,'Chongqing division must be configured');
assert.equal(chongqingDef.seedStationId,byName('重庆北'));
const [chongqing]=resolve(data,[chongqingDef]);
assert.equal(chongqing.errors.length,0,`Chongqing division: ${chongqing.errors.join('; ')}`);
assert.equal(chongqing.stationIds.size,39);
assert.equal(chongqing.edgeIds.size,41);
assert.equal(chongqing.boundaries.length,15);
const expectedChongqingSides=new Map([
  ['high_speed:langyu_04|langyu_wusheng',['武胜','南充北']],
  ['high_speed:xiyu_dazu|xiyu_guangandong',['广安东','大竹']],
  ['high_speed:yuwan_dianjiang|yuwan_liangpingnan',['垫江','梁平南']],
  ['high_speed:yuwan_fengdubei|yuwan_zhongxian',['丰都北','忠县']],
  ['high_speed:wanqian_shizhu|yuxia_pengshuixi',['彭水西','石柱']],
  ['high_speed:yifu_huangshui|yifu_lichuan',['黄水','利川']],
  ['high_speed:yuxia_02|yuxia_xianfeng',['黔江','咸丰']],
  ['conventional:yuhuai_tongren|yuhuai_xiushan',['秀山','铜仁']],
  ['high_speed:yugui_qijiangdong|yugui_tongzidong',['綦江东','桐梓东']],
  ['high_speed:yugui2_wansheng|yugui2_zhengan',['万盛','正安']],
  ['high_speed:yukun_baisha|yukun_hejiang',['白沙','合江']],
  ['high_speed:yukun_luzhoudong|yukun_yongchuannan',['永川南','泸州东']],
  ['high_speed:chengdawan_03|chengdawan_tongnan',['潼南','遂宁']],
  ['high_speed:chengyu_anyue|chengyu_dazushike',['大足石刻','安岳']],
  ['high_speed:chengyu_longchangbei|chengyu_rongchangbei',['荣昌北','隆昌北']]
]);
for(const b of chongqing.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedChongqingSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedChongqingSides.get(b.edgeId)[1]);
}
for(const other of resolve(data,defs).filter(div=>div.id!=='chongqing')) {
  assert.equal([...chongqing.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Chongqing overlaps ${other.name}`);
}
const guangyuanDef=defs.find(def=>def.id==='guangyuan');
assert(guangyuanDef,'Guangyuan division must be configured');
assert.deepEqual(new Set(guangyuanDef.seedStationIds),new Set([byName('广元'),byName('盐亭')]));
const [guangyuan]=resolve(data,[guangyuanDef]);
assert.equal(guangyuan.errors.length,0,`Guangyuan division: ${guangyuan.errors.join('; ')}`);
assert.equal(guangyuan.stationIds.size,17);
assert.equal(guangyuan.edgeIds.size,15);
assert.equal(guangyuan.boundaries.length,10);
const expectedGuangyuanSides=new Map([
  ['high_speed:xicheng_jiangyoubei|xicheng_qingchuan',['青川','江油北']],
  ['high_speed:chengbaan_yanting|miansuinei_santai',['盐亭','三台']],
  ['high_speed:chengdawan_pengxinan|langyu_04',['南充北','蓬溪南']],
  ['high_speed:bazhong_01|guangbada_pingchang',['巴中','平昌']],
  ['high_speed:chengbaan_bazhongdong|chengbaan_tongjiang',['巴中东','通江']],
  ['high_speed:chengdawan_quxianbei|chengdawan_yingshanxi',['营山西','渠县北']],
  ['high_speed:langyu_04|langyu_wusheng',['南充北','武胜']],
  ['high_speed:xicheng_chaotiannan|xicheng_ningqiangnan',['朝天南','宁强南']],
  ['conventional:baocheng_yangpingguan|baocheng_yanzibian',['燕子砭','阳平关']],
  ['conventional:langyu_02|langyu_yaodu',['姚渡','陇南']]
]);
for(const b of guangyuan.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedGuangyuanSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedGuangyuanSides.get(b.edgeId)[1]);
}
for(const other of resolve(data,defs).filter(div=>div.id!=='guangyuan')) {
  assert.equal([...guangyuan.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Guangyuan overlaps ${other.name}`);
}
const dazhouDef=defs.find(def=>def.id==='dazhou');
assert(dazhouDef,'Dazhou division must be configured');
assert.deepEqual(new Set(dazhouDef.seedStationIds),new Set([byName('达州南'),byName('通江')]));
const [dazhou]=resolve(data,[dazhouDef]);
assert.equal(dazhou.errors.length,0,`Dazhou division: ${dazhou.errors.join('; ')}`);
assert.equal(dazhou.stationIds.size,10);
assert.equal(dazhou.edgeIds.size,8);
assert.equal(dazhou.boundaries.length,8);
const expectedDazhouSides=new Map([
  ['high_speed:bazhong_01|guangbada_pingchang',['平昌','巴中']],
  ['high_speed:chengbaan_bazhongdong|chengbaan_tongjiang',['通江','巴中东']],
  ['high_speed:chengdawan_quxianbei|chengdawan_yingshanxi',['渠县北','营山西']],
  ['high_speed:xiyu_dazu|xiyu_guangandong',['大竹','广安东']],
  ['high_speed:xiyu_fankuai|xiyu_kaizhou',['樊哙','开州']],
  ['high_speed:chengdawan_kaijiang|chengdawan_kaizhounan',['开江','开州南']],
  ['high_speed:chengbaan_wanyuanbei|chengbaan_ziyangnan',['万源北','紫阳南']],
  ['high_speed:xiyu_chengkou|xiyu_langao',['城口','岚皋']]
]);
for(const b of dazhou.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedDazhouSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedDazhouSides.get(b.edgeId)[1]);
}
for(const other of resolve(data,defs).filter(div=>div.id!=='dazhou')) {
  assert.equal([...dazhou.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Dazhou overlaps ${other.name}`);
}
const wanzhouDef=defs.find(def=>def.id==='wanzhou');
assert(wanzhouDef,'Wanzhou division must be configured');
assert.equal(wanzhouDef.seedStationId,byName('万州'));
const [wanzhou]=resolve(data,[wanzhouDef]);
assert.equal(wanzhou.errors.length,0,`Wanzhou division: ${wanzhou.errors.join('; ')}`);
assert.equal(wanzhou.stationIds.size,10);
assert.equal(wanzhou.edgeIds.size,9);
assert.equal(wanzhou.boundaries.length,7);
const expectedWanzhouSides=new Map([
  ['high_speed:xiyu_fankuai|xiyu_kaizhou',['开州','樊哙']],
  ['high_speed:chengdawan_kaijiang|chengdawan_kaizhounan',['开州南','开江']],
  ['high_speed:yuwan_dianjiang|yuwan_liangpingnan',['梁平南','垫江']],
  ['high_speed:yuwan_fengdubei|yuwan_zhongxian',['忠县','丰都北']],
  ['high_speed:wanqian_shizhu|yuxia_pengshuixi',['石柱','彭水西']],
  ['high_speed:zhengyu_badong|zhengyu_wushan',['巫山','巴东']],
  ['conventional:yiwan_lichuan|yiwan_wanzhou',['万州','利川']]
]);
for(const b of wanzhou.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedWanzhouSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedWanzhouSides.get(b.edgeId)[1]);
}
assert(wanzhou.stationIds.has(byName('万州北')),'万州—万州北 conventional connector remains inside Wanzhou division');
for(const other of resolve(data,defs).filter(div=>div.id!=='wanzhou')) {
  assert.equal([...wanzhou.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Wanzhou overlaps ${other.name}`);
}
const yibinDef=defs.find(def=>def.id==='yibin');
assert(yibinDef,'Yibin division must be configured');
assert.deepEqual(new Set(yibinDef.seedStationIds),new Set([byName('宜宾'),byName('合江')]));
const [yibin]=resolve(data,[yibinDef]);
assert.equal(yibin.errors.length,0,`Yibin division: ${yibin.errors.join('; ')}`);
assert.equal(yibin.stationIds.size,24);
assert.equal(yibin.edgeIds.size,23);
assert.equal(yibin.boundaries.length,9);
const expectedYibinSides=new Map([
  ['high_speed:chengyi_weiyuan|chengyi_zizhongxi',['威远','资中西']],
  ['high_speed:chengyu_03|chengziyi_03',['自贡','内江北']],
  ['high_speed:chenggui_nixi|chenggui_qianwei',['泥溪','犍为']],
  ['conventional:yixipan_leibo|yixipan_suijiang',['绥江','雷波']],
  ['high_speed:yukun_luzhoudong|yukun_yongchuannan',['泸州东','永川南']],
  ['high_speed:yukun_baisha|yukun_hejiang',['合江','白沙']],
  ['high_speed:chenggui_weixin|chenggui_xingwen',['兴文','威信']],
  ['high_speed:yukun_junlian|yukun_yanjinnan',['筠连','盐津南']],
  ['high_speed:chenggui_05|yukun_gulin',['古蔺','毕节']]
]);
for(const b of yibin.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedYibinSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedYibinSides.get(b.edgeId)[1]);
}
for(const other of resolve(data,defs).filter(div=>div.id!=='yibin')) {
  assert.equal([...yibin.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Yibin overlaps ${other.name}`);
}
const guiyangDef=defs.find(def=>def.id==='guiyang');
assert(guiyangDef,'Guiyang division must be configured');
assert.equal(guiyangDef.seedStationId,byName('贵阳'));
const [guiyang]=resolve(data,[guiyangDef]);
assert.equal(guiyang.errors.length,0,`Guiyang division: ${guiyang.errors.join('; ')}`);
assert.equal(guiyang.stationIds.size,31);
assert.equal(guiyang.edgeIds.size,31);
assert.equal(guiyang.boundaries.length,9);
const expectedGuiyangSides=new Map([
  ['high_speed:yugui_qijiangdong|yugui_tongzidong',['桐梓东','綦江东']],
  ['high_speed:yugui2_wansheng|yugui2_zhengan',['正安','万盛']],
  ['high_speed:chenggui_dafang|chenggui_qianxi',['黔西','大方']],
  ['high_speed:anliu_liuzhinan|hukun_19',['安顺西','六枝南']],
  ['high_speed:hukun_guanling|hukun_puanxian',['关岭','普安县']],
  ['high_speed:hukun_tongrennan|hukun_xinhuangxi',['铜仁南','新晃西']],
  ['high_speed:guinan_huanjiang|guinan_libo',['荔波','环江']],
  ['high_speed:guigang_congjiang|guigang_sanjiangnan',['从江','三江南']],
  ['conventional:qiangui_dushan|qiangui_nandan',['独山','南丹']]
]);
for(const b of guiyang.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedGuiyangSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedGuiyangSides.get(b.edgeId)[1]);
}
for(const other of resolve(data,defs).filter(div=>div.id!=='guiyang')) {
  assert.equal([...guiyang.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Guiyang overlaps ${other.name}`);
}
const liupanshuiDef=defs.find(def=>def.id==='liupanshui');
assert(liupanshuiDef,'Liupanshui division must be configured');
assert.equal(liupanshuiDef.seedStationId,byName('六盘水'));
const [liupanshui]=resolve(data,[liupanshuiDef]);
assert.equal(liupanshui.errors.length,0,`Liupanshui division: ${liupanshui.errors.join('; ')}`);
assert.equal(liupanshui.stationIds.size,18);
assert.equal(liupanshui.edgeIds.size,17);
assert.equal(liupanshui.boundaries.length,10);
const expectedLiupanshuiSides=new Map([
  ['high_speed:chenggui_weixin|chenggui_xingwen',['威信','兴文']],
  ['high_speed:chenggui_05|yukun_gulin',['毕节','古蔺']],
  ['high_speed:chenggui_dafang|chenggui_qianxi',['大方','黔西']],
  ['high_speed:anliu_liuzhinan|hukun_19',['六枝南','安顺西']],
  ['high_speed:hukun_guanling|hukun_puanxian',['普安县','关岭']],
  ['high_speed:yukun_04|zhaoliu_weining',['威宁','昭通东']],
  ['high_speed:anliu_05|liukun_xuanwei',['六盘水','宣威']],
  ['high_speed:hukun_fuyuanbei|hukun_panzhou',['盘州','富源北']],
  ['high_speed:xingbai_ceheng|xingbai_tianlin',['册亨','田林']],
  ['conventional:nankun_luoping|nankun_weishe',['威舍','罗平']]
]);
for(const b of liupanshui.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedLiupanshuiSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedLiupanshuiSides.get(b.edgeId)[1]);
}
for(const other of resolve(data,defs).filter(div=>div.id!=='liupanshui')) {
  assert.equal([...liupanshui.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Liupanshui overlaps ${other.name}`);
}
const kunmingDef=defs.find(def=>def.id==='kunming');
assert(kunmingDef,'Kunming division must be configured');
assert.equal(kunmingDef.seedStationId,byName('昆明'));
const [kunming]=resolve(data,[kunmingDef]);
assert.equal(kunming.errors.length,0,`Kunming division: ${kunming.errors.join('; ')}`);
assert.equal(kunming.stationIds.size,30);
assert.equal(kunming.edgeIds.size,30);
assert.equal(kunming.boundaries.length,11);
const expectedKunmingSides=new Map([
  ['high_speed:yukun_junlian|yukun_yanjinnan',['盐津南','筠连']],
  ['conventional:chengkun_03|chengkun_yongren',['永仁','攀枝花南']],
  ['high_speed:yukun_04|zhaoliu_weining',['昭通东','威宁']],
  ['high_speed:anliu_05|liukun_xuanwei',['宣威','六盘水']],
  ['high_speed:hukun_fuyuanbei|hukun_panzhou',['富源北','盘州']],
  ['conventional:chengkun_nanhua|chengkun_xiangyun',['南华','祥云']],
  ['conventional:kunmo_02|kunmo_jinningdong',['晋宁东','玉溪']],
  ['conventional:nankun_mile|yumi_huaning',['弥勒','华宁']],
  ['high_speed:mimeng_zhuyuan|nankun_mile',['弥勒','竹园']],
  ['high_speed:nankun_02|nankun_funing',['富宁','百色']],
  ['conventional:nankun_luoping|nankun_weishe',['罗平','威舍']]
]);
for(const b of kunming.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedKunmingSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedKunmingSides.get(b.edgeId)[1]);
}
for(const other of resolve(data,defs).filter(div=>div.id!=='kunming')) {
  assert.equal([...kunming.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Kunming overlaps ${other.name}`);
}
const daliDef=defs.find(def=>def.id==='dali');
assert(daliDef,'Dali division must be configured');
assert.equal(daliDef.seedStationId,byName('大理'));
const [dali]=resolve(data,[daliDef]);
assert.equal(dali.errors.length,0,`Dali division: ${dali.errors.join('; ')}`);
assert.equal(dali.stationIds.size,22);
assert.equal(dali.edgeIds.size,21);
assert.equal(dali.boundaries.length,2);
const expectedDaliSides=new Map([
  ['conventional:chengkun_nanhua|chengkun_xiangyun',['祥云','南华']],
  ['conventional:dianzang_deqin|dianzang_yanjing',['德钦','盐井']]
]);
for(const b of dali.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedDaliSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedDaliSides.get(b.edgeId)[1]);
}
for(const other of resolve(data,defs).filter(div=>div.id!=='dali')) {
  assert.equal([...dali.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Dali overlaps ${other.name}`);
}
const yuxiDef=defs.find(def=>def.id==='yuxi');
assert(yuxiDef,'Yuxi division must be configured');
assert.equal(yuxiDef.seedStationId,byName('玉溪'));
const [yuxi]=resolve(data,[yuxiDef]);
assert.equal(yuxi.errors.length,0,`Yuxi division: ${yuxi.errors.join('; ')}`);
assert.equal(yuxi.stationIds.size,24);
assert.equal(yuxi.edgeIds.size,23);
assert.equal(yuxi.boundaries.length,3);
const expectedYuxiSides=new Map([
  ['conventional:kunmo_02|kunmo_jinningdong',['玉溪','晋宁东']],
  ['conventional:nankun_mile|yumi_huaning',['华宁','弥勒']],
  ['high_speed:mimeng_zhuyuan|nankun_mile',['竹园','弥勒']]
]);
for(const b of yuxi.boundaries) {
  assert.equal(data.stations.find(s=>s.id===b.insideId).name,expectedYuxiSides.get(b.edgeId)[0]);
  assert.equal(data.stations.find(s=>s.id===b.outsideId).name,expectedYuxiSides.get(b.edgeId)[1]);
}
for(const other of resolve(data,defs).filter(div=>div.id!=='yuxi')) {
  assert.equal([...yuxi.stationIds].filter(id=>other.stationIds.has(id)).length,0,`Yuxi overlaps ${other.name}`);
}
assert.equal(JSON.stringify(data),before,'ownership must not change physical connections');
const sample={stations:[{id:'a',lat:0,lon:0},{id:'b',lat:0,lon:1},{id:'c',lat:0,lon:2},{id:'d',lat:0,lon:-1},{id:'e',lat:0,lon:-2}],connections:[
  {id:'ab',from:'a',to:'b',type:'high_speed'},{id:'bc',from:'b',to:'c',type:'high_speed'},
  {id:'ad',from:'a',to:'d',type:'conventional'},{id:'de',from:'d',to:'e',type:'conventional'}]};
const [measured]=resolve(sample,[{id:'sample',seedStationId:'a',boundaryEdgeIds:['bc','de']}]);
const expectedKm=6371.0088*Math.PI/180*1.5;
assert(Math.abs(measured.lengthKm.high_speed-expectedKm)<1e-9,'high speed includes one full segment and one half');
assert(Math.abs(measured.lengthKm.conventional-expectedKm)<1e-9,'conventional measured independently, with only inside half');
const bypass={...data,connections:[...data.connections,{id:'test-bypass',from:byName('佳木斯'),to:byName('哈尔滨'),type:'high_speed'}]};
assert(resolve(bypass,defs)[0].errors.length>0,'a bypass must invalidate the boundary');
assert(resolve(data,[{...defs[0],boundaryEdgeIds:['missing']}])[0].errors.length>0);
const overlapping=resolve(data,[...defs,{...defs[0],id:'duplicate'}]);
assert(overlapping[0].errors.length>0&&overlapping.at(-1).errors.length>0,'overlapping divisions must be reported');
console.log('PASS: Jiamusi 33/32, Mudanjiang 18/17, Chifeng 27/25, Zhangjiakou 22/20, Beijing 48/45, Tangshan 13/12, Tianjin 23/23, Xiong’an 17/17, Shijiazhuang 29/28, Datong 12/11, Taiyuan 23/22, Changzhi 11/9, Houma 15/14, Jining 12/11, Hohhot 8/7, Baotou 20/19, Yinchuan 12/11, Zhongwei 11/10, Xi’an 48/48, Baoji 12/11, Ankang 12/11, Suide 7/6, Lanzhou 38/37, Pingliang 17/16, Wuwei 9/7, Zhangye 20/18, Xining 12/11, Golmud 20/19, Hami 5/4, Urumqi 10/8, Kuitun 19/18, Korla 17/16, Kashgar 13/12, Lhasa 33/33, Chengdu 86/89, Chongqing 39/41, Guangyuan 17/15, Dazhou 10/8, Wanzhou 10/9, Yibin 24/23, Guiyang 31/31, Liupanshui 18/17, Kunming 30/30, Dali 22/21, and Yuxi 24/23; all boundaries close without overlap.');
