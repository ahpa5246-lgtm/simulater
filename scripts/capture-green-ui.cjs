'use strict';
const {chromium}=require('playwright');
const {spawn}=require('node:child_process');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const folder='screenshots/green-ui';fs.mkdirSync(folder,{recursive:true});
const server=spawn('python',['server.py'],{stdio:'inherit'});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const shots=[];
async function snap(page,file,caption,selector=null){
 await page.waitForTimeout(120);
 if(selector)await page.locator(selector).screenshot({path:path.join(folder,file),animations:'disabled'});
 else await page.screenshot({path:path.join(folder,file),fullPage:true,animations:'disabled'});
 const bytes=fs.statSync(path.join(folder,file)).size;
 assert(bytes>10000,'Empty screenshot '+file);shots.push({file,caption,bytes,url:page.url()});
 console.log('SAVED '+file+' '+bytes);
}
async function main(){
 for(let i=0;i<100;i++){try{if((await fetch('http://127.0.0.1:8765/')).ok)break;}catch{}await sleep(150);}
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const p=await browser.newPage({viewport:{width:1440,height:960},deviceScaleFactor:1,bypassCSP:true});
 const errors=[];p.on('pageerror',e=>errors.push(e.message));
 try{
  await p.goto('http://127.0.0.1:8765/lab.html');
  await p.locator('#add-model option').first().waitFor({state:'attached'});
  assert.equal(await p.locator('link[href="/visual-refresh.css"]').count(),1);
  assert.match(await p.evaluate(()=>getComputedStyle(document.body).backgroundImage),/linear-gradient/);
  await p.selectOption('#project-example','imu');await p.locator('#load-example').click();
  await snap(p,'01-mpu6050-practical-green.png','MPU-6050 experiment and green technical-grid interface');
  await p.selectOption('#project-example','multi');await p.locator('#load-example').click();
  await snap(p,'02-multiple-device-workspace.png','Multiple I2C and GPIO sensor controls');

  await p.goto('http://127.0.0.1:8765/boards.html');
  await p.locator('#board-catalogue .board-option').first().waitFor();
  await snap(p,'03-arduino-green-workspace.png','Arduino board, sensor controls and firmware studio');
  await p.selectOption('#sensor-model','hcsr04');
  await snap(p,'04-ultrasonic-board-view.png','HC-SR04 hardware preview and green PCB-style grid');
  await p.locator('#open-upstream').click();
  await p.locator('#upstream-elements .part-card').first().waitFor({timeout:20000});
  await snap(p,'05-open-source-component-gallery.png','Visual component library dialog on current app');

  await p.goto('http://127.0.0.1:8765/');
  await p.locator('#schematic').waitFor();
  await snap(p,'06-analog-schematic-grid.png','Analog schematic editor with green grid');
  await p.setViewportSize({width:390,height:844});
  await p.goto('http://127.0.0.1:8765/lab.html');
  await p.locator('#add-model option').first().waitFor({state:'attached'});
  await p.selectOption('#project-example','imu');await p.locator('#load-example').click();
  await snap(p,'07-mobile-practical-layout.png','Mobile screen at 390px width');

  assert.deepEqual(errors,[],'JavaScript page errors: '+errors.join(' | '));
  fs.writeFileSync(path.join(folder,'manifest.json'),JSON.stringify({commit:process.env.GITHUB_SHA,notice:'Authentic app screenshots; quick capture does not execute firmware.',shots},null,2));
  console.log('PASS: '+shots.length+' actual green-grid UI screenshots.');
 }finally{await browser.close();}
}
main().catch(e=>{console.error(e);process.exitCode=1}).finally(()=>server.kill());
