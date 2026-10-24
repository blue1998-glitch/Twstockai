const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict'),crypto=require('crypto');
const pw=require('/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');const root=__dirname,fixture=path.resolve('core-next'),fragment=fs.readFileSync('/workspace/major-pressure-context.html','utf8'),checks=[],errors=[];let browser,server;
const html=`<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>@font-face{font-family:Noto;src:url('/font')} :root{--foreground:#d7e2ef;--background:#101923;--border:#405469;--popover:#213244;--popover-foreground:#e5effb;--destructive:#ff7777;--red:#ff786f;--green:#38cdaa;--viz-series-1:#c3a8f4;--viz-series-2:#79b5e8} body{background:var(--background);color:var(--foreground);font-family:Noto,system-ui;margin:12px}.viz-controls{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}.btn{font:inherit;padding:8px;min-height:44px;background:var(--popover);color:var(--foreground);border:1px solid var(--border);border-radius:6px}.form-control{box-sizing:border-box;width:100%;font:inherit}.text-small{font-size:12px}.form-label{display:block}[hidden]{display:none!important} </style></head><body>${fragment}</body></html>`;
const pass=(size,name)=>checks.push({size,name,status:'PASS'});
(async()=>{try{server=http.createServer((q,r)=>{if(q.url==='/d3'){r.setHeader('Content-Type','text/javascript');r.end(fs.readFileSync(path.join(fixture,'d3.min.js')));}else if(q.url==='/font'){r.end(fs.readFileSync(process.env.M1_QA_FONT||path.join(fixture,'qa-font.otf')));}else {r.setHeader('Content-Type','text/html;charset=utf-8');r.end(html);}});await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;
 browser=await pw.chromium.launch({executablePath:process.env.CODEX_BROWSER_EXECUTABLE_PATH||path.join(fixture,'browser/runtime/chromium'),headless:true,args:['--no-sandbox','--disable-gpu','--disable-software-rasterizer']});
 for(const size of [{width:390,height:844},{width:844,height:390},{width:320,height:740},{width:1280,height:900}]){
  const context=await browser.newContext({viewport:size,deviceScaleFactor:1,hasTouch:size.width!==1280,isMobile:size.width!==1280,reducedMotion:'reduce'}),page=await context.newPage();page.on('pageerror',e=>errors.push(e.stack));
  await page.route('https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js',route=>route.fulfill({contentType:'text/javascript',body:fs.readFileSync(path.join(fixture,'d3.min.js'))}));
  await page.goto(origin);await page.locator('.price .candle').first().waitFor();await page.evaluate(()=>document.fonts.ready);
  const source=await page.locator('.source').textContent(),data=JSON.parse(source),bars=data.bars;
  const parent=JSON.parse(fs.readFileSync('box-reference/publish/docs/visual-discussion/20261019_previous_box_representative/source.json','utf8'));
  assert.deepEqual(bars,parent.bars);for(const k of ['source_id','frame_id','chart_base','analysis_as_of'])assert.equal(data[k],parent[k]);
  assert.equal(data.user_region.records,39);assert.equal(data.user_region.user_selected_representative.date,'2025-05-13');assert.equal(data.user_region.user_selected_representative.high,'31.40');
  assert.equal(data.major_pressure_band.start_month,'2023-06');assert.equal(data.major_pressure_band.end_month,'2025-04');assert.equal(data.major_pressure_band.exact_start,null);assert.equal(data.major_pressure_band.exact_end,null);assert.equal(data.major_pressure_band.representative,null);
  assert.equal(data.major_display.full_month_context_records,463);assert.equal(data.major_display.display_month_window_is_approved_box_membership,false);
  pass(size,'source1213/frame/basis fixed;local39-row repMay13 recorded;major priority and month precision kept without invented exact boundaries');
  assert.equal(await page.locator('.price .candle').count(),493);assert.equal(await page.locator('.volume .vol').count(),493);
  for(const svg of ['price','volume']){
    assert.equal(await page.locator('.'+svg+' .major-fill').count(),1);assert.equal(await page.locator('.'+svg+' .local-fill').count(),1);
    const stops=await page.locator('.'+svg+' linearGradient stop').evaluateAll(ns=>ns.map(n=>({offset:n.getAttribute('offset'),opacity:n.getAttribute('stop-opacity')})));
    assert.equal(stops.length,4);assert.equal(stops[0].opacity,'0');assert.equal(stops[1].opacity,'1');assert.equal(stops[2].opacity,'1');assert.equal(stops[3].opacity,'0');
    assert.equal(await page.locator('.'+svg+' .major-fill').getAttribute('stroke'),'none');
  }
  const g=await page.locator('.price').evaluate(svg=>{
    const ticks=[...svg.querySelectorAll('.yaxis .tick')].map(t=>({v:Number(t.querySelector('text').textContent),y:Number(t.getAttribute('transform').match(/,([^)]*)\)/)[1])}));
    const a=ticks[0],b=ticks[1],axisOffset=window.d3.axisLeft(window.d3.scaleLinear()).offset(),map=v=>a.y-axisOffset+(v-a.v)*(b.y-a.y)/(b.v-a.v),fill=svg.querySelector('.major-fill');
    return {top:+fill.getAttribute('y'),bottom:+fill.getAttribute('y')+ +fill.getAttribute('height'),expectTop:map(39.25),expectBottom:map(28.45)};
  });
  assert(Math.abs(g.top-g.expectTop)<.1&&Math.abs(g.bottom-g.expectBottom)<.1);
  if([390,1280].includes(size.width))await page.screenshot({path:path.join(root,'major-context-'+size.width+'.png'),fullPage:true});
  pass(size,'493-row long view aligns K/volume;full month-context envelope28.45..39.25 with faded unknown edge months;no region border');
  await page.locator('[data-action="reference"]').click();assert.equal(await page.locator('#major-pressure-context').getAttribute('data-selected-date'),'2025-05-13');
  assert((await page.locator('.readout').textContent()).includes('高31.40'));assert.equal(await page.locator('.source-point.legacy-g1').count(),0);assert.equal(await page.locator('line.reference.legacy-g1').count(),0);
  const clipped=await page.locator('.price').evaluate(svg=>+svg.querySelector('.major-fill').getAttribute('y')<+svg.querySelector('rect[data-chart-frame]').getAttribute('y'));
  assert(clipped);assert.equal(JSON.parse(await page.locator('.source').textContent()).major_display.wick_high,'39.25');
  pass(size,'local view queries confirmedMay13;offscreen G1 not faked;full major envelope clips rather than recomputing visible-window max');
  await page.locator('[data-action="background"]').click();
  assert.equal(await page.locator('#major-pressure-context').getAttribute('data-selected-date'),'2026-10-16');
  const expected=bars.filter(b=>b.date>='2023-06-01').length;assert.equal(+await page.locator('#major-pressure-context').getAttribute('data-count'),expected);
  for(const cl of ['legacy-g1','repeat-high','local-rep','jan27'])assert.equal(await page.locator('.source-point.'+cl).count(),1);
  assert.equal(await page.locator('line.reference.latest').count(),1);
  if([390,1280].includes(size.width))await page.screenshot({path:path.join(root,'major-overview-'+size.width+'.png'),fullPage:true});
  pass(size,'same source overview contains real oldG1/Mar12/localMay13/Jan27 dates and latest27.30 without promoting oldG1 to unique major representative');
  await page.locator('[data-action="recent"]').click();assert.equal(await page.locator('.context-fill').count(),0);assert.equal(await page.locator('.source-point.local-rep,.source-point.legacy-g1').count(),0);assert.equal(await page.locator('.source-point.jan27').count(),1);
  const n=+await page.locator('#major-pressure-context').getAttribute('data-count');await page.locator('[data-action="in"]').click();assert(+await page.locator('#major-pressure-context').getAttribute('data-count')<n);
  assert.equal(await page.locator('#major-pressure-context').getAttribute('data-analysis-as-of'),'2026-10-16');assert.equal(await page.locator('.source').textContent(),source);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  const labels=await page.locator('.price text,.volume text').evaluateAll(ns=>ns.filter(n=>n.getAttribute('visibility')!=='hidden').map(n=>{const b=n.getBoundingClientRect();return {left:b.left,right:b.right};}));assert(labels.every(b=>b.left>=-1&&b.right<=size.width+1));
  pass(size,'recent view has no fake historical region or source point;zoom works;source/monthly uncertainty/analysis fixed and responsive labels fit');
  await context.close();
 }
 assert.deepEqual(errors,[]);fs.writeFileSync(path.join(root,'browser-report.json'),JSON.stringify({status:'PASS',checks,browser:browser.version(),fragment_sha256:crypto.createHash('sha256').update(fragment).digest('hex'),javascript_errors:errors,physical_android:'NOT_TESTED',inline_chat_host:'NOT_INDEPENDENTLY_EXECUTED',cdn:'QA fulfilled exact downloaded pinned D3 bytes; user CDN access not established',file_policy:'NOT_RETRIED_OR_BYPASSED'},null,2));console.log('PASS',checks.length);
}catch(e){fs.writeFileSync(path.join(root,'browser-report.json'),JSON.stringify({status:'FAIL',checks,error:e.stack},null,2));console.error(e);process.exitCode=1;}finally{if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));}})();
