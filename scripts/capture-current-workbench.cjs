'use strict';
const {chromium}=require('playwright');
const {spawn}=require('node:child_process');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const OUTPUT='screenshots/current';
fs.mkdirSync(OUTPUT,{recursive:true});
const server=spawn('python',['server.py'],{stdio:'inherit'});
const manifest=[];
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function ready(){for(let i=0;i<160;i++){try{let r=await fetch('http://127.0.0.1:8765');if(r.ok)return;}catch{}await sleep(250);}throw Error('Local server never started');}
async function waitFor(page,id,fragment){
 await page.waitForFunction(([id,fragment])=>document.getElementById(id)?.textContent.includes(fragment),[id,fragment],{timeout:90000});
}
async function capture(page,file,description,selector=null){
 await page.waitForTimeout(200);
 const full=path.join(OUTPUT,file);
 if(selector)await page.locator(selector).screenshot({path:full,timeout:60000,animations:'disabled'});
 else await page.screenshot({path:full,fullPage:true,timeout:60000,animations:'disabled'});
 const size=fs.statSync(full).size;assert(size>12000,'Screenshot is abnormally small: '+file);
 manifest.push({file,description,bytes:size,at:new Date().toISOString(),url:page.url()});
 console.log('CAPTURE '+file+' ('+size+' bytes) '+description);
}
async function run(){
 await ready();const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1440,height:960},deviceScaleFactor:1,acceptDownloads:true,bypassCSP:true});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 try {
  await page.goto('http://127.0.0.1:8765/lab.html');
  await waitFor(page,'project-status','Ready.');
  await page.selectOption('#project-example','imu');await page.locator('#load-example').click();
  assert.equal(await page.locator('.device-row').count(),2);
  await page.locator('#execute-project').click();await waitFor(page,'project-status','Execution complete');
  assert.match(await page.locator('#project-serial').innerText(),/AX:8192 AZ:16384 GY:11790/);
  await capture(page,'01-mpu6050-live-firmware.png','MPU-6050 registers read by compiled Arduino Wire firmware');

  await page.getByLabel('imu Acceleration X, Y, Z (g)').fill('0, 0.5, 1');
  await page.getByLabel('imu Acceleration X, Y, Z (g)').press('Tab');
  await page.locator('#execute-project').click();await waitFor(page,'project-status','Execution complete');
  assert.match(await page.locator('#project-serial').innerText(),/AX:0 AZ:16384 GY:11790/);
  await capture(page,'02-mpu6050-updated-motion.png','Changed IMU stimulus; fresh actual firmware output');

  await page.selectOption('#project-example','multi');await page.locator('#load-example').click();
  await page.locator('#execute-project').click();await waitFor(page,'project-status','Execution complete');
  assert.match(await page.locator('#project-serial').innerText(),/1200,25,160,0,819/);
  await capture(page,'03-multiple-connected-sensors.png','Multi-device I2C and scheduled GPIO/ADC simulation');

  await page.goto('http://127.0.0.1:8765/boards.html');
  await page.locator('#use-bundled').click();await waitFor(page,'board-status','Bundled firmware ready');
  await page.locator('#run-board').click();await waitFor(page,'board-status','Execution complete');
  assert.match(await page.locator('#serial-output').innerText(),/ADC:/);
  await capture(page,'04-board-firmware-workspace.png','Arduino board, connected sensor and firmware studio');
  await page.selectOption('#sketch-example','ultrasonic');
  await page.locator('#sensor-value').fill('100');
  await page.locator('#use-bundled').click();await waitFor(page,'board-status','Bundled firmware ready');
  await page.locator('#run-board').click();await waitFor(page,'board-status','Execution complete');
  assert.match(await page.locator('#serial-output').innerText(),/5800/);
  await capture(page,'05-oscilloscope-logic-analyser.png','Logic analyser and live HC-SR04 firmware pulse widths','.instrument-workspace');

  await page.locator('#open-upstream').click();
  await page.locator('#community-parts .part-card').first().waitFor({timeout:30000});
  await capture(page,'06-component-catalogue.png','Current open-source component library and search dialogue');

  await page.goto('http://127.0.0.1:8765/');
  await page.selectOption('#example','rc');
  await page.getByRole('button',{name:'Run simulation'}).click();
  await waitFor(page,'status','complete');
  assert.ok(await page.locator('#plot path').count()>0);
  await capture(page,'07-ngspice-analog-workbench.png','Actual ngspice RC circuit schematic and waveform');

  await page.setViewportSize({width:390,height:844});
  await page.goto('http://127.0.0.1:8765/lab.html');
  await waitFor(page,'project-status','Ready.');
  await page.selectOption('#project-example','imu');await page.locator('#load-example').click();
  await capture(page,'08-mobile-layout.png','Current mobile-width responsive firmware workspace');
  assert.deepEqual(errors,[],'Browser JS exceptions: '+errors.join('; '));
  fs.writeFileSync(path.join(OUTPUT,'capture-manifest.json'),JSON.stringify({sourceCommit:process.env.GITHUB_SHA||'unknown',generated:new Date().toISOString(),screenshots:manifest},null,2));
  console.log('PASS captured '+manifest.length+' genuine browser states without page errors');
 } finally {await browser.close();}
}
run().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>server.kill());
