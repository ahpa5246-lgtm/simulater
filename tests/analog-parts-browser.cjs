const {chromium}=require('playwright');
const assert=require('node:assert/strict'),fs=require('node:fs');
const {spawn}=require('node:child_process');
const server=spawn('python',['server.py'],{stdio:'ignore'});let browser;
process.on('exit',()=>server.kill());
async function run(page){await page.locator('#run').click();for(let i=0;i<200;i++){const text=await page.locator('#status').innerText();if(text.includes('Simulation complete'))return;if(await page.locator('#status-dot').getAttribute('class')==='error')throw Error(text);await new Promise(r=>setTimeout(r,50));}throw Error('Simulation timed out');}
(async()=>{
 for(let i=0;i<80;i++){try{await fetch('http://127.0.0.1:8765');break;}catch{await new Promise(r=>setTimeout(r,100));}}
 browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1536,height:1000}}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));await page.goto('http://127.0.0.1:8765');
 await page.locator('#component-list button').first().waitFor();assert.equal(await page.locator('#component-list button').count(),39);
 await page.locator('#search').fill('N-channel MOSFET');await page.getByRole('button',{name:'Place N-channel MOSFET',exact:true}).click();
 await page.locator('#schematic').click({position:{x:250,y:200}});
 assert.equal(await page.locator('[data-cid="M1"] [data-pin]').count(),4);
 assert.ok(await page.locator('#prop-c').isVisible());assert.ok(await page.locator('#prop-d').isVisible());
 await page.locator('#wire-tool').click();await page.locator('[data-pin="M1:c"]').click();await page.locator('[data-pin="M1:d"]').click();
 assert.equal(await page.locator('#prop-c').inputValue(),await page.locator('#prop-d').inputValue());
 await page.locator('#select-tool').click();await page.locator('#rotate').click();
 assert.equal(await page.locator('[data-cid="M1"] [data-pin]').count(),4);
 const saving=page.waitForEvent('download');await page.locator('#save').click();const saved=await saving;
 const contents=fs.readFileSync(await saved.path());const p=JSON.parse(contents);const mos=p.components.find(c=>c.type==='M');assert.equal(mos.part,'nmos');assert.equal(mos.rotation,90);
 await page.locator('#delete').click();assert.equal(await page.locator('[data-cid="M1"]').count(),0);await page.locator('#undo').click();assert.equal(await page.locator('[data-cid="M1"]').count(),1);
 await page.locator('#file-input').setInputFiles({name:'roundtrip.mina',mimeType:'application/json',buffer:contents});assert.match(await page.locator('#status').innerText(),/opened/);
 for(const [id,expected] of [['npn',.1],['opamp',1],['and',0],['bridge',3.6]]){
  await page.selectOption('#example','ref:'+id);await run(page);
  const out=await page.locator('#measurements').innerText();assert.match(out,/V\(out\)/);
  if(id==='opamp')assert.match(out,/1\.000 V/);
 }
 const exportEvent=page.waitForEvent('download');await page.locator('#export').click();const exp=await exportEvent;
 const deck=fs.readFileSync(await exp.path(),'utf8');assert.match(deck,/Xdut supply 0 out negative MINA_BRIDGE/);assert.match(deck,/\.subckt MINA_BRIDGE/);assert.match(deck,/\.tran/);
 await page.selectOption('#example','ref:opamp');await run(page);await page.screenshot({path:'screenshots/expanded-opamp.png',fullPage:true});
 const bad=JSON.parse(JSON.stringify(p));bad.components.find(c=>c.type==='M').part='npn';
 await page.locator('#file-input').setInputFiles({name:'bad.mina',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(bad))});assert.match(await page.locator('#status').innerText(),/Invalid/);
 for(const id of ['diode','dc-source','ac-source','capacitor']){
  await page.locator('#open-parts').click();await page.locator(`[data-part="${id}"] button`).click();assert.equal(await page.locator('#mode-label').innerText(),'PLACE MODE');await page.keyboard.press('Escape');
 }
 const sine={version:1,name:'Imported sine source',components:[{id:'V1',type:'V',part:'v-sine',value:5,a:'out',b:'0',x:240,y:240,rotation:0}],wires:[],analysis:{stop:.002,step:.00001}};
 await page.locator('#file-input').setInputFiles({name:'sine.mina',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(sine))});
 await page.locator('[data-cid="V1"]').click();assert.equal(await page.locator('#properties select').inputValue(),'sine');await run(page);
 sine.components[0].part=null;await page.locator('#file-input').setInputFiles({name:'null.mina',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(sine))});assert.match(await page.locator('#status').innerText(),/Invalid/);
 assert.deepEqual(errors,[]);console.log('PASS expanded analog browser: 39 palette presets, 4-terminal placement/wiring/rotation, undo, import/export and real solver examples');
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();server.kill();});
