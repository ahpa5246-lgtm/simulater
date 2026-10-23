const {chromium}=require(process.env.PLAYWRIGHT_PATH||'playwright');
const assert=require('node:assert/strict'),{spawn}=require('node:child_process');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'mina-board-ui-'));
const server=spawn('python',['server.py'],{stdio:'ignore',env:{...process.env,MINA_LIBRARY_DIR:path.join(temp,'libraries')}});
let browser;process.on('exit',()=>{server.kill();fs.rmSync(temp,{recursive:true,force:true});});
async function waitText(page,id,needle){for(let i=0;i<300;i++){const t=await page.locator('#'+id).innerText();if(t.includes(needle))return;if((await page.locator('#build-output').getAttribute('class')||'').includes('error'))throw Error(t+' / '+await page.locator('#build-output').innerText());await new Promise(r=>setTimeout(r,100));}throw Error('Timed out: '+await page.locator('#'+id).innerText());}
(async()=>{for(let i=0;i<60;i++){try{await fetch('http://127.0.0.1:8765');break;}catch{await new Promise(r=>setTimeout(r,100));}}
browser=await chromium.launch({headless:true,args:['--no-sandbox']});const page=await browser.newPage({viewport:{width:1536,height:1080},deviceScaleFactor:1});const errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://127.0.0.1:8765/boards.html');await page.locator('#use-bundled').click();await waitText(page,'board-status','Bundled firmware ready');await page.locator('#run-board').click();await waitText(page,'board-status','Execution complete');assert.match(await page.locator('#serial-output').innerText(),/ADC: 51/);
await page.locator('#sensor-value').fill('100');await page.locator('#run-board').click();await waitText(page,'board-status','Execution complete');assert.match(await page.locator('#serial-output').innerText(),/ADC: 204/);assert.equal(await page.locator('#led-label').innerText(),'HIGH');
await page.selectOption('#sketch-example','i2c');await page.locator('#sensor-value').fill('30');await page.locator('#run-board').click();await waitText(page,'board-status','Execution complete');assert.match(await page.locator('#serial-output').innerText(),/Temperature: 30.0 C/);assert.match(await page.locator('#bus-output').innerText(),/ADDRESS READ/);
await page.getByRole('button',{name:'Library manager'}).click();assert.ok(await page.locator('#library-dialog').isVisible());
const zipPath=path.join(temp,'DoubleADC.zip');const code="import zipfile,sys\nwith zipfile.ZipFile(sys.argv[1],'w') as z:\n z.writestr('DoubleADC/library.properties','name=DoubleADC\\nversion=1.0.0\\nlicense=MIT\\n')\n z.writestr('DoubleADC/src/DoubleADC.h','#pragma once\\ninline int doubleADC(int x){return x*2;}\\n')";
const {spawnSync}=require('node:child_process');assert.equal(spawnSync('python',['-c',code,zipPath]).status,0);
await page.locator('#library-file').setInputFiles(zipPath);await waitText(page,'library-message','Installed DoubleADC');assert.match(await page.locator('#library-list').innerText(),/DoubleADC/);await page.locator('#libraries-close').click();
await page.locator('#source-editor').fill('#include <DoubleADC.h>\nvoid setup(){Serial.begin(9600);}\nvoid loop(){Serial.println(doubleADC(analogRead(A0)));delay(10);}');await page.selectOption('#sensor-model','lm35');await page.locator('#sensor-value').fill('25');await page.locator('#run-board').click();await waitText(page,'board-status','Execution complete');assert.match(await page.locator('#serial-output').innerText(),/102/);
await page.getByRole('button',{name:/Raspberry Pi Pico/}).click();assert.ok(await page.evaluate(()=>JSON.parse(localStorage.getItem('mina-board-project')).source.includes('doubleADC')),'Pico selection must preserve Arduino source');await page.locator('#run-board').click();await waitText(page,'board-status','Execution complete');assert.ok(Number(await page.locator('#transition-count').innerText())>5);assert.match(await page.locator('#board-status').innerText(),/RP2040js/);
await page.getByRole('button',{name:/Arduino Uno R3/}).click();
await page.evaluate(()=>{window.originalFileText=File.prototype.text;File.prototype.text=function(){return new Promise(resolve=>{window.finishFirmwareRead=resolve;});};});
await page.locator('#firmware-file').setInputFiles({name:'pending.hex',mimeType:'text/plain',buffer:Buffer.from(':00000001FF')});
await page.getByRole('button',{name:/Raspberry Pi Pico/}).click();
await page.evaluate(()=>window.finishFirmwareRead(':00000001FF'));
for(let i=0;i<30;i++){if((await page.locator('#board-status').innerText()).includes('changed during import'))break;await new Promise(r=>setTimeout(r,50));}
assert.match(await page.locator('#board-status').innerText(),/changed during import/);
await page.evaluate(()=>{File.prototype.text=window.originalFileText;});
await page.getByRole('button',{name:/Arduino Uno R3/}).click();await page.selectOption('#sketch-example','analog');await page.locator('#sensor-value').fill('100');await page.locator('#run-board').click();await waitText(page,'board-status','Execution complete');await page.screenshot({path:'screenshots/boards-sensors.png',fullPage:true});
assert.deepEqual(errors,[]);console.log('PASS board browser: ADC response, GPIO output, Wire I2C, library ZIP install and compile, Pico ARM execution, screenshot; no page errors');await browser.close();server.kill();})().catch(async e=>{console.error(e);if(browser)await browser.close();server.kill();process.exit(1)});
