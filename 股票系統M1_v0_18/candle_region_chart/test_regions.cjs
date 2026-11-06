'use strict';
// Actual Chromium input/rendering on shipped HTML. HTTP only: known file policy
// blocker is carried forward; mobile emulation is not physical Android.
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict'),crypto=require('crypto');
const folder=path.resolve(process.env.M1_HURDLE_DIR),out=path.resolve(process.env.M1_REGION_BROWSER_OUTPUT_DIR);
const source=fs.readFileSync(path.join(folder,'M1_v0_19_candle_regions_v04.html'));
const checks=[],errors=[],external=[];let browser,server;
fs.mkdirSync(out,{recursive:true});
function pass(name,size,extra={}){checks.push({name,status:'PASS',size,...extra});}
(async()=>{try{
 const pw=require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES?path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'):'playwright');
 browser=await pw.chromium.launch({headless:true,executablePath:process.env.CODEX_BROWSER_EXECUTABLE_PATH||'/usr/bin/chromium'});
 server=http.createServer((q,r)=>{r.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});r.end(source);});await new Promise(r=>server.listen(0,'127.0.0.1',r));const url='http://127.0.0.1:'+server.address().port;
 for(const size of [{width:1280,height:900},{width:390,height:844},{width:844,height:390},{width:320,height:740}]){
  const mobile=size.width!==1280,ctx=await browser.newContext({viewport:size,isMobile:mobile,hasTouch:mobile,deviceScaleFactor:mobile?2:1,acceptDownloads:true}),page=await ctx.newPage();
  page.on('pageerror',e=>errors.push(e.stack));page.on('request',r=>{if(/^https?:/.test(r.url())&&new URL(r.url()).origin!==url)external.push(r.url());});
  await page.addInitScript(()=>{window.painted=[];const original=CanvasRenderingContext2D.prototype.fillText;CanvasRenderingContext2D.prototype.fillText=function(t,x,y,...rest){painted.push({text:String(t),x,y});return original.call(this,t,x,y,...rest);};});
  await page.goto(url);await page.waitForFunction(()=>typeof regions!=='undefined'&&regions&&frame.as_of==='2026-10-16');
  const identity=()=>page.evaluate(()=>[current.key,current.source.id,frame.frame_id,frame.as_of,frame.chart_base]);const ident=await identity();
  const selection=await page.evaluate(()=>JSON.stringify(selected()));
  const windowValue=()=>page.evaluate(()=>({start:view.start,end:view.end}));
  const shot=async name=>{await page.locator('#chartWrap').screenshot({path:path.join(out,name+'-'+size.width+'.png')});};
  async function layout(){assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.deepEqual(await identity(),ident);}
  assert.equal(await page.locator('#interaction').inputValue(),'query');assert.equal(await page.locator('#pointDetails').getAttribute('open'),null);
  assert.equal(await page.evaluate(()=>view.end-view.start+1),486);assert.equal(await page.evaluate(()=>regions.regions.find(r=>r.id==='G1').exact_start_date),null);
  await layout();await shot('recent24');pass('initial24 month real bars/default query/representative details collapsed/no horizontal overflow',size);
  const layer=await page.evaluate(()=>regions);const g1=layer.regions.find(r=>r.id==='G1'),g2=layer.regions.find(r=>r.id==='G2'),c=layer.regions.find(r=>r.id==='C_RIGHT');
  assert.equal(g2.exact_start_date,'2023-01-16');assert.equal(g2.exact_end_date,'2023-08-16');assert.equal(g2.representative.raw_high,'40.25');assert.equal(g1.exact_start_date,null);assert.equal(c.end_date,null);
  for(const r of [g1,g2]){assert.equal(r.price_bounds,null);assert.equal(r.total_volume,null);}
  assert.equal(layer.volume_evidence.length,2);assert.deepEqual(layer.volume_evidence.map(e=>e.bar.date),['2023-10-18','2023-11-30']);
  pass('original case limits retained: exact G2 dates, unknown G1 edge/prices/region volume/C extent, true separate volume references',size);
  for(const id of ['G1','G2','C_RIGHT']){
   await page.locator('#'+({G1:'focusG1',G2:'focusG2',C_RIGHT:'focusC'}[id])).click();await layout();
   const r=layer.regions.find(r=>r.id===id);assert.deepEqual(await windowValue(),{start:r.navigation.start,end:r.navigation.end});
   assert.equal(await page.evaluate(()=>JSON.stringify(selected())),selection);
   await page.locator('#regionEvidence').click();const evidence=await page.locator('#evidenceBody').textContent();
   assert(evidence.includes('未定'));assert(evidence.includes('Raw'));if(id==='G2'){assert(evidence.includes('2023-01-16'));assert(evidence.includes('2023-08-16'));assert(evidence.includes('34494589'));assert(evidence.includes('30022247'));}
   if(id==='G1'){assert(evidence.includes('110992007'));assert(evidence.includes('106415572'));assert(evidence.includes('2023-09-14'));}
   await page.locator('#evidence').screenshot({path:path.join(out,'evidence-'+id+'-'+size.width+'.png')});await page.locator('#dismiss').click();await shot('focus-'+id);
   pass('time-region focus and source evidence do not change analysis/download: '+id,size);
  }
  await page.locator('#focusG2').click();
  const refs=await page.evaluate(()=>{painted.length=0;draw();return {text:painted.map(p=>p.text),source:hits.filter(h=>h.id.startsWith('manual:G2:')).map(h=>base().bars[h.index].date),shared:geometry.price.x===geometry.volume.x&&geometry.volume.x===geometry.macd.x};});
  assert(refs.text.some(t=>t.includes('G2')));assert.deepEqual(refs.source,['2023-05-02']);assert(refs.shared);
  pass('G2 time band rendered, representative stays true source date, K/volume/MACD share x function',size);
  await page.locator('#focusG1').click();const volumeHits=await page.evaluate(()=>hits.filter(h=>h.id.startsWith('region:volume:')).map(h=>base().bars[h.index].date));assert.deepEqual(volumeHits,['2023-10-18','2023-11-30']);
  assert(await page.evaluate(()=>hits.some(h=>h.id==='region:C'&&base().bars[h.index].date==='2024-01-19')));
  pass('G1 volume markers and C marker use actual dates, not representative day or future bars',size);
  await page.locator('#months24').click();assert.equal(await page.evaluate(()=>view.end-view.start+1),486);
  await page.locator('#queryDate').selectOption('2023-01-16');
  let rows=await page.evaluate(()=>({row:base().bars[view.cursor],next:base().bars[view.cursor+1],after:base().bars[view.cursor+2],m:base().macd[view.cursor]}));
  for(const v of ['2023-01-16','36.55','36.90','36.15','36.50','34494589'])assert((await page.locator('#cursorValues').textContent()).includes(v));
  assert.deepEqual(rows.row,g2.endpoints.start);await page.locator('#queryNext').click();assert.equal(await page.locator('#queryDate').inputValue(),rows.next.date);await page.locator('#queryNext').click();assert.equal(await page.locator('#queryDate').inputValue(),rows.after.date);
  assert.equal(rows.next.date,'2023-01-17');assert.equal(rows.after.date,'2023-01-30');await page.locator('#queryPrev').click();assert.equal(await page.locator('#queryDate').inputValue(),'2023-01-17');
  assert.deepEqual(await identity(),ident);pass('exact OHLCV/volume preserved; query next/prev traverses actual Jan17→Jan30 holiday gap without analysis jump',size);
  await page.locator('#months24').click();await page.locator('#chartWrap').scrollIntoViewIfNeeded();
  // Native mouse or CDP touch input, not a call to the implementation's query helper.
  async function drag(){const b=await page.locator('#chart').boundingBox(),g=await page.evaluate(()=>geometry);const a={x:Math.round(b.x+g.left+(g.right-g.left)*.3),y:Math.round(b.y+g.price.top+25)},z={x:Math.round(b.x+g.left+(g.right-g.left)*.65),y:a.y};
   if(mobile){const session=await ctx.newCDPSession(page);await session.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{...a,id:1}]});await session.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{...z,id:1}]});await session.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await session.detach();}
   else {await page.mouse.move(a.x,a.y);await page.mouse.down();await page.mouse.move(z.x,z.y,{steps:8});await page.mouse.up();}}
  const oldWindow=await windowValue(),oldCursor=await page.evaluate(()=>view.cursor);await drag();assert.deepEqual(await windowValue(),oldWindow);assert.notEqual(await page.evaluate(()=>view.cursor),oldCursor);assert.deepEqual(await identity(),ident);
  await shot('query-drag');pass('native one-pointer query drag changes cursor only, leaves date/window/source unchanged',size,{input:mobile?'CDP touch':'mouse'});
  await page.selectOption('#interaction','pan');await page.locator('#chartWrap').scrollIntoViewIfNeeded();await drag();assert.notDeepEqual(await windowValue(),oldWindow);assert.deepEqual(await identity(),ident);pass('explicit pan drag moves window, not analysis',size);
  if(mobile){await page.locator('#months24').click();await page.locator('#chartWrap').scrollIntoViewIfNeeded();const b=await page.locator('#chart').boundingBox(),g=await page.evaluate(()=>geometry),y=Math.round(b.y+g.price.top+25),mid=b.x+(g.left+g.right)/2,dist=(g.right-g.left)*.12,s=await ctx.newCDPSession(page);const points=d=>[{x:mid-d,y,id:1},{x:mid+d,y,id:2}];const before=await page.evaluate(()=>view.end-view.start+1);await s.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:points(dist)});await s.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:points(dist*1.6)});await s.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await s.detach();assert((await page.evaluate(()=>view.end-view.start+1))<before);assert.deepEqual(await identity(),ident);pass('native two-finger pinch zoom keeps fixed analysis identity',size);}
  await page.selectOption('#interaction','query');await page.locator('#draftTools > summary').click();await page.locator('#queryDate').selectOption('2023-01-16');await page.locator('#draftStart').click();await page.locator('#queryDate').selectOption('2023-08-16');await page.locator('#draftEnd').click();
  const draft=JSON.parse(await page.locator('#draftText').inputValue());assert.equal(draft.status,'DRAFT_NOT_SUBMITTED_NOT_APPROVED');assert.equal(draft.case_update,'NONE_REQUIRES_USER_SUBMISSION_AND_REVIEW');assert.deepEqual(draft.start,g2.endpoints.start);assert.deepEqual(draft.end,g2.endpoints.end);assert.equal(draft.order,'FORWARD');assert.equal(draft.binding.frame_id,ident[2]);assert.equal(draft.binding.source_id,ident[1]);assert.equal(draft.binding.analysis_as_of,'2026-10-16');assert.equal(draft.binding.chart_base,ident[4]);assert.equal(await page.evaluate(()=>JSON.stringify(selected())),selection);
  const e=page.waitForEvent('download');await page.locator('#draftDownload').click();const download=await e;assert.deepEqual(JSON.parse(fs.readFileSync(await download.path(),'utf8')),draft);await page.locator('#draftTools').screenshot({path:path.join(out,'draft-'+size.width+'.png')});
  pass('separate draft download exact endpoint rows/identity/status; approved case and main JSON unchanged',size);
  await page.locator('#queryDate').selectOption('2023-01-16');await page.locator('#draftEnd').click();await page.locator('#queryDate').selectOption('2023-08-16');await page.locator('#draftStart').click();assert.equal(JSON.parse(await page.locator('#draftText').inputValue()).order,'REVERSED_UNRESOLVED');
  await page.locator('#draftClear').click();const empty=JSON.parse(await page.locator('#draftText').inputValue());assert.equal(empty.start,null);assert.equal(empty.end,null);assert(await page.locator('#draftDownload').isDisabled());await page.locator('#draftStart').click();await page.reload();await page.waitForFunction(()=>typeof regions!=='undefined'&&regions);assert.equal(await page.evaluate(()=>draftValue().start),null);
  pass('reversed drafts not auto-reordered; clear and reload erase memory-only draft',size);
  await page.locator('#draftTools > summary').click();await page.locator('#draftStart').click();await page.selectOption('#asOf','2026-10-15');assert.equal(await page.evaluate(()=>regions),null);assert.equal(await page.evaluate(()=>draftValue().start),null);assert(await page.locator('#regionControls').isHidden());assert.equal(await page.evaluate(()=>selected().manual_regions),null);assert.equal(await page.evaluate(()=>frame.index+1),1212);assert.equal(await page.locator('#queryDate option').count(),1212);assert.equal(await page.evaluate(()=>base().bars[frame.index].date),'2026-10-15');
  await page.selectOption('#asOf','2026-10-16');await page.locator('#draftStart').click();await page.selectOption('#stock','2884');assert.equal(await page.evaluate(()=>regions),null);assert.equal(await page.evaluate(()=>draftValue().start),null);
  const old=await page.evaluate(()=>{const s=series.find(s=>s.price_mode!=='RAW_CANDIDATE');return {code:s.code,key:s.key};});await page.selectOption('#stock',old.code);await page.selectOption('#mode',old.key);assert.equal(await page.evaluate(()=>regions),null);assert.equal(await page.evaluate(()=>selected().manual_regions),null);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));pass('analysis/source changes clear draft/layer; other stock/Adjusted unbound; past query options exclude future bars',size);
  await ctx.close();
 }
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 fs.writeFileSync(path.join(out,'region-report.json'),JSON.stringify({status:'PASS',browser:browser.version(),source_html_sha256:crypto.createHash('sha256').update(source).digest('hex'),checks,javascript_errors:errors,external_requests:external,physical_android:'NOT_TESTED_NEW_BUILD',file_open:'PRIOR_POLICY_BLOCKER_NOT_RETRIED'},null,2));console.log('PASS',checks.length,'region checks');
}catch(error){fs.writeFileSync(path.join(out,'region-report.json'),JSON.stringify({status:'FAIL',error:error.stack,checks,javascript_errors:errors,external_requests:external},null,2));console.error(error);process.exitCode=1;}finally{if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));}})();
