/* Directed real Chromium display checks. No numeric producer or market requests. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const {chromium}=require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'));
const app=path.join(__dirname,'..'),repo=path.join(app,'..');
const input=process.env.P03_READABLE_DIR||path.join(__dirname,'output/readable2');
const output=process.env.P03_READABLE_EVIDENCE||path.join(__dirname,'validation_readability_20261024/browser');
const parent=path.join(repo,'deliveries/m1-p03-structure-state-20261024/artifacts');
fs.mkdirSync(output,{recursive:true});
const html=fs.readFileSync(path.join(input,'M1_P03_structure_state_readable_v02.html')),oldHtml=fs.readFileSync(path.join(parent,'M1_P03_structure_state_v01.html'));
const expected=JSON.parse(fs.readFileSync(path.join(parent,'structure-state.json'))),layer=JSON.parse(fs.readFileSync(path.join(parent,'chart-layer.json')));
const checks=[],errors=[],outside=[],measurements=[],downloads=[];
const ok=(name,fn)=>{fn();checks.push(name);};
const state=page=>page.evaluate(()=>P03Inspect());
async function date(page,d){await page.fill('#manualDate',d);await page.dispatchEvent('#manualDate','change');}
async function capture(page,name,end='#p03Events'){
 await page.evaluate(()=>scrollTo(0,0));await page.waitForTimeout(60);
 const a=await page.locator('#p03Bar').boundingBox(),b=await page.locator(end).boundingBox();
 await page.screenshot({path:path.join(output,name+'.png'),fullPage:true,clip:{x:0,y:Math.floor(a.y),width:page.viewportSize().width,height:Math.ceil(b.y+b.height-a.y+8)}});
}
async function run(){
 for(const n of ['structure-state.json','chart-layer.json','facts-input.json','scenario.json','role-selection.json'])ok('unchanged-bytes:'+n,()=>assert.deepEqual(fs.readFileSync(path.join(input,n)),fs.readFileSync(path.join(parent,n))));
 const server=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html; charset=utf-8');res.end(req.url==='/old'?oldHtml:html);});
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const url=`http://127.0.0.1:${server.address().port}`,browser=await chromium.launch({executablePath:process.env.CODEX_BROWSER_EXECUTABLE_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 try{
  // Geometry comparison only, without repainting/saving any historical PNG.
  const prior=await browser.newPage({viewport:{width:390,height:844}});await prior.goto(url+'/old');await prior.waitForFunction(()=>!!window.P03Inspect);await prior.click('#p03OpenCase');await prior.click('#p03Local');
  const before=await state(prior);await prior.close();
  for(const viewport of [{width:1280,height:1000},{width:390,height:844},{width:844,height:390}]){
   const w=viewport.width,context=await browser.newContext({viewport,isMobile:w<900,hasTouch:w<900,deviceScaleFactor:1}),page=await context.newPage();
   page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(!r.url().startsWith(url)&&!r.url().startsWith('blob:'))outside.push(r.url());});
   await page.goto(url);await page.waitForFunction(()=>!!window.P03Readability);await page.click('#p03OpenCase');
   let s=await state(page),exp=await page.evaluate(()=>P03Export());
   ok(w+':all-records-events-exact-old-output',()=>{assert.deepEqual(exp.structure_state.records,expected.records);assert.deepEqual(exp.structure_state.events,expected.events);assert.equal(exp.view_version,'p03-existing-chart/0.2');});
   ok(w+':all-original-input-values-kept',()=>{assert.equal(exp.structure_state.evaluated_prefix_fingerprint,layer.frame_map[expected.as_of].source_prefix_fingerprint);assert.equal(exp.structure_state.historical_signal_eligible,false);});
   for(const view of ['Wide','Local']){
    await page.click('#p03'+view);s=await state(page);
    const text=await page.locator('#p03Events').innerText(),refs=await page.locator('#p03References').innerText();
    ok(w+':'+view+':visible-dates-close-state-reference',()=>{
     for(const d of ['2026-10-12','2026-10-13','2026-10-14','2026-10-15','2026-10-16'])assert.match(text,new RegExp(d));
     assert.match(text,/27.00/);assert.match(text,/原突破已記錄/);assert.match(text,/返回後P0-3：證據不足/);
     assert.match(text,/26.85/);assert.match(text,/整理 → 轉強/);assert.match(refs,/原突破參照.*26.95/);assert.match(refs,/返回階段高點.*26.85/);assert.match(refs,/研究下緣.*20.25/);
    });
    ok(w+':'+view+':three-distinct-reference-roles',()=>{assert.equal(s.geometry.references.length,3);assert.equal(new Set(s.geometry.references.map(r=>r.role)).size,3);assert.equal(s.geometry.references.find(r=>r.role==='ORIGINAL_BOX_UPPER').price,'26.95');});
    ok(w+':'+view+':axis-and-cursor-synchronized',()=>{assert.equal(s.chartGeometry.panes_share_axis,true);assert.equal(new Set(s.chartGeometry.pane_cursor_x).size,1);assert.equal(s.snapshot.as_of,expected.as_of);assert.deepEqual(s.snapshot.current,expected.records.at(-1));});
    const layout=await page.evaluate(()=>{const z=document.querySelector('#panelZoom').getBoundingClientRect(),c=document.querySelector('#chart').getBoundingClientRect();return {z:{x:z.x-c.x,y:z.y-c.y,width:z.width,height:z.height},font:getComputedStyle(document.querySelector('#p03State')).fontSize,buttons:[...document.querySelectorAll('#panelZoom button')].map(e=>({width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height})),doc:document.documentElement.scrollWidth,inner:innerWidth};});
    ok(w+':'+view+':zoom-controls-touch-size-and-contained',()=>{assert.ok(layout.buttons.every(b=>b.width>=44&&b.height>=44));assert.ok(layout.z.x+layout.z.width<=s.chartGeometry.width);assert.ok(layout.doc<=layout.inner);});
    await capture(page,view.toLowerCase()+'-'+w);
   }
   const geom=await page.evaluate(()=>{const c=document.querySelector('#chart');return {height:c.clientHeight,zoomY:parseFloat(document.querySelector('#panelZoom').style.top)};});
   s=await state(page);
   ok(w+':zoom-between-price-and-volume-label',()=>{assert.ok(geom.zoomY>geom.height*.53);assert.ok(geom.zoomY+44<geom.height*.67-9);});
   if(w===390){
    measurements.push({viewport:w,previous:before.chartGeometry,current:s.chartGeometry,previous_plot_width:before.chartGeometry.right-before.chartGeometry.left,current_plot_width:s.chartGeometry.right-s.chartGeometry.left});
    ok('390:more-real-candle-width-without-smaller-text',()=>{assert.ok(s.chartGeometry.right-s.chartGeometry.left>before.chartGeometry.right-before.chartGeometry.left+70);assert.equal(s.chartGeometry.priceLow,before.chartGeometry.priceLow);assert.equal(s.chartGeometry.priceHigh,before.chartGeometry.priceHigh);});
   }
   const volume=await page.locator('#p03Volume').innerText();
   ok(w+':neutral-volume-own-label-and-original-raw-evidence',()=>{assert.match(volume,/量觀察/);assert.match(volume,/較前一保存筆/);assert.match(volume,/不判好壞/);assert.match(volume,/不是整帶代表量/);assert.deepEqual(s.snapshot.current.evidence,expected.records.at(-1).evidence);});
   await page.locator('#p03Provenance').evaluate(e=>e.open=true);
   const sources=await page.locator('#p03ProvenanceBody').innerText();
   ok(w+':source-date-roles-split-without-changing-values',()=>{assert.match(sources,/原價位K日期\n2026-01-27/);assert.match(sources,/原價位K日期\n2025-11-19/);assert.match(sources,/候選來源末轉折日\n2026-07-14/);assert.match(sources,/候選確認日\n2026-09-01/);assert.match(sources,/角色可知日/);assert.match(sources,/實際後來選取時間\n2026-10-24/);assert.doesNotMatch(sources,/原值發生／候選來源末轉折/);});
   await capture(page,'sources-'+w,'#p03Provenance');await page.locator('#p03Provenance').evaluate(e=>e.open=false);
   await page.locator('#p03References [data-role="ORIGINAL_BOX_FLOOR"]').click();
   const targeted=await page.locator('#evidenceBody .p03SourceCard').count();
   ok(w+':reference-evidence-access-moved-outside-candles',()=>assert.equal(targeted,1));
   await page.click('#dismiss');await page.click('#p03Evidence');const drawer=await page.locator('#evidenceBody').innerText();
   ok(w+':existing-drawer-retained-and-date-labels-improved',()=>{assert.match(drawer,/保留的突破與狀態路徑/);assert.match(drawer,/原價位K日期/);assert.match(drawer,/原核心supporting／opposing/);});
   await page.locator('#evidenceBody').getByRole('button',{name:'定位原K 2025-11-19',exact:true}).click();s=await state(page);
   ok(w+':source-location-no-date-state-change',()=>{assert.equal(s.snapshot.as_of,expected.as_of);assert.deepEqual(s.snapshot.current,expected.records.at(-1));});
   await page.click('#p03Local');await page.selectOption('#interaction','pan');await page.locator('#chart').scrollIntoViewIfNeeded();let a=await state(page),box=await page.locator('#chart').boundingBox();
   await page.mouse.move(box.x+100,box.y+120);await page.mouse.down();await page.mouse.move(box.x+160,box.y+120,{steps:5});await page.mouse.up();let b=await state(page);
   ok(w+':pan-no-analysis-or-state-change',()=>{assert.ok(b.view.start<a.view.start);assert.deepEqual(b.snapshot,a.snapshot);});
   if(w<900){await page.tap('#zoomIn');const t=await state(page);ok(w+':touch-zoom-preserves-JSON',()=>{assert.ok(t.view.end-t.view.start<b.view.end-b.view.start);assert.deepEqual(t.snapshot,b.snapshot);});}
   await page.selectOption('#interaction','query');await page.locator('#chart').scrollIntoViewIfNeeded();box=await page.locator('#chart').boundingBox();await page.mouse.move(box.x+90,box.y+120);const q=await state(page);
   ok(w+':query-cursor-sync-without-state-change',()=>{assert.equal(new Set(q.chartGeometry.pane_cursor_x).size,1);assert.deepEqual(q.snapshot,b.snapshot);});
   for(const day of ['2026-10-12','2026-10-13','2026-10-15']){
    await date(page,day);const snap=(await state(page)).snapshot,read=await page.evaluate(()=>P03Readability());
    const title=await page.locator('#p03State').innerText();
    ok(w+':prefix-'+day,()=>{assert.deepEqual(snap.current,expected.records.find(r=>r.date===day));assert.deepEqual(snap.events,expected.events.filter(e=>e.date<=day));assert.ok(!read.events.includes('2026-10-16'));if(day==='2026-10-12'){assert.match(title,/返回後角色尚不可知/);assert.ok(!title.includes('2021-10-18'));assert.match(read.events,/原突破已記錄/);assert.match(read.events,/返回後P0-3：證據不足/);assert.ok(!read.events.includes('26.85'));assert.ok(!read.source_dates.includes('26.85'));assert.ok(!read.events.includes('2026-10-13'));}});
    const wait=page.waitForEvent('download');await page.click('#p03Download');const dl=await wait,target=path.join(output,`download-${w}-${day}.json`);await dl.saveAs(target);const actual=JSON.parse(fs.readFileSync(target)),direct=await page.evaluate(()=>P03Export());
    ok(w+':download-'+day,()=>assert.deepEqual(actual,direct));downloads.push({file:path.basename(target),bytes:fs.statSync(target).size,sha256:crypto.createHash('sha256').update(fs.readFileSync(target)).digest('hex')});
   }
   if(w===390){await date(page,'2026-10-12');await page.click('#p03Local');await capture(page,'breakout-prefix-'+w);}
   await date(page,expected.as_of);await page.click('#years5');const full=await state(page);ok(w+':full-history-kept',()=>assert.equal(full.view.end-full.view.start+1,1213));
   await page.selectOption('#analysisMode','ADJUSTED_CANDIDATE');const unavailable=await state(page);ok(w+':no-source-fallback-or-stale-events',()=>{assert.equal(unavailable.ready,false);assert.equal(unavailable.snapshot.events.length,0);});
   await page.selectOption('#stock','8069');await date(page,'2026-09-30');const other=await state(page);ok(w+':other-stock-no-layer-reuse',()=>{assert.equal(other.snapshot.source_matched,false);assert.equal(other.snapshot.events.length,0);});
   const width=await page.evaluate(()=>({doc:document.documentElement.scrollWidth,inner:innerWidth}));ok(w+':no-horizontal-overflow',()=>assert.ok(width.doc<=width.inner));
   await context.close();
  }
  ok('no-JavaScript-errors',()=>assert.deepEqual(errors,[]));ok('no-outside-network-requests',()=>assert.deepEqual(outside,[]));
  const report={status:'PASS',browser:await browser.version(),checks:checks.length,passed:checks,measurements,downloads,errors,outside,old_65_94_not_rerun:true,android:'NOT_TESTED_NEW_BUILD'};
  fs.writeFileSync(path.join(output,'browser-report.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:'PASS',checks:checks.length,browser:report.browser}));
 }catch(e){fs.writeFileSync(path.join(output,'browser-failure.json'),JSON.stringify({status:'FAIL',error:e.stack,checks,errors,outside},null,2)+'\n');throw e;}
 finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
