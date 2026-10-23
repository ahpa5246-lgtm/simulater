const {chromium}=require(process.env.PLAYWRIGHT_PATH || 'playwright');
const assert=require('node:assert/strict');
const {spawn}=require('node:child_process');
const server=spawn('python',['server.py'],{stdio:'ignore'});
process.on('exit',()=>server.kill());
async function completed(page){for(let i=0;i<150;i++){const text=await page.locator('#status').innerText();if(text.includes('complete'))return;if(await page.locator('#status-dot').getAttribute('class')==='error')throw Error(text);await new Promise(r=>setTimeout(r,100));}throw Error(await page.locator('#status').innerText());}
(async()=>{for(let i=0;i<50;i++){try{await fetch('http://127.0.0.1:8765');break;}catch{await new Promise(r=>setTimeout(r,100));}}const browser=await chromium.launch({headless:true,args:['--no-sandbox']});const page=await browser.newPage({viewport:{width:1536,height:1000},deviceScaleFactor:1});let errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://127.0.0.1:8765');await page.getByRole('button',{name:'Run simulation'}).click();await completed(page);
assert.ok(await page.locator('#plot path').count()>0);await page.selectOption('#example','divider');await page.getByRole('button',{name:'Run simulation'}).click();await completed(page);assert.match(await page.locator('#measurements').innerText(),/5\.000/);
await page.locator('[data-cid="R2"]').first().click();await page.locator('#prop-value').fill('2000');await page.locator('#prop-value').press('Tab');await page.getByRole('button',{name:'Run simulation'}).click();await completed(page);assert.match(await page.locator('#measurements').innerText(),/6\.667/);
await page.locator('#undo').click();await page.getByRole('button',{name:'Run simulation'}).click();await completed(page);assert.match(await page.locator('#measurements').innerText(),/5\.000/);
await page.reload();assert.equal(await page.locator('#example').inputValue(),'divider');await page.selectOption('#example','rc');await page.getByRole('button',{name:'Run simulation'}).click();await completed(page);await page.locator('[data-cid="R1"]').first().click();
assert.ok(await page.evaluate(()=>document.documentElement.scrollHeight)<=1000,'Desktop workbench must fit viewport');await page.screenshot({path:'screenshots/workbench.png',fullPage:true});
const malicious={version:1,name:'Unsafe import',components:[{id:'V1',type:'V',value:5,a:'v','b':'0',x:200,y:200,rotation:0,wave:'sine',frequency:'1000)\n.control\nshell echo IMPORT_EXECUTED\n.endc\n*'}],wires:[]};
await page.locator('#file-input').setInputFiles({name:'unsafe.mina',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(malicious))});
assert.match(await page.locator('#status').innerText(),/Invalid/);assert.equal(await page.locator('#project-name').innerText(),'RC low-pass filter');
await page.selectOption('#example','divider');await page.locator('#wire-tool').click();await page.locator('[data-pin="R1:a"]').click();await page.locator('[data-pin="R1:b"]').click();await page.locator('#select-tool').click();await page.locator('[data-cid="R1"]').first().click();await page.getByRole('button',{name:'Disconnect pin 1',exact:true}).click();assert.notEqual(await page.locator('#prop-a').inputValue(),await page.locator('#prop-b').inputValue());
assert.deepEqual(errors,[]);console.log('PASS: simulation, divider, edit, undo, persistence, RC and screenshot; no browser errors');await browser.close();server.kill();})().catch(e=>{console.error(e);process.exit(1)});
