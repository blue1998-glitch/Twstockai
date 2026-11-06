'use strict';
// Real Chromium layout and input against shipped data, including offscreen cards.
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict'),crypto=require('crypto');
const folder=path.resolve(process.env.M1_HURDLE_DIR),out=path.resolve(process.env.M1_LABEL_BROWSER_OUTPUT_DIR);
const source=fs.readFileSync(path.join(folder,'M1_v0_19_candle_regions_v04.html'));
const checks=[],errors=[],requests=[];let browser,server;
fs.mkdirSync(out,{recursive:true});
function pass(name,extra={}){checks.push({name,status:'PASS',...extra});}
function intersects(a,b){return a.x<b.x+b.width&&a.x+a.width>b.x&&a.y<b.y+b.height&&a.y+a.height>b.y;}
(async()=>{try{
 const pw=require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES?path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'):'playwright');
 browser=await pw.chromium.launch({headless:true,executablePath:process.env.CODEX_BROWSER_EXECUTABLE_PATH||'/usr/bin/chromium'});
 server=http.createServer((q,r)=>{r.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});r.end(source);});await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const url='http://127.0.0.1:'+server.address().port;
 for(const size of [{width:1280,height:900},{width:390,height:844},{width:844,height:390},{width:320,height:740}]){
  const mobile=size.width!==1280,context=await browser.newContext({viewport:size,isMobile:mobile,hasTouch:mobile,deviceScaleFactor:mobile?2:1,acceptDownloads:true}),page=await context.newPage();
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url())&&new URL(r.url()).origin!==url)requests.push(r.url());});
  await page.addInitScript(()=>{window.paintedText=[];const old=CanvasRenderingContext2D.prototype.fillText;CanvasRenderingContext2D.prototype.fillText=function(t,x,y,...rest){paintedText.push({text:String(t),x,y,width:this.measureText(t).width});return old.call(this,t,x,y,...rest);};});
  await page.goto(url);await page.waitForFunction(()=>typeof manual!=='undefined'&&manual&&view.end===1212);await page.locator('#pointDetails > summary').click();
  const identity=()=>page.evaluate(()=>[current.key,current.source.id,frame.frame_id,frame.as_of,frame.chart_base]);
  const originalIdentity=await identity();
  async function settle(){await page.waitForFunction(()=>geometry.height===$('chart').getBoundingClientRect().height&&$('chart').width===Math.round($('chart').getBoundingClientRect().width*devicePixelRatio));}
  async function checkLayout(label){
   await settle();const values=await page.evaluate(()=>{paintedText.length=0;draw();const c=$('chart').getBoundingClientRect();return {expected:(manual?.references||[]).filter(r=>Number(r.reference.raw_high)>=geometry.priceLow&&Number(r.reference.raw_high)<=geometry.priceHigh).map(r=>r.reference.id).sort(),chart:{x:c.x,y:c.y,width:c.width,height:c.height},right:geometry.right,price:geometry.price,axisText:paintedText.filter(t=>t.x===geometry.right+3&&t.y>=geometry.price.top&&t.y<=geometry.price.bottom),sourceHits:hits.filter(h=>h.id.startsWith('manual:')).map(h=>({id:h.id,index:h.index})),priceLow:geometry.priceLow,priceHigh:geometry.priceHigh};});
   const labels=page.locator('.manualPriceLabel'),ids=await labels.evaluateAll(nodes=>nodes.map(n=>n.dataset.reference).sort());assert.deepEqual(ids,values.expected);
   const boxes=[];for(const node of await labels.all()){
    const box=await node.boundingBox();assert(box.width>=44&&box.height>=44);assert(box.x>=values.chart.x+values.right+39);
    assert(box.y>=values.chart.y+values.price.top-1&&box.y+box.height<=values.chart.y+values.price.bottom+1);
    assert(box.x+box.width<=values.chart.x+values.chart.width);
    assert(!intersects(box,await page.locator('#zoomIn').boundingBox()));assert(!intersects(box,await page.locator('#zoomOut').boundingBox()));
    for(const other of boxes)assert(!intersects(box,other));boxes.push(box);
    for(const t of values.axisText)assert(!intersects(box,{x:values.chart.x+t.x,y:values.chart.y+t.y-8,width:t.width,height:16}));
    const text=await node.textContent();assert(/G[123]/.test(text)&&/\d+\.\d{2}/.test(text));
    const y=Number(await node.getAttribute('data-actual-y')),price=Number(await node.getAttribute('data-price'));
    const actual=values.price.bottom-(price-values.priceLow)/(values.priceHigh-values.priceLow)*(values.price.bottom-values.price.top);assert(Math.abs(y-actual)<1e-7);
   }
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   assert.deepEqual(await identity(),originalIdentity);pass('labels avoid candles/axis/zoom/each other and retain exact line ordinate: '+label,{size,labels:ids});return values;
  }
  const recent=await checkLayout('recent24 source offscreen');assert.deepEqual(recent.expected,['G1']);assert.equal(recent.sourceHits.length,0);assert.equal(recent.priceLow,18.426);assert.equal(recent.priceHigh,37.274);
  await page.evaluate(()=>scrollTo(0,$('chartWrap').getBoundingClientRect().top+scrollY));assert(await page.evaluate(()=>$('manualPanel').getBoundingClientRect().bottom<0));
  await page.locator('#chartWrap').screenshot({path:path.join(out,'after-'+size.width+'.png')});
  const oldSelection=await page.evaluate(()=>JSON.stringify(selected())),oldView=await page.evaluate(()=>({...view}));
  const g1=page.locator('.manualPriceLabel[data-reference="G1"]');if(mobile)await g1.tap();else await g1.click();
  assert((await page.locator('#evidenceTitle').textContent()).includes('G1'));assert((await page.locator('#evidenceBody').textContent()).includes('2023-11-28'));await page.locator('#dismiss').click();
  assert.deepEqual(await page.evaluate(()=>({...view})),oldView);assert.equal(await page.evaluate(()=>JSON.stringify(selected())),oldSelection);
  await g1.focus();await page.keyboard.press('Enter');assert(await page.locator('#evidence').isVisible());await page.locator('#dismiss').click();assert.deepEqual(await page.evaluate(()=>({...view})),oldView);
  pass('offscreen source label is visible with cards scrolled away; touch/click/Enter opens exact evidence without moving date/cursor',{size});
  await page.locator('[data-hurdle="G1"] .hurdleLocate').click();const located=await checkLayout('G1 real source visible');assert(located.sourceHits.some(h=>h.id.startsWith('manual:G1:')));
  assert.equal(await page.evaluate(()=>base().bars[view.cursor].date),'2023-11-28');await page.locator('#chartWrap').screenshot({path:path.join(out,'G1-source-'+size.width+'.png')});
  await page.locator('#months24').click();await checkLayout('return24');assert.equal(await page.evaluate(()=>view.end-view.start+1),486);
  await page.locator('[data-hurdle="G3"] .hurdleLocate').click();for(let i=0;i<4;i++)await page.locator('#zoomIn').click();
  const g3=await checkLayout('G3 source visible, G1/G2 below axis');assert.deepEqual(g3.expected,['G3']);assert.equal(g3.sourceHits.filter(h=>h.id.startsWith('manual:G3:')).length,5);
  assert((await page.locator('[data-hurdle="G1"]').textContent()).includes('低於目前價格軸'));assert((await page.locator('[data-hurdle="G2"]').textContent()).includes('低於目前價格軸'));
  await page.locator('#chartWrap').screenshot({path:path.join(out,'G3-source-'+size.width+'.png')});
  await page.locator('#years5').click();const all=await checkLayout('all five years, three labels');assert.deepEqual(all.expected,['G1','G2','G3']);assert.equal(all.sourceHits.length,7);
  await page.locator('#focus').click();await checkLayout('focus three labels');await page.locator('#exitFocus').click();
  await page.locator('#recent').click();const short=await checkLayout('60 recent bars, all above axis');assert.deepEqual(short.expected,[]);assert.equal(short.sourceHits.length,0);
  for(const id of ['G1','G2','G3'])assert((await page.locator(`[data-hurdle="${id}"]`).textContent()).includes('高於目前價格軸'));
  await page.locator('#months24').click();await checkLayout('24-month label restored');
  const event=page.waitForEvent('download');await page.locator('#download').click();const file=await event;const exported=JSON.parse(fs.readFileSync(await file.path(),'utf8'));
  assert.equal(exported.view_version,'candle-region-chart-view/0.4');assert.equal(exported.manual_hurdles.review.references[0].raw_high,'35.50');assert.equal(exported.new_history_analysis.frame.frame_id,originalIdentity[2]);
  pass('label layout does not alter downloaded source/frame/precision or manual case',{size});
  await page.selectOption('#asOf','2026-10-15');assert.equal(await page.locator('.manualPriceLabel').count(),0);assert.equal(await page.evaluate(()=>selected().manual_hurdles),null);
  await page.selectOption('#asOf','2026-10-16');assert.equal(await page.locator('.manualPriceLabel').count(),1);
  await page.selectOption('#stock','2884');assert.equal(await page.locator('.manualPriceLabel').count(),0);assert.equal(await page.evaluate(()=>manual),null);
  const adjusted=await page.evaluate(()=>{const s=series.find(s=>s.price_mode!=='RAW_CANDIDATE');return {code:s.code,key:s.key};});await page.selectOption('#stock',adjusted.code);await page.selectOption('#mode',adjusted.key);
  assert.equal(await page.locator('.manualPriceLabel').count(),0);assert.equal(await page.evaluate(()=>manual),null);
  pass('other dates, stocks and Adjusted cannot retain stale manual line labels',{size});await context.close();
 }
 assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
 fs.writeFileSync(path.join(out,'label-report.json'),JSON.stringify({status:'PASS',browser:browser.version(),source_html_sha256:crypto.createHash('sha256').update(source).digest('hex'),checks,javascript_errors:errors,external_requests:requests,physical_android:'NOT_TESTED_NEW_BUILD',file_open:'PRIOR_POLICY_BLOCKER_NOT_RETRIED'},null,2));console.log('PASS',checks.length,'label checks');
}catch(error){fs.writeFileSync(path.join(out,'label-report.json'),JSON.stringify({status:'FAIL',error:error.stack,checks,javascript_errors:errors,external_requests:requests},null,2));console.error(error);process.exitCode=1;}finally{if(browser)await browser.close();if(server)await new Promise(resolve=>server.close(resolve));}})();
