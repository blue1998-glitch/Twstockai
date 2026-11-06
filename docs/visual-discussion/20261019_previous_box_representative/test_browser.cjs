const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict'),crypto=require('crypto');
const pw=require('/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');const root=__dirname,fixture=path.resolve('core-next'),fragment=fs.readFileSync('/workspace/box-reference-review.html','utf8'),checks=[],errors=[];let browser,server;
const html=`<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>@font-face{font-family:Noto;src:url('/font')} :root{--foreground:#d7e2ef;--background:#101923;--border:#405469;--popover:#213244;--popover-foreground:#e5effb;--destructive:#ff7777;--red:#ff786f;--green:#38cdaa;--viz-series-1:#c3a8f4} body{background:var(--background);color:var(--foreground);font-family:Noto,system-ui;margin:12px}.viz-controls{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}.btn{font:inherit;padding:8px;min-height:44px;background:var(--popover);color:var(--foreground);border:1px solid var(--border);border-radius:6px}.form-control{box-sizing:border-box;width:100%;font:inherit}.text-small{font-size:12px}.form-label{display:block}[hidden]{display:none!important} </style></head><body>${fragment}</body></html>`;
const pass=(size,name)=>checks.push({size,name,status:'PASS'});
(async()=>{try{server=http.createServer((q,r)=>{if(q.url==='/d3'){r.setHeader('Content-Type','text/javascript');r.end(fs.readFileSync(path.join(fixture,'d3.min.js')));}else if(q.url==='/font'){r.end(fs.readFileSync(process.env.M1_QA_FONT||path.join(fixture,'qa-font.otf')));}else {r.setHeader('Content-Type','text/html;charset=utf-8');r.end(html);}});await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;
 browser=await pw.chromium.launch({executablePath:process.env.CODEX_BROWSER_EXECUTABLE_PATH||path.join(fixture,'browser/runtime/chromium'),headless:true,args:['--no-sandbox','--disable-gpu','--disable-software-rasterizer']});
 for(const size of [{width:390,height:844},{width:844,height:390},{width:320,height:740},{width:1280,height:900}]){
  const context=await browser.newContext({viewport:size,deviceScaleFactor:1,hasTouch:size.width!==1280,isMobile:size.width!==1280,reducedMotion:'reduce'}),page=await context.newPage();page.on('pageerror',e=>errors.push(e.stack));
  await page.route('https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js',route=>route.fulfill({contentType:'text/javascript',body:fs.readFileSync(path.join(fixture,'d3.min.js'))}));
  await page.goto(origin);await page.locator('.price .candle').first().waitFor();await page.evaluate(()=>document.fonts.ready);
  const source=await page.locator('.source').textContent(),data=JSON.parse(source),bars=data.bars;
  const parent=JSON.parse(fs.readFileSync('reviewed-box/publish/docs/visual-discussion/20261019_previous_box_pressure/reviewed_1635/source.json','utf8'));
  assert.deepEqual(bars,parent.bars);assert.deepEqual(data.user_region,parent.user_region);assert.deepEqual(data.region_display,parent.region_display);
  assert.equal(data.user_region.records,39);assert.equal(data.reference_inspection.user_selected_date,null);assert.equal(await page.locator('#box-reference-review').getAttribute('data-selected-date'),'2025-05-13');
  assert.equal(await page.locator('.price .candle').count(),45);assert.equal(await page.locator('.volume .vol').count(),45);
  pass(size,'1213 exact bars,reviewed39-row time range/display/source unchanged;default queryMay13 does not select case representative');
  const foreground=()=>page.locator('.price .candle,.price .wick,.volume .vol').evaluateAll(nodes=>nodes.map(n=>({tag:n.tagName,attrs:[...n.attributes].filter(a=>['x','y','width','height','x1','x2','y1','y2','fill','stroke'].includes(a.name)).map(a=>[a.name,a.value])})));
  const initial=await foreground();
  for(const date of ['2025-04-07','2025-05-13','2025-06-02']){
    await page.locator('[data-ref-date="'+date+'"]').click();const b=bars.find(b=>b.date===date);
    assert.equal(await page.locator('#box-reference-review').getAttribute('data-selected-date'),date);
    const text=await page.locator('.readout').textContent();assert(text.includes('開'+b.open)&&text.includes('高'+b.high)&&text.includes('低'+b.low)&&text.includes('收'+b.close)&&text.includes(Number(b.volume_shares_scaled).toLocaleString('en-US')));
    assert.equal(await page.locator('[data-ref-date="'+date+'"]').getAttribute('aria-pressed'),'true');
    assert.deepEqual(await foreground(),initial);
    if([390,1280].includes(size.width)&&date!=='2025-06-02')await page.screenshot({path:path.join(root,'reference-'+date+'-'+size.width+'.png'),fullPage:true});
  }
  assert.equal(await page.locator('#box-reference-review').getAttribute('data-case-representative'),'NOT_SELECTED');
  assert.equal(await page.locator('.source').textContent(),source);
  pass(size,'all3 reference buttons show exact OHLCV and synchronize guides;foreground marks/geometry and source unchanged;no approval event');
  const g=await page.locator('.price').evaluate(svg=>{const fill=svg.querySelector('.region-fill');return {y:+fill.getAttribute('y'),low:+fill.getAttribute('y')+ +fill.getAttribute('height'),highPoint:+svg.querySelector('.price-date').getAttribute('cy'),lowPoint:+svg.querySelector('.range-low').getAttribute('cy'),opacity:fill.getAttribute('fill-opacity'),stroke:fill.getAttribute('stroke')};});
  assert.equal(g.y,g.highPoint);assert(Math.abs(g.low-g.lowPoint)<1e-7);assert.equal(g.opacity,'0.18');assert.equal(g.stroke,'none');
  assert.equal(await page.locator('.source-point.representative').count(),0);await page.locator('[data-action="recent"]').click();assert.equal(await page.locator('.source-point,.region-fill').count(),0);
  assert.equal(await page.locator('#box-reference-review').getAttribute('data-selected-date'),'2026-10-16');
  pass(size,'full39-row27.65..31.40 borderless display retained;Jan27/old source dates never fake current points');
  await page.locator('[data-ref-date="2025-04-07"]').click();await page.locator('[data-action="next"]').click();assert.equal(await page.locator('#box-reference-review').getAttribute('data-selected-date'),'2025-04-08');
  await page.locator('[data-ref-date="2025-06-02"]').click();await page.locator('[data-action="next"]').click();assert.equal(await page.locator('#box-reference-review').getAttribute('data-selected-date'),'2025-06-03');
  assert.equal(await page.locator('[data-ref-date="2025-06-02"]').getAttribute('aria-pressed'),'false');
  const before=+await page.locator('#box-reference-review').getAttribute('data-count');await page.locator('[data-action="in"]').click();assert(+await page.locator('#box-reference-review').getAttribute('data-count')<before);
  pass(size,'actual-record stepping and query-button pressed state follow date;zoom remains operational');
  assert.equal(await page.locator('#box-reference-review').getAttribute('data-analysis-as-of'),'2026-10-16');
  assert.equal(await page.locator('#box-reference-review').getAttribute('data-case-representative'),'NOT_SELECTED');
  assert.equal(await page.locator('.source').textContent(),source);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  const labels=await page.locator('.price text,.volume text').evaluateAll(nodes=>nodes.filter(n=>n.getAttribute('visibility')!=='hidden').map(n=>{const b=n.getBoundingClientRect();return {left:b.left,right:b.right};}));assert(labels.every(b=>b.left>=-1&&b.right<=size.width+1));
  pass(size,'source/analysis/undecided case stay immutable;all reference controls and labels fit viewport');
  await context.close();
 }
 assert.deepEqual(errors,[]);fs.writeFileSync(path.join(root,'browser-report.json'),JSON.stringify({status:'PASS',checks,browser:browser.version(),fragment_sha256:crypto.createHash('sha256').update(fragment).digest('hex'),javascript_errors:errors,physical_android:'NOT_TESTED',inline_chat_host:'NOT_INDEPENDENTLY_EXECUTED',cdn:'QA fulfilled exact downloaded pinned D3 bytes; user CDN access not established',file_policy:'NOT_RETRIED_OR_BYPASSED'},null,2));console.log('PASS',checks.length);
}catch(e){fs.writeFileSync(path.join(root,'browser-report.json'),JSON.stringify({status:'FAIL',checks,error:e.stack},null,2));console.error(e);process.exitCode=1;}finally{if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));}})();
