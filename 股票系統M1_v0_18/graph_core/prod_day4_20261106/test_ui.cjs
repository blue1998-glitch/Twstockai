const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const {chromium}=require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'));
(async()=>{
 const base='/workspace/twstockai-local-data',work=base+'/prod_day4_20261106';
 const cfg=JSON.parse(fs.readFileSync(work+'/browser-config-private.json'));
 const svc=JSON.parse(fs.readFileSync(base+'/prod_core1_20261105/service-current-private.json'));
 const out=work+'/browser-final';fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium',args:['--disk-cache-size=1048576','--media-cache-size=1048576']});
 const checks=[],loads=[],errors=[],external=[];const check=(width,name)=>checks.push({width,name,status:'PASS'});
 try{
  for(const [width,height] of [[390,844],[844,390]]){
   const ctx=await browser.newContext({viewport:{width,height},isMobile:width<900,hasTouch:width<900,httpCredentials:cfg.auth});const p=await ctx.newPage();p.setDefaultTimeout(20000);
   p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>{if(/^https?:/.test(r.url())&&new URL(r.url()).origin!==cfg.origin)external.push('NON_OWNER_REQUEST');});
   const cdp=await ctx.newCDPSession(p);await cdp.send('Performance.enable');const t=Date.now();
   await p.goto(cfg.origin+svc.entry,{waitUntil:'networkidle'});await p.waitForFunction(()=>window.productStatus?.status==='COMPLETE');
   const s=await p.evaluate(()=>({total:marketState.stocks.length,unique:new Set(marketState.stocks.map(x=>x.identity)).size,counts:marketState.scan_summary,date:marketState.summary.as_of,charts:data.series.length}));
   assert.equal(s.total,1986);assert.equal(s.unique,1986);assert.equal(s.date,'2026-11-05');assert.equal(s.charts,0);
   assert.deepEqual([s.counts.executed,s.counts.insufficient,s.counts.refused,s.counts.failed],[1967,1967,19,0]);
   assert((await p.locator('#latestIntake').innerText()).includes('接件完成')); assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   loads.push({width,load_ms:Date.now()-t,html_bytes:await p.evaluate(()=>performance.getEntriesByType('navigation')[0].encodedBodySize),JS_heap_bytes:(await cdp.send('Performance.getMetrics')).metrics.find(x=>x.name==='JSHeapUsedSize').value});check(width,'real1986 unique /date /scan counts /qualified new intake /zero initial chart');
   await p.selectOption('#marketFilter','來源拒用');assert.equal(await p.locator('#marketResults article').count(),19);await p.selectOption('#marketFilter','ALL');
   await p.selectOption('#marketExchange','TPEX');assert((await p.locator('#marketResults').innerText()).length>0);await p.selectOption('#marketExchange','ALL');check(width,'status +market filter');
   for(const c of cfg.cases){
    await p.click('#searchTab');await p.fill('#marketSearch',c.code);await p.locator(`[data-market-code="${c.code}"]`).click();await p.waitForSelector('#lazyGraphButton');
    for(const field of ['open','high','low','close','volume_shares_scaled'])assert.equal(await p.locator(`[data-quote-field="${field}"]`).innerText(),c.fact.bar[field]);
    await p.click('#lazyGraphButton');await p.waitForSelector('#lazySegmentNote');const v=await p.evaluate(()=>lazyGraphResponse);
    assert.equal(v.identity,c.identity);assert.equal(v.core_calls,0);assert.equal(v.scan_core_calls,1);assert.deepEqual(v.series.bars,[c.fact.bar]);assert.equal(v.history_joined,false);assert.equal(v.series.results[0].source_records,1);assert.equal(v.series.results[0].boxes.length,0);assert(v.series.macd.every(x=>x.dif===null&&x.dea===null&&x.histogram===null));
    const id=v.series.results[0].result_id;await p.click('#lazyBack');await p.click('#lazyGraphButton');await p.waitForSelector('#lazySegmentNote');assert.equal(await p.evaluate(()=>result.result_id),id);assert.equal(await p.evaluate(()=>lazyGraphCache),'HIT');
    if(width<900)await p.locator('#chart').tap({position:{x:35,y:150}});assert.equal(await p.evaluate(()=>result.as_of),'2026-11-05');assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));check(width,'exact '+c.market+' real OHLCV /saved core /single segment /repeat cache');
   }
   const c=cfg.refused;await p.click('#searchTab');await p.fill('#marketSearch',c.code);await p.locator(`[data-market-code="${c.code}"]`).click();await p.waitForSelector('#lazyGraphButton');await p.click('#lazyGraphButton');await p.waitForFunction(()=>window.lazyGraphResponse?.status==='SOURCE_REFUSED');assert.equal(await p.evaluate(()=>result),null);check(width,'rejected stock no old chart fallback');
   if(width===390){
    for(const old of cfg.old_cases){
     await p.goto(old.url,{waitUntil:'networkidle'});assert.equal(await p.evaluate(()=>marketState.summary.as_of),old.as_of);
     for(const s of old.stocks){await p.fill('#marketSearch',s.code);await p.locator(`[data-compare-id="${s.identity}"]`).click();}
     await p.click('#compareTab');await p.waitForFunction(()=>document.querySelector('#compareStatus').dataset.scope);assert.equal(await p.locator('[data-compared-stock]').count(),2);
     await p.locator(`[data-open-compared="${old.stocks[0].identity}"]`).click();await p.waitForFunction(d=>result?.as_of===d,old.as_of);assert(await p.evaluate(()=>bars().length>1));check(width,'retained '+old.as_of+' two-stock comparison +original graph');
    }
   }
   await p.goto(cfg.origin+'/batches',{waitUntil:'networkidle'});for(const dt of ['2026-11-05','2026-11-03','2026-11-02','2026-10-30'])assert((await p.locator('body').innerText()).includes(dt));
   await p.goto(cfg.origin+svc.entry,{waitUntil:'networkidle'});await p.waitForFunction(()=>window.productStatus?.status==='COMPLETE');await p.reload({waitUntil:'networkidle'});assert.equal(await p.evaluate(()=>marketState.summary.as_of),'2026-11-05');check(width,'date selection +refresh retains real batch');
   await ctx.close();
  }
  const desktop=await browser.newContext({viewport:{width:1280,height:900},httpCredentials:cfg.auth});const dp=await desktop.newPage();await dp.goto(cfg.origin+svc.entry,{waitUntil:'networkidle'});assert.equal(await dp.evaluate(()=>marketState.summary.as_of),'2026-11-05');assert(await dp.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));check(1280,'new day desktop default +no overflow');await desktop.close();
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
  const ctx=await browser.newContext({httpCredentials:cfg.auth});const request=ctx.request;
  const controls=[];
  for(const [url,method,status,headers] of [['/product-status.json','GET',403,{Origin:'https://invalid.example'}],['/product-status.json','POST',405,{}],['/product-status.json?file=secret','GET',404,{}],['/product-status.json','HEAD',204,{}],['/../private','GET',404,{}]]){
   const r=await request.fetch(cfg.origin+url,{method,headers});assert.equal(r.status(),status);controls.push({method,status});
  }
  const anonymous=await browser.newContext();assert.equal((await anonymous.request.get(cfg.origin+'/product-status.json')).status(),401);await anonymous.close();controls.push({method:'GET_UNAUTHORIZED',status:401});
  const status=await(await request.get(cfg.origin+'/product-status.json')).json();assert.equal(status.reference,1986);assert.equal(status.latest_intake.status,'COMPLETE');await ctx.close();
  const report={status:'PASS',groups:checks.length,checks,loads,owner_controls:controls,page_errors:errors,external_requests:external,android:'NOT_TESTED_NEW_BUILD',private_url:'LOOPBACK_ONLY',live_status:status};fs.writeFileSync(out+'/verification-private.json',JSON.stringify(report,null,2));console.log(JSON.stringify({status:'PASS',groups:checks.length,loads,controls}));
 }catch(e){fs.writeFileSync(out+'/failure-private.json',JSON.stringify({message:e.message,checks,loads,errors,external},null,2));throw e;}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
