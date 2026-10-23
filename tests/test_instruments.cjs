const test=require('node:test'),assert=require('node:assert/strict');
const {summarize, toVCD}=require('../boards/instruments.cjs');
test('independent edge measurements recover 50Hz and 1500us high pulse',()=>{
 const edges=[{cycle:16000,pin:'D9',value:true},{cycle:40000,pin:'D9',value:false},{cycle:336000,pin:'D9',value:true},{cycle:360000,pin:'D9',value:false}];
 const m=summarize(edges,640000)['D9'];assert.equal(m.highUs,1500);assert.equal(m.frequencyHz,50);assert.equal(m.dutyPercent,7.5);
});
test('VCD carries measured cycle timestamps rather than illustrative samples',()=>{const v=toVCD([{cycle:16,pin:'D2',value:true},{cycle:32,pin:'D2',value:false}],640);assert.match(v,/\$timescale 1ns/);assert.match(v,/#1000/);assert.match(v,/#2000/);assert.match(v,/D2/);});
test('overflowed capture stops VCD and observed duration at recorded prefix',()=>{
 const {run}=require('../boards/runner.cjs');const bytes=Buffer.from([0x21,0x9a,0x29,0x9a,0x29,0x98,0xfd,0xcf]);const row=[bytes.length,0,0,0,...bytes];row.push((-row.reduce((a,b)=>a+b,0))&255);const hex=':'+Buffer.from(row).toString('hex')+'\n:00000001FF';const r=run({board:'arduino-uno',hex,durationMs:10});assert.equal(r.evidence.traceTruncated,true);const end=r.logic.at(-1).cycle;assert.equal(r.evidence.capturedCycles,end);assert.equal(r.instruments.D9.observedMs,end/16000);assert.equal(r.vcd.trim().split('\n').at(-1),'#'+Math.round(end/16e6*1e9));
});
