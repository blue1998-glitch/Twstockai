// Real new-day private batch UI checks; no permanent listener or source requests. Config, screenshots and exact downloads stay Git-external.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const cp=require('child_process');
function savedChart(p){const code="import sys,json;from pathlib import Path;from rotation_research.artifact_codec import read_bytes;from technical_chart.interned_json import unpack;s=unpack(json.loads(read_bytes(Path(sys.argv[1]))));print(json.dumps(dict(result=s['results'][0],input=dict(bars=s['bars']),indicators=dict(macd=s['macd'],moving_averages=s['moving_averages']))))";return JSON.parse(cp.execFileSync('python3',['-c',code,p],{maxBuffer:128*1024*1024}));}
const {chromium}=require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'));
(async()=>{
 const cfg=JSON.parse(fs.readFileSync(process.argv[2])),out=process.argv[3];fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium'}),checks=[],errors=[],external=[];
 let downloads=0;
 try{
 for(const [width,height] of [[320,844],[390,844],[844,390],[1280,900]]){
  const context=await browser.newContext({viewport:{width,height},isMobile:width<900,hasTouch:width<900,acceptDownloads:true,httpCredentials:cfg.auth});
  const p=await context.newPage();p.setDefaultTimeout(90000);p.on('pageerror',e=>errors.push(e.message));
  p.on('request',r=>{if(/^https?:/.test(r.url())&&new URL(r.url()).origin!==cfg.origin)external.push(new URL(r.url()).origin)});
  await p.goto(cfg.url,{waitUntil:'domcontentloaded',timeout:120000});await p.waitForSelector('#marketSearch');
  assert.equal(await p.evaluate(()=>marketState.stocks.length),cfg.expected);
  assert.equal(await p.evaluate(()=>marketState.stocks.filter(s=>s.preview_series).length),cfg.charts);
  assert.deepEqual(await p.evaluate(()=>marketState.stocks.reduce((v,s)=>(v[s.status]=(v[s.status]||0)+1,v),{})),cfg.terminal_counts);
  assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  const allIds=[];while(true){allIds.push(...await p.locator('#marketResults [data-compare-id]').evaluateAll(xs=>xs.map(x=>x.dataset.compareId)));const next=p.getByRole('button',{name:'下一頁',exact:true});if(await next.isDisabled())break;await next.click();}
  assert.equal(allIds.length,cfg.expected);assert.deepEqual(allIds.sort(),await p.evaluate(()=>marketState.stocks.map(s=>s.identity).sort()));
  await p.fill('#marketSearch',cfg.compare[0].name);assert.equal(await p.locator('[data-market-code="'+cfg.compare[0].code+'"]').count(),1);
  checks.push({width,height,check:'actual reference IDs across every page /name and code search /actual new-day lazy descriptors /responsive search',status:'PASS'});
  for(const row of cfg.compare){
   await p.fill('#marketSearch',row.code);await p.locator('[data-compare-id="'+row.identity+'"]').click();
  }
  await p.click('#compareTab');await p.waitForSelector('#compareStatus[data-scope="LIMITED_DESCRIPTIVE"]');assert.equal(await p.locator('#compareCards article').count(),4);
  for(const row of cfg.compare){const text=await p.locator('[data-compared-stock="'+row.code+'"]').textContent();assert(text.includes(cfg.as_of));assert(text.includes(row.result_id));}
  assert.equal(await p.evaluate(()=>data.series.length),1);assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await p.screenshot({path:path.join(out,'private-comparison-'+width+'.png'),fullPage:true});checks.push({width,height,check:'4 true same-day bound cards /limited descriptive /no source promotion or eager market-series memory',status:'PASS'});
  for(const row of [cfg.compare[0],cfg.compare[2]]){
   await p.locator('[data-open-compared="'+row.identity+'"]').click();await p.waitForFunction(code=>current.code===code&&!document.querySelector('main').hidden,row.code);
   assert.equal(await p.evaluate(()=>result.as_of),cfg.as_of);assert.equal(await p.evaluate(()=>geometry.price.x===geometry.volume.x&&geometry.volume.x===geometry.macd.x),true);
   const event=p.waitForEvent('download');await p.click('#download');const d=await event,actual=JSON.parse(fs.readFileSync(await d.path())),expected=savedChart(row.chart_path);
   assert.deepEqual(actual.core,expected.result);assert.deepEqual(actual.bars,expected.input.bars);assert.deepEqual(actual.macd,expected.indicators.macd);assert.deepEqual(actual.moving_averages,expected.indicators.moving_averages);downloads++;assert.equal(actual.bars.at(-1).date,cfg.as_of);assert.equal(actual.macd.at(-1).histogram,null);for(const curve of Object.values(actual.moving_averages))assert.equal(curve.at(-1),null);assert(actual.core.data_gaps.basis_resets.includes(cfg.as_of));assert.equal(actual.core.comparison.primary_pressure_id,null);
   const before=await p.evaluate(()=>view.end-view.start);await p.click('#zoomIn');assert(await p.evaluate(()=>view.end-view.start)<before);await p.click('#left');assert.equal(await p.evaluate(()=>result.as_of),cfg.as_of);
   await p.click('#all');assert.equal(await p.evaluate(()=>view.end-view.start+1),expected.input.bars.length);
   await p.click('#evidenceButton');assert(await p.locator('#evidence').isVisible());await p.click('#dismiss');
   if(width<900){await p.selectOption('#interaction','query');await p.locator('#chart').scrollIntoViewIfNeeded();const b=await p.locator('#chart').boundingBox();await p.touchscreen.tap(b.x+b.width*.5,b.y+Math.min(b.height*.35,100));assert.equal(await p.evaluate(()=>result.as_of),cfg.as_of);}
   assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await p.click('#compareTab');assert.equal(await p.locator('#compareCards article').count(),4);
  }
  checks.push({width,height,check:'TWSE and TPEX new-day K/core/MA/MACD and explicit warmup-null exact downloads /sync/zoom/pan/touch/evidence/return',status:'PASS'});
  // Remove and replace without ranking or automatic selection.
  const last=cfg.compare[3];await p.locator('[data-remove-compare="'+last.identity+'"]').click();await p.waitForSelector('#compareStatus[data-scope="LIMITED_DESCRIPTIVE"]');assert.equal(await p.locator('#compareCards article').count(),3);
  await p.getByRole('button',{name:'搜尋',exact:true}).click();await p.fill('#marketSearch',cfg.short.code);await p.locator('[data-compare-id="'+cfg.short.identity+'"]').click();await p.click('#compareTab');await p.waitForSelector('#compareStatus[data-scope="REFUSED"]');assert((await p.locator('#compareStatus').textContent()).includes('歷史不足'));checks.push({width,height,check:'explicit remove/replace with retained insufficient-history stock refuses comparison',status:'PASS'});
  if(cfg.gap_case){
   const g=cfg.gap_case;await p.evaluate(id=>window.openResearchStock(id),g.identity);await p.waitForFunction(code=>current.code===code&&!document.querySelector('main').hidden,g.code);
   assert.deepEqual(await p.evaluate(()=>result.data_gaps),g.data_gaps);
   if(g.query_date){await p.selectOption('#queryDate',g.query_date);assert((await p.locator('#readout').textContent()).includes('缺值'));}
   assert.equal(await p.evaluate(()=>result.as_of),cfg.as_of);assert(await p.evaluate(()=>geometry.priceLow>0));
   checks.push({width,height,check:'actual source-boundary and retained gap flags unchanged /no zero imputation',status:'PASS'});
  }
  await p.click('#radarTab');assert((await p.locator('#radarSummary').textContent()).includes(cfg.event_stocks+'檔股票／'+cfg.event_records+'筆原候選事件'));
  assert.equal(await p.evaluate(()=>document.querySelector('#radarDate').value),cfg.as_of);
  const row=cfg.event_case;await p.selectOption('#radarMarket',row.market);const btn=p.locator('[data-radar-stock="'+row.code+'"]').first();await btn.locator('xpath=ancestor::details').evaluate(n=>n.open=true);await btn.click();await p.waitForFunction(code=>current.code===code&&!document.querySelector('main').hidden,row.code);
  assert.equal(await p.evaluate(()=>result.as_of),cfg.as_of);if(await p.locator('#evidence').isVisible())await p.click('#dismiss');checks.push({width,height,check:'true current radar stock/event counts distinct /first-observed date /event-to-original evidence',status:'PASS'});
  await p.screenshot({path:path.join(out,'private-chart-'+width+'.png'),fullPage:true});
  for(const row of cfg.refused){
   await p.getByRole('button',{name:'搜尋',exact:true}).click();await p.fill('#marketSearch',row.code);await p.locator('[data-market-code="'+row.code+'"]').click();assert(await p.locator('main').isHidden());assert((await p.locator('#workStatus').textContent()).includes(row.code));
  }
  checks.push({width,height,check:'quality-refused and missing-anchor rows keep refusal /no stale chart',status:'PASS'});
  await context.close();
 }
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 fs.writeFileSync(path.join(out,'summary.json'),JSON.stringify({status:'PASS_REAL_PRIVATE_BROWSER',checks,downloads,page_errors:errors,external_origins:external,android:'NOT_TESTED_NEW_BUILD'},null,2));console.log(JSON.stringify({status:'PASS',checks:checks.length,downloads}));
 }catch(e){fs.writeFileSync(path.join(out,'failure.json'),JSON.stringify({error:e.message,stack:e.stack,checks,downloads,page_errors:errors,external_origins:external},null,2));throw e}
 finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
