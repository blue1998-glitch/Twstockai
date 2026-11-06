const assert=require('node:assert/strict'),fs=require('node:fs'),http=require('node:http'),path=require('node:path');
const {chromium}=require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES+'/playwright');
const root=__dirname, data=JSON.parse(fs.readFileSync(path.join(root,'cutoff-facts.json')));
if(!process.env.CHROME_HEADLESS_SHELL)throw Error('Set CHROME_HEADLESS_SHELL to an existing Chrome headless shell executable');
(async()=>{
const server=http.createServer((req,res)=>{res.setHeader('content-type','text/html; charset=utf-8');res.end(fs.readFileSync(path.join(root,'review.html')))});server.listen(0,'127.0.0.1');await new Promise(r=>server.once('listening',r));server.unref();
const browser=await chromium.launch({executablePath:process.env.CHROME_HEADLESS_SHELL,headless:true,args:['--no-sandbox'],env:{...process.env}});
const errors=[],results=[];
try{
const page=await browser.newPage({viewport:{width:1200,height:850}});page.on('pageerror',e=>errors.push(e.message));await page.goto('http://127.0.0.1:'+server.address().port);await page.waitForFunction(()=>!!window.cutoffStudyInspect);
for(const c of data.cases){await page.selectOption('#pv-case',c.id);for(const s of c.snapshots){await page.selectOption('#pv-date',s.as_of);assert.deepEqual(await page.evaluate(()=>window.cutoffStudyInspect()),s);assert.match(await page.locator('#pv-status').innerText(),/未知/);results.push(c.id+'@'+s.as_of);}}
await page.selectOption('#pv-case','1101-2025');await page.selectOption('#pv-date','2025-05-29');await page.check('#pv-review');assert.doesNotMatch(await page.locator('#pv-notes').innerText(),/6\/3|破底|待消化/);
await page.selectOption('#pv-date','2025-06-03');assert.match(await page.locator('#pv-notes').innerText(),/人工紀錄日 2026-10-22/);
await page.selectOption('#pv-date','2025-05-29');assert.doesNotMatch(await page.locator('#pv-notes').innerText(),/6\/3|破底/);await page.uncheck('#pv-review');
await page.screenshot({path:path.join(root,'desktop-cutoff.png'),fullPage:true});
await page.setViewportSize({width:390,height:844});await page.selectOption('#pv-case','2884-2026');await page.selectOption('#pv-date','2026-10-15');
assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
const labels=await page.locator('svg text').evaluateAll(nodes=>nodes.map(n=>{const r=n.getBoundingClientRect();return {text:n.textContent,x:r.left,right:r.right}}));assert(labels.every(n=>n.x>=-1&&n.right<=391));
await page.screenshot({path:path.join(root,'mobile-cutoff.png'),fullPage:true});
assert.deepEqual(errors,[]);const report={status:'PASS',browser_version:browser.version(),snapshot_oracles:results,early_review_future_text_hidden:true,mobile_width:390,horizontal_overflow:false,JS_errors:errors,scope:'LOCAL_HTTP_RESEARCH_VIEW_ONLY_NOT_ANDROID_OR_PRODUCT_REGRESSION'};fs.writeFileSync(path.join(root,'browser-verification.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
}finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
