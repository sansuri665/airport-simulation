const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const context={window:{}};
for(const file of ['railway-data.js','railway-divisions.js']) vm.runInNewContext(fs.readFileSync(path.join(__dirname,file),'utf8'),context);
const {RAILWAY_DATA:data,RAILWAY_DIVISIONS:defs,resolveRailwayDivisions:resolve}=context.window;
const before=JSON.stringify(data);
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
assert(overlapping[0].errors.length>0&&overlapping[2].errors.length>0,'overlapping divisions must be reported');
console.log('PASS: Jiamusi 33 stations/32 internal connections; Mudanjiang 18/17; both have 3 closed midpoint boundaries, no overlap, and physical network unchanged.');
