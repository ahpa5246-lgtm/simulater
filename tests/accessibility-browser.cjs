// Deque axe-core runs locally through DevTools; application CSP stays enabled.
const {chromium}=require('playwright');
const axe=require('axe-core');
const assert=require('node:assert/strict');
const {spawn}=require('node:child_process');
const fs=require('node:fs');
const pause=ms=>new Promise(r=>setTimeout(r,ms));
const tags=['wcag2a','wcag2aa','wcag21a','wcag21aa'];
const routes=[['/','#component-list button'],['/boards.html','.board-option'],['/lab.html','.device-row'],['/university.html','.experiment-item'],['/studio.html','#circuit-editor']];
const server=spawn('python',['server.py'],{stdio:'ignore'});
let browser;
process.on('exit',()=>server.kill());
(async()=>{const scans=[];try{
  for(let i=0;i<80;i++){try{await fetch('http://127.0.0.1:8765');break}catch{await pause(100)}}
  browser=await chromium.launch({args:['--no-sandbox']});
  const page=await browser.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  for(const width of [1440,390])for(const [route,ready] of routes){
    await page.setViewportSize({width,height:1050});
    await page.goto('http://127.0.0.1:8765'+route);
    await page.locator(ready).first().waitFor();
    if(route==='/boards.html'){
      const pin=page.getByRole('button',{name:'A0: Connected to sensor OUT',exact:true});
      await pin.focus();await pin.press('Enter');
      assert.match(await page.locator('#wiring-description').innerText(),/A0 · Connected to sensor OUT/);
    }
    await page.evaluate(axe.source);
    const result=await page.evaluate(tags=>axe.run(document,{runOnly:{type:'tag',values:tags},iframes:false}),tags);
    const compact=v=>({id:v.id,impact:v.impact,help:v.help,helpUrl:v.helpUrl,nodes:v.nodes.map(n=>({target:n.target,html:n.html,failureSummary:n.failureSummary}))});
    scans.push({route,width,passes:result.passes.length,violations:result.violations.map(compact),incomplete:result.incomplete.map(compact)});
    console.log(route,width,result.violations.map(v=>`${v.id}:${v.nodes.length}`).join(',')||'no automatic violations');
  }
  fs.mkdirSync('evidence',{recursive:true});
  fs.writeFileSync('evidence/accessibility-audit.json',JSON.stringify({engine:axe.version,repository:'https://github.com/dequelabs/axe-core',license:'MPL-2.0',tags,scans,keyboardChecks:['Board A0 connector can receive focus and activate with Enter at both widths.'],scope:'Automated checks of first-party workspace DOM at desktop/mobile sizes. Embedded upstream CircuitJS canvas/editor, open dialogs, screen-reader usability and general manual keyboard audit are not certified by this scan. Incomplete findings require manual review; they are retained and are not counted as passes.'},null,2)+'\n');
  assert.deepEqual(errors,[]);
  assert.deepEqual(scans.flatMap(s=>s.violations.map(v=>({route:s.route,width:s.width,id:v.id,nodes:v.nodes.map(n=>n.target)}))),[],'Accessibility defects; see evidence/accessibility-audit.json');
  console.log('PASS accessibility: five workspaces at two widths; no automated WCAG A/AA violations in scanned first-party DOM');
}finally{if(browser)await browser.close();server.kill()}})().catch(e=>{console.error(e);process.exitCode=1});
