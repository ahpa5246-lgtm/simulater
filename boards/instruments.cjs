// Instruments consume CPU-cycle edges; they never create signal samples.
const CLOCK=16e6;
function summarize(edges,totalCycles,clockHz=CLOCK){
 const result={};
 for(const pin of [...new Set(edges.map(e=>e.pin))]){
  const events=edges.filter(e=>e.pin===pin);let rise=null;const highs=[],rises=[];
  for(const event of events){if(event.value){rise=event.cycle;rises.push(rise);}else if(rise!==null){highs.push(event.cycle-rise);rise=null;}}
  const periods=rises.slice(1).map((x,i)=>x-rises[i]);const mean=a=>a.length?a.reduce((s,x)=>s+x,0)/a.length:null;
  const period=mean(periods),high=mean(highs);
  result[pin]={edges:events.length,highUs:high===null?null:high/clockHz*1e6,periodUs:period===null?null:period/clockHz*1e6,frequencyHz:period?clockHz/period:null,dutyPercent:period&&high!==null?100*high/period:null,completePulses:highs.length,observedMs:totalCycles/clockHz*1000};
 }
 return result;
}
function toVCD(edges,totalCycles,clockHz=CLOCK){
 const channels=Array.from({length:14},(_,i)=>'D'+i),symbols=Object.fromEntries(channels.map((p,i)=>[p,String.fromCharCode(33+i)]));
 const lines=['$version Mina GPIO cycle trace $end','$timescale 1ns $end','$scope module arduino $end',...channels.map(pin=>`$var wire 1 ${symbols[pin]} ${pin} $end`),'$upscope $end','$enddefinitions $end','#0',...channels.map(pin=>'0'+symbols[pin])];
 let last=-1;for(const edge of edges){if(!(edge.pin in symbols))continue;const time=Math.round(edge.cycle/clockHz*1e9);if(time!==last){lines.push('#'+time);last=time;}lines.push((edge.value?'1':'0')+symbols[edge.pin]);}lines.push('#'+Math.round(totalCycles/clockHz*1e9));return lines.join('\n')+'\n';
}
module.exports={summarize,toVCD};
