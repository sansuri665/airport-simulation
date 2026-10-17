'use strict';
const assert=require('node:assert/strict');
const {generate,accuracy,meanErrorPct,errorForScore,scoreForError}=require('./economy-forecast.js');
const randomFor=seed=>()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};

assert.equal(meanErrorPct([100,200],[110,180]),10);
assert.equal(accuracy([100,200],[102.5,195]),80);
assert.equal(accuracy(Array(5).fill(100),Array(5).fill(105)),80);
assert.ok(Math.abs(accuracy(Array(10).fill(100),Array(10).fill(108.5))-80)<1e-10);
assert.equal(accuracy([100,100],[250,250]),0);
for(const horizon of [2,5,10])for(let score=0;score<=100;score++) {
  assert.ok(Math.abs(scoreForError(errorForScore(score,horizon),horizon)-score)<1e-10);
  if(score>0)assert.ok(errorForScore(score,horizon)<errorForScore(score-1,horizon));
}
assert.equal(errorForScore(80,2),2.5);
assert.equal(errorForScore(80,5),5);
assert.equal(errorForScore(80,10),8.5);
assert.throws(()=>generate({history:[100],future:[101],expectedScore:80}));
assert.throws(()=>generate({history:[100],future:[101,102],expectedScore:101}));
const perfectFuture=[103,105,91,94,99];
const perfect=generate({history:[100],future:perfectFuture,expectedScore:100,random:()=>{throw new Error('Perfect forecasts must not draw randomness');}});
assert.deepEqual(perfect.values,perfectFuture);
assert.notEqual(perfect.values,perfectFuture);
assert.equal(perfect.actualScore,100);

for(const horizon of [2,5,10]) {
  const futures=[
    Array.from({length:horizon},()=>100),
    Array.from({length:horizon},(_,i)=>100*Math.exp(.05*(i+1))),
    Array.from({length:horizon},(_,i)=>100*Math.exp(-.06*(i+1))),
    Array.from({length:horizon},(_,i)=>i<horizon/2?90-i*4:70+(i-horizon/2)*7)
  ];
  for(const future of futures)for(const expectedScore of [0,1,20,50,80,99,100]) {
    const result=generate({history:[90,94,96,100],future,expectedScore,random:randomFor(83)});
    assert.equal(result.values.length,horizon);
    assert.ok(result.values.every(value=>Number.isFinite(value)&&value>0));
    assert.ok(Math.abs(result.actualScore-expectedScore)<=4.1,`${horizon} years / target ${expectedScore}: ${result.actualScore}`);
    assert.equal(result.actualScore,accuracy(future,result.values));
    assert.ok(Math.abs(result.meanErrorPct-meanErrorPct(future,result.values))<1e-10);
    const worst=Math.max(...result.values.map((value,i)=>100*Math.abs(value/future[i]-1)));
    assert.ok(worst<=2.4*result.meanErrorPct+1e-8);
    if(expectedScore===100)assert.deepEqual(result.values,future);
  }
}
const settings={history:[100,101,102],future:[105,108,92,94,99],expectedScore:80};
const first=generate({...settings,random:randomFor(1)});
const second=generate({...settings,random:randomFor(2)});
assert.notDeepEqual(first.values,second.values);
assert.ok(Math.abs(first.actualScore-80)<=4.1&&Math.abs(second.actualScore-80)<=4.1);
console.log('Forecast checks passed: score definition, 2/5/10-year bounds, near-target errors, positive values and varied predictions.');
