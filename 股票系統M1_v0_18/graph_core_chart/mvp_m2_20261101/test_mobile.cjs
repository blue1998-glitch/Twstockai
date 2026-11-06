'use strict';
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict'),crypto=require('crypto');
const here=__dirname,folder=path.resolve(here,'../output/mvp_m2_20261101'),out=process.env.M1_M2_BROWSER_OUTPUT||path.join(here,'browser-first');fs.mkdirSync(out,{recursive:true});
const raw=fs.readFileSync(path.join(folder,'M1_graph_comparison_mvp_m2_v01.html')),oracle=JSON.parse(fs.readFileSync(path.join(here,'download-oracle.json'))),checks=[],errors=[],external=[];
const canonical=v=>Array.isArray(v)?'['+v.map(canonical).join(',')+']':v&&typeof v==='object'?'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}':JSON.stringify(v);
const hash=v=>'sha256:'+crypto.createHash('sha256').update(canonical(v)).digest('hex');
let browser,server;
(async()=>{try{
 const pw=require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'));browser=await pw.chromium.launch({headless:true,executablePath:'/usr/bin/chromium'});
 server=http.createServer((q,r)=>{r.writeHead(200,{'Content-Type':'text/html;charset=utf-8'});r.end(raw)});await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;
 for(const size of [{width:1280,height:900},{width:390,height:844},{width:844,height:390},{width:320,height:740}]){
  const mobile=size.width!==1280,ctx=await browser.newContext({viewport:size,isMobile:mobile,hasTouch:mobile,acceptDownloads:true}),p=await ctx.newPage();
  const pass=name=>checks.push({name,size,status:'PASS'});p.on('pageerror',e=>errors.push(e.stack));p.on('request',r=>{if(/^https?:/.test(r.url())&&new URL(r.url()).origin!==origin)external.push(r.url());});
  await p.goto(origin);await p.waitForFunction(()=>typeof comparison!=='undefined');assert(await p.locator('#comparisonView').isHidden());
  const original=await p.evaluate(()=>JSON.stringify(selected()));await p.click('#compareTab');assert(await p.locator('main').isHidden());
  assert.equal(await p.locator('.stockCard').count(),4);assert(await p.evaluate(()=>comparison.stocks.every(s=>s.as_of==='2026-10-16')));
  assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.equal(await p.evaluate(()=>JSON.stringify(selected())),original);pass('fixed-date comparison toggle without changing original selection or overflow');
  assert((await p.locator('[data-code="2884"] [data-nearest-distance]').textContent()).includes('NULL'));
  assert.equal(await p.locator('[data-code="6488"] [data-box-id]').count(),8);
  for(const code of ['6488','8069'])assert((await p.locator(`[data-code="${code}"]`).textContent()).includes('×1000不增加精度'));
  assert(await p.evaluate(()=>comparison.stocks.every(s=>s.primary_pressure_id===null&&s.classification_quality==='NOT_VALIDATED')));pass('2884 null,6488 all8 ties,original volume precision and formal limits visible');
  for(const code of ['1101','2884','6488','8069']){
   const saved=await p.evaluate(code=>comparison.stocks.find(s=>s.code===code),code),body=await p.locator(`[data-code="${code}"]`).textContent();
   for(const kinds of Object.values(saved.latest_confirmed_by_scale))for(const points of Object.values(kinds))for(const point of points){assert(body.includes(point.occurred_at));assert(body.includes(point.confirmed_at));assert(body.includes(point.price));}
   for(const point of saved.pending_extrema){assert(body.includes(point.high.price));assert(body.includes(point.low.price));}
   assert(body.includes('整箱位置'));assert(body.includes('pending'));assert(body.includes('歷史available_at UNKNOWN'));
  }
  pass('confirmed dates/prices and all pending extrema visibly match saved per-stock evidence');
  await p.screenshot({path:path.join(out,'comparison-'+size.width+'.png'),fullPage:true});
  for(const c of oracle.cases){
   await p.locator(`[data-open-stock="${c.code}"]`).click();assert(await p.locator('#comparisonView').isHidden());
   assert.deepEqual(await p.evaluate(()=>[current.code,result.as_of]),[c.code,'2026-10-16']);
   await p.click('#zoomIn');await p.selectOption('#queryDate','2026-10-15');assert((await p.locator('#readout').textContent()).includes('2026-10-15'));
   assert(await p.evaluate(()=>geometry.price.x(view.cursor)===geometry.volume.x(view.cursor)&&geometry.volume.x(view.cursor)===geometry.macd.x(view.cursor)));
   const event=p.waitForEvent('download');await p.click('#download');const d=await event;const value=JSON.parse(fs.readFileSync(await d.path()));assert.equal(hash(value),c.fingerprint);pass('stock jump/shared cursor/zoom/exact unchanged JSON '+c.code);
   await p.click('#compareTab');await p.waitForTimeout(700);
  }
  const ties=await p.locator('[data-code="6488"] [data-box-id]').evaluateAll(ns=>ns.map(n=>n.dataset.boxId));
  for(const id of ties){await p.locator(`.ties [data-box-id="${id}"]`).click();assert.equal(await p.locator('#boxSelect').inputValue(),id);assert.equal(await p.evaluate(()=>bars()[view.cursor].date),await p.evaluate(id=>box(id).source_end,id));assert.equal(await p.evaluate(()=>current.code),'6488');await p.click('#compareTab');}
  pass('all8 explicit related boxes locate exact original structure without picking a primary');
  await p.click('#chartTab');await p.selectOption('#stock','1101');await p.selectOption('#asOf','2025-05-14');
  assert(await p.locator('#manualAudit').isHidden());assert(await p.evaluate(()=>!result.boxes.some(b=>b.id==='sha256:8bc16b7b1f4d83cc1cdf9f4ffc5644941e58dcd2356a6c1fd02b66695d43bdd5')));
  await p.click('#compareTab');assert((await p.locator('#comparisonView h1').textContent()).includes('2026-10-16'));
  await p.locator('[data-open-stock="1101"]').click();assert.equal(await p.locator('#asOf').inputValue(),'2026-10-16');
  await p.click('#evidenceButton');assert.equal(await p.locator('#evidenceBody section').count(),3);await p.click('#compareTab');assert(await p.locator('#evidence').isHidden());pass('fixed comparison independent of old chart dates; manual hindsight separated; original evidence preserved');
  assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await p.click('#chartTab');await p.locator('#chartWrap').screenshot({path:path.join(out,'chart-return-'+size.width+'.png')});
  await ctx.close();
 }
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({status:'PASS',browser:browser.version(),checks,precision_downloads:16,javascript_errors:errors,external_requests:external,html_sha256:crypto.createHash('sha256').update(raw).digest('hex'),new_android:'NOT_TESTED_USER_DEVICE',prior_MG3_android:'USER_REPORTED_NORMAL_FIRST_CASE',test_transport:'LOOPBACK_HTTP_FILE_POLICY_NOT_RETRIED'},null,2));console.log('PASS',checks.length,'checks /16 exact JSON downloads');
}catch(e){fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({status:'FAIL',error:e.stack,checks,errors,external},null,2));console.error(e);process.exitCode=1;}finally{if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));}})();
