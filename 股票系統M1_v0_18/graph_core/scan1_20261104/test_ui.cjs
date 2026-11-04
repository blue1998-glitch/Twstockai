const fs=require("fs"),path=require("path"),assert=require("assert/strict"),crypto=require("crypto");
const {chromium}=require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,"playwright"));
(async()=>{
const work="/workspace/twstockai-local-data/scan1_20261104",cfg=JSON.parse(fs.readFileSync(work+"/browser-config-private.json"));
const out=work+"/browser-final";fs.mkdirSync(out,{recursive:true});
const browser=await chromium.launch({headless:true,executablePath:"/usr/bin/chromium",args:["--disk-cache-size=1048576","--media-cache-size=1048576"]});
const savedIndex=JSON.parse(fs.readFileSync(work+"/complete-index.json"));const savedRows=new Map(savedIndex.records.map(r=>[r.identity,r]));
const checks=[],loads=[],calculations=[],errors=[],external=[];let downloads=0;
const check=(width,test)=>checks.push({width,test,status:"PASS"});
try{
for(const [width,height]of [[390,844],[844,390],[1280,900]]){
 const ctx=await browser.newContext({viewport:{width,height},hasTouch:width<900,isMobile:width<900,httpCredentials:cfg.auth,acceptDownloads:true});const p=await ctx.newPage();p.setDefaultTimeout(20000);
 let lazy=0;p.on("pageerror",e=>errors.push(e.message));p.on("request",r=>{if(/^https?:/.test(r.url())){if(new URL(r.url()).origin!==cfg.origin)external.push(r.url());if(/lazy-[a-f0-9]{64}\.json$/.test(r.url()))lazy++;}});
 const cdp=await ctx.newCDPSession(p);await cdp.send("Performance.enable");const start=Date.now();await p.goto(cfg.url,{waitUntil:"networkidle"});await p.waitForSelector("#marketResults article");
 assert.equal(await p.evaluate(()=>marketState.stocks.length),1986);assert.equal(await p.evaluate(()=>data.series.length),0);assert.equal(lazy,0);assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 const heap=(await cdp.send("Performance.getMetrics")).metrics.find(x=>x.name==="JSHeapUsedSize").value;
 loads.push({width,load_ms:Date.now()-start,heap_bytes:heap,initial_lazy_calls:lazy,html_bytes:await p.evaluate(()=>performance.getEntriesByType("navigation")[0].encodedBodySize)});check(width,"initial1986 search /zero compute /no overflow");
 const ss=await p.evaluate(()=>marketState.scan_summary);assert.deepEqual([ss.total,ss.executed,ss.insufficient,ss.refused,ss.failed],[1986,1955,1955,31,0]);assert((await p.locator("#marketOverview").innerText()).includes("已執行"));check(width,"actual complete scan denominators visible");
 if(width===390){await p.screenshot({path:out+"/home-390.png"});const ids=[];for(;;){ids.push(...await p.locator("[data-market-code]").evaluateAll(xs=>xs.map(x=>x.dataset.marketCode)));if(await p.getByRole("button",{name:"下一頁",exact:true}).isDisabled())break;await p.getByRole("button",{name:"下一頁",exact:true}).click();}assert.equal(ids.length,1986);assert.equal(new Set(ids).size,1986);check(width,"all1986 identities reachable with actual saved statuses");}

 for(let i=0;i<cfg.cases.length;i++){
  const c=cfg.cases[i];await p.click("#searchTab");await p.fill("#marketSearch",c.code);await p.locator(`[data-market-code="${c.code}"]`).click();await p.waitForSelector("#lazyGraphButton");assert.equal(await p.evaluate(()=>dailyQuote.identity),c.identity);
  const start=Date.now();await p.click("#lazyGraphButton");await p.waitForSelector("#lazySegmentNote");const value=await p.evaluate(()=>lazyGraphResponse);calculations.push({width,case_index:i,market:c.market,ms:Date.now()-start,cache:await p.evaluate(()=>lazyGraphCache),worker:value.metrics});
  assert.equal(value.identity,c.identity);assert.equal(value.core_calls,0);assert.equal(value.scan_core_calls,1);assert.equal(value.scan_status,"EXECUTED_INSUFFICIENT_HISTORY");const saved=JSON.parse(fs.readFileSync(work+"/results/"+savedRows.get(c.identity).key+".json")).value;assert.deepEqual(value.series.results[0],saved.result);assert.deepEqual(value.series.bars,[c.fact.bar]);assert.equal(value.history_joined,false);assert.equal(value.meaningful_structure,false);assert.equal(value.series.results[0].source_records,1);assert.equal(value.series.results[0].boxes.length,0);assert.equal(value.series.results[0].reference_candidates.length,0);assert.equal(value.fact_source.daily_sha256,c.fact.source.daily_sha256);assert.equal(value.series.price_basis_id,c.fact.source.price_basis_id);assert.equal(value.decision.headline,"歷史不足");
  assert(value.series.macd.every(x=>x.dif===null&&x.dea===null&&x.histogram===null));
  assert.equal(await p.evaluate(()=>result.as_of),"2026-11-03");assert.equal(await p.evaluate(()=>bars().length),1);assert(await p.locator("#dailyQuotePanel").isHidden());assert(await p.locator("main").isVisible());assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  const before=await p.evaluate(()=>({as_of:result.as_of,id:result.result_id,day:bars()[view.cursor].date}));
  if(width<900)await p.locator("#chart").tap({position:{x:40,y:150}});else await p.locator("#chart").click({position:{x:40,y:150}});await p.evaluate(()=>{zoom(1.4);pan(1);query(0);});
  assert.deepEqual(await p.evaluate(()=>({as_of:result.as_of,id:result.result_id,day:bars()[view.cursor].date})),before);check(width,`real ${c.market} case${i%2+1} source /single bar /insufficient /shared cursor no date change`);
  if(i===0){
   await p.screenshot({path:out+`/graph-${width}.png`,fullPage:true});
   await p.locator("#technicalDetails").evaluate(el=>el.open=true);const dw=p.waitForEvent("download");await p.click("#download");const d=await dw;const chunks=[];for await(const b of await d.createReadStream())chunks.push(b);assert.deepEqual(JSON.parse(Buffer.concat(chunks)),await p.evaluate(()=>selected()));downloads++;await p.locator("#technicalDetails").evaluate(el=>el.open=false);check(width,"selected core result exact JSON download");
   const statusBefore=await(await ctx.request.get(cfg.status_url)).json();await p.click("#lazyBack");await p.waitForSelector("#lazyGraphButton");await p.click("#lazyGraphButton");await p.waitForSelector("#lazySegmentNote");assert.equal(await p.evaluate(()=>lazyGraphCache),"HIT");const statusAfter=await(await ctx.request.get(cfg.status_url)).json();assert.equal(statusAfter.core_calls,statusBefore.core_calls);assert(statusAfter.cache_entries<=8&&statusAfter.cache_bytes<=2097152);assert.equal(await p.evaluate(()=>result.result_id),before.id);check(width,"repeat HIT zero new core /bounded RAM cache /same result");
  }
 }
 for(const [s,kind]of [[cfg.short_case,"short-history"],[cfg.refused,"source-refused"]]){
  await p.click("#searchTab");await p.fill("#marketSearch",s.code);await p.locator(`[data-market-code="${s.code}"]`).click();await p.waitForSelector("#lazyGraphButton");await p.click("#lazyGraphButton");
  if(kind==="short-history"){await p.waitForSelector("#lazySegmentNote");assert.equal(await p.evaluate(()=>lazyGraphResponse.status),"INSUFFICIENT_COMPARABLE_HISTORY");assert.equal(await p.evaluate(()=>result.source_records),1);}
  else {await p.waitForFunction(()=>window.lazyGraphResponse?.status==="SOURCE_REFUSED");assert.equal(await p.evaluate(()=>lazyGraphResponse.series),null);assert.equal(await p.evaluate(()=>result),null);assert(await p.locator("main").isHidden());assert((await p.locator("#workStatus").innerText()).includes("來源拒用"));}
  check(width,kind+" honest refusal /no fabricated chart");
 }
 if(width===390){
  for(const old of cfg.old_cases){await p.goto(old.url,{waitUntil:"networkidle"});await p.waitForSelector("#marketSearch");assert.equal(await p.evaluate(()=>marketState.summary.as_of),old.as_of);
   for(const s of old.stocks){await p.fill("#marketSearch",s.code);await p.locator(`[data-compare-id="${s.identity}"]`).click();}
   await p.click("#compareTab");await p.waitForFunction(()=>document.querySelector("#compareStatus").dataset.scope);assert.equal(await p.locator("[data-compared-stock]").count(),2);await p.locator(`[data-open-compared="${old.stocks[0].identity}"]`).click();await p.waitForFunction(d=>result?.as_of===d&&!document.querySelector("main").hidden,old.as_of);assert.equal(await p.evaluate(()=>bars().length>1),true);await p.screenshot({path:out+`/old-${old.as_of}.png`});check(width,old.as_of+" original chart +2-stock compare +exact date retained");
  }
 }
 await ctx.close();
}
assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
const ctx=await browser.newContext({httpCredentials:cfg.auth});const finalMetrics=await(await ctx.request.get(cfg.status_url)).json();await ctx.close();
assert.equal(finalMetrics.core_calls,0);assert.equal(finalMetrics.new_numeric_core_calls,0);const report={status:"PASS",groups:checks.length,checks,loads,calculations,exact_downloads:downloads,page_errors:errors,external_requests:external,final_metrics:finalMetrics,android:"NOT_TESTED_NEW_BUILD"};fs.writeFileSync(out+"/verification-private.json",JSON.stringify(report,null,2));console.log(JSON.stringify({status:"PASS",groups:checks.length,loads,exact_downloads:downloads,final_metrics:finalMetrics}));
}catch(e){fs.writeFileSync(out+"/failure-private.json",JSON.stringify({message:e.message,stack:e.stack,checks,loads,calculations,errors,external},null,2));throw e;}finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
