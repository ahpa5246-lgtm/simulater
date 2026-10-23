const {chromium}=require('playwright'),assert=require('node:assert/strict'),{spawn}=require('node:child_process'),fs=require('node:fs');
const server=spawn('python',['server.py'],{stdio:'ignore'});let browser;
async function waitText(page,pattern){for(let i=0;i<450;i++){const text=await page.locator('#project-status').innerText();if(pattern.test(text))return;await new Promise(r=>setTimeout(r,100));}throw Error(await page.locator('#project-status').innerText());}
async function completed(page){await waitText(page,/Execution complete|Error|conflict|Unsupported|must be|failed/i);}
(async()=>{
 for(let i=0;i<100;i++){try{await fetch('http://127.0.0.1:8765');break;}catch{await new Promise(r=>setTimeout(r,100));}}
 browser=await chromium.launch({args:['--no-sandbox']});const page=await browser.newPage({viewport:{width:1440,height:1050}}),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto('http://127.0.0.1:8765/lab.html');await waitText(page,/^Ready\./);
 assert.equal(await page.locator('.device-row').count(),6);assert.match(await page.locator('#audit-summary').innerText(),/363 catalogue entries/);
 await page.locator('#execute-project').click();await completed(page);assert.match(await page.locator('#project-status').innerText(),/Execution complete/);assert.match(await page.locator('#project-serial').innerText(),/1200,25,160,0,819/);assert.match(await page.locator('#output-devices').innerText(),/HIGH/);assert.match(await page.locator('#project-evidence').textContent(),/stimulus/);assert.ok(await page.locator('#project-waveform path').count());
 const saving=page.waitForEvent('download');await page.locator('#export-result').click();let d=await saving;const result=JSON.parse(fs.readFileSync(await d.path()));assert.equal(result.i2cDevices.length,3);assert.equal(result.outputs[0].high,true);assert.ok(result.evidence.firmwareSha256);
 const first=page.locator('.device-row').first();await first.getByLabel(/Connected/).uncheck();assert.equal(await page.locator('#export-result').isDisabled(),true);assert.match(await page.locator('#project-serial').innerText(),/Configuration changed/);
 await page.reload();await waitText(page,/^Ready\./);assert.equal(await page.locator('.device-row').first().getByLabel(/Connected/).isChecked(),false);
 await page.selectOption('#project-example','adc');await page.locator('#load-example').click();await page.locator('#execute-project').click();await completed(page);assert.match(await page.locator('#project-serial').innerText(),/ADC: 8000/);
 await page.locator('#add-model').selectOption('ads1115');await page.locator('#add-device').click();await page.locator('#execute-project').click();await completed(page);assert.match(await page.locator('#project-status').innerText(),/address conflict/i);
 await page.selectOption('#project-example','multi');await page.locator('#load-example').click();await page.locator('#execute-project').click();await completed(page);
 await page.screenshot({path:'screenshots/practical-simulation.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+2));
 await page.locator('#audit-search').fill('ADS1115');assert.match(await page.locator('#audit-records').innerText(),/Model available: ads1115/);
 assert.deepEqual(errors,[]);console.log('PASS practical browser: real multi-device firmware, scheduled input feedback, result export, invalidation, persistence, ADS1115 conversion, conflict rejection, catalogue audit and narrow-screen layout');
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();server.kill();});
