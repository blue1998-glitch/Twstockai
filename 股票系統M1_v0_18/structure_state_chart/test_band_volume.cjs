/* Real Chromium / temporary loopback HTTP; never source GETs or file://. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'));
const repo=path.join(__dirname,'../..'),parent=path.join(repo,'deliveries/m1-p03-readability-20261024/artifacts');
const input=process.env.BAND_VOLUME_DIR||path.join(__dirname,'output/band-volume-initial');
const output=process.env.BAND_VOLUME_EVIDENCE||path.join(__dirname,'validation_band_volume_20261024/browser');fs.mkdirSync(output,{recursive:true});
const html=fs.readFileSync(path.join(input,'M1_P03_explicit_band_volume_v03.html'));
const expected=JSON.parse(fs.readFileSync(path.join(input,'band-volume.json'))),p03=JSON.parse(fs.readFileSync(path.join(parent,'structure-state.json')));
const checks=[],errors=[],outside=[],downloads=[];const ok=(label,fn)=>{fn();checks.push(label);};
const snap=page=>page.evaluate(()=>({band:BandVolumeInspect(),p03:P03Inspect()}));
async function date(page,d){await page.fill('#manualDate',d);await page.dispatchEvent('#manualDate','change');}
async function shot(page,name){await page.evaluate(()=>scrollTo(0,0));await page.waitForTimeout(60);const a=await page.locator('#p03Bar').boundingBox(),b=await page.locator('#p03Events').boundingBox();await page.screenshot({path:path.join(output,name+'.png'),fullPage:true,clip:{x:0,y:Math.floor(a.y),width:page.viewportSize().width,height:Math.ceil(b.y+b.height-a.y+8)}});}
async function download(page,name){const waiting=page.waitForEvent('download');await page.click('#p03Download');const dl=await waiting,target=path.join(output,name+'.json');await dl.saveAs(target);return JSON.parse(fs.readFileSync(target));}
(async()=>{
 for(const n of ['structure-state.json','chart-layer.json','facts-input.json','scenario.json','role-selection.json'])ok('original-five-bytes:'+n,()=>assert.deepEqual(fs.readFileSync(path.join(input,n)),fs.readFileSync(path.join(parent,n))));
 const server=http.createServer((q,r)=>{r.setHeader('Content-Type','text/html; charset=utf-8');r.end(html);});await new Promise(r=>server.listen(0,'127.0.0.1',r));const url=`http://127.0.0.1:${server.address().port}`;
 const browser=await chromium.launch({executablePath:process.env.CODEX_BROWSER_EXECUTABLE_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 try{for(const viewport of [{width:1280,height:1000},{width:390,height:844},{width:844,height:390}]){
  const w=viewport.width,context=await browser.newContext({viewport,isMobile:w<900,hasTouch:w<900,deviceScaleFactor:1}),page=await context.newPage();
  page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(!r.url().startsWith(url)&&!r.url().startsWith('blob:'))outside.push(r.url());});
  await page.goto(url);await page.waitForFunction(()=>!!window.BandVolumeInspect);let s=await snap(page);
  ok(w+':initial-no-implicit-reference',()=>{assert.equal(s.band.snapshot.reference,null);assert.equal(s.band.snapshot.available,false);});
  await page.click('#p03OpenCase');s=await snap(page);
  ok(w+':exact-real-155-saved-case-and-date',()=>{assert.deepEqual(s.band.snapshot,expected.snapshots['2026-10-16']);assert.equal(s.band.snapshot.reference.actual_records,155);assert.equal(s.band.snapshot.reference.max_single_day_shares,'98217134');assert.deepEqual(s.band.snapshot.reference.max_single_day_dates,['2026-01-12']);assert.equal(s.band.snapshot.comparison.delta,'-40779250');});
  ok(w+':P03-all-states-events-and-IDs-unchanged',()=>{assert.deepEqual(s.p03.snapshot.records,p03.records);assert.deepEqual(s.p03.snapshot.events,p03.events);assert.equal(s.p03.snapshot.current.state,'STRENGTHENING');});
  const text=await page.locator('#p03BandVolume').innerText(),previous=await page.locator('#p03Volume').innerText();
  ok(w+':previous-volume-and-complete-maximum-not-mixed',()=>{assert.match(previous,/前筆量觀察/);assert.match(previous,/2026-10-15/);assert.match(text,/98,217,134/);assert.match(text,/57,437,884/);assert.match(text,/-40,779,250/);assert.match(text,/尚未越過/);assert.match(text,/未越不判壞/);assert.match(text,/密集量峰代表線：未實作/);});
  const fixed=s.band.snapshot;
  for(const view of ['Wide','Local']){
   await page.click('#p03'+view);s=await snap(page);
   ok(w+':'+view+':full-band-unaffected-by-visible-window',()=>{assert.deepEqual(s.band.snapshot,fixed);assert.equal(s.p03.view.end-s.p03.view.start+1,view==='Wide'?486:31);assert.equal(s.band.snapshot.reference.source_rows.length,155);});
   ok(w+':'+view+':maximum-line-only-in-volume-pane',()=>{const g=s.band.geometry;assert.equal(g.visible,true);assert.ok(g.y>=g.volumeTop&&g.y<=g.volumeBottom);assert.equal(g.maximum_shares,'98217134');assert.equal(s.p03.chartGeometry.panes_share_axis,true);assert.equal(new Set(s.p03.chartGeometry.pane_cursor_x).size,1);});
   ok(w+':'+view+':actual-source-marker-not-current-date',()=>{assert.deepEqual(s.band.geometry.source_points.map(x=>x.date),view==='Wide'?['2026-01-12']:[]);});
   await shot(page,view.toLowerCase()+'-'+w);
  }
  await page.click('#bandVolumeEvidence');const body=await page.locator('#evidenceBody').innerText();
  ok(w+':original-max-K-and-all-dates-evidence',()=>{assert.match(body,/2026-01-12/);assert.match(body,/98217134/);assert.match(body,/候選確認 2026-09-01/);assert.match(body,/量參照可知 2026-09-01/);assert.match(body,/實際後來選取/);});
  await page.locator('#evidenceBody details').first().evaluate(e=>e.open=true);
  const table=await page.locator('#bandSourceRows tr').count();ok(w+':all-155-source-OHLCV-rows-retained',()=>assert.equal(table,156));
  await page.locator('#evidenceBody details').first().evaluate(e=>e.open=false);
  await page.locator('#evidence').screenshot({path:path.join(output,'source-evidence-'+w+'.png')});
  await page.getByRole('button',{name:'定位最大量原K 2026-01-12',exact:true}).click();s=await snap(page);
  ok(w+':source-location-keeps-analysis-state-and-reference',()=>{assert.equal(s.p03.snapshot.as_of,'2026-10-16');assert.deepEqual(s.band.snapshot,fixed);assert.deepEqual(s.p03.snapshot.current,p03.records.at(-1));});
  await page.click('#p03Local');await page.selectOption('#interaction','pan');await page.locator('#chart').scrollIntoViewIfNeeded();let before=await snap(page),box=await page.locator('#chart').boundingBox();
  await page.mouse.move(box.x+100,box.y+120);await page.mouse.down();await page.mouse.move(box.x+160,box.y+120,{steps:5});await page.mouse.up();let after=await snap(page);
  ok(w+':actual-pan-keeps-reference-and-P03',()=>{assert.ok(after.p03.view.start<before.p03.view.start);assert.deepEqual(after.band.snapshot,before.band.snapshot);assert.deepEqual(after.p03.snapshot,before.p03.snapshot);});
  if(w<900){await page.tap('#zoomIn');after=await snap(page);ok(w+':touch-zoom-keeps-whole-source-reference',()=>assert.deepEqual(after.band.snapshot,fixed));}
  await page.selectOption('#interaction','query');
  for(const d of ['2026-07-14','2026-08-31','2026-09-01','2026-10-12','2026-10-13','2026-10-14','2026-10-15','2026-10-16']){
   await date(page,d);s=await snap(page);const t=await page.locator('#p03BandVolume').innerText();
   ok(w+':historical-prefix-'+d,()=>{assert.deepEqual(s.band.snapshot,expected.snapshots[d]);assert.deepEqual(s.p03.snapshot.current,p03.records.find(r=>r.date===d));assert.ok(s.p03.snapshot.events.every(e=>e.date<=d));if(d<'2026-09-01'){assert.equal(s.band.snapshot.reference,null);assert.ok(!t.includes('98,217,134'));assert.ok(!JSON.stringify(s.band.snapshot).includes('98217134'));}if(d==='2026-10-12'){assert.equal(s.band.snapshot.comparison.relation,'ABOVE');assert.equal(s.p03.snapshot.current.state,'INSUFFICIENT');assert.ok(s.p03.snapshot.events.some(e=>e.kind==='ORIGINAL_BREAKOUT_CLOSE'&&e.date===d));}});
  }
  const actual=await download(page,'download-'+w),direct=await page.evaluate(()=>P03Export());
  ok(w+':actual-download-exact-old-P03-plus-new-facts',()=>{assert.deepEqual(actual,direct);assert.equal(actual.view_version,'p03-existing-chart/0.3');assert.deepEqual(actual.band_volume,expected.snapshots['2026-10-16']);assert.deepEqual(actual.structure_state.current,p03.records.at(-1));});downloads.push('download-'+w+'.json');
  if(w===390){await date(page,'2026-07-14');await page.click('#p03Wide');await shot(page,'not-yet-known-'+w);const old=await download(page,'download-before-confirmation');ok('download-before-confirmation-no-complete-reference',()=>assert.equal(old.band_volume.reference,null));downloads.push('download-before-confirmation.json');await date(page,'2026-10-16');}
  await page.selectOption('#analysisMode','ADJUSTED_CANDIDATE');s=await snap(page);
  ok(w+':missing-Adjusted-no-fallback-no-stale-volume',()=>{assert.equal(s.p03.ready,false);assert.equal(s.band.snapshot.reference,null);assert.equal(s.band.snapshot.available,false);});
  await page.selectOption('#stock','8069');await date(page,'2026-09-30');s=await snap(page);ok(w+':other-stock-cannot-reuse-band',()=>{assert.equal(s.p03.ready,true);assert.equal(s.band.snapshot.reference,null);});
  const width=await page.evaluate(()=>({doc:document.documentElement.scrollWidth,viewport:innerWidth}));ok(w+':no-horizontal-overflow',()=>assert.ok(width.doc<=width.viewport));
  await context.close();
 }
 ok('no-JavaScript-errors',()=>assert.deepEqual(errors,[]));ok('no-outside-network-requests',()=>assert.deepEqual(outside,[]));
 const r={status:'PASS',checks:checks.length,passed:checks,browser:await browser.version(),downloads,errors,outside,scope:'NEW_EXPLICIT_BAND_VOLUME_ONLY_NOT_OLD_SUITE_OR_ANDROID',android:'NOT_TESTED_NEW_BUILD'};fs.writeFileSync(path.join(output,'browser-report.json'),JSON.stringify(r,null,2)+'\n');console.log(JSON.stringify({status:r.status,checks:r.checks,browser:r.browser}));
 }catch(e){fs.writeFileSync(path.join(output,'browser-failure.json'),JSON.stringify({error:e.stack,checks,errors,outside},null,2)+'\n');throw e;}
 finally{await browser.close();await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);process.exitCode=1;});
