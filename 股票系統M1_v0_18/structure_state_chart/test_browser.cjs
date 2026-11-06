/* Real Chromium over ephemeral loopback HTTP; never file:// or deployment. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'));
const root=path.join(__dirname,'..'),input=process.env.P03_ARTIFACT_DIR||path.join(__dirname,'output/v01');
const output=process.env.P03_BROWSER_OUTPUT||path.join(__dirname,'validation_20261024/browser');
fs.mkdirSync(output,{recursive:true});
const html=fs.readFileSync(path.join(input,'M1_P03_structure_state_v01.html'));
const expected=JSON.parse(fs.readFileSync(path.join(input,'structure-state.json')));
const layer=JSON.parse(fs.readFileSync(path.join(input,'chart-layer.json')));
const source=JSON.parse(fs.readFileSync(path.join(root,'cross_scale_chart/generated/comparison-data.json')));
const checks=[],errors=[],outside=[];
function ok(name,fn){fn();checks.push(name);}
async function snapshot(page){return page.evaluate(()=>P03Inspect());}
async function chooseDate(page,date){await page.fill('#manualDate',date);await page.dispatchEvent('#manualDate','change');}
async function shot(page,name){await page.evaluate(()=>scrollTo(0,0));await page.waitForTimeout(100);const a=await page.locator('#p03Bar').boundingBox(),b=await page.locator('#cursorValues').boundingBox();await page.screenshot({path:path.join(output,name+'.png'),fullPage:true,clip:{x:0,y:Math.floor(a.y),width:page.viewportSize().width,height:Math.ceil(b.y+b.height-a.y+8)}});}
async function run(){
 const server=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html; charset=utf-8');res.end(html);});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const url=`http://127.0.0.1:${server.address().port}/chart.html`;
 const browser=await chromium.launch({executablePath:process.env.CODEX_BROWSER_EXECUTABLE_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 try{
  for(const viewport of [{width:1280,height:1000},{width:390,height:844},{width:844,height:390}]){
   const context=await browser.newContext({viewport,isMobile:viewport.width<900,hasTouch:viewport.width<900,deviceScaleFactor:1});
   const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(!r.url().startsWith('http://127.0.0.1:')&&!r.url().startsWith('blob:'))outside.push(r.url());});
   await page.goto(url);await page.waitForFunction(()=>!!window.P03Inspect,{timeout:60000});
   ok(`${viewport.width}:initial-mode-choice-preserved`,()=>assert.equal(layer.result.historical_signal_eligible,false));
   let state=await snapshot(page);ok(`${viewport.width}:initial-insufficient`,()=>{assert.equal(state.snapshot.source_matched,false);assert.equal(state.snapshot.current.state,'INSUFFICIENT');});
   await page.click('#p03OpenCase');state=await snapshot(page);
   ok(`${viewport.width}:explicit-case-exact-source`,()=>{assert.equal(state.snapshot.as_of,'2026-10-16');assert.equal(state.snapshot.source_matched,true);assert.deepEqual(state.snapshot.current,expected.records.at(-1));assert.equal(state.snapshot.current.state,'STRENGTHENING');});
   const auxiliary=await page.locator('#p03Auxiliary').innerText();ok(`${viewport.width}:direct-support-opposition-missing-qualification`,()=>{assert.match(auxiliary,/支持/);assert.match(auxiliary,/反面/);assert.match(auxiliary,/缺證/);assert.match(auxiliary,/正式原箱未核定/);});
   let exp=await page.evaluate(()=>P03Export());
   ok(`${viewport.width}:all-original-OHLCV-MA-MACD-exact`,()=>{const a=exp.saved_selection.new_history_analysis;assert.deepEqual(a.bars,source.bars);assert.deepEqual(a.macd,source.macd);assert.deepEqual(a.moving_averages,source.moving_averages);assert.equal(a.frame.frame_id,source.source_frame_id);});
   await page.click('#p03Wide');await shot(page,'wide-'+viewport.width);state=await snapshot(page);
   ok(`${viewport.width}:wide-retained-history`,()=>{assert.equal(state.snapshot.records.length,1213);assert.equal(state.view.end-state.view.start+1,486);});
   ok(`${viewport.width}:K-volume-MACD-same-axis`,()=>{assert.equal(state.chartGeometry.panes_share_axis,true);assert.equal(new Set(state.chartGeometry.pane_cursor_x).size,1);});
   const caseWidth=await page.evaluate(()=>({document:document.documentElement.scrollWidth,viewport:innerWidth}));ok(`${viewport.width}:case-no-overflow`,()=>assert.ok(caseWidth.document<=caseWidth.viewport));
   await page.locator('#p03Legacy').evaluate(e=>e.open=true);await page.check('#p03LegacyOverlays');let oldLayer=await snapshot(page);await page.uncheck('#p03LegacyOverlays');await page.locator('#p03Legacy').evaluate(e=>e.open=false);
   ok(`${viewport.width}:legacy-overlay-opt-in-does-not-change-state`,()=>assert.deepEqual(oldLayer.snapshot,state.snapshot));
   for(const [day,want]of [['2026-10-13','CONSOLIDATING'],['2026-10-14','STRENGTHENING'],['2026-10-15','CONSOLIDATING'],['2026-10-16','STRENGTHENING']]){
    await chooseDate(page,day);state=await snapshot(page);const oracle=expected.records.find(r=>r.date===day);
    ok(`${viewport.width}:date-${day}-UI-JSON-oracle`,()=>{assert.equal(state.snapshot.current.state,want);assert.deepEqual(state.snapshot.current,oracle);assert.ok(state.snapshot.events.every(e=>e.date<=day));assert.equal(state.snapshot.source_binding.frame_id,layer.frame_map[day].frame_id);});
   }
   await chooseDate(page,'2026-10-12');state=await snapshot(page);
   ok(`${viewport.width}:future-pullback-price-not-exposed`,()=>{assert.equal(state.snapshot.current.state,'INSUFFICIENT');assert.equal(state.snapshot.reference_catalog.find(r=>r.role==='PULLBACK_HIGH').source_reference.price,null);assert.ok(state.snapshot.events.some(e=>e.kind==='ORIGINAL_BREAKOUT_CLOSE'&&e.date==='2026-10-12'));});
   await chooseDate(page,'2026-10-16');await page.click('#p03Local');state=await snapshot(page);
   ok(`${viewport.width}:local-does-not-change-analysis`,()=>{assert.equal(state.snapshot.as_of,'2026-10-16');assert.ok(state.view.end-state.view.start+1>=25);assert.ok(state.view.end-state.view.start+1<100);});
   ok(`${viewport.width}:original-breakout-marker-visible-and-retained`,()=>assert.ok(state.geometry.events.some(e=>e.kind==='ORIGINAL_BREAKOUT_CLOSE'&&e.date==='2026-10-12')));
   const hint=await page.locator('#p03References').innerText();
   ok(`${viewport.width}:off-axis-floor-not-fake-plotted`,()=>{assert.equal(state.geometry.references.find(r=>r.role==='ORIGINAL_BOX_FLOOR').inAxis,false);assert.ok(state.chartGeometry.priceLow>20.25);assert.match(hint,/20.25.*價格軸外/);});
   assert.equal(await page.locator('.p03LineLabel[data-role="ORIGINAL_BOX_FLOOR"]').count(),0);checks.push(`${viewport.width}:no-wrong-axis-label`);
   await shot(page,'local-'+viewport.width);
   await page.selectOption('#interaction','query');await page.locator('#chart').scrollIntoViewIfNeeded();let rect=await page.locator('#chart').boundingBox();
   await page.mouse.move(rect.x+state.chartGeometry.left+35,rect.y+160);await page.mouse.down();await page.mouse.move(rect.x+state.chartGeometry.left+(state.chartGeometry.right-state.chartGeometry.left)*.65,rect.y+160,{steps:4});await page.mouse.up();let dragged=await snapshot(page);
   ok(`${viewport.width}:actual-drag-query-keeps-analysis`,()=>{assert.equal(dragged.snapshot.as_of,'2026-10-16');assert.equal(dragged.chartGeometry.panes_share_axis,true);assert.notEqual(dragged.view.cursor,state.view.cursor);});
   await page.selectOption('#interaction','pan');await page.locator('#chart').scrollIntoViewIfNeeded();rect=await page.locator('#chart').boundingBox();let beforePan=await snapshot(page);await page.mouse.move(rect.x+100,rect.y+170);await page.mouse.down();await page.mouse.move(rect.x+160,rect.y+170,{steps:5});await page.mouse.up();let afterPan=await snapshot(page);
   ok(`${viewport.width}:actual-pan-keeps-state`,()=>{assert.equal(afterPan.snapshot.as_of,'2026-10-16');assert.ok(afterPan.view.start<beforePan.view.start);});
   if(viewport.width<900){await page.tap('#zoomIn');let tapped=await snapshot(page);ok(`${viewport.width}:touch-zoom-operable`,()=>{assert.equal(tapped.snapshot.as_of,'2026-10-16');assert.ok(tapped.view.end-tapped.view.start<afterPan.view.end-afterPan.view.start);});}
   await page.selectOption('#interaction','query');
   await page.click('#p03Evidence');const body=await page.locator('#evidenceBody').innerText();
   ok(`${viewport.width}:role-and-later-selection-disclosure`,()=>{assert.match(body,/研究假設/);assert.match(body,/角色可知/);assert.match(body,/2026-10-24/);});
   await page.getByRole('button',{name:'定位原K 2025-11-19',exact:true}).click();state=await snapshot(page);
   ok(`${viewport.width}:true-source-location-no-analysis-jump`,()=>{assert.equal(state.snapshot.as_of,'2026-10-16');assert.equal(source.bars[state.view.cursor].date,'2025-11-19');});
   await page.click('#p03Wide');await page.click('#queryPrev');const after=await snapshot(page);
   ok(`${viewport.width}:cursor-query-keeps-state-and-analysis`,()=>{assert.deepEqual(after.snapshot,state.snapshot);assert.equal(after.snapshot.as_of,'2026-10-16');});
   await page.click('#years5');state=await snapshot(page);ok(`${viewport.width}:full-1213-history-kept`,()=>assert.equal(state.view.end-state.view.start+1,1213));
   await page.click('#p03Wide');await page.click('#zoomIn');const zoom=await snapshot(page);await page.click('#left');const pan=await snapshot(page);
   ok(`${viewport.width}:zoom-pan-no-date-jump`,()=>{assert.ok(zoom.view.end-zoom.view.start<486);assert.equal(pan.snapshot.as_of,'2026-10-16');assert.ok(pan.view.start<=zoom.view.start);});
   await page.click('#p03Local');
   const download=page.waitForEvent('download');await page.click('#p03Download');const dl=await download;
   const target=path.join(output,`download-${viewport.width}.json`);await dl.saveAs(target);const actual=JSON.parse(fs.readFileSync(target));
   const direct=await page.evaluate(()=>P03Export());
   ok(`${viewport.width}:actual-downloaded-JSON-exact`,()=>{assert.deepEqual(actual,direct);assert.deepEqual(actual.structure_state.current,expected.records.at(-1));assert.equal(actual.structure_state.historical_signal_eligible,false);});
   await page.selectOption('#analysisMode','ADJUSTED_CANDIDATE');state=await snapshot(page);exp=await page.evaluate(()=>P03Export());
   ok(`${viewport.width}:missing-adjusted-no-fallback-no-stale-structure`,()=>{assert.equal(state.ready,false);assert.equal(state.snapshot.source_matched,false);assert.equal(exp.saved_selection,null);assert.equal(exp.structure_state.current.state,'INSUFFICIENT');assert.equal(exp.structure_state.events.length,0);});
   await page.selectOption('#stock','8069');await chooseDate(page,'2026-09-30');state=await snapshot(page);exp=await page.evaluate(()=>P03Export());
   ok(`${viewport.width}:existing-adjusted-route-preserved-not-duplicated`,()=>{assert.equal(state.ready,true);assert.equal(exp.request.price_mode,'ADJUSTED_CANDIDATE');assert.equal(state.snapshot.source_matched,false);assert.equal(exp.saved_selection.saved_analysis.analysis.frame.price_mode,'ADJUSTED_CANDIDATE');});
   const width=await page.evaluate(()=>({document:document.documentElement.scrollWidth,viewport:innerWidth}));
   ok(`${viewport.width}:no-horizontal-overflow`,()=>assert.ok(width.document<=width.viewport));
   await page.click('#p03OpenCase');await page.click('#p03Replay');await page.waitForTimeout(4300);state=await snapshot(page);
   ok(`${viewport.width}:four-day-replay-ends-on-saved-day`,()=>{assert.equal(state.snapshot.as_of,'2026-10-16');assert.equal(state.snapshot.current.state,'STRENGTHENING');});
   await context.close();
  }
  ok('no-JavaScript-errors',()=>assert.deepEqual(errors,[]));ok('no-external-network-requests',()=>assert.deepEqual(outside,[]));
  fs.writeFileSync(path.join(output,'browser-report.json'),JSON.stringify({status:'PASS',browser:await browser.version(),checks:checks.length,passed:checks,errors,outside,scope:'REAL_CHROMIUM_HTTP_NOT_ANDROID',android:'NOT_TESTED_NEW_BUILD'},null,2));
  console.log(JSON.stringify({status:'PASS',checks:checks.length,browser:await browser.version(),output}));
 }catch(e){fs.writeFileSync(path.join(output,'browser-failure.json'),JSON.stringify({status:'FAIL',error:e.stack,passed:checks,errors,outside},null,2));throw e;}
 finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
