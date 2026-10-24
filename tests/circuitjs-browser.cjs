const {chromium}=require('playwright'),assert=require('node:assert/strict'),{spawn}=require('node:child_process'),fs=require('node:fs'),path=require('node:path');
const server=spawn('python',['server.py'],{stdio:'ignore'});let browser;process.on('exit',()=>server.kill());
const pause=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{try{
 for(let i=0;i<80;i++){try{await fetch('http://127.0.0.1:8765');break}catch{await pause(100)}}
 browser=await chromium.launch({headless:true,args:['--no-sandbox']});const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[],external=[],parseErrors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(/unrecognized dump type|exception while undumping|unknown element/i.test(m.text()))parseErrors.push(m.text())});page.on('request',r=>{if(!r.url().startsWith('http://127.0.0.1:8765/')&&!r.url().startsWith('data:'))external.push(r.url())});
 await page.goto('http://127.0.0.1:8765/circuitjs/circuitjs.html');for(let i=0;i<100;i++){if(await page.evaluate(()=>!!window.CircuitJS1))break;await pause(50)}
 assert.ok(await page.evaluate(()=>!!window.CircuitJS1));
 const divider='$ 1 0.000005 10.20027730826997 50 5 43\nv 80 240 80 80 0 0 40 10 0 0 0.5\nr 80 80 240 80 0 1000\nr 240 80 240 240 0 1000\nw 240 240 80 240 0\ng 80 240 80 272 0\n';
 await page.evaluate(c=>{CircuitJS1.importCircuit(c,false);CircuitJS1.setSimRunning(true)},divider);await pause(250);
 const reading=await page.evaluate(()=>({time:CircuitJS1.getTime(),r:CircuitJS1.getElements().filter(e=>e.getType()==='ResistorElm').map(e=>({v:e.getVoltageDiff(),i:e.getCurrent()})),exported:CircuitJS1.exportCircuit()}));assert.ok(reading.time>0);assert.equal(reading.r.length,2);for(const r of reading.r){assert.ok(Math.abs(Math.abs(r.v)-5)<1e-6);assert.ok(Math.abs(Math.abs(r.i)-.005)<1e-9)}assert.match(reading.exported,/1000/);
 await page.evaluate(()=>CircuitJS1.setSimRunning(false));assert.equal(await page.evaluate(()=>CircuitJS1.isRunning()),false);
 await page.screenshot({path:'screenshots/circuitjs-integrated.png',fullPage:true});
 const stoppedTime=await page.evaluate(()=>CircuitJS1.getTime());await pause(70);assert.equal(await page.evaluate(()=>CircuitJS1.getTime()),stoppedTime,'Stopped simulator must not advance');
 const rcChecks=[];
 for(const resistance of [1000,4700]){
  const rc=divider.replace('0.000005','0.0000005').replace('r 80 80 240 80 0 1000',`r 80 80 240 80 0 ${resistance}`).replace('r 240 80 240 240 0 1000','c 240 80 240 240 0 0.000001 0');
  const tau=resistance*.000001;
  await page.evaluate(({c,tau})=>{CircuitJS1.importCircuit(c,false);window.__rcSample=null;CircuitJS1.ontimestep=api=>{if(api.getTime()>=tau/2){window.__rcSample={time:api.getTime(),voltage:api.getElements().find(e=>e.getType()==='CapacitorElm').getVoltageDiff()};api.setSimRunning(false);delete api.ontimestep;}};CircuitJS1.setSimRunning(true)},{c:rc,tau});
  let sample;for(let i=0;i<400;i++){await pause(10);sample=await page.evaluate(()=>window.__rcSample);if(sample)break}
  assert.ok(sample,'RC simulation must actually advance');assert.ok(sample.time/tau>=.49&&sample.time/tau<=.51,'Measure inside the transient, not after settling');const expected=10*(1-Math.exp(-sample.time/tau));assert.ok(Math.abs(sample.voltage-expected)<.015,JSON.stringify({resistance,...sample,expected}));rcChecks.push({resistance,...sample,timeConstant:tau,expected,absoluteError:Math.abs(sample.voltage-expected),tolerance:.015});
 }
 fs.writeFileSync('evidence/circuitjs-runtime.json',JSON.stringify({scope:'Independent time-domain RC exponential and stopped-clock checks in the real browser engine.',rcChecks},null,2)+'\n');

 const circuits=fs.readdirSync('web/circuitjs/circuitjs/circuits').filter(n=>n.endsWith('.txt'));const results=[];
 for(const name of circuits){const text=fs.readFileSync(path.join('web/circuitjs/circuitjs/circuits',name),'utf8');const before=errors.length,parseBefore=parseErrors.length;let diagnostic=null;try{await page.evaluate(c=>{CircuitJS1.importCircuit(c,false);CircuitJS1.setSimRunning(true)},text);await pause(35);const state=await page.evaluate(()=>({time:CircuitJS1.getTime(),running:CircuitJS1.isRunning(),elements:CircuitJS1.getElements().length,finite:CircuitJS1.getElements().filter(e=>e.getPostCount()>0).every(e=>Number.isFinite(e.getCurrent())&&Number.isFinite(e.getVoltageDiff()))}));results.push({name,...state,parseErrors:parseErrors.slice(parseBefore),status:parseErrors.length===parseBefore&&errors.length===before&&state.finite&&(state.elements>0||name==='blank.txt')?'loaded':'needs-review'});}catch(e){diagnostic=e.message;results.push({name,status:'needs-review',diagnostic})}}
 fs.mkdirSync('evidence',{recursive:true});fs.writeFileSync('evidence/circuitjs-catalog.json',JSON.stringify({scope:'Import and finite-output smoke checks only. Not numerical validation of every example or interactive tool.',referenceDivider:reading.r,examples:results,needsReview:results.filter(r=>r.status!=='loaded')},null,2)+'\n');
 assert.deepEqual(external,[],'Engine must work without external requests');assert.deepEqual(errors,[],'Upstream example runtime exceptions');assert.deepEqual(parseErrors,[],'No dropped/unrecognized upstream elements');assert.equal(results.filter(r=>r.status!=='loaded').length,0,'Catalog smoke checks: see evidence/circuitjs-catalog.json');
 assert.equal((await page.request.get('http://127.0.0.1:8765/circuitjs/../../server.py')).status(),404);console.log(`PASS CircuitJS: 10V divider = 5V / 5mA, start/stop/export, ${results.length} local examples import with finite outputs; no external network`);
 }finally{if(browser)await browser.close();server.kill()}})().catch(e=>{console.error(e);process.exitCode=1});
