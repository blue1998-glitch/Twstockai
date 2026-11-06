'use strict';
// Real-data files and screenshots remain outside the public Git worktree.
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict');
const root=process.env.FM2_ROOT,out=process.env.FM2_OUT,raw=fs.readFileSync(process.env.FM2_HTML);fs.mkdirSync(out,{recursive:true});
const checks=[],errors=[],external=[];let browser,server;
(async()=>{try{
 const pw=require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'));browser=await pw.chromium.launch({headless:true,executablePath:'/usr/bin/chromium'});
 server=http.createServer((q,r)=>{r.writeHead(200,{'Content-Type':'text/html;charset=utf-8'});r.end(raw)});await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;
 for(const width of [1280,390,320]){
  const ctx=await browser.newContext({viewport:{width,height:844},isMobile:width<500,hasTouch:width<500,acceptDownloads:true}),p=await ctx.newPage();
  p.on('pageerror',e=>errors.push({name:e.name,message:e.message}));p.on('request',r=>{if(/^http/.test(r.url())&&new URL(r.url()).origin!==origin)external.push(r.url());});
  await p.goto(origin);await p.waitForFunction(()=>typeof marketState!=='undefined');
  assert.equal(await p.evaluate(()=>marketState.stocks.length),1986);await p.selectOption('#marketFilter','ANALYZED_RETAINED_HISTORY');assert.equal(await p.locator('#marketResults button').count(),4);
  assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));checks.push({width,name:'current reference cohort explicit; four retained histories selectable,not a full historical universe',status:'PASS'});
  for(const code of ['1101','2884','6488','8069']){
   await p.locator(`[data-market-code="${code}"]`).click();assert.equal(await p.evaluate(()=>current.code),code);assert.equal(await p.evaluate(()=>result.as_of),'2026-10-16');
   assert.equal(await p.evaluate(()=>result.source_records),['1101','2884'].includes(code)?1213:1214);
   assert(await p.evaluate(()=>current.macd.some(v=>v.histogram!==null)));
   assert(await p.evaluate(()=>selected().source.role==='RETAINED_OFFICIAL_MONTHLY_NOT_NEW_BULK_NATIVE_FEED'));
   assert(await p.evaluate(()=>selected().source_input_binding.source_role===selected().source.role));
   if(['6488','8069'].includes(code))assert.equal(await p.evaluate(()=>selected().source.volume_provenance.exact_native_share_precision),false);
   if(code==='2884')assert(await p.evaluate(()=>result.boxes.filter(b=>!b.usable_at_anchor).length===32&&result.boxes.every(b=>b.usable_at_anchor||b.pressure_distance_fraction===null)));
   const stock=await p.evaluate(code=>marketState.stocks.find(s=>s.code===code),code);
   const expected=JSON.parse(fs.readFileSync(path.join(root,'results',stock.result_key+'.json'))).value;
   const wait=p.waitForEvent('download');await p.click('#download');const d=await wait;const selected=JSON.parse(fs.readFileSync(await d.path()));
   assert.deepEqual(selected.core,expected.result);assert.deepEqual(selected.bars,expected.input.bars);assert.deepEqual(selected.macd,expected.indicators.macd);assert.deepEqual(selected.moving_averages,expected.indicators.moving_averages);
   assert.equal(selected.core.classification_quality,'NOT_VALIDATED');assert.equal(selected.core.comparison.primary_pressure_id,null);
   await p.click('#evidenceButton');assert.equal(await p.locator('#evidenceBody section').count(),3);await p.click('#dismiss');
   if(code==='1101')await p.locator('#chartWrap').screenshot({path:path.join(out,'private-history-chart-'+width+'.png')});
   checks.push({width,name:'real multi-day '+code+' exact source/core/indicators/precision/F01/evidence/download',status:'PASS'});await p.waitForTimeout(700);
  }
  await p.selectOption('#marketFilter','HISTORY_SOURCE_UNAVAILABLE');assert.equal(await p.locator('#marketResults button').count(),50);await p.locator('#marketResults button').first().click();assert(await p.locator('main').isHidden());checks.push({width,name:'unavailable history clear refusal,no stale chart',status:'PASS'});
  await ctx.close();
 }
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({status:'PASS',checks,precision_downloads:12,javascript_errors:errors,external_requests:external,android:'NOT_TESTED',deployment:false},null,2));console.log('PASS',checks.length,'checks;12 exact original-history downloads');
}catch(e){fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({status:'FAIL',error:e.stack,checks,errors,external},null,2));console.error(e);process.exitCode=1;}finally{if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));}})();
