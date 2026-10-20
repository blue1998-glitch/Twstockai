const {chromium}=require('/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),http=require('http'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const dir=__dirname,html=fs.readFileSync(path.join(dir,'input/M1_v019_cross_scale_real_v01.html'));
const font='/workspace/scratch/ca1bc9758970/core-next/qa-font.otf';
const server=http.createServer((req,res)=>{res.setHeader('Content-Type',req.url==='/font.otf'?'font/otf':'text/html;charset=utf-8');res.end(req.url==='/font.otf'?fs.readFileSync(font):html);});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await chromium.launch({executablePath:'/workspace/scratch/ca1bc9758970/core-next/browser/runtime/chromium',headless:true,args:['--no-sandbox']});
const page=await browser.newPage({viewport:{width:1400,height:1050}}),errors=[],observations=[],checks=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://127.0.0.1:'+server.address().port);await page.screenshot({path:path.join(dir,'first-original-font.png')});
await page.addStyleTag({content:'@font-face{font-family:ReviewCJK;src:url(/font.otf)}body,button,select{font-family:ReviewCJK,system-ui!important}'});await page.evaluate(()=>document.fonts.ready);
await page.evaluate(()=>{const d=Object.getOwnPropertyDescriptor(CanvasRenderingContext2D.prototype,'font');Object.defineProperty(CanvasRenderingContext2D.prototype,'font',{get:d.get,set(v){d.set.call(this,v.replace(/system-ui/g,'ReviewCJK'));}});draw();});
const fixed=await page.evaluate(()=>({as_of:data.as_of,result:data.core.result_id,artifact:data.artifact_id,serialized:JSON.stringify(data)}));
async function capture(name){await page.locator('#chartWrap').screenshot({path:path.join(dir,name+'.png')});observations.push(await page.evaluate(name=>({name,window:document.querySelector('#window').textContent,readout:document.querySelector('#readout').textContent,evidence:document.querySelector('#evidence').innerText,selected:window.M1_CROSS_SCALE.state().selected_layer}),name));}
await capture('overview');
await page.click('[data-mode="major"]');await page.selectOption('#layerSelect','b77');await page.click('#focus');await capture('major-b77');
await page.selectOption('#layerSelect','left');await page.click('#focus');await capture('major-left');
await page.selectOption('#queryDate','2023-05-02');assert((await page.locator('#readout').innerText()).includes('高40.25'));checks.push('Left witness May02 high40.25 queried in original UI');
await page.selectOption('#layerSelect','right');await page.click('#focus');await capture('major-right');
await page.selectOption('#queryDate','2025-04-08');checks.push('Right witness Apr08 queried in original UI');
await page.click('[data-mode="previous"]');await capture('previous');
await page.selectOption('#layerSelect','same');await page.click('#focus');await capture('previous-same');
for(const date of ['2025-05-13','2025-05-14','2025-05-27','2025-05-29','2025-06-02','2025-06-03']){await page.selectOption('#queryDate',date);observations.push({date,readout:await page.locator('#readout').innerText()});}
checks.push('Source end / two confirmations / prior inside / research outside / manual end checked as separate dates');
await page.click('[data-mode="recent"]');await capture('recent');
await page.evaluate(()=>{view.start=rows.findIndex(r=>r.date==='2025-06-02');view.end=rows.length-1;view.cursor=view.end;draw();});await capture('recent-full-context');
await page.click('[data-mode="previous"]');await page.selectOption('#layerSelect','same');await page.click('#focus');await page.locator('#timeline').screenshot({path:path.join(dir,'previous-date-axis.png')});
await page.click('[data-mode="major"]');
await page.evaluate(()=>{visible.clear();visible.add('major');visible.add('b77');selectedLayer='b77';view.start=rows.findIndex(r=>r.date>='2023-05-01');view.end=rows.findLastIndex(r=>r.date<='2025-06-10');view.cursor=view.end;buildLayers();evidence();draw();});await capture('major-manual-b77');
await page.click('[data-mode="recent"]');
for(const date of ['2026-01-27','2026-10-12','2026-10-13','2026-10-14','2026-10-15','2026-10-16']){await page.selectOption('#queryDate',date);observations.push({date,readout:await page.locator('#readout').innerText()});}
await page.click('#zoomIn');let state=await page.evaluate(()=>window.M1_CROSS_SCALE.state());const count=state.view.end-state.view.start+1;
await page.selectOption('#interaction','pan');const r=await page.locator('#chart').boundingBox();await page.mouse.move(r.x+r.width*.50,r.y+r.height*.3);await page.mouse.down();await page.mouse.move(r.x+r.width*.62,r.y+r.height*.3,{steps:8});await page.mouse.up();let moved=await page.evaluate(()=>window.M1_CROSS_SCALE.state());assert.equal(moved.view.end-moved.view.start+1,count);assert.notEqual(moved.view.start,state.view.start);checks.push('Actual mouse drag pans after zoom, preserves record count');
await page.click('#return');await page.setViewportSize({width:390,height:1000});await page.click('[data-mode="major"]');await capture('major-390');
await page.click('[data-mode="previous"]');await capture('previous-390');
const after=await page.evaluate(()=>({as_of:data.as_of,result:data.core.result_id,artifact:data.artifact_id,serialized:JSON.stringify(data)}));assert.deepEqual(after,fixed);checks.push('All original numeric data/core/analysis identity unchanged across observations');assert.equal(errors.length,0);
const report={scope:'LIMITED_WORK_HTTP_ARTIFACT_OBSERVATION_NOT_FULL_REGRESSION_OR_ANDROID',html_sha256:crypto.createHash('sha256').update(html).digest('hex'),browser:await browser.version(),font:'Original first screenshot preserved; observation-only ReviewCJK DOM and canvas font substitution, artifact bytes unchanged',checks,errors,observations};fs.writeFileSync(path.join(dir,'browser-observation.json'),JSON.stringify(report,null,2));
await browser.close();server.close();console.log(JSON.stringify({status:'OBSERVED',checks:checks.length,screenshots:fs.readdirSync(dir).filter(f=>f.endsWith('.png')).length,errors}));})().catch(e=>{console.error(e);server.close();process.exit(1)});
