'use strict';
// All real HTML, screenshots and browser results remain outside the public Git tree.
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict');
const raw=fs.readFileSync(process.env.FM1_HTML),out=process.env.FM1_BROWSER_OUT;fs.mkdirSync(out,{recursive:true});
const checks=[],errors=[],external=[];let browser,server;
(async()=>{try{
 const pw=require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'));browser=await pw.chromium.launch({headless:true,executablePath:'/usr/bin/chromium'});
 server=http.createServer((q,r)=>{r.writeHead(200,{'Content-Type':'text/html;charset=utf-8'});r.end(raw)});await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;
 for(const width of [1280,390,320]){
  const ctx=await browser.newContext({viewport:{width,height:844},isMobile:width<500,hasTouch:width<500,acceptDownloads:true}),p=await ctx.newPage();
  p.on('pageerror',e=>errors.push({name:e.name,message:e.message,stack:e.stack}));p.on('request',r=>{if(/^http/.test(r.url())&&new URL(r.url()).origin!==origin)external.push(r.url());});
  await p.goto(origin);await p.waitForFunction(()=>typeof marketState!=='undefined');
  assert.equal(await p.evaluate(()=>marketState.stocks.length),1986);assert.equal(await p.locator('#marketResults button').count(),50);
  assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));checks.push({width,name:'full1986 universe,explicit50 pagination,nooverflow',status:'PASS'});
  await p.fill('#marketSearch','1101');assert.equal(await p.locator('#marketResults button').count(),1);await p.locator('#marketResults button').click();
  assert.equal(await p.evaluate(()=>current.code),'1101');assert.equal(await p.evaluate(()=>result.as_of),'2026-10-30');
  assert.equal(await p.evaluate(()=>bars().length),1);assert.equal(await p.evaluate(()=>result.comparison.primary_pressure_id),null);
  assert(await p.evaluate(()=>current.macd.every(m=>m.histogram===null)));assert(await p.locator('#zoomIn').isDisabled());
  const event=p.waitForEvent('download');await p.click('#download');const download=await event;const selected=JSON.parse(fs.readFileSync(await download.path()));
  assert.equal(selected.bars.length,1);assert.equal(selected.as_of,'2026-10-30');assert.equal(selected.classification_quality,'NOT_VALIDATED');checks.push({width,name:'realstock search/source day/singleK/volume/warmupMACD/JSON not fabricated history',status:'PASS'});
  await p.fill('#marketSearch','');await p.selectOption('#marketFilter','MISSING_QUOTE');assert.equal(await p.locator('#marketResults button').count(),5);await p.locator('#marketResults button').first().click();assert(await p.locator('main').isHidden());
  await p.selectOption('#marketFilter','ALL');await p.fill('#marketSearch','NO_SUCH_STOCK');assert.equal(await p.locator('#marketResults button').count(),0);checks.push({width,name:'missing quote reason no stale chart and zero-match search',status:'PASS'});
  await p.screenshot({path:path.join(out,'private-'+width+'.png'),fullPage:true});await ctx.close();
 }
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({status:'PASS',checks,javascript_errors:errors,external_requests:external,android:'NOT_TESTED',public_deployment:false},null,2));console.log('PASS',checks.length,'private preview checks');
}catch(e){fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({status:'FAIL',error:e.stack,checks,errors,external},null,2));console.error(e);process.exitCode=1;}finally{if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));}})();
