// Game forecast generator. The research page already holds the full scenario.
// A production game must run this behind its server-side future-data boundary.
((root,factory)=>{
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  else root.RAILWAY_FORECAST=api;
})(typeof window==='undefined'?globalThis:window,()=>{
  'use strict';
  const clamp=(value,lo,hi)=>Math.max(lo,Math.min(hi,value));
  // Game quality score -> whole-period mean absolute percentage error.
  // Interpolate between knots; different horizons have different tolerances.
  const scales=[
    {score:0,2:25,5:50,10:80},
    {score:50,2:12,5:25,10:40},
    {score:60,2:8,5:17,10:28},
    {score:70,2:5,5:10,10:17},
    {score:80,2:2.5,5:5,10:8.5},
    {score:90,2:1.2,5:2.5,10:4.5},
    {score:95,2:.6,5:1.2,10:2.2},
    {score:100,2:0,5:0,10:0}
  ];
  function errorForScore(score,horizon) {
    if(![2,5,10].includes(horizon)||!Number.isFinite(score)||score<0||score>100)throw new Error('预测评分设置无效');
    for(let i=1;i<scales.length;i++)if(score<=scales[i].score) {
      const a=scales[i-1],b=scales[i],fraction=(score-a.score)/(b.score-a.score);
      return a[horizon]+fraction*(b[horizon]-a[horizon]);
    }
  }
  function scoreForError(error,horizon) {
    if(![2,5,10].includes(horizon)||!Number.isFinite(error)||error<0)throw new Error('预测偏差无效');
    if(error>=scales[0][horizon])return 0;
    for(let i=1;i<scales.length;i++)if(error>=scales[i][horizon]) {
      const a=scales[i-1],b=scales[i],fraction=(a[horizon]-error)/(a[horizon]-b[horizon]);
      return a.score+fraction*(b.score-a.score);
    }
  }
  function meanErrorPct(actual,predicted) {
    if(actual.length!==predicted.length||actual.length===0)throw new Error('预测与实际数据长度不一致');
    const error=actual.reduce((sum,value,i)=>{
      if(!Number.isFinite(value)||value<=0||!Number.isFinite(predicted[i])||predicted[i]<=0)throw new Error('指数必须为正数');
      return sum+Math.abs(predicted[i]-value)/value;
    },0)/actual.length;
    return error*100;
  }
  function accuracy(actual,predicted) {return scoreForError(meanErrorPct(actual,predicted),actual.length);}
  function generate({history,future,expectedScore,random=()=>crypto.getRandomValues(new Uint32Array(1))[0]/4294967296}) {
    if(![2,5,10].includes(future.length)||!history.length||!Number.isFinite(expectedScore)||expectedScore<0||expectedScore>100)throw new Error('预测设置无效');
    if([...history,...future].some(value=>!Number.isFinite(value)||value<=0))throw new Error('指数数据无效');
    if(expectedScore===100)return {values:[...future],expectedScore,actualScore:100,meanErrorPct:0};
    const recent=history.slice(-6),anchor=recent.at(-1),horizon=future.length;
    const trend=recent.length>1?clamp(Math.log(anchor/recent[0])/(recent.length-1),-.08,.08):0;
    // A fresh persistent bias and smooth error shape define this forecast's
    // central estimate; repeated UI draws never reroll this forecast.
    const target=clamp(expectedScore+(random()*2-1)*4,.1,99.9),targetError=errorForScore(target,horizon)/100;
    const bias=random()*2-1,slope=random()*2-1,phase=random()*Math.PI*2;
    let drift=0;
    let errors=future.map((value,i)=>{
      const fraction=(i+1)/horizon;
      drift=.7*drift+.3*(random()*2-1);
      const extrapolation=Math.log(anchor)+trend*(i+1)-Math.log(value);
      const judgement=Math.sqrt(fraction)*(bias+.45*Math.sin(phase+fraction*Math.PI*1.5)+.35*slope*fraction+.18*drift);
      return (1-expectedScore/100)*extrapolation+(.12+.018*horizon)*judgement;
    });
    const magnitude=Math.max(...errors.map(Math.abs),.000001);
    errors=errors.map(value=>Math.sign(value||1)*Math.max(.06,Math.abs(value/magnitude)));
    // Bound each year's error so a good average score cannot conceal one
    // wildly wrong year. Keep indices positive even for low-quality reports.
    const annualLimit=2.4*targetError;
    const relativeError=(scale,error)=>clamp(Math.expm1(clamp(scale*error,-32,32)),-Math.min(.95,annualLimit),annualLimit);
    const errorAt=scale=>errors.reduce((sum,error)=>sum+Math.abs(relativeError(scale,error)),0)/horizon;
    let lo=0,hi=32;
    for(let i=0;i<55;i++) {const mid=(lo+hi)/2;if(errorAt(mid)<targetError)lo=mid;else hi=mid;}
    const scale=(lo+hi)/2;
    const values=future.map((value,i)=>value*(1+relativeError(scale,errors[i])));
    return {values,expectedScore,actualScore:accuracy(future,values),meanErrorPct:meanErrorPct(future,values)};
  }
  return {generate,accuracy,meanErrorPct,errorForScore,scoreForError};
});
